"""
Dynamic Navigation Tools — LLM-driven route resolution.

This module provides LangChain tools that let the AI agent navigate users
to pages and trigger UI actions. Instead of a hardcoded route map, routes
are synced dynamically from the frontend's route registry via the
FileStorageService.

Auto-Sync Architecture:
───────────────────────
  ┌──────────────┐  startup   ┌──────────────┐  routes.json  ┌─────────────┐
  │  Frontend    │───────────▶│  POST /sync  │──────────────▶│  File       │
  │  Route       │  push new/ │  Endpoint    │   persist     │  Storage    │
  │  Registry    │  changed   └──────────────┘               │  Service    │
  └──────────────┘                                            └──────┬──────┘
                                                                     │ read
  ┌──────────────┐  action     ┌──────────────┐  picks best   ┌─────▼──────┐
  │  Frontend    │◀────────────│  Chat API    │◀──────────────│  LLM Agent │
  │  Action      │  payload    │  (extract)   │  route/action │  Nav Tool  │
  │  Executor    │             └──────────────┘               └────────────┘

Key Design Decisions:
─────────────────────
1. No hardcoded routes — all routes come from routes.json (synced by frontend)
2. No aliases — the LLM decides the best match based on user intent
3. Actions are listed per-route (e.g., Dashboard has DELETE, SHARE, NEW_CHAT)
4. The LLM reads the full route list at tool-call time, so new pages
   are immediately available after the next frontend sync
"""

import json
from typing import Any, Dict, List, Optional

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from app.agent.tools.base.registry import ToolRegistry
from app.core.utils.logger import get_logger
from app.infrastructure.storage import FileStorageService

logger = get_logger(__name__)

# Shared storage instance — same file the /api/v1/routes/sync endpoint writes to
_route_storage = FileStorageService("routes")


def _load_synced_routes() -> List[Dict[str, Any]]:
    """
    Load routes from the synced routes.json file.

    Returns an empty list if no routes have been synced yet.
    """
    data = _route_storage.load(default={"routes": []})
    return data.get("routes", [])


def _format_routes_for_llm() -> str:
    """
    Format the current routes as a readable string for the LLM tool description.

    This is called at tool-creation time AND can be refreshed when the
    tool is invoked. The LLM reads this to decide which route/action matches.
    """
    routes = _load_synced_routes()

    if not routes:
        return (
            "No routes are currently synced from the frontend. "
            "The application needs to start and sync its routes first."
        )

    lines = ["Available pages and actions in the application:"]
    for route in routes:
        actions_str = ", ".join(route.get("actions", []))
        protected_str = " [requires login]" if route.get("protected") else ""
        lines.append(
            f"  - {route['label']} ({route['path']}){protected_str}: "
            f"{route['description']}"
        )
        if actions_str:
            lines.append(f"    Actions: {actions_str}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
# Pydantic input schemas for tool arguments
# ─────────────────────────────────────────────────────────────────────


class NavigateInput(BaseModel):
    """Input schema for navigate_to_route tool."""

    route_path: str = Field(
        description=(
            "The path of the route to navigate to (e.g., '/main-dashboard', '/signup'). "
            "Use the exact path from the available routes list."
        )
    )
    action_name: Optional[str] = Field(
        default=None,
        description=(
            "Optional action to perform on the target page "
            "(e.g., 'NEW_CHAT', 'DELETE', 'SHARE', 'RENAME', 'LOAD_SESSION', 'LOGOUT'). "
            "Only use actions listed for that route."
        ),
    )
    action_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional parameters for the action. For example: "
            '{"session_id": "abc123"} for DELETE, '
            '{"title": "My Chat"} for LOAD_SESSION, '
            '{"session_id": "abc123", "new_title": "Renamed"} for RENAME.'
        ),
    )
    reason: Optional[str] = Field(
        default=None,
        description="Brief explanation of why this navigation/action was chosen",
    )


class ListRoutesInput(BaseModel):
    """Input schema for list_available_routes tool."""

    category: Optional[str] = Field(
        default=None,
        description="Filter routes by 'protected' or 'public'. Leave empty for all routes.",
    )


# ─────────────────────────────────────────────────────────────────────
# Tool provider class
# ─────────────────────────────────────────────────────────────────────


@ToolRegistry.register("navigation", "navigation")
class NavigationTools:
    """
    Dynamic navigation tools for the AI agent.

    Routes are loaded from routes.json (synced by the frontend) at call-time.
    The LLM decides the best route/action match — no hardcoded aliases needed.

    Provides two tools:
    1. navigate_to_route — Navigate to a page and/or trigger a UI action
    2. list_available_routes — List all available routes and their actions
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize NavigationTools (config accepted for registry compatibility)."""
        self.config = config or {}

    @staticmethod
    def get_tools() -> List[StructuredTool]:
        """Return all navigation tools."""
        return [
            NavigationTools._create_navigate_tool(),
            NavigationTools._create_list_routes_tool(),
        ]

    @staticmethod
    def _create_navigate_tool() -> StructuredTool:
        """Create the navigate_to_route tool."""

        def navigate_to_route(
            route_path: str,
            action_name: Optional[str] = None,
            action_params: Optional[Dict[str, Any]] = None,
            reason: Optional[str] = None,
        ) -> str:
            """
            Navigate the user to a specific page or trigger a page action.

            ALWAYS use this tool when the user wants to:
            - Go to a different page (e.g., "go to dashboard", "take me to signup")
            - Perform an action on a page (e.g., "start new chat", "delete this session",
              "log out", "sign out")
            - Both navigate AND act (e.g., "go to dashboard and start a new chat")

            This tool loads routes dynamically — call it to discover what's available.
            Pass the route path and optional action name.
            """
            routes = _load_synced_routes()

            # Provide the LLM with current route info as part of the output
            # so it can self-correct if it picked a wrong path
            route_info = _format_routes_for_llm()
            logger.info(
                f"Navigation tool called: path={route_path}, action={action_name}, "
                f"available_routes={len(routes)}"
            )

            if not routes:
                return json.dumps(
                    {
                        "action_type": "ERROR",
                        "action": {},
                        "message": "No routes are currently synced from the frontend. "
                        "The application needs to start and sync its routes first.",
                    }
                )

            route_path_clean = route_path.strip()

            # Find the matching route
            matched_route = None
            for route in routes:
                if route["path"] == route_path_clean:
                    matched_route = route
                    break

            if not matched_route:
                # Try partial match (e.g., user said "/dashboard" but route is "/main-dashboard")
                # Skip trivially short paths like "/" to avoid false positives.
                for route in routes:
                    route_path_val = route["path"]
                    if len(route_path_val) <= 1 or len(route_path_clean) <= 1:
                        continue  # Skip root "/" partial matches
                    if (
                        route_path_clean in route_path_val
                        or route_path_val in route_path_clean
                    ):
                        matched_route = route
                        break

            if not matched_route:
                available = [f"{r['label']} ({r['path']})" for r in routes]
                logger.warning(f"Navigation tool: no match for path={route_path_clean}")
                return json.dumps(
                    {
                        "action_type": "ERROR",
                        "action": {},
                        "message": f"No route found for '{route_path}'. Available: {', '.join(available) or 'none (routes not synced yet)'}",
                    }
                )

            # Determine action type
            if action_name:
                # Validate the action is available for this route
                available_actions = matched_route.get("actions", [])
                if action_name.upper() not in [a.upper() for a in available_actions]:
                    logger.warning(
                        f"Action '{action_name}' not available on {matched_route['path']}. "
                        f"Available: {available_actions}"
                    )
                    return json.dumps(
                        {
                            "action_type": "ERROR",
                            "action": {},
                            "message": (
                                f"Action '{action_name}' is not available on {matched_route['label']}. "
                                f"Available actions: {', '.join(available_actions) or 'none'}"
                            ),
                        }
                    )

                # Build action payload
                action_payload = {
                    "action_type": "UI_ACTION",
                    "action": {
                        "route": matched_route["path"],
                        "title": matched_route["label"],
                        "protected": matched_route.get("protected", False),
                        "name": action_name.upper(),
                        "params": action_params or {},
                    },
                    "message": f"Executing {action_name} on {matched_route['label']}",
                }
            else:
                # Pure navigation
                action_payload = {
                    "action_type": "NAVIGATE",
                    "action": {
                        "route": matched_route["path"],
                        "title": matched_route["label"],
                        "protected": matched_route.get("protected", False),
                    },
                    "message": f"Navigating to {matched_route['label']} ({matched_route['path']})",
                }

            if reason:
                action_payload["reason"] = reason

            logger.info(
                f"Navigation tool: type={action_payload['action_type']}, "
                f"path={matched_route['path']}, action={action_name}"
            )

            return json.dumps(action_payload)

        return StructuredTool.from_function(
            func=navigate_to_route,
            name="navigate_to_route",
            description=(
                "Navigate the user to a page or trigger a UI action. ALWAYS use this "
                "tool when the user wants to go somewhere, start a new chat, delete a "
                "session, share, rename, log out, sign out, or perform any UI operation. "
                "The tool loads available routes dynamically at call-time. "
                "Common routes: / (Login), /signup (Sign Up), /main-dashboard (Dashboard). "
                "Common actions on Dashboard: NEW_CHAT, DELETE, SHARE, RENAME, "
                "LOAD_SESSION, SHOW_CAPABILITIES, LOGOUT."
            ),
            args_schema=NavigateInput,
            return_direct=False,
        )

    @staticmethod
    def _create_list_routes_tool() -> StructuredTool:
        """Create the list_available_routes tool."""

        def list_available_routes(category: Optional[str] = None) -> str:
            """
            List all available routes and actions in the application.

            Use this when the user asks what pages are available, what they
            can do, or when you need to find the right page/action to suggest.

            The routes are loaded dynamically from the frontend's synced registry.
            """
            routes = _load_synced_routes()
            result = {"routes": []}

            for route in routes:
                is_protected = route.get("protected", False)

                if category == "protected" and not is_protected:
                    continue
                if category == "public" and is_protected:
                    continue

                result["routes"].append(
                    {
                        "path": route["path"],
                        "label": route["label"],
                        "description": route["description"],
                        "protected": is_protected,
                        "actions": route.get("actions", []),
                    }
                )

            return json.dumps(result, indent=2)

        return StructuredTool.from_function(
            func=list_available_routes,
            name="list_available_routes",
            description=(
                "List all pages and UI actions available in the application. "
                "Use when the user asks 'where can I go?', 'what can I do?', "
                "or 'what pages are available?'. Routes are loaded dynamically "
                "from the frontend's synced registry."
            ),
            args_schema=ListRoutesInput,
            return_direct=False,
        )
