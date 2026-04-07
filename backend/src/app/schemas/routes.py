"""
Route sync schemas.

These models define the contract between the frontend route registry
and the backend route storage. The frontend pushes its routes on startup,
and the backend stores them so the LLM agent can read them dynamically.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RouteDefinition(BaseModel):
    """
    A single route definition synced from the frontend.

    This is the metadata the LLM reads to decide which route/action
    matches a user's intent. The frontend owns these definitions
    and pushes them to the backend on startup.
    """

    path: str = Field(description="React Router path (e.g., '/main-dashboard')")
    label: str = Field(description="Human-readable name (e.g., 'Dashboard')")
    description: str = Field(
        description="What this page does — the LLM uses this to match intent"
    )
    protected: bool = Field(
        default=False,
        description="Whether the route requires authentication",
    )
    actions: List[str] = Field(
        default_factory=list,
        description="Available actions on this page (e.g., ['NEW_CHAT', 'DELETE', 'SHARE']). "
        "The LLM picks from these based on user intent.",
    )


class RouteSyncRequest(BaseModel):
    """
    Request body for POST /api/v1/routes/sync.

    The frontend sends its full route registry. The backend compares
    with what's stored and updates accordingly.
    """

    routes: List[RouteDefinition] = Field(
        description="Complete list of routes from the frontend registry"
    )


class RouteSyncResponse(BaseModel):
    """Response from a route sync operation."""

    success: bool
    synced_count: int = Field(description="Number of routes stored")
    message: str


class RouteListResponse(BaseModel):
    """Response for GET /api/v1/routes — returns currently synced routes."""

    success: bool
    routes: List[RouteDefinition]
    total: int


class ActionCompletedRequest(BaseModel):
    """
    Request body for POST /api/v1/routes/action-completed.

    After the frontend executes an action (navigate, delete session, etc.),
    it notifies the backend so the agent can continue the conversation
    with awareness of what happened.

    Inspired by novitari-ai-service's action completion loop.
    """

    action_type: str = Field(
        description="The action that was executed (e.g., 'NAVIGATE', 'DELETE')"
    )
    action_name: Optional[str] = Field(
        default=None,
        description="Specific action name (e.g., 'DELETE', 'SHARE', 'NEW_CHAT')",
    )
    success: bool = Field(description="Whether the action completed successfully")
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Any result data from the action execution",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="The chat session ID for context",
    )
    message: Optional[str] = Field(
        default=None,
        description="Human-readable summary of what happened",
    )


class ActionCompletedResponse(BaseModel):
    """Response acknowledging an action completion notification."""

    success: bool
    message: str
