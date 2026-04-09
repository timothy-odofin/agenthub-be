import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.capabilities import SystemCapabilities
from app.core.exceptions import InternalError, ServiceUnavailableError
from app.core.security import get_current_user
from app.db.models.user import UserInDB
from app.schemas.chat import (
    ActionPayload,
    ChatRequest,
    ChatResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    DeleteSessionResponse,
    SessionHistoryResponse,
    SessionListItem,
    SessionListResponse,
    SessionMessage,
    UpdateSessionTitleRequest,
    UpdateSessionTitleResponse,
)
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter()
chat_service = ChatService()


def _extract_action_from_response(
    response_text: str,
    tools_used: list,
    tool_outputs: Optional[dict] = None,
) -> Optional[ActionPayload]:
    """
    Extract a structured action payload from the agent's response.

    When the agent uses the navigate_to_route tool, the tool returns a JSON
    payload with action_type, action, and message. This function extracts
    that payload so the frontend can execute the action.

    Strategy:
      1. First, check the raw tool output (most reliable — it's the exact
         JSON our tool returned, unmodified by the LLM)
      2. Fall back to parsing JSON from the LLM's text response (the LLM
         sometimes embeds the JSON, but often reformulates it as prose)
    """
    # Only check if navigation tool was actually used
    if "navigate_to_route" not in tools_used:
        return None

    # Strategy 1: Use raw tool output (captured from intermediate_steps)
    if tool_outputs and "navigate_to_route" in tool_outputs:
        try:
            raw_output = tool_outputs["navigate_to_route"]
            if isinstance(raw_output, str):
                action_data = json.loads(raw_output)
            elif isinstance(raw_output, dict):
                action_data = raw_output
            else:
                action_data = None

            if action_data and "action_type" in action_data:
                logger.info(
                    f"Action extracted from tool output: {action_data.get('action_type')}"
                )
                return ActionPayload(**action_data)
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse action from tool output: {e}")

    # Strategy 2: Fall back to parsing JSON from response text
    try:
        start_markers = ['{"action_type":', '{ "action_type":']
        for marker in start_markers:
            idx = response_text.find(marker)
            if idx != -1:
                # Find the matching closing brace
                brace_count = 0
                for i in range(idx, len(response_text)):
                    if response_text[i] == "{":
                        brace_count += 1
                    elif response_text[i] == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = response_text[idx : i + 1]
                            action_data = json.loads(json_str)
                            return ActionPayload(**action_data)
                break

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning(f"Failed to parse action from response text: {e}")

    logger.warning(
        "navigate_to_route was used but action payload could not be extracted"
    )
    return None


@router.post("/message", response_model=ChatResponse)
async def send_message(
    req: ChatRequest, current_user: UserInDB = Depends(get_current_user)
):
    """
    Send a message to the AI agent.

    Requires authentication via JWT Bearer token.

    - **message**: The user's message/question
    - **session_id**: Optional session ID. If not provided, creates a new session
    - **provider**: Optional LLM provider (e.g., 'openai', 'anthropic'). Falls back to system default if not provided.
    - **model**: Optional specific model (e.g., 'gpt-4', 'claude-sonnet-4-5'). Falls back to provider's default if not provided.
    - **metadata**: Optional metadata for context (e.g., capability selection)

    Returns the agent's response with metadata.
    When the agent uses the navigate_to_route tool, the response includes an
    `action` field with a structured payload for the frontend to execute.

    Note: Provider/model parameters are reserved for future use. Currently uses system defaults.
    """
    response = await chat_service.chat(
        message=req.message,
        user_id=str(current_user.id),
        session_id=req.session_id,
        protocol="rest",
        provider=req.provider,
        model=req.model,
        metadata=req.metadata,
    )

    # Extract navigation/UI action from response if the agent used navigation tools
    tools_used = response.get("tools_used", [])
    metadata = response.get("metadata", {})
    tool_outputs = metadata.get("tool_outputs")
    action = _extract_action_from_response(
        response["message"], tools_used, tool_outputs
    )

    # Remove tool_outputs from metadata before sending to frontend (internal only)
    if "tool_outputs" in metadata:
        metadata = {k: v for k, v in metadata.items() if k != "tool_outputs"}

    return ChatResponse(
        success=response["success"],
        message=response["message"],
        session_id=response["session_id"],
        user_id=response["user_id"],
        timestamp=response["timestamp"],
        processing_time_ms=response["processing_time_ms"],
        tools_used=tools_used,
        errors=response.get("errors", []),
        metadata=metadata,
        action=action,
    )


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    req: CreateSessionRequest, current_user: UserInDB = Depends(get_current_user)
):
    """
    Create a new chat session.

    Requires authentication via JWT Bearer token.

    - **title**: Optional title for the session

    Returns the new session details.
    """
    session_id = chat_service.create_session(
        user_id=str(current_user.id), title=req.title
    )

    return CreateSessionResponse(
        success=True,
        session_id=session_id,
        title=req.title or chat_service.title_service.get_default_title(),
        created_at=datetime.now().isoformat(),
    )


@router.put("/sessions/{session_id}/title", response_model=UpdateSessionTitleResponse)
async def update_session_title(
    session_id: str,
    req: UpdateSessionTitleRequest,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Update the title of a chat session.

    Requires authentication via JWT Bearer token.

    - **session_id**: ID of the session to update
    - **title**: New title for the session

    Returns the updated session details.
    """
    success = await chat_service.update_session_title(
        user_id=str(current_user.id), session_id=session_id, title=req.title
    )

    if success:
        return UpdateSessionTitleResponse(
            success=True,
            session_id=session_id,
            title=req.title,
            message="Session title updated successfully",
        )
    else:
        return UpdateSessionTitleResponse(
            success=False,
            session_id=session_id,
            title=req.title,
            message="Failed to update session title",
        )


@router.delete("/sessions/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(
    session_id: str, current_user: UserInDB = Depends(get_current_user)
):
    """
    Delete a chat session and all its messages.

    Requires authentication via JWT Bearer token.

    - **session_id**: ID of the session to delete

    Returns confirmation of deletion with timestamp.
    Note: This action cannot be undone.
    """
    success = chat_service.delete_session(
        user_id=str(current_user.id), session_id=session_id
    )

    if success:
        return DeleteSessionResponse(
            success=True,
            session_id=session_id,
            message="Session and all associated messages deleted successfully",
            deleted_at=datetime.now().isoformat(),
        )
    else:
        return DeleteSessionResponse(
            success=False,
            session_id=session_id,
            message="Session not found or you don't have permission to delete it",
            deleted_at=datetime.now().isoformat(),
        )


@router.get("/sessions/{session_id}/messages", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    current_user: UserInDB = Depends(get_current_user),
    limit: Optional[int] = Query(
        50, description="Maximum number of messages to return"
    ),
):
    """
    Get the message history for a specific session.

    Requires authentication via JWT Bearer token.

    - **session_id**: ID of the session
    - **limit**: Maximum number of messages to return (default: 50)

    Returns the session's message history.
    """
    messages = await chat_service.get_session_history(
        user_id=str(current_user.id), session_id=session_id, limit=limit
    )

    session_messages = [
        SessionMessage(
            role=msg["role"],
            content=msg["content"],
            timestamp=msg.get("timestamp"),
            id=msg.get("id"),
        )
        for msg in messages
    ]

    return SessionHistoryResponse(
        success=True,
        session_id=session_id,
        messages=session_messages,
        count=len(session_messages),
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_user_sessions(
    current_user: UserInDB = Depends(get_current_user),
    page: int = Query(0, description="Page number (0-based)"),
    limit: int = Query(10, description="Number of sessions per page"),
):
    """
    List all chat sessions for a user.

    Requires authentication via JWT Bearer token.

    - **page**: Page number (0-based, default: 0)
    - **limit**: Number of sessions per page (default: 10)

    Returns paginated list of user's sessions.
    """
    sessions_data = chat_service.list_user_sessions(
        user_id=str(current_user.id), page=page, limit=limit
    )

    session_items = []
    for session in sessions_data.get("sessions", []):
        session_items.append(
            SessionListItem(
                session_id=session.get("session_id", ""),
                title=session.get("title", "Untitled Session"),
                created_at=session.get("created_at"),
                last_message_at=session.get("last_message_at"),
                message_count=session.get("message_count"),
            )
        )

    return SessionListResponse(
        success=True,
        sessions=session_items,
        total=sessions_data.get("total", 0),
        page=page,
        limit=limit,
        has_more=sessions_data.get("has_more", False),
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
    health_status = await chat_service.health_check()

    if health_status["status"] == "healthy":
        return health_status
    else:
        raise ServiceUnavailableError(
            service_name="chat_service",
            message="Chat service is unhealthy",
            details=health_status,
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
    capabilities = SystemCapabilities().get_capabilities(category=category)

    return {
        "success": True,
        "total": len(capabilities),
        "categories": SystemCapabilities().get_categories(),
        "capabilities": capabilities,
    }
