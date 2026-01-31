from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from app.core.enums import AgentStatus


@dataclass
class AgentContext:
    user_id: str
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False
    approval_callback: Optional[callable] = None
    timeout_seconds: Optional[int] = None
    max_iterations: int = 10
    tools_allowed: Optional[List[str]] = None
    tools_denied: Optional[List[str]] = None


@dataclass
class AgentResponse:
    content: str
    status: AgentStatus
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tools_used: List[str] = field(default_factory=list)
    processing_time_ms: float = 0
    token_usage: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def success(self) -> bool:
        return self.status not in [AgentStatus.ERROR, AgentStatus.CANCELLED]


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    result: Any
    error_message: Optional[str] = None
    execution_time_ms: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
