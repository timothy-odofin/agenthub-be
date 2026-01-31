from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatMessage:
    message_id: str
    session_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime