from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatSession:
    session_id: str
    title: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, any]