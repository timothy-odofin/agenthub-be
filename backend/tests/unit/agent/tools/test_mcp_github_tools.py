"""
Unit tests for MCP GitHub tools implementation.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from langchain.tools import StructuredTool

from app.agent.tools.mcp_github.mcp_github_tools import (
    MCPGitHubToolsProvider,
    _call_mcp_tool,
    _call_mcp_tool_sync,
    _call_tool_via_http,
    _create_tool_wrapper,
    _discover_tool_schemas,
    _discover_via_http,
    _extract_jsonrpc_tool_result,
    _extract_text_from_result,
    _filter_tools,
    _get_mcp_github_config,
    _sanitize_github_args,
)

# ── Helpers ───────────────────────────────────────────────────────────


def _make_tool(name: str) -> StructuredTool:
    """Create a mock StructuredTool with the given name."""
    return StructuredTool.from_function(
        name=name,
        description=f"Mock tool: {name}",
        func=lambda: None,
    )


# ── Config loading ────────────────────────────────────────────────────


class TestGetMCPGitHubConfig:
    """Tests for _get_mcp_github_config."""

    @patch("app.agent.tools.mcp_github.mcp_github_tools.settings")
    def test_returns_disabled_when_section_not_found(self, mock_settings):
        """Config returns disabled when github section is missing."""
        mock_settings.get_section.return_value = None
        config = _get_mcp_github_config()
        assert config == {"enabled": False}

    @patch("app.agent.tools.mcp_github.mcp_github_tools.settings")
    def test_returns_disabled_when_not_enabled(self, mock_settings):
        """Config returns disabled when enabled is False."""
        mock_settings.get_section.return_value = {"enabled": False}
        config = _get_mcp_github_config()
        assert config == {"enabled": False}

    @patch("app.agent.tools.mcp_github.mcp_github_tools.settings")
    def test_returns_full_config_when_present(self, mock_settings):
        """Config returns the full resolved dict from settings."""
        github_dict = {
            "enabled": True,
            "transport": "http",
            "command": "github-mcp-server",
            "args": ["--stdio"],
            "url": "https://api.githubcopilot.com/mcp/",
            "headers": {"Authorization": "Bearer ghp_test"},
            "tool_filter": ["search_repositories", "list_issues"],
        }
        mock_settings.get_section.return_value = github_dict

        config = _get_mcp_github_config()

        assert config is github_dict
        assert config["enabled"] is True
        assert config["transport"] == "http"
        assert config["headers"] == {"Authorization": "Bearer ghp_test"}
        assert config["tool_filter"] == ["search_repositories", "list_issues"]
        mock_settings.get_section.assert_called_once_with("tools.tools.github")

    @patch("app.agent.tools.mcp_github.mcp_github_tools.settings")
    def test_returns_disabled_on_exception(self, mock_settings):
        """Config returns disabled gracefully on error."""
        mock_settings.get_section.side_effect = Exception("boom")
        config = _get_mcp_github_config()
        assert config == {"enabled": False}


# ── Tool filtering ────────────────────────────────────────────────────


class TestFilterTools:
    """Tests for _filter_tools."""

    def test_returns_all_when_no_filter(self):
        """All tools returned when allowed_tools is empty."""
        tools = [_make_tool("a"), _make_tool("b"), _make_tool("c")]
        result = _filter_tools(tools, [])
        assert len(result) == 3

    def test_filters_to_allowed_only(self):
        """Only tools in the allowed list are returned."""
        tools = [_make_tool("a"), _make_tool("b"), _make_tool("c")]
        result = _filter_tools(tools, ["a", "c"])
        assert [t.name for t in result] == ["a", "c"]

    def test_handles_no_matching_tools(self):
        """Returns empty when no tools match the filter."""
        tools = [_make_tool("a"), _make_tool("b")]
        result = _filter_tools(tools, ["x", "y"])
        assert result == []

    def test_handles_empty_tools_list(self):
        """Returns empty when tools list is empty."""
        result = _filter_tools([], ["a", "b"])
        assert result == []


# ── Provider class ────────────────────────────────────────────────────


class TestMCPGitHubToolsProvider:
    """Tests for MCPGitHubToolsProvider."""

    def test_init_defaults(self):
        """Provider initializes with default config."""
        provider = MCPGitHubToolsProvider()
        assert provider.config == {}
        assert provider._tools_cache is None

    def test_init_with_config(self):
        """Provider accepts custom config."""
        provider = MCPGitHubToolsProvider(config={"key": "value"})
        assert provider.config == {"key": "value"}

    @patch("app.agent.tools.mcp_github.mcp_github_tools._get_mcp_github_config")
    def test_get_tools_returns_empty_when_disabled(self, mock_config):
        """get_tools returns empty list when github is disabled."""
        mock_config.return_value = {"enabled": False}
        provider = MCPGitHubToolsProvider()
        tools = provider.get_tools()
        assert tools == []

    @patch("app.agent.tools.mcp_github.mcp_github_tools._mcp_tools_cache", None)
    @patch("app.agent.tools.mcp_github.mcp_github_tools._load_mcp_tools_sync")
    @patch("app.agent.tools.mcp_github.mcp_github_tools._get_mcp_github_config")
    def test_get_tools_loads_and_caches(self, mock_config, mock_load):
        """get_tools loads tools from MCP server and caches them."""
        mock_tools = [_make_tool("search_repositories"), _make_tool("list_issues")]
        mock_config.return_value = {"enabled": True, "tool_filter": []}
        mock_load.return_value = mock_tools

        provider = MCPGitHubToolsProvider()
        tools = provider.get_tools()

        assert len(tools) == 2
        assert tools[0].name == "search_repositories"
        assert tools[1].name == "list_issues"
        mock_load.assert_called_once()

    @patch("app.agent.tools.mcp_github.mcp_github_tools._mcp_tools_cache", None)
    @patch("app.agent.tools.mcp_github.mcp_github_tools._load_mcp_tools_sync")
    @patch("app.agent.tools.mcp_github.mcp_github_tools._get_mcp_github_config")
    def test_get_tools_applies_filter(self, mock_config, mock_load):
        """get_tools applies tool_filter from config."""
        all_tools = [
            _make_tool("search_repositories"),
            _make_tool("list_issues"),
            _make_tool("create_pull_request"),
        ]
        mock_config.return_value = {
            "enabled": True,
            "tool_filter": ["search_repositories", "list_issues"],
        }
        mock_load.return_value = all_tools

        provider = MCPGitHubToolsProvider()
        tools = provider.get_tools()

        assert len(tools) == 2
        names = [t.name for t in tools]
        assert "search_repositories" in names
        assert "list_issues" in names
        assert "create_pull_request" not in names

    @patch("app.agent.tools.mcp_github.mcp_github_tools._mcp_tools_cache")
    def test_get_tools_uses_global_cache(self, mock_cache):
        """get_tools returns cached tools without re-loading."""
        cached = [_make_tool("cached_tool")]
        mock_cache.__len__ = Mock(return_value=1)
        mock_cache.__iter__ = Mock(return_value=iter(cached))

        # Patch at module level so the 'is not None' check works
        with patch(
            "app.agent.tools.mcp_github.mcp_github_tools._mcp_tools_cache", cached
        ):
            provider = MCPGitHubToolsProvider()
            tools = provider.get_tools()
            assert len(tools) == 1
            assert tools[0].name == "cached_tool"

    def test_get_tools_uses_instance_cache(self):
        """get_tools returns instance-cached tools without re-loading."""
        provider = MCPGitHubToolsProvider()
        cached = [_make_tool("instance_cached")]
        provider._tools_cache = cached

        tools = provider.get_tools()
        assert len(tools) == 1
        assert tools[0].name == "instance_cached"

    @patch("app.agent.tools.mcp_github.mcp_github_tools._mcp_tools_cache", None)
    @patch("app.agent.tools.mcp_github.mcp_github_tools._load_mcp_tools_sync")
    @patch("app.agent.tools.mcp_github.mcp_github_tools._get_mcp_github_config")
    def test_get_tools_returns_empty_on_exception(self, mock_config, mock_load):
        """get_tools returns empty list on MCP connection failure."""
        mock_config.return_value = {"enabled": True, "tool_filter": []}
        mock_load.side_effect = Exception("Connection refused")

        provider = MCPGitHubToolsProvider()
        tools = provider.get_tools()
        assert tools == []

    def test_invalidate_cache_clears_all(self):
        """invalidate_cache clears instance and global caches."""
        import app.agent.tools.mcp_github.mcp_github_tools as mod

        provider = MCPGitHubToolsProvider()
        provider._tools_cache = [_make_tool("stale")]
        mod._mcp_tools_cache = [_make_tool("stale")]

        provider.invalidate_cache()

        assert provider._tools_cache is None
        assert mod._mcp_tools_cache is None

    @patch("app.agent.tools.mcp_github.mcp_github_tools._get_mcp_github_config")
    def test_get_connection_info(self, mock_config):
        """get_connection_info returns provider metadata."""
        mock_config.return_value = {
            "enabled": True,
            "transport": "stdio",
            "command": "github-mcp-server",
            "url": None,
        }
        provider = MCPGitHubToolsProvider()
        info = provider.get_connection_info()

        assert info["provider"] == "mcp"
        assert info["transport"] == "stdio"
        assert info["enabled"] is True


# ── Schema discovery ──────────────────────────────────────────────────


class TestDiscoverToolSchemas:
    """Tests for _discover_tool_schemas (routes to transport-specific discovery)."""

    @pytest.mark.asyncio
    async def test_unsupported_transport_returns_empty(self):
        """Unsupported transport type returns empty list."""
        config = {"transport": "grpc"}
        schemas = await _discover_tool_schemas(config)
        assert schemas == []

    @pytest.mark.asyncio
    async def test_stdio_transport_delegates(self):
        """stdio transport delegates to _discover_via_stdio."""
        with patch(
            "app.agent.tools.mcp_github.mcp_github_tools._discover_via_stdio",
            new_callable=AsyncMock,
        ) as mock_discover:
            mock_discover.return_value = [
                {"name": "test", "description": "", "input_schema": {}}
            ]
            config = {"transport": "stdio"}
            schemas = await _discover_tool_schemas(config)
            assert len(schemas) == 1
            mock_discover.assert_awaited_once_with(config)

    @pytest.mark.asyncio
    async def test_sse_transport_delegates(self):
        """sse transport delegates to _discover_via_sse."""
        with patch(
            "app.agent.tools.mcp_github.mcp_github_tools._discover_via_sse",
            new_callable=AsyncMock,
        ) as mock_discover:
            mock_discover.return_value = [
                {"name": "test", "description": "", "input_schema": {}}
            ]
            config = {"transport": "sse"}
            schemas = await _discover_tool_schemas(config)
            assert len(schemas) == 1
            mock_discover.assert_awaited_once_with(config)

    @pytest.mark.asyncio
    async def test_http_transport_delegates(self):
        """http transport delegates to _discover_via_http."""
        with patch(
            "app.agent.tools.mcp_github.mcp_github_tools._discover_via_http",
            new_callable=AsyncMock,
        ) as mock_discover:
            mock_discover.return_value = [
                {"name": "test", "description": "", "input_schema": {}}
            ]
            config = {"transport": "http"}
            schemas = await _discover_tool_schemas(config)
            assert len(schemas) == 1
            mock_discover.assert_awaited_once_with(config)


# ── HTTP discovery ────────────────────────────────────────────────────


class TestDiscoverViaHTTP:
    """Tests for _discover_via_http (Streamable HTTP / GitHub hosted MCP)."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_url(self):
        """Returns empty list when url is not configured."""
        config = {"url": None, "headers": {}}
        schemas = await _discover_via_http(config)
        assert schemas == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_auth(self):
        """Returns empty list when no Authorization header."""
        config = {"url": "https://api.githubcopilot.com/mcp/", "headers": {}}
        schemas = await _discover_via_http(config)
        assert schemas == []

    @pytest.mark.asyncio
    async def test_passes_auth_header_to_client(self):
        """Authorization header from config is passed to streamablehttp_client."""
        with (
            patch(
                "app.agent.tools.mcp_github.mcp_github_tools.streamablehttp_client"
            ) as mock_client,
            patch(
                "app.agent.tools.mcp_github.mcp_github_tools.ClientSession"
            ) as mock_session_cls,
        ):
            # Set up the async context manager chain
            mock_transport = (AsyncMock(), AsyncMock(), AsyncMock())
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_transport)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            # Mock list_tools result
            mock_tool = MagicMock()
            mock_tool.name = "search_repositories"
            mock_tool.description = "Search repos"
            mock_tool.inputSchema = {"type": "object", "properties": {}}

            mock_session = AsyncMock()
            mock_session.list_tools = AsyncMock(
                return_value=MagicMock(tools=[mock_tool])
            )
            mock_session_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            config = {
                "url": "https://api.githubcopilot.com/mcp/",
                "headers": {"Authorization": "Bearer ghp_abc123"},
            }

            schemas = await _discover_via_http(config)

            # Verify streamablehttp_client was called with correct headers
            call_args = mock_client.call_args
            assert call_args is not None
            _, kwargs = call_args
            assert kwargs.get("headers", {}).get("Authorization") == "Bearer ghp_abc123"

            # Verify schemas were extracted
            assert len(schemas) == 1
            assert schemas[0]["name"] == "search_repositories"


# ── Tool wrapper creation ─────────────────────────────────────────────


class TestCreateToolWrapper:
    """Tests for _create_tool_wrapper."""

    def test_creates_structured_tool_with_sync_and_async(self):
        """Wrapper has both sync func and async coroutine."""
        config = {"transport": "http", "url": "https://example.com/mcp/", "headers": {}}
        tool = _create_tool_wrapper(
            tool_name="search_repositories",
            tool_description="Search GitHub repositories",
            tool_input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
            },
            config=config,
        )

        assert isinstance(tool, StructuredTool)
        assert tool.name == "search_repositories"
        assert tool.description == "Search GitHub repositories"
        # Has both sync and async paths
        assert tool.func is not None
        assert tool.coroutine is not None

    def test_sync_call_invokes_mcp(self):
        """Sync func calls _call_mcp_tool_sync under the hood."""
        config = {"transport": "http", "url": "https://example.com/mcp/", "headers": {}}
        tool = _create_tool_wrapper(
            tool_name="get_repo",
            tool_description="Get repo info",
            tool_input_schema={
                "type": "object",
                "properties": {"owner": {"type": "string"}},
            },
            config=config,
        )

        with patch(
            "app.agent.tools.mcp_github.mcp_github_tools._call_mcp_tool_sync"
        ) as mock_sync:
            mock_sync.return_value = '{"name": "agenthub-be"}'
            result = tool.func(owner="timothy-odofin")
            mock_sync.assert_called_once_with(
                "get_repo", {"owner": "timothy-odofin"}, config
            )
            assert result == '{"name": "agenthub-be"}'

    @pytest.mark.asyncio
    async def test_async_call_invokes_mcp(self):
        """Async coroutine calls _call_mcp_tool under the hood."""
        config = {"transport": "http", "url": "https://example.com/mcp/", "headers": {}}
        tool = _create_tool_wrapper(
            tool_name="get_repo",
            tool_description="Get repo info",
            tool_input_schema={
                "type": "object",
                "properties": {"owner": {"type": "string"}},
            },
            config=config,
        )

        with patch(
            "app.agent.tools.mcp_github.mcp_github_tools._call_mcp_tool",
            new_callable=AsyncMock,
        ) as mock_async:
            mock_async.return_value = '{"name": "agenthub-be"}'
            result = await tool.coroutine(owner="timothy-odofin")
            mock_async.assert_awaited_once_with(
                "get_repo", {"owner": "timothy-odofin"}, config
            )
            assert result == '{"name": "agenthub-be"}'


# ── Tool call routing ────────────────────────────────────────────────


# ── Argument sanitization ─────────────────────────────────────────────


class TestSanitizeGithubArgs:
    """Tests for _sanitize_github_args."""

    def test_strips_none_values(self):
        """None values are removed from arguments."""
        result = _sanitize_github_args(
            "get_file_contents",
            {
                "owner": "acme",
                "repo": "repo",
                "path": "README.md",
                "sha": None,
                "branch": None,
            },
        )
        assert result == {"owner": "acme", "repo": "repo", "path": "README.md"}

    def test_keeps_all_non_none_values(self):
        """Non-None values are preserved."""
        result = _sanitize_github_args(
            "search_repositories",
            {"query": "agenthub", "page": 1},
        )
        assert result == {"query": "agenthub", "page": 1}

    def test_strips_sha_passed_as_path_for_get_file_contents(self):
        """Full 40-char SHA passed as 'path' is replaced with '' (repo root) in get_file_contents."""
        sha = "96d1bbd89e8c4976206647dcb035404d25ba9b4a"
        result = _sanitize_github_args(
            "get_file_contents",
            {"owner": "timothy-odofin", "repo": "agenthub-be", "path": sha},
        )
        assert result["path"] == ""
        assert result == {"owner": "timothy-odofin", "repo": "agenthub-be", "path": ""}

    def test_strips_short_sha_passed_as_path(self):
        """Abbreviated 7-char SHA passed as 'path' is replaced with ''."""
        result = _sanitize_github_args(
            "get_file_contents",
            {"owner": "acme", "repo": "repo", "path": "96d1bbd"},
        )
        assert result["path"] == ""

    def test_does_not_strip_real_file_path(self):
        """Normal file paths are NOT stripped."""
        result = _sanitize_github_args(
            "get_file_contents",
            {"owner": "acme", "repo": "repo", "path": "src/app/main.py"},
        )
        assert result["path"] == "src/app/main.py"

    def test_does_not_strip_sha_path_for_other_tools(self):
        """SHA-like path is only guarded for get_file_contents, not other tools."""
        sha = "96d1bbd89e8c4976206647dcb035404d25ba9b4a"
        result = _sanitize_github_args(
            "get_commit",
            {"owner": "acme", "repo": "repo", "sha": sha},
        )
        assert result["sha"] == sha


class TestCallMCPTool:
    """Tests for _call_mcp_tool (routes to transport-specific callers)."""

    @pytest.mark.asyncio
    async def test_http_transport_routes_correctly(self):
        """http transport routes to _call_tool_via_http."""
        with patch(
            "app.agent.tools.mcp_github.mcp_github_tools._call_tool_via_http",
            new_callable=AsyncMock,
        ) as mock_http:
            mock_http.return_value = "result"
            config = {"transport": "http"}
            result = await _call_mcp_tool("search", {"q": "test"}, config)
            assert result == "result"
            mock_http.assert_awaited_once_with("search", {"q": "test"}, config)

    @pytest.mark.asyncio
    async def test_unsupported_transport_raises(self):
        """Unsupported transport raises ValueError."""
        config = {"transport": "grpc"}
        with pytest.raises(ValueError, match="Unsupported MCP transport: grpc"):
            await _call_mcp_tool("search", {}, config)

    @pytest.mark.asyncio
    async def test_strips_none_values_from_arguments(self):
        """None values are stripped from arguments before calling transport."""
        with patch(
            "app.agent.tools.mcp_github.mcp_github_tools._call_tool_via_http",
            new_callable=AsyncMock,
        ) as mock_http:
            mock_http.return_value = "result"
            config = {"transport": "http"}
            result = await _call_mcp_tool(
                "get_file_contents",
                {
                    "owner": "timothy-odofin",
                    "repo": "agenthub-be",
                    "path": "README.md",
                    "sha": None,
                },
                config,
            )
            assert result == "result"
            call_args = mock_http.call_args
            assert call_args[0][1] == {
                "owner": "timothy-odofin",
                "repo": "agenthub-be",
                "path": "README.md",
            }

    @pytest.mark.asyncio
    async def test_strips_sha_used_as_path(self):
        """SHA passed as 'path' in get_file_contents is replaced with ''."""
        with patch(
            "app.agent.tools.mcp_github.mcp_github_tools._call_tool_via_http",
            new_callable=AsyncMock,
        ) as mock_http:
            mock_http.return_value = "result"
            config = {"transport": "http"}
            sha = "96d1bbd89e8c4976206647dcb035404d25ba9b4a"
            await _call_mcp_tool(
                "get_file_contents",
                {"owner": "timothy-odofin", "repo": "agenthub-be", "path": sha},
                config,
            )
            call_args = mock_http.call_args
            forwarded_args = call_args[0][1]
            assert forwarded_args.get("path") == ""


# ── HTTP tool invocation (direct httpx) ──────────────────────────────


class TestCallToolViaHTTP:
    """Tests for _call_tool_via_http (direct httpx JSON-RPC calls)."""

    @pytest.mark.asyncio
    async def test_sends_jsonrpc_payload(self):
        """Sends correct JSON-RPC 2.0 payload to the MCP endpoint."""
        with patch(
            "app.agent.tools.mcp_github.mcp_github_tools.httpx.AsyncClient"
        ) as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "result": {
                    "content": [
                        {"type": "text", "text": '{"full_name": "owner/repo"}'}
                    ],
                    "isError": False,
                },
                "id": 1,
            }
            mock_response.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)

            config = {
                "url": "https://api.githubcopilot.com/mcp/",
                "headers": {"Authorization": "Bearer ghp_test"},
            }

            result = await _call_tool_via_http(
                "get_repository", {"owner": "test"}, config
            )

            # Verify the JSON-RPC payload
            call_args = mock_client.post.call_args
            assert call_args is not None
            payload = call_args.kwargs.get("json") or call_args[1].get("json")
            assert payload["jsonrpc"] == "2.0"
            assert payload["method"] == "tools/call"
            assert payload["params"]["name"] == "get_repository"
            assert payload["params"]["arguments"] == {"owner": "test"}
            assert result == '{"full_name": "owner/repo"}'

    @pytest.mark.asyncio
    async def test_handles_jsonrpc_error(self):
        """Returns an 'Error: ...' string on JSON-RPC error response (no raise)."""
        with patch(
            "app.agent.tools.mcp_github.mcp_github_tools.httpx.AsyncClient"
        ) as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "error": {"code": -32600, "message": "Invalid request"},
                "id": 1,
            }
            mock_response.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)

            config = {
                "url": "https://api.githubcopilot.com/mcp/",
                "headers": {"Authorization": "Bearer ghp_test"},
            }

            result = await _call_tool_via_http("bad_tool", {}, config)
            assert result.startswith("Error:")
            assert "Invalid request" in result

    @pytest.mark.asyncio
    async def test_passes_auth_header(self):
        """Authorization header is passed to httpx."""
        with patch(
            "app.agent.tools.mcp_github.mcp_github_tools.httpx.AsyncClient"
        ) as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": "ok"}],
                    "isError": False,
                },
                "id": 1,
            }
            mock_response.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)

            config = {
                "url": "https://api.githubcopilot.com/mcp/",
                "headers": {"Authorization": "Bearer ghp_secret"},
            }

            await _call_tool_via_http("search", {}, config)

            # Verify headers include Authorization
            call_args = mock_client.post.call_args
            headers = call_args.kwargs.get("headers") or call_args[1].get("headers")
            assert headers["Authorization"] == "Bearer ghp_secret"


# ── JSON-RPC result extraction ───────────────────────────────────────


class TestExtractJsonrpcToolResult:
    """Tests for _extract_jsonrpc_tool_result."""

    def test_single_text_content(self):
        """Single text content returned as-is."""
        result = {
            "content": [{"type": "text", "text": "hello world"}],
            "isError": False,
        }
        assert _extract_jsonrpc_tool_result(result) == "hello world"

    def test_multiple_text_contents(self):
        """Multiple text contents are joined with newlines."""
        result = {
            "content": [
                {"type": "text", "text": "a"},
                {"type": "text", "text": "b"},
            ],
            "isError": False,
        }
        output = _extract_jsonrpc_tool_result(result)
        assert "a" in output and "b" in output

    def test_error_returns_error_string(self):
        """isError returns an 'Error: ...' string instead of raising."""
        result = {
            "content": [{"type": "text", "text": "not found"}],
            "isError": True,
        }
        output = _extract_jsonrpc_tool_result(result)
        assert output.startswith("Error:")
        assert "not found" in output

    def test_empty_content(self):
        """Empty content returns JSON of the result."""
        result = {"content": [], "isError": False}
        output = _extract_jsonrpc_tool_result(result)
        assert output  # Returns json.dumps of the result dict


# ── Extract text from result ─────────────────────────────────────────


class TestExtractTextFromResult:
    """Tests for _extract_text_from_result."""

    def test_single_text_content(self):
        """Single text content is returned as-is."""
        from mcp.types import TextContent

        result = MagicMock()
        result.isError = False
        result.content = [TextContent(type="text", text="hello")]
        assert _extract_text_from_result(result) == "hello"

    def test_multiple_text_contents(self):
        """Multiple text contents are joined with newlines."""
        from mcp.types import TextContent

        result = MagicMock()
        result.isError = False
        result.content = [
            TextContent(type="text", text="a"),
            TextContent(type="text", text="b"),
        ]
        output = _extract_text_from_result(result)
        assert "a" in output and "b" in output

    def test_error_result_returns_error_string(self):
        """Error results return 'Error: ...' string instead of raising."""
        from mcp.types import TextContent

        result = MagicMock()
        result.isError = True
        result.content = [TextContent(type="text", text="not found")]
        output = _extract_text_from_result(result)
        assert output.startswith("Error:")
        assert "not found" in output

    def test_empty_content_returns_empty_string(self):
        """Empty content returns empty string."""
        result = MagicMock()
        result.isError = False
        result.content = []
        assert _extract_text_from_result(result) == ""


# ── Registry integration ─────────────────────────────────────────────


class TestRegistryIntegration:
    """Tests for ToolRegistry registration."""

    def test_provider_registered_under_github_category(self):
        """MCPGitHubToolsProvider is registered under 'github' category."""
        from app.agent.tools.base.registry import ToolRegistry

        categories = ToolRegistry.get_categories()
        assert "github" in categories

        github_tools = ToolRegistry.get_tools_by_category("github")
        class_names = [cls.__name__ for cls in github_tools]
        assert "MCPGitHubToolsProvider" in class_names

    def test_provider_registered_under_github_package(self):
        """MCPGitHubToolsProvider is in the 'github' package."""
        from app.agent.tools.base.registry import ToolRegistry

        packages = ToolRegistry.get_packages()
        assert "github" in packages

        github_tools = ToolRegistry.get_tools_by_package("github")
        class_names = [cls.__name__ for cls in github_tools]
        assert "MCPGitHubToolsProvider" in class_names

    def test_provider_has_get_tools_method(self):
        """MCPGitHubToolsProvider has get_tools for ToolRegistry contract."""
        provider = MCPGitHubToolsProvider()
        assert hasattr(provider, "get_tools")
        assert callable(provider.get_tools)
