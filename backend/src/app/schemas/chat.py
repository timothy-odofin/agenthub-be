from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    provider: Optional[str] = Field(
        None,
        description="LLM provider to use (e.g., 'openai', 'anthropic'). Falls back to system default if not provided.",
    )
    model: Optional[str] = Field(
        None,
        description="Specific model to use (e.g., 'gpt-4', 'claude-sonnet-4-5'). Falls back to provider's default if not provided.",
    )
    metadata: Optional[Dict[str, Any]] = (
        None  # For capability selection and other context
    )


class ActionPayload(BaseModel):
    """
    Structured action payload returned when the agent wants the frontend
    to perform a navigation or UI action (e.g., voice command "go to dashboard").

    This follows the pattern from novitari-ai-service where the backend emits
    action payloads that the frontend's action executor interprets and runs.

    action_type:
        - "NAVIGATE"   — Navigate to a different route/page
        - "UI_ACTION"   — Perform an in-page action (new chat, show capabilities, etc.)
        - "ERROR"       — The requested action could not be resolved

    action:
        - For NAVIGATE: { "route": "/path", "title": "Page Title", "protected": bool }
        - For UI_ACTION: { "name": "NEW_CHAT", "title": "Start New Chat" }

    message:
        Human-readable description of the action for the chat message.
    """

    action_type: str = Field(
        description="Type of action: NAVIGATE, UI_ACTION, or ERROR"
    )
    action: Dict[str, Any] = Field(
        default_factory=dict,
        description="Action details (route path, action name, etc.)",
    )
    message: str = Field(
        description="Human-readable description of the action",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Why the agent chose this action",
    )


class ChatResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    user_id: str
    timestamp: str
    processing_time_ms: float
    tools_used: List[str] = []
    errors: List[str] = []
    metadata: Dict[str, Any] = {}
    action: Optional[ActionPayload] = Field(
        default=None,
        description="Optional structured action for the frontend to execute "
        "(e.g., navigation, UI action). Present when the agent uses "
        "the navigate_to_route tool.",
    )


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None


class CreateSessionResponse(BaseModel):
    success: bool
    session_id: str
    title: str
    created_at: str
    errors: List[str] = []


class UpdateSessionTitleRequest(BaseModel):
    title: str


class UpdateSessionTitleResponse(BaseModel):
    success: bool
    session_id: str
    title: str
    message: Optional[str] = None


class SessionMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None
    id: Optional[str] = None


class SessionHistoryResponse(BaseModel):
    success: bool
    session_id: str
    messages: List[SessionMessage]
    count: int
    errors: List[str] = []


class SessionListItem(BaseModel):
    session_id: str
    title: str
    created_at: Optional[str] = None
    last_message_at: Optional[str] = None
    message_count: Optional[int] = None


class SessionListResponse(BaseModel):
    success: bool
    sessions: List[SessionListItem]
    total: int
    page: int
    limit: int
    has_more: bool
    errors: List[str] = []


class DeleteSessionResponse(BaseModel):
    success: bool
    session_id: str
    message: str
    deleted_at: str
