export interface SignupState {
  sessionId: string | null;
  currentStep: string | null;
  progress: number;
  fieldsRemaining: number;
  isComplete: boolean;
  accessToken: string | null;
}

export interface Message {
  text: string;
  isBot: boolean;
  timestamp: Date;
}

export interface LoginData {
  identifier: string;
  password: string;
}

export interface SendChatMessagePayload {
  message: string;
  session_id: string | null;
  provider: string;
  model: string;
  mcp_server_ids?: string[];
  metadata?: {
    capability_id?: string;
    is_capability_selection?: boolean;
    [key: string]: any;
  };
}

export interface ModelVersion {
  name: string;
  display_name: string;
  model_versions: string[];
  default_model: string;
  is_default: boolean;
}

export interface ProvidersResponse {
  success: boolean;
  providers: ModelVersion[];
  total: number;
}

export interface ChatSession {
  session_id: string;
  title: string;
  created_at?: string;
  last_message_at?: string;
  message_count?: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  id?: string;
}

// ─────────────────────────────────────────────────────────────────────
// MCP tool picker types  (mirrors GET /api/v1/tools/mcp response)
// ─────────────────────────────────────────────────────────────────────

export interface McpToolInfo {
  name: string;
  description: string;
}

export interface McpServerInfo {
  id: string;
  name: string;
  description: string;
  tool_count: number;
  tools: McpToolInfo[];
}

export interface McpGroupInfo {
  category: string;
  label: string;
  servers: McpServerInfo[];
}

export interface McpToolsResponse {
  success: boolean;
  groups: McpGroupInfo[];
}

// ─────────────────────────────────────────────────────────────────────
// Action types for voice/text-driven navigation (auto-sync architecture)
// ─────────────────────────────────────────────────────────────────────
// The backend LLM reads routes dynamically from routes.json (synced by
// the frontend on startup). When the agent detects navigation/action
// intent, it returns a structured ActionPayload in the chat response.
//
// Flow:
//   User speaks "delete this chat"
//     → LLM reads synced routes from routes.json
//       → LLM picks Dashboard route + DELETE action
//         → Backend returns ChatResponse with `action` field
//           → Frontend ActionExecutor executes the action
//           → Frontend POSTs /action-completed to notify backend
// ─────────────────────────────────────────────────────────────────────

/** The type of action the frontend should execute */
export type ActionType = "NAVIGATE" | "UI_ACTION" | "ERROR";

/** Action details for a pure NAVIGATE action (no in-page action) */
export interface NavigateActionDetail {
  route: string;
  title: string;
  protected: boolean;
}

/**
 * Action details for a UI_ACTION — in-page action with optional navigation.
 *
 * When the LLM picks an action (e.g., DELETE, SHARE, NEW_CHAT), the
 * action payload includes the route, the action name, and any params
 * the LLM inferred from context (e.g., session_id for DELETE).
 */
export interface UIActionDetail {
  route: string;
  title: string;
  protected: boolean;
  name: string;
  params: Record<string, any>;
}

/**
 * Structured action payload from the backend.
 * Present in ChatResponse when the agent uses the navigate_to_route tool.
 */
export interface ActionPayload {
  action_type: ActionType;
  action: NavigateActionDetail | UIActionDetail | Record<string, any>;
  message: string;
  reason?: string;
}

/**
 * Extended chat API response that includes the optional action field.
 * This is what the frontend receives from POST /api/v1/chat/message.
 */
export interface ChatApiResponse {
  success: boolean;
  message: string;
  session_id: string;
  user_id: string;
  timestamp: string;
  processing_time_ms: number;
  tools_used: string[];
  errors: string[];
  metadata: Record<string, any>;
  action?: ActionPayload | null;
}
