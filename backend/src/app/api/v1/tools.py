"""
MCP Tools API endpoint.

Exposes the backend's live ToolRegistry to authenticated clients so that
thick clients (e.g. the JavaFX desktop) can populate their tool-picker UI
with real, server-side data rather than hardcoded lists.

Route prefix (registered in main.py): /api/v1/tools
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends

from app.agent.tools.base.registry import ToolRegistry
from app.core.security import get_current_user
from app.db.models.user import UserInDB
from app.schemas.tools import McpGroupInfo, McpServerInfo, McpToolInfo, McpToolsResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Human-readable labels for the categories registered in ToolRegistry.
# Extend this dict whenever a new tool package is added to the registry.
# ---------------------------------------------------------------------------
_CATEGORY_LABELS: Dict[str, str] = {
    "github": "GitHub",
    "jira": "Jira",
    "confluence": "Confluence",
    "datadog": "Datadog",
    "vector": "Knowledge Base",
    "web": "Web",
    "navigation": "Navigation",
}


@router.get("/mcp", response_model=McpToolsResponse)
async def list_mcp_tools(
    current_user: UserInDB = Depends(get_current_user),
) -> McpToolsResponse:
    """
    Return all enabled MCP tool providers grouped by registry category.

    Each group contains one or more server entries.  Each server lists the
    tools it exposes (name + description).  Tools are sourced directly from
    the live ToolRegistry, so the response always reflects the current
    server configuration (enabled flags, tool_filter overrides, etc.).

    Requires a valid JWT Bearer token.  The endpoint is intentionally
    authenticated so that tool availability stays private to logged-in users.

    **Response shape:**
    ```json
    {
      "success": true,
      "groups": [
        {
          "category": "github",
          "label": "GitHub",
          "servers": [
            {
              "id": "github",
              "name": "GitHub",
              "description": "GitHub tools",
              "tool_count": 10,
              "tools": [
                { "name": "search_code", "description": "..." }
              ]
            }
          ]
        }
      ]
    }
    ```
    """
    groups: List[McpGroupInfo] = []

    for category in ToolRegistry.get_categories():
        tool_classes = ToolRegistry.get_tools_by_category(category)
        if not tool_classes:
            continue

        servers: List[McpServerInfo] = []

        for tool_class in tool_classes:
            class_name = getattr(tool_class, "__name__", repr(tool_class))
            try:
                provider = tool_class()
                langchain_tools = provider.get_tools()
            except Exception:
                logger.warning(
                    "Could not instantiate provider '%s' for category '%s' — skipping",
                    class_name,
                    category,
                )
                continue

            if not langchain_tools:
                logger.debug(
                    "Provider '%s' returned no tools for category '%s'",
                    class_name,
                    category,
                )
                continue

            tool_infos: List[McpToolInfo] = [
                McpToolInfo(
                    name=t.name,
                    description=t.description or "",
                )
                for t in langchain_tools
            ]

            display_name = _CATEGORY_LABELS.get(category, category.title())
            servers.append(
                McpServerInfo(
                    id=category,
                    name=display_name,
                    description=f"{display_name} tools",
                    tool_count=len(tool_infos),
                    tools=tool_infos,
                )
            )

        if servers:
            groups.append(
                McpGroupInfo(
                    category=category,
                    label=_CATEGORY_LABELS.get(category, category.title()),
                    servers=servers,
                )
            )

    return McpToolsResponse(success=True, groups=groups)
