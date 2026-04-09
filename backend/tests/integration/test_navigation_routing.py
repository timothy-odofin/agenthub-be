"""
Integration test for navigation routing via the LLM agent.

This test uses the REAL LLM (via LLMFactory) to verify that when a user
sends a navigation-intent message, the agent:
  1. Uses the `navigate_to_route` tool
  2. Returns a response that references the correct destination

Pre-conditions:
  - A valid .env with LLM credentials (OPENAI_API_KEY, etc.)
  - No mocking of the LLM — we want to see real tool-calling behaviour

Architecture under test:
  User message ─▶ Agent (ReAct) ─▶ navigate_to_route tool ─▶ routes.json lookup ─▶ action payload
"""

import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock

import pytest

# Ensure src is on the path (same pattern as existing conftest.py)
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from app.agent import AgentContext, AgentFactory, AgentResponse
from app.agent.tools.navigation.navigation_tools import NavigationTools, _route_storage
from app.core.constants import AgentFramework, AgentType, LLMProvider
from app.infrastructure.llm.factory.llm_factory import LLMFactory

# ──────────────────────────────────────────────────────────────────
# Test route data — mirrors the frontend ROUTE_REGISTRY
# ──────────────────────────────────────────────────────────────────

TEST_ROUTES: List[Dict[str, Any]] = [
    {
        "path": "/",
        "label": "Home / Signup",
        "description": "Landing page with conversational signup and login",
        "protected": False,
        "actions": [],
    },
    {
        "path": "/signup",
        "label": "Signup",
        "description": "User registration and account creation page",
        "protected": False,
        "actions": [],
    },
    {
        "path": "/main-dashboard",
        "label": "Main Dashboard",
        "description": "Primary chat interface with session management, AI assistant, and all main features",
        "protected": True,
        "actions": [
            "NEW_CHAT",
            "DELETE",
            "SHARE",
            "RENAME",
            "LOAD_SESSION",
            "SHOW_CAPABILITIES",
        ],
    },
]


# ──────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def seed_routes():
    """
    Write the test routes into routes.json before each test,
    and clean up after.
    """
    _route_storage.save({"routes": TEST_ROUTES})
    yield
    _route_storage.delete()


@pytest.fixture
def mock_session_repo():
    """
    Provide a mock session repository so the agent doesn't need a real DB.
    The navigation tool doesn't interact with sessions — it only reads routes.json.

    Every method the LangChainReactAgent awaits must be an AsyncMock:
      - ensure_session_exists(session_id, user_id, data)
      - get_session_history(user_id, session_id)
      - add_message(session_id, role, content)
    """
    repo = AsyncMock()
    repo.ensure_session_exists = AsyncMock(return_value=True)
    repo.get_session_history = AsyncMock(return_value=[])
    repo.add_message = AsyncMock(return_value=True)
    repo.save_message = AsyncMock(return_value=True)
    repo.create_session = AsyncMock(return_value=str(uuid.uuid4()))
    repo.get_session = AsyncMock(return_value=None)
    repo.update_session = AsyncMock(return_value=True)
    return repo


@pytest.fixture
async def llm():
    """Get a real LLM instance via the factory (reads .env credentials)."""
    return await LLMFactory.get_llm(LLMProvider.OPENAI)


@pytest.fixture
async def navigation_agent(llm, mock_session_repo):
    """
    Create a real ReAct agent wired to the real LLM.
    Only the session repository is mocked (no DB needed for nav tests).
    """
    agent = await AgentFactory.create_agent(
        agent_type=AgentType.REACT,
        framework=AgentFramework.LANGCHAIN,
        llm_provider=llm,
        session_repository=mock_session_repo,
        verbose=False,
    )
    return agent


def _make_context(user_id: str = "test-user-nav") -> AgentContext:
    """Build a minimal AgentContext for testing."""
    return AgentContext(
        user_id=user_id,
        session_id=str(uuid.uuid4()),
        metadata={"protocol": "rest"},
    )


# ──────────────────────────────────────────────────────────────────
# Direct tool tests — call the navigation tool function directly
# to verify route resolution without LLM latency.
# ──────────────────────────────────────────────────────────────────


class TestNavigationToolDirect:
    """
    Unit-style tests that call the navigate_to_route tool function
    directly (no LLM involved). Fast and deterministic.
    """

    def _get_nav_tool(self):
        """Get the navigate_to_route StructuredTool instance."""
        tools = NavigationTools().get_tools()
        nav_tool = next(t for t in tools if t.name == "navigate_to_route")
        return nav_tool

    def test_navigate_to_dashboard_direct(self):
        """Direct tool call with /main-dashboard should return NAVIGATE payload."""
        tool = self._get_nav_tool()
        result = tool.invoke({"route_path": "/main-dashboard"})
        payload = json.loads(result)

        assert payload["action_type"] == "NAVIGATE"
        assert payload["action"]["route"] == "/main-dashboard"
        assert payload["action"]["title"] == "Main Dashboard"
        assert payload["action"]["protected"] is True

    def test_navigate_to_signup_direct(self):
        """Direct tool call with /signup should return NAVIGATE payload."""
        tool = self._get_nav_tool()
        result = tool.invoke({"route_path": "/signup"})
        payload = json.loads(result)

        assert payload["action_type"] == "NAVIGATE"
        assert payload["action"]["route"] == "/signup"
        assert payload["action"]["title"] == "Signup"
        assert payload["action"]["protected"] is False

    def test_navigate_to_home_direct(self):
        """Direct tool call with / should return NAVIGATE payload."""
        tool = self._get_nav_tool()
        result = tool.invoke({"route_path": "/"})
        payload = json.loads(result)

        assert payload["action_type"] == "NAVIGATE"
        assert payload["action"]["route"] == "/"
        assert payload["action"]["title"] == "Home / Signup"

    def test_new_chat_action_direct(self):
        """Direct tool call for NEW_CHAT action on /main-dashboard."""
        tool = self._get_nav_tool()
        result = tool.invoke(
            {
                "route_path": "/main-dashboard",
                "action_name": "NEW_CHAT",
            }
        )
        payload = json.loads(result)

        assert payload["action_type"] == "UI_ACTION"
        assert payload["action"]["name"] == "NEW_CHAT"
        assert payload["action"]["route"] == "/main-dashboard"

    def test_delete_action_direct(self):
        """Direct tool call for DELETE action on /main-dashboard."""
        tool = self._get_nav_tool()
        result = tool.invoke(
            {
                "route_path": "/main-dashboard",
                "action_name": "DELETE",
            }
        )
        payload = json.loads(result)

        assert payload["action_type"] == "UI_ACTION"
        assert payload["action"]["name"] == "DELETE"
        assert payload["action"]["route"] == "/main-dashboard"

    def test_share_action_direct(self):
        """Direct tool call for SHARE action on /main-dashboard."""
        tool = self._get_nav_tool()
        result = tool.invoke(
            {
                "route_path": "/main-dashboard",
                "action_name": "SHARE",
            }
        )
        payload = json.loads(result)

        assert payload["action_type"] == "UI_ACTION"
        assert payload["action"]["name"] == "SHARE"

    def test_invalid_route_returns_error(self):
        """Direct tool call with unknown path should return ERROR."""
        tool = self._get_nav_tool()
        result = tool.invoke({"route_path": "/xyz-totally-unknown-987"})
        payload = json.loads(result)

        assert payload["action_type"] == "ERROR"
        assert "No route found" in payload["message"]

    def test_invalid_action_for_route_returns_error(self):
        """Requesting an action not available on the route should return ERROR."""
        tool = self._get_nav_tool()
        result = tool.invoke(
            {
                "route_path": "/signup",
                "action_name": "DELETE",
            }
        )
        payload = json.loads(result)

        assert payload["action_type"] == "ERROR"
        assert "not available" in payload["message"]

    def test_action_with_params_direct(self):
        """Direct tool call for RENAME with params."""
        tool = self._get_nav_tool()
        result = tool.invoke(
            {
                "route_path": "/main-dashboard",
                "action_name": "RENAME",
                "action_params": {"session_id": "abc123", "new_title": "My Chat"},
            }
        )
        payload = json.loads(result)

        assert payload["action_type"] == "UI_ACTION"
        assert payload["action"]["name"] == "RENAME"
        assert payload["action"]["params"]["session_id"] == "abc123"
        assert payload["action"]["params"]["new_title"] == "My Chat"

    def test_navigate_with_reason_direct(self):
        """Direct tool call with a reason should include it in payload."""
        tool = self._get_nav_tool()
        result = tool.invoke(
            {
                "route_path": "/main-dashboard",
                "reason": "User asked to go to the dashboard",
            }
        )
        payload = json.loads(result)

        assert payload["action_type"] == "NAVIGATE"
        assert payload["reason"] == "User asked to go to the dashboard"


# ──────────────────────────────────────────────────────────────────
# LLM integration tests — verify the agent picks the right tool
# when the user expresses a navigation intent.
# ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestNavigationRouting:
    """
    Integration tests that verify the LLM agent:
      1. Recognises a navigation intent
      2. Invokes the navigate_to_route tool (verified via tools_used)
      3. Responds with relevant content

    These tests call the REAL LLM — they require valid API credentials.
    """

    async def test_navigate_to_dashboard(self, navigation_agent):
        """'Go to dashboard' should invoke navigate_to_route."""
        response = await navigation_agent.execute(
            "Go to the dashboard", _make_context()
        )

        assert response.success, f"Agent failed: {response.errors}"
        assert (
            "navigate_to_route" in response.tools_used
        ), f"Expected navigate_to_route in tools_used, got: {response.tools_used}"
        # The LLM's natural-language response should reference dashboard
        content_lower = response.content.lower()
        assert any(
            word in content_lower for word in ["dashboard", "main"]
        ), f"Response should mention 'dashboard': {response.content}"

    async def test_navigate_to_signup(self, navigation_agent):
        """'Take me to signup' should invoke navigate_to_route."""
        response = await navigation_agent.execute(
            "Take me to the signup page", _make_context()
        )

        assert response.success, f"Agent failed: {response.errors}"
        assert (
            "navigate_to_route" in response.tools_used
        ), f"Expected navigate_to_route in tools_used, got: {response.tools_used}"
        content_lower = response.content.lower()
        assert any(
            word in content_lower for word in ["signup", "sign up", "registration"]
        ), f"Response should mention 'signup': {response.content}"

    async def test_navigate_to_home(self, navigation_agent):
        """'Go home' should invoke navigate_to_route."""
        response = await navigation_agent.execute(
            "Go to the home page", _make_context()
        )

        assert response.success, f"Agent failed: {response.errors}"
        assert (
            "navigate_to_route" in response.tools_used
        ), f"Expected navigate_to_route in tools_used, got: {response.tools_used}"
        content_lower = response.content.lower()
        assert any(
            word in content_lower for word in ["home", "landing"]
        ), f"Response should mention 'home': {response.content}"

    async def test_new_chat_action(self, navigation_agent):
        """'Start a new chat' should invoke navigate_to_route with NEW_CHAT."""
        response = await navigation_agent.execute("Start a new chat", _make_context())

        assert response.success, f"Agent failed: {response.errors}"
        assert (
            "navigate_to_route" in response.tools_used
        ), f"Expected navigate_to_route in tools_used, got: {response.tools_used}"
        content_lower = response.content.lower()
        assert any(
            word in content_lower for word in ["new chat", "started", "created", "new"]
        ), f"Response should mention 'new chat': {response.content}"

    async def test_delete_session_action(self, navigation_agent):
        """'Delete this session' should invoke navigate_to_route with DELETE.

        Note: The LLM may sometimes ask for confirmation before executing a
        destructive action. We accept either: the tool was called, or the
        LLM responded asking for confirmation (both are valid behaviours).
        """
        response = await navigation_agent.execute(
            "Delete this chat session", _make_context()
        )

        assert response.success, f"Agent failed: {response.errors}"
        content_lower = response.content.lower()

        if "navigate_to_route" in response.tools_used:
            # Tool was called — verify response mentions deletion
            assert any(
                word in content_lower for word in ["delet", "remov"]
            ), f"Response should mention 'delete': {response.content}"
        else:
            # LLM may have asked for confirmation — that's acceptable
            assert any(
                word in content_lower
                for word in [
                    "delet",
                    "remov",
                    "confirm",
                    "sure",
                    "which",
                    "session",
                ]
            ), f"LLM should either delete or ask for confirmation: {response.content}"

    async def test_non_navigation_message_skips_tool(self, navigation_agent):
        """A regular question should NOT invoke the navigation tool."""
        response = await navigation_agent.execute(
            "What is the capital of France?", _make_context()
        )

        assert response.success, f"Agent failed: {response.errors}"
        assert "navigate_to_route" not in response.tools_used, (
            f"navigate_to_route should NOT be used for a general question, "
            f"but tools_used = {response.tools_used}"
        )

    async def test_show_capabilities_action(self, navigation_agent):
        """'Show me what you can do' may trigger SHOW_CAPABILITIES."""
        response = await navigation_agent.execute(
            "Show me your capabilities", _make_context()
        )

        assert response.success, f"Agent failed: {response.errors}"
        # This could go either way — the LLM might answer directly or use the tool.
        # If the tool was used, just verify the agent succeeded.
        if "navigate_to_route" in response.tools_used:
            assert (
                "capabilit" in response.content.lower()
                or "can do" in response.content.lower()
            )
