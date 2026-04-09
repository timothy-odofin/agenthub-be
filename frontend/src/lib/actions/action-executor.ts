/**
 * Action Executor for Voice/Text-Driven Navigation (Auto-Sync Architecture)
 * ════════════════════════════════════════════════════════════════════════════
 *
 * Processes structured action payloads from the backend LLM agent and
 * executes them in the frontend. The LLM reads routes dynamically from
 * routes.json (synced by the frontend on startup) and picks the best
 * route + action match based on user intent.
 *
 *   ┌──────────┐    ┌──────────┐    ┌────────────┐    ┌───────────────┐
 *   │  User    │───▶│  LLM     │───▶│  API       │───▶│  Action       │
 *   │  "delete │    │  reads   │    │  Response  │    │  Executor     │
 *   │  this    │    │  synced  │    │  + action  │    │  (this file)  │
 *   │  chat"   │    │  routes  │    │  payload   │    │               │
 *   └──────────┘    └──────────┘    └────────────┘    └───────┬───────┘
 *                                                             │
 *                                                    ┌────────▼───────┐
 *                                                    │  POST          │
 *                                                    │  /action-      │
 *                                                    │  completed     │
 *                                                    └────────────────┘
 *
 * Supported action types:
 *   NAVIGATE       — Route the user to a different page
 *   UI_ACTION      — Perform an in-page action:
 *     NEW_CHAT        — Start a fresh chat session
 *     DELETE          — Delete a chat session
 *     SHARE           — Open the share modal
 *     RENAME          — Rename a session
 *     LOAD_SESSION    — Load a session by title
 *     SHOW_CAPABILITIES — Show capabilities view
 *     LOGOUT          — Clear tokens and redirect to login
 *
 * To extend: Add a new case to handleUIAction and register the action
 * in the route registry (routes/registry.ts). No backend changes needed.
 */

import type { ActionPayload, NavigateActionDetail, UIActionDetail } from "@/types";
import { notifyActionCompleted } from "@/api/routes";
import { logout } from "@/utils/auth";

// ─────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────

/** Callbacks the ChatLayout provides so the executor can drive the UI */
export interface ActionHandlers {
  /** React Router navigate function */
  navigate: (path: string) => void;
  /** Start a new chat (clear messages, reset session) */
  startNewChat: () => void;
  /** Delete a session by ID */
  deleteSession: (sessionId: string) => void;
  /** Open the share modal for a session */
  shareSession: (sessionId: string) => void;
  /** Rename a session */
  renameSession: (sessionId: string, newTitle: string) => void;
  /** Load/open a session (by session ID) */
  openSession: (sessionId: string) => void;
  /** Get the current session ID */
  getCurrentSessionId: () => string | null;
  /** Show a toast/notification to the user */
  showToast?: (message: string, type?: "success" | "error" | "info") => void;
}

/** Result of executing an action */
export interface ActionResult {
  executed: boolean;
  actionType: string;
  actionName?: string;
  message: string;
}

// ─────────────────────────────────────────────────────────────────────
// Action Completion — notify backend after executing an action
// ─────────────────────────────────────────────────────────────────────

async function reportActionCompleted(
  actionType: string,
  actionName: string | undefined,
  success: boolean,
  sessionId?: string | null,
  message?: string
) {
  try {
    await notifyActionCompleted({
      action_type: actionType,
      action_name: actionName,
      success,
      session_id: sessionId ?? undefined,
      message,
    });
  } catch {
    // Non-fatal — action completion notification is best-effort
    console.warn("⚠️ Failed to report action completion (non-fatal)");
  }
}

// ─────────────────────────────────────────────────────────────────────
// Action Handlers
// ─────────────────────────────────────────────────────────────────────

/**
 * Handle a NAVIGATE action — route the user to a different page.
 */
function handleNavigate(
  action: NavigateActionDetail,
  handlers: ActionHandlers,
  message: string
): ActionResult {
  const { route, title, protected: isProtected } = action;

  // Check auth for protected routes
  if (isProtected) {
    const token = localStorage.getItem("access_token");
    if (!token) {
      handlers.showToast?.(
        `Cannot navigate to ${title} — you need to log in first.`,
        "error"
      );
      reportActionCompleted("NAVIGATE", undefined, false, null, "Auth required");
      return {
        executed: false,
        actionType: "NAVIGATE",
        message: `Authentication required for ${title}`,
      };
    }
  }

  console.log(`🧭 Action Executor: Navigating to ${route} (${title})`);
  handlers.navigate(route);
  handlers.showToast?.(`Navigated to ${title}`, "success");
  reportActionCompleted("NAVIGATE", undefined, true, null, `Navigated to ${title}`);

  return {
    executed: true,
    actionType: "NAVIGATE",
    message,
  };
}

/**
 * Handle a UI_ACTION — perform an in-page action.
 *
 * The action includes a `name` field (e.g., "DELETE", "SHARE")
 * and optional `params` (e.g., { session_id: "abc123" }).
 */
function handleUIAction(
  action: UIActionDetail,
  handlers: ActionHandlers,
  message: string
): ActionResult {
  const { name, params, route, title, protected: isProtected } = action;
  const currentSessionId = handlers.getCurrentSessionId();

  // Check auth for protected routes
  if (isProtected) {
    const token = localStorage.getItem("access_token");
    if (!token) {
      handlers.showToast?.(
        `Cannot perform ${name} on ${title} — you need to log in first.`,
        "error"
      );
      reportActionCompleted("UI_ACTION", name, false, currentSessionId, "Auth required");
      return {
        executed: false,
        actionType: "UI_ACTION",
        actionName: name,
        message: `Authentication required for ${title}`,
      };
    }
  }

  // If the action is on a different page, navigate first
  const currentPath = window.location.pathname;
  const targetBasePath = route.replace(/\/:.*$/, ""); // Remove dynamic params
  if (!currentPath.startsWith(targetBasePath)) {
    console.log(`🧭 Action Executor: Navigating to ${route} before ${name}`);
    handlers.navigate(route);
  }

  switch (name) {
    case "NEW_CHAT": {
      console.log("🧭 Action Executor: Starting new chat");
      handlers.startNewChat();
      handlers.showToast?.("Started a new chat", "success");
      reportActionCompleted("UI_ACTION", "NEW_CHAT", true, currentSessionId);
      return { executed: true, actionType: "UI_ACTION", actionName: "NEW_CHAT", message };
    }

    case "DELETE": {
      const sessionId = params?.session_id || currentSessionId;
      if (!sessionId) {
        handlers.showToast?.("No session to delete", "error");
        reportActionCompleted("UI_ACTION", "DELETE", false, null, "No session ID");
        return {
          executed: false,
          actionType: "UI_ACTION",
          actionName: "DELETE",
          message: "No session to delete — no active session",
        };
      }
      console.log(`🧭 Action Executor: Deleting session ${sessionId}`);
      handlers.deleteSession(sessionId);
      reportActionCompleted("UI_ACTION", "DELETE", true, sessionId);
      return { executed: true, actionType: "UI_ACTION", actionName: "DELETE", message };
    }

    case "SHARE": {
      const sessionId = params?.session_id || currentSessionId;
      if (!sessionId) {
        handlers.showToast?.("No session to share", "error");
        reportActionCompleted("UI_ACTION", "SHARE", false, null, "No session ID");
        return {
          executed: false,
          actionType: "UI_ACTION",
          actionName: "SHARE",
          message: "No session to share — no active session",
        };
      }
      console.log(`🧭 Action Executor: Sharing session ${sessionId}`);
      handlers.shareSession(sessionId);
      handlers.showToast?.("Opening share options", "info");
      reportActionCompleted("UI_ACTION", "SHARE", true, sessionId);
      return { executed: true, actionType: "UI_ACTION", actionName: "SHARE", message };
    }

    case "RENAME": {
      const sessionId = params?.session_id || currentSessionId;
      const newTitle = params?.new_title;
      if (!sessionId) {
        handlers.showToast?.("No session to rename", "error");
        reportActionCompleted("UI_ACTION", "RENAME", false, null, "No session ID");
        return {
          executed: false,
          actionType: "UI_ACTION",
          actionName: "RENAME",
          message: "No session to rename — no active session",
        };
      }
      if (!newTitle) {
        handlers.showToast?.("No new title provided", "error");
        reportActionCompleted("UI_ACTION", "RENAME", false, sessionId, "No title");
        return {
          executed: false,
          actionType: "UI_ACTION",
          actionName: "RENAME",
          message: "Cannot rename — no new title was provided",
        };
      }
      console.log(`🧭 Action Executor: Renaming session ${sessionId} to "${newTitle}"`);
      handlers.renameSession(sessionId, newTitle);
      handlers.showToast?.(`Renamed to "${newTitle}"`, "success");
      reportActionCompleted("UI_ACTION", "RENAME", true, sessionId);
      return { executed: true, actionType: "UI_ACTION", actionName: "RENAME", message };
    }

    case "LOAD_SESSION": {
      const sessionId = params?.session_id;
      if (!sessionId) {
        handlers.showToast?.("No session specified to load", "error");
        reportActionCompleted("UI_ACTION", "LOAD_SESSION", false, null, "No session ID");
        return {
          executed: false,
          actionType: "UI_ACTION",
          actionName: "LOAD_SESSION",
          message: "Cannot load session — no session ID provided",
        };
      }
      console.log(`🧭 Action Executor: Loading session ${sessionId}`);
      handlers.openSession(sessionId);
      handlers.showToast?.("Loading session", "info");
      reportActionCompleted("UI_ACTION", "LOAD_SESSION", true, sessionId);
      return { executed: true, actionType: "UI_ACTION", actionName: "LOAD_SESSION", message };
    }

    case "SHOW_CAPABILITIES": {
      console.log("🧭 Action Executor: Showing capabilities");
      handlers.startNewChat(); // Starting a new chat shows capabilities view
      handlers.showToast?.("Showing capabilities", "info");
      reportActionCompleted("UI_ACTION", "SHOW_CAPABILITIES", true, currentSessionId);
      return { executed: true, actionType: "UI_ACTION", actionName: "SHOW_CAPABILITIES", message };
    }

    case "LOGOUT": {
      console.log("🧭 Action Executor: Logging out");
      handlers.showToast?.("Logging out...", "info");
      reportActionCompleted("UI_ACTION", "LOGOUT", true, currentSessionId);
      // Small delay so the toast is visible before redirect
      setTimeout(() => logout(), 500);
      return { executed: true, actionType: "UI_ACTION", actionName: "LOGOUT", message };
    }

    default: {
      console.warn(`🧭 Action Executor: Unknown UI action "${name}"`);
      handlers.showToast?.(`Unknown action: ${name}`, "error");
      reportActionCompleted("UI_ACTION", name, false, currentSessionId, "Unknown action");
      return {
        executed: false,
        actionType: "UI_ACTION",
        actionName: name,
        message: `Unknown UI action: ${name}`,
      };
    }
  }
}

// ─────────────────────────────────────────────────────────────────────
// Main Executor
// ─────────────────────────────────────────────────────────────────────

/**
 * Execute a structured action payload from the backend.
 *
 * Call this after receiving a chat API response that includes an `action` field.
 *
 * @param action   — The action payload from the API response
 * @param handlers — Callbacks to drive the UI (navigate, delete, share, etc.)
 * @returns ActionResult with execution status
 *
 * @example
 * ```ts
 * const res = await sendChatMessage(payload);
 * if (res.data?.action) {
 *   const result = executeAction(res.data.action, actionHandlers);
 *   console.log(result.executed ? "Action done!" : "Action failed");
 * }
 * ```
 */
export function executeAction(
  action: ActionPayload,
  handlers: ActionHandlers
): ActionResult {
  console.log("🧭 Action Executor: Processing action", action);

  switch (action.action_type) {
    case "NAVIGATE":
      return handleNavigate(
        action.action as NavigateActionDetail,
        handlers,
        action.message
      );

    case "UI_ACTION":
      return handleUIAction(
        action.action as UIActionDetail,
        handlers,
        action.message
      );

    case "ERROR":
      console.warn("🧭 Action Executor: Action error —", action.message);
      handlers.showToast?.(action.message, "error");
      return {
        executed: false,
        actionType: "ERROR",
        message: action.message,
      };

    default:
      console.warn("🧭 Action Executor: Unknown action type —", action.action_type);
      return {
        executed: false,
        actionType: action.action_type,
        message: `Unknown action type: ${action.action_type}`,
      };
  }
}
