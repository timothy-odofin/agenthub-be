"""
Route Sync API — endpoints for frontend ↔ backend route synchronization.

The frontend owns the route definitions and pushes them to this API on
startup. The backend stores them in a JSON file (via FileStorageService)
so the LLM navigation tool can read them dynamically.

Endpoints:
──────────
  GET  /api/v1/routes          — Get currently synced routes
  POST /api/v1/routes/sync     — Push routes from frontend
  POST /api/v1/routes/action-completed — Notify backend that an action was executed

This eliminates the need to hardcode routes in the backend. When the
frontend adds a new page, it appears in the registry and gets synced
automatically — no backend change required.
"""

import logging

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.db.models.user import UserInDB
from app.infrastructure.storage import FileStorageService
from app.schemas.routes import (
    ActionCompletedRequest,
    ActionCompletedResponse,
    RouteDefinition,
    RouteListResponse,
    RouteSyncRequest,
    RouteSyncResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Single shared storage instance for routes
_route_storage = FileStorageService("routes")


@router.get("", response_model=RouteListResponse)
async def get_routes():
    """
    Get the currently synced routes from storage.

    No auth required — routes are public metadata (path, label, description).
    The frontend calls this on startup to compare against its local
    registry and determine which routes are new or changed.
    """
    data = _route_storage.load(default={"routes": []})
    routes = [RouteDefinition(**r) for r in data.get("routes", [])]

    return RouteListResponse(
        success=True,
        routes=routes,
        total=len(routes),
    )


@router.post("/sync", response_model=RouteSyncResponse)
async def sync_routes(
    req: RouteSyncRequest,
):
    """
    Sync routes from the frontend registry to backend storage.

    No auth required — routes are public metadata. The frontend sends
    its complete route list on every app startup. The backend replaces
    the stored routes with the incoming set. This is idempotent —
    sending the same routes twice has no adverse effect.

    The LLM navigation tool reads these routes at call-time, so any
    new routes are immediately available for voice/text navigation.
    """
    routes_data = [r.model_dump() for r in req.routes]

    saved = _route_storage.save({"routes": routes_data})

    if saved:
        logger.info(f"Routes synced: {len(routes_data)} routes")
        return RouteSyncResponse(
            success=True,
            synced_count=len(routes_data),
            message=f"Successfully synced {len(routes_data)} routes",
        )
    else:
        logger.error("Failed to save routes to storage")
        return RouteSyncResponse(
            success=False,
            synced_count=0,
            message="Failed to save routes to storage",
        )


@router.post("/action-completed", response_model=ActionCompletedResponse)
async def action_completed(
    req: ActionCompletedRequest,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Notify the backend that the frontend has completed an action.

    Inspired by novitari-ai-service's action completion loop where:
      1. Backend tells frontend what action to perform
      2. Frontend executes the action
      3. Frontend POSTs back here with the result
      4. Backend can use this for logging, analytics, or chaining actions

    For now this is a logging/acknowledgment endpoint. It can be extended
    to trigger follow-up actions or update agent context.
    """
    status = "succeeded" if req.success else "failed"
    action_desc = req.action_name or req.action_type

    logger.info(
        f"Action completed: {action_desc} {status} "
        f"(user={current_user.id}, session={req.session_id})"
    )

    return ActionCompletedResponse(
        success=True,
        message=f"Action '{action_desc}' completion acknowledged",
    )
