"""
Unit tests for GET /api/v1/tools/mcp endpoint.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_tool(name: str, description: str = "A tool"):
    """Return a lightweight mock resembling a ToolRegistry tool entry."""
    tool = MagicMock()
    tool.name = name
    tool.description = description
    return tool


def _make_mock_provider(tools: list):
    """Return a mock MCP provider that yields the given tools."""
    provider = MagicMock()
    provider.get_tools = MagicMock(return_value=tools)
    return provider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_tool_registry():
    """Patch ToolRegistry so the endpoint is independent of real providers."""
    with patch("src.app.api.v1.tools.ToolRegistry") as MockRegistry:
        registry_instance = MockRegistry.return_value
        yield registry_instance


@pytest.fixture
def authed_client():
    """Return a TestClient with a dummy JWT injected via override."""
    from src.app.core.auth import get_current_user
    from src.app.main import app

    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.email = "test@example.com"

    app.dependency_overrides[get_current_user] = lambda: mock_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMcpToolsEndpoint:
    """Test suite for GET /api/v1/tools/mcp."""

    def test_returns_200_with_groups(self, authed_client, mock_tool_registry):
        """Endpoint returns HTTP 200 and a 'groups' list when providers are available."""
        tool = _make_mock_tool("search", "Search the web")
        provider = _make_mock_provider([tool])

        mock_tool_registry.get_categories.return_value = {
            "knowledge": [("web-search", "Web Search", "Search tools", provider)]
        }

        response = authed_client.get("/api/v1/tools/mcp")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["success"] is True
        assert isinstance(body["groups"], list)
        assert len(body["groups"]) >= 1

    def test_groups_contain_servers_and_tools(self, authed_client, mock_tool_registry):
        """Each group must contain at least one server with its tools."""
        tool = _make_mock_tool("run_python", "Execute Python")
        provider = _make_mock_provider([tool])

        mock_tool_registry.get_categories.return_value = {
            "code": [("code-interpreter", "Code Interpreter", "Runs code", provider)]
        }

        response = authed_client.get("/api/v1/tools/mcp")
        body = response.json()

        group = next(
            (g for g in body["groups"] if g["category"] == "code"),
            None,
        )
        assert group is not None, "Expected a 'code' group"

        server = next(
            (s for s in group["servers"] if s["id"] == "code-interpreter"),
            None,
        )
        assert server is not None
        assert server["name"] == "Code Interpreter"
        assert server["tool_count"] == 1
        assert any(t["name"] == "run_python" for t in server["tools"])

    def test_provider_exception_is_skipped_gracefully(
        self, authed_client, mock_tool_registry
    ):
        """A provider that raises during get_tools() is skipped; others still appear."""
        bad_provider = MagicMock()
        bad_provider.get_tools.side_effect = RuntimeError("provider down")

        good_tool = _make_mock_tool("fetch_url", "Fetch URL")
        good_provider = _make_mock_provider([good_tool])

        mock_tool_registry.get_categories.return_value = {
            "knowledge": [
                ("bad-server", "Bad Server", "Broken", bad_provider),
                ("good-server", "Good Server", "Working", good_provider),
            ]
        }

        response = authed_client.get("/api/v1/tools/mcp")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()

        group = next(
            (g for g in body["groups"] if g["category"] == "knowledge"),
            None,
        )
        assert group is not None
        server_ids = [s["id"] for s in group["servers"]]
        assert "bad-server" not in server_ids
        assert "good-server" in server_ids

    def test_empty_registry_returns_empty_groups(
        self, authed_client, mock_tool_registry
    ):
        """When the registry has no categories the groups list is empty."""
        mock_tool_registry.get_categories.return_value = {}

        response = authed_client.get("/api/v1/tools/mcp")
        body = response.json()

        assert body["success"] is True
        assert body["groups"] == []

    def test_requires_authentication(self):
        """Unauthenticated requests should be rejected (no override applied)."""
        from src.app.main import app

        unauthenticated_client = TestClient(app, raise_server_exceptions=False)
        response = unauthenticated_client.get("/api/v1/tools/mcp")
        # Expect 401 or 403 — exact code depends on the auth middleware.
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
