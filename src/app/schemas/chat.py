from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # For capability selection and other context

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
