"""
Pydantic schemas for the MCP tools discovery endpoint.

These models describe the response shape of GET /api/v1/tools/mcp,
which exposes the backend's live ToolRegistry to thick clients such as
the JavaFX desktop application.
"""

from typing import List

from pydantic import BaseModel


class McpToolInfo(BaseModel):
    """A single tool exposed by a provider."""

    name: str
    description: str


class McpServerInfo(BaseModel):
    """
    A logical server entry grouping tools from one provider class.

    In most cases one category maps to one server (e.g. GitHub → one server
    with N tools). The list allows for future providers that register
    multiple server entries under the same category.
    """

    id: str
    name: str
    description: str
    tool_count: int
    tools: List[McpToolInfo]


class McpGroupInfo(BaseModel):
    """Tools grouped by their registry category (e.g. 'github', 'jira')."""

    category: str
    label: str
    servers: List[McpServerInfo]


class McpToolsResponse(BaseModel):
    """Top-level response returned by GET /api/v1/tools/mcp."""

    success: bool
    groups: List[McpGroupInfo]
