/**
 * Frontend Route Registry — source of truth for all navigable routes.
 *
 * This registry defines every route in the application along with metadata
 * that the backend LLM agent uses to match user intent to navigation actions.
 *
 * Auto-Sync Architecture:
 * ───────────────────────
 *   1. This file defines routes with labels, descriptions, and actions
 *   2. On app startup, useRouteSync() GETs current backend routes
 *   3. Compares with this registry — if different, POSTs the new set
 *   4. Backend stores in routes.json via FileStorageService
 *   5. LLM reads routes.json at tool-call time to match user intent
 *
 * To add a new route:
 *   1. Add the route to routes/index.tsx (React Router)
 *   2. Add an entry to ROUTE_REGISTRY below
 *   3. That's it — the sync hook will push it to the backend on next load
 *
 * No backend changes needed.
 */

export interface RouteRegistryEntry {
  /** React Router path (e.g., "/main-dashboard") */
  path: string;
  /** Human-readable name shown in navigation (e.g., "Dashboard") */
  label: string;
  /** Description of what the page does — the LLM uses this to match intent */
  description: string;
  /** Whether the route requires authentication */
  protected: boolean;
  /**
   * Actions available on this page.
   * The LLM picks from these based on user intent.
   * No aliases needed — the LLM decides based on semantics.
   */
  actions: string[];
}

/**
 * The complete route registry.
 *
 * Every route in the app should have an entry here. The sync hook
 * compares this against what the backend has stored and pushes
 * any new or changed routes automatically.
 */
export const ROUTE_REGISTRY: RouteRegistryEntry[] = [
  {
    path: "/",
    label: "Login",
    description: "Sign in to your account",
    protected: false,
    actions: [],
  },
  {
    path: "/signup",
    label: "Sign Up",
    description:
      "Create a new account via the conversational signup flow",
    protected: false,
    actions: [],
  },
  {
    path: "/main-dashboard",
    label: "Dashboard",
    description:
      "Main chat dashboard where you can chat with the AI agent, view sessions, " +
      "manage conversations, share chats, and explore agent capabilities",
    protected: true,
    actions: [
      "NEW_CHAT",
      "DELETE",
      "SHARE",
      "RENAME",
      "LOAD_SESSION",
      "SHOW_CAPABILITIES",
      "LOGOUT",
    ],
  },
];
