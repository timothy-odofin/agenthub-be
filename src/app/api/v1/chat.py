from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from app.schemas.chat import (
    ChatRequest, 
    ChatResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    SessionHistoryResponse,
    SessionListResponse,
    SessionMessage,
    SessionListItem
)
from app.services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()


@router.post("/message", response_model=ChatResponse)
async def send_message(req: ChatRequest):
    """
    Send a message to the AI agent.
    
    - **message**: The user's message/question
    - **user_id**: ID of the user sending the message  
    - **session_id**: Optional session ID. If not provided, creates a new session
    
    Returns the agent's response with metadata.
    """
    try:
        response = await chat_service.chat(
            message=req.message,
            user_id=req.user_id,
            session_id=req.session_id,
            protocol="rest"
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(req: CreateSessionRequest):
    """
    Create a new chat session.
    
    - **user_id**: ID of the user creating the session
    - **title**: Optional title for the session
    
    Returns the new session details.
    """
    try:
        session_id = chat_service.create_session(
            user_id=req.user_id,
            title=req.title
        )
        
        return CreateSessionResponse(
            success=True,
            session_id=session_id,
            title=req.title or f"Chat session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            created_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    user_id: str = Query(..., description="ID of the user"),
    limit: Optional[int] = Query(50, description="Maximum number of messages to return")
):
    """
    Get the message history for a specific session.
    
    - **session_id**: ID of the session
    - **user_id**: ID of the user (for authorization)
    - **limit**: Maximum number of messages to return (default: 50)
    
    Returns the session's message history.
    """
    try:
        messages = await chat_service.get_session_history(
            user_id=user_id,
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=SessionListResponse)
async def list_user_sessions(
    user_id: str = Query(..., description="ID of the user"),
    page: int = Query(0, description="Page number (0-based)"),
    limit: int = Query(10, description="Number of sessions per page")
):
    """
    List all chat sessions for a user.
    
    - **user_id**: ID of the user
    - **page**: Page number (0-based, default: 0)
    - **limit**: Number of sessions per page (default: 10)
    
    Returns paginated list of user's sessions.
    """
    try:
        sessions_data = chat_service.list_user_sessions(
            user_id=user_id,
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Check the health status of the chat service.
    
    Returns service health information including agent status and available tools.
    """
    try:
        health_status = chat_service.health_check()
        
        if health_status["status"] == "healthy":
            return health_status
        else:
            raise HTTPException(status_code=503, detail=health_status)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
