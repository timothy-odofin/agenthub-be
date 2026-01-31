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
