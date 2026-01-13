from fastapi import APIRouter, Query, Depends
from typing import Optional
from datetime import datetime

from app.schemas.chat import (
    ChatRequest, 
    ChatResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    UpdateSessionTitleRequest,
    UpdateSessionTitleResponse,
    SessionHistoryResponse,
    SessionListResponse,
    SessionMessage,
    SessionListItem
)
from app.services.chat_service import ChatService
from app.core.security import get_current_user
from app.db.models.user import UserInDB
from app.core.exceptions import ServiceUnavailableError, InternalError

router = APIRouter()
chat_service = ChatService()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    req: ChatRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Send a message to the AI agent.
    
    Requires authentication via JWT Bearer token.
    
    - **message**: The user's message/question
    - **session_id**: Optional session ID. If not provided, creates a new session
    - **metadata**: Optional metadata for context (e.g., capability selection)
    
    Returns the agent's response with metadata.
    """
    response = await chat_service.chat(
        message=req.message,
        user_id=str(current_user.id),
        session_id=req.session_id,
        protocol="rest",
        metadata=req.metadata
    )
    
    return ChatResponse(
        success=response["success"],
        message=response["message"],
        session_id=response["session_id"],
        user_id=response["user_id"],
        timestamp=response["timestamp"],
        processing_time_ms=response["processing_time_ms"],
        tools_used=response.get("tools_used", []),
        errors=response.get("errors", []),
        metadata=response.get("metadata", {})
    )


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    req: CreateSessionRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Create a new chat session.
    
    Requires authentication via JWT Bearer token.
    
    - **title**: Optional title for the session
    
    Returns the new session details.
    """
    session_id = chat_service.create_session(
        user_id=str(current_user.id),
        title=req.title
    )
    
    return CreateSessionResponse(
        success=True,
        session_id=session_id,
        title=req.title or chat_service.title_service.get_default_title(),
        created_at=datetime.now().isoformat()
    )


@router.put("/sessions/{session_id}/title", response_model=UpdateSessionTitleResponse)
async def update_session_title(
    session_id: str,
    req: UpdateSessionTitleRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Update the title of a chat session.
    
    Requires authentication via JWT Bearer token.
    
    - **session_id**: ID of the session to update
    - **title**: New title for the session
    
    Returns the updated session details.
    """
    success = await chat_service.update_session_title(
        user_id=str(current_user.id),
        session_id=session_id,
        title=req.title
    )
    
    if success:
        return UpdateSessionTitleResponse(
            success=True,
            session_id=session_id,
            title=req.title,
            message="Session title updated successfully"
        )
    else:
        return UpdateSessionTitleResponse(
            success=False,
            session_id=session_id,
            title=req.title,
            message="Failed to update session title"
        )


@router.get("/sessions/{session_id}/messages", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    current_user: UserInDB = Depends(get_current_user),
    limit: Optional[int] = Query(50, description="Maximum number of messages to return")
):
    """
    Get the message history for a specific session.
    
    Requires authentication via JWT Bearer token.
    
    - **session_id**: ID of the session
    - **limit**: Maximum number of messages to return (default: 50)
    
    Returns the session's message history.
    """
    messages = await chat_service.get_session_history(
        user_id=str(current_user.id),
        session_id=session_id,
        limit=limit
    )
    
    session_messages = [
        SessionMessage(
            role=msg["role"],
            content=msg["content"],
            timestamp=msg.get("timestamp"),
            id=msg.get("id")
        )
        for msg in messages
    ]
    
    return SessionHistoryResponse(
        success=True,
        session_id=session_id,
        messages=session_messages,
        count=len(session_messages)
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_user_sessions(
    current_user: UserInDB = Depends(get_current_user),
    page: int = Query(0, description="Page number (0-based)"),
    limit: int = Query(10, description="Number of sessions per page")
):
    """
    List all chat sessions for a user.
    
    Requires authentication via JWT Bearer token.
    
    - **page**: Page number (0-based, default: 0)
    - **limit**: Number of sessions per page (default: 10)
    
    Returns paginated list of user's sessions.
    """
    sessions_data = chat_service.list_user_sessions(
        user_id=str(current_user.id),
        page=page,
        limit=limit
    )
    
    session_items = []
    for session in sessions_data.get("sessions", []):
        session_items.append(
            SessionListItem(
                session_id=session.get("session_id", ""),
                title=session.get("title", "Untitled Session"),
                created_at=session.get("created_at"),
                last_message_at=session.get("last_message_at"),
                message_count=session.get("message_count")
            )
        )
    
    return SessionListResponse(
        success=True,
        sessions=session_items,
        total=sessions_data.get("total", 0),
        page=page,
        limit=limit,
        has_more=sessions_data.get("has_more", False)
    )


@router.get("/health")
async def health_check():
    """
    Check the health status of the chat service.
    
    Returns service health information including agent status and available tools.
    
    Raises:
        ServiceUnavailableError: If service is unhealthy
        InternalError: If health check fails
    """
    try:
        health_status = chat_service.health_check()
        
        if health_status["status"] == "healthy":
            return health_status
        else:
            raise ServiceUnavailableError(
                service_name="chat_service",
                message="Chat service is unhealthy",
                details=health_status
            )
            
    except ServiceUnavailableError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        raise InternalError(
            message="Health check failed",
            internal_details={"error": str(e), "type": type(e).__name__}
        )


@router.get("/capabilities")
async def get_capabilities(
    category: Optional[str] = Query(None, description="Filter by capability category")
):
    """
    Get agent capabilities based on enabled tools.
    
    Returns a list of capabilities that the agent can perform,
    derived from currently enabled and configured tools.
    
    This endpoint is public (no authentication required) so clients
    can display capabilities before login.
    
    - **category**: Optional filter to get capabilities for specific category only
    
    Returns:
        List of capability objects with display metadata
    """
    from app.core.capabilities import SystemCapabilities
    
    try:
        capabilities = SystemCapabilities().get_capabilities(category=category)
        
        return {
            "success": True,
            "total": len(capabilities),
            "categories": SystemCapabilities().get_categories(),
            "capabilities": capabilities
        }
        
    except Exception as e:
        raise InternalError(
            message="Failed to retrieve capabilities",
            internal_details={"error": str(e), "type": type(e).__name__}
        )
