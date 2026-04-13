"""
MCP GitHub Tools Provider — GitHub integration via Model Context Protocol.

Uses the official GitHub MCP server (github.com/github/github-mcp-server)
running as a subprocess (stdio transport) or remote HTTP endpoint.

The MCP server handles:
- GitHub API authentication (via GITHUB_TOKEN)
- All GitHub operations (repos, issues, PRs, code search, file ops, branches)
- Rate-limiting, pagination, error handling

Supported transports:
- stdio: Spawns github-mcp-server as a local subprocess (dev/local)
- sse:   Connects to a remote MCP server via Server-Sent Events
- http:  Connects to a remote MCP server via Streamable HTTP
         (GitHub's hosted endpoint: https://api.githubcopilot.com/mcp/)

This provider bridges MCP tools into the LangChain ToolRegistry so they are
consumed identically to Jira, Confluence, Datadog, etc.

Architecture:
    During initialization, we connect to the MCP server to discover tool
    **schemas** (name, description, inputSchema) — then immediately disconnect.

    Each tool is wrapped in a StructuredTool with both a sync `func` and async
    `coroutine`. When the agent invokes a tool, the wrapper opens a fresh MCP
    connection, calls the tool, reads the result, and closes the connection.

    This solves two problems:
    1. LangChain agents that call tools synchronously (AgentExecutor.invoke)
       get a sync `func` — no "does not support sync invocation" error.
    2. The MCP session is always alive during tool execution — no stale
       session references from a long-closed initialization connection.
"""

import asyncio
import concurrent.futures
import json
import os
import re
from typing import Any, Dict, List, Optional

import httpx
from langchain.tools import StructuredTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import TextContent

from app.agent.tools.base.registry import ToolRegistry
from app.core.config.framework.settings import settings
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

# Global cache for MCP tools (avoids reconnecting on every request)
_mcp_tools_cache: Optional[List[StructuredTool]] = None


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------


def _get_mcp_github_config() -> Dict[str, Any]:
    """
    Get MCP GitHub configuration from application-tools.yaml.

    Uses settings.get_section() which returns a plain dict with all
    environment variables already resolved and DynamicConfig unwrapped.

    Returns:
        Dictionary with MCP GitHub configuration
    """
    try:
        github_config = settings.get_section("tools.tools.github")
        if not github_config or not isinstance(github_config, dict):
            return {"enabled": False}

        if not github_config.get("enabled", False):
            return {"enabled": False}

        return github_config
    except Exception as e:
        logger.warning(f"Could not load MCP GitHub config: {e}")
        return {"enabled": False}


def _filter_tools(
    tools: List[StructuredTool], allowed_tools: List[str]
) -> List[StructuredTool]:
    """
    Filter MCP tools to only include the ones specified in configuration.

    The GitHub MCP server exposes ~30+ tools. Filtering keeps the agent's
    tool list focused and reduces token usage in the system prompt.

    Args:
        tools: Full list of tools from MCP server
        allowed_tools: List of tool names to keep (empty = keep all)

    Returns:
        Filtered list of tools
    """
    if not allowed_tools:
        return tools

    allowed_set = set(allowed_tools)
    filtered = [t for t in tools if t.name in allowed_set]

    logger.info(
        f"Filtered MCP GitHub tools: {len(filtered)}/{len(tools)} "
        f"(allowed: {allowed_tools})"
    )
    return filtered


# ---------------------------------------------------------------------------
# MCP connection helpers — open a fresh connection per tool invocation
# ---------------------------------------------------------------------------


def _extract_text_from_result(result) -> str:
    """Extract text content from an MCP CallToolResult.

    Returns the content as a string. If the server signals isError, the error
    message is returned as a plain "Error: ..." string so LangChain feeds it
    back to the LLM for recovery rather than crashing.
    """
    texts = []
    for content in result.content:
        if isinstance(content, TextContent):
            texts.append(content.text)

    message = texts[0] if len(texts) == 1 else "\n".join(texts)

    if result.isError:
        logger.warning(f"MCP tool returned an error: {message}")
        return f"Error: {message}"

    return message if message else ""


async def _call_tool_via_http(
    tool_name: str, arguments: Dict[str, Any], config: Dict[str, Any]
) -> str:
    """
    Call a single MCP tool via direct HTTP POST (JSON-RPC 2.0).

    Uses raw httpx instead of the MCP SDK's streamablehttp_client to avoid
    the anyio TaskGroup teardown issue ("unhandled errors in a TaskGroup")
    that occurs when asyncio.run() inside a ThreadPoolExecutor shuts down
    while the MCP client's background tasks are still running.

    The MCP Streamable HTTP protocol is JSON-RPC 2.0 over HTTP POST:
    - POST to the MCP endpoint with Content-Type: application/json
    - Body: {"jsonrpc": "2.0", "method": "tools/call", "params": {...}, "id": 1}
    - Response: {"jsonrpc": "2.0", "result": {...}, "id": 1}

    We skip the initialize handshake since GitHub's hosted MCP endpoint
    handles stateless tool calls directly.
    """
    url = config["url"]
    headers = dict(config.get("headers") or {})
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "application/json, text/event-stream"

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
        "id": 1,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()

        # Handle JSON response (most common for tool calls)
        if "application/json" in content_type:
            result = response.json()

            # Check for JSON-RPC error
            if "error" in result:
                error = result["error"]
                msg = f"Error: {error.get('message', 'Unknown error')}"
                logger.warning(f"MCP JSON-RPC error for tool call: {msg}")
                return msg

            # Extract tool result from JSON-RPC response
            tool_result = result.get("result", {})
            return _extract_jsonrpc_tool_result(tool_result)

        # Handle SSE response (some servers stream results)
        elif "text/event-stream" in content_type:
            return _extract_sse_tool_result(response.text)

        else:
            return response.text


def _extract_jsonrpc_tool_result(tool_result: Dict[str, Any]) -> str:
    """Extract text content from a JSON-RPC tool call result.

    Returns the content as a string. If the server signals isError=true, the
    error message is returned as a plain string (prefixed with "Error:") so
    LangChain feeds it back to the LLM for recovery rather than crashing.
    """
    content = tool_result.get("content", [])
    is_error = tool_result.get("isError", False)

    texts = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            texts.append(item.get("text", ""))

    if not texts:
        error_or_result = json.dumps(tool_result) if tool_result else ""
        return f"Error: {error_or_result}" if is_error else error_or_result

    message = texts[0] if len(texts) == 1 else "\n".join(texts)

    if is_error:
        logger.warning(f"MCP tool returned an error: {message}")
        return f"Error: {message}"

    return message


def _extract_sse_tool_result(sse_text: str) -> str:
    """Extract the final result from an SSE response body."""
    last_data = ""
    for line in sse_text.split("\n"):
        line = line.strip()
        if line.startswith("data:"):
            last_data = line[5:].strip()

    if not last_data:
        return sse_text

    try:
        result = json.loads(last_data)
        if "result" in result:
            return _extract_jsonrpc_tool_result(result["result"])
        return last_data
    except json.JSONDecodeError:
        return last_data


async def _call_tool_via_sse(
    tool_name: str, arguments: Dict[str, Any], config: Dict[str, Any]
) -> str:
    """Call a single MCP tool via SSE transport."""
    url = config["url"]
    headers = config.get("headers") or None

    async with sse_client(url, headers=headers) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return _extract_text_from_result(result)


async def _call_tool_via_stdio(
    tool_name: str, arguments: Dict[str, Any], config: Dict[str, Any]
) -> str:
    """Call a single MCP tool via stdio transport."""
    server_params = StdioServerParameters(
        command=config.get("command", "github-mcp-server"),
        args=config.get("args", []),
        env=dict(os.environ),
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return _extract_text_from_result(result)


# Matches a full or abbreviated git SHA (7–40 hex chars)
_SHA_PATTERN = re.compile(r"^[0-9a-f]{7,40}$", re.IGNORECASE)


def _sanitize_github_args(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize arguments before sending to the MCP GitHub server.

    1. Strip None values — MCP server rejects null for typed params
       (e.g. "parameter sha is not of type string, is <nil>")
    2. For get_file_contents, guard against the LLM passing a raw git SHA
       as the `path` parameter. A SHA is not a file path; omit it so the
       server defaults to the repo root on the default branch.
    """
    # 1. Strip None values
    args = {k: v for k, v in arguments.items() if v is not None}

    # 2. Guard: if 'path' looks like a bare SHA, replace with "" (repo root listing)
    #    and warn — a SHA is not a file path; "" causes the server to list the root dir.
    if tool_name == "get_file_contents":
        path_val = args.get("path", "")
        if isinstance(path_val, str) and _SHA_PATTERN.match(path_val):
            logger.warning(
                f"get_file_contents called with path='{path_val}' which looks like "
                f"a git SHA — replacing with '' to list the repo root instead. "
                f"Use a real file path (e.g. 'README.md') to read a specific file."
            )
            args["path"] = ""

    return args


async def _call_mcp_tool(
    tool_name: str, arguments: Dict[str, Any], config: Dict[str, Any]
) -> str:
    """
    Route a tool call to the appropriate transport.

    Opens a fresh MCP connection, invokes the tool, and closes cleanly.
    Sanitizes arguments before forwarding to protect against common LLM
    mistakes (null values, SHA passed as file path).
    """
    sanitized_args = _sanitize_github_args(tool_name, arguments)

    transport = config.get("transport", "http")

    if transport == "http":
        return await _call_tool_via_http(tool_name, sanitized_args, config)
    elif transport == "sse":
        return await _call_tool_via_sse(tool_name, sanitized_args, config)
    elif transport == "stdio":
        return await _call_tool_via_stdio(tool_name, sanitized_args, config)
    else:
        raise ValueError(f"Unsupported MCP transport: {transport}")


def _call_mcp_tool_sync(
    tool_name: str, arguments: Dict[str, Any], config: Dict[str, Any]
) -> str:
    """
    Synchronous wrapper for _call_mcp_tool.

    Used when the LangChain agent invokes tools via AgentExecutor.invoke()
    (sync path) rather than ainvoke() (async path).
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(
                asyncio.run, _call_mcp_tool(tool_name, arguments, config)
            )
            return future.result(timeout=60)
    else:
        return asyncio.run(_call_mcp_tool(tool_name, arguments, config))


# ---------------------------------------------------------------------------
# Tool schema discovery — fetch schemas then disconnect
# ---------------------------------------------------------------------------


def _create_tool_wrapper(
    tool_name: str,
    tool_description: str,
    tool_input_schema: Dict[str, Any],
    config: Dict[str, Any],
    description_override: Optional[str] = None,
) -> StructuredTool:
    """
    Create a StructuredTool wrapper for a single MCP tool.

    The wrapper has both a sync `func` and async `coroutine` so it works
    with both AgentExecutor.invoke() and ainvoke().

    Each invocation opens a fresh MCP connection, calls the tool, and
    returns the result as a string.

    Args:
        description_override: If provided, replaces the MCP server's description
            with a concise, agent-optimised version from application-tools.yaml.
    """
    effective_description = (
        description_override or tool_description or f"GitHub MCP tool: {tool_name}"
    )

    def _sync_call(**kwargs: Any) -> str:
        return _call_mcp_tool_sync(tool_name, kwargs, config)

    async def _async_call(**kwargs: Any) -> str:
        return await _call_mcp_tool(tool_name, kwargs, config)

    return StructuredTool.from_function(
        func=_sync_call,
        coroutine=_async_call,
        name=tool_name,
        description=effective_description,
        args_schema=tool_input_schema,
    )


def _load_mcp_tools_sync(config: Dict[str, Any]) -> List[StructuredTool]:
    """
    Discover MCP tool schemas and create StructuredTool wrappers.

    1. Connects to the MCP server
    2. Fetches tool schemas (name, description, inputSchema)
    3. Disconnects immediately
    4. Creates StructuredTool wrappers that call the MCP server on demand

    Description overrides from ``config["tool_descriptions"]`` replace the
    MCP server's verbose API-doc wording with concise, agent-optimised text
    that steers the LLM toward efficient tool selection.

    Args:
        config: MCP GitHub configuration dictionary

    Returns:
        List of LangChain StructuredTool objects
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, _discover_tool_schemas(config))
            schemas = future.result(timeout=30)
    else:
        schemas = asyncio.run(_discover_tool_schemas(config))

    # Description overrides from application-tools.yaml
    description_overrides: Dict[str, str] = config.get("tool_descriptions") or {}

    # Create wrapper tools from schemas
    tools = []
    for schema in schemas:
        name = schema["name"]
        tool = _create_tool_wrapper(
            tool_name=name,
            tool_description=schema["description"],
            tool_input_schema=schema["input_schema"],
            config=config,
            description_override=description_overrides.get(name),
        )
        tools.append(tool)

    logger.info(f"Created {len(tools)} MCP GitHub tool wrappers")
    overridden = [n for n in description_overrides if any(t.name == n for t in tools)]
    if overridden:
        logger.info(f"Applied description overrides for: {overridden}")
    return tools


async def _discover_tool_schemas(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Connect to the MCP server, fetch tool schemas, and disconnect.

    Returns a list of dicts with keys: name, description, input_schema.
    These schemas are used to create StructuredTool wrappers.
    """
    transport = config.get("transport", "http")

    if transport == "http":
        return await _discover_via_http(config)
    elif transport == "sse":
        return await _discover_via_sse(config)
    elif transport == "stdio":
        return await _discover_via_stdio(config)
    else:
        logger.error(f"Unsupported MCP transport: {transport}")
        return []


async def _discover_via_stdio(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Discover tool schemas via stdio transport."""
    server_params = StdioServerParameters(
        command=config.get("command", "github-mcp-server"),
        args=config.get("args", []),
        env=dict(os.environ),
    )

    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                schemas = _tools_to_schemas(result.tools)
                logger.info(
                    f"Discovered {len(schemas)} tool schemas from MCP GitHub server (stdio)"
                )
                return schemas
    except Exception as e:
        logger.error(f"Failed to discover MCP GitHub tools via stdio: {e}")
        return []


async def _discover_via_sse(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Discover tool schemas via SSE transport."""
    url = config.get("url")
    if not url:
        logger.error("MCP SSE transport requires 'url' in configuration")
        return []

    headers = config.get("headers") or None

    try:
        async with sse_client(url, headers=headers) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                schemas = _tools_to_schemas(result.tools)
                logger.info(
                    f"Discovered {len(schemas)} tool schemas from MCP GitHub server (sse: {url})"
                )
                return schemas
    except Exception as e:
        logger.error(f"Failed to discover MCP GitHub tools via SSE: {e}")
        return []


async def _discover_via_http(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Discover tool schemas via Streamable HTTP transport.

    This is the transport used by GitHub's hosted MCP endpoint:
        https://api.githubcopilot.com/mcp/

    The endpoint requires an Authorization header with a GitHub PAT:
        Authorization: Bearer <GITHUB_TOKEN>
    """
    url = config.get("url")
    if not url:
        logger.error("MCP HTTP transport requires 'url' in configuration")
        return []

    headers = dict(config.get("headers") or {})

    if not headers.get("Authorization"):
        logger.error(
            "MCP HTTP transport requires 'Authorization' header in configuration"
        )
        return []

    try:
        async with streamablehttp_client(url, headers=headers) as transport:
            read_stream, write_stream = transport[:2]

            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                schemas = _tools_to_schemas(result.tools)
                logger.info(
                    f"Discovered {len(schemas)} tool schemas from MCP GitHub server (http: {url})"
                )
                return schemas
    except Exception as e:
        logger.error(f"Failed to discover MCP GitHub tools via HTTP: {e}")
        return []


def _tools_to_schemas(tools) -> List[Dict[str, Any]]:
    """Convert MCP Tool objects to plain dicts with name/description/input_schema."""
    return [
        {
            "name": t.name,
            "description": t.description or "",
            "input_schema": t.inputSchema,
        }
        for t in tools
    ]


@ToolRegistry.register("github", "github")
class MCPGitHubToolsProvider:
    """
    MCP-based GitHub Tools Provider.

    Replaces the custom GitHubToolsProvider with a standardized MCP integration.
    Uses the official GitHub MCP server to expose GitHub operations as LangChain tools.

    The MCP server handles all GitHub API complexity:
    - Authentication (GitHub Token / GitHub App)
    - Repository discovery and access control
    - Rate limiting and pagination
    - Error handling and retries

    This provider simply:
    1. Reads config from application-tools.yaml
    2. Connects to the MCP server to discover tool schemas
    3. Creates StructuredTool wrappers (sync + async) for each tool
    4. Filters tools based on configuration
    5. Returns them to the ToolRegistry

    Each tool invocation opens a fresh MCP connection, so the agent can
    call tools long after initialization without stale session errors.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize MCP GitHub tools provider."""
        self.config = config or {}
        self._tools_cache = None

    def get_tools(self) -> List[StructuredTool]:
        """
        Get GitHub tools from the MCP server.

        Returns:
            List of LangChain StructuredTool objects from the MCP GitHub server
        """
        global _mcp_tools_cache

        # Use global cache if available
        if _mcp_tools_cache is not None:
            logger.info(
                f"✅ Loaded {len(_mcp_tools_cache)} MCP GitHub tools from cache"
            )
            return _mcp_tools_cache

        # Use instance cache if available
        if self._tools_cache is not None:
            return self._tools_cache

        mcp_config = _get_mcp_github_config()

        if not mcp_config.get("enabled", False):
            logger.info("MCP GitHub tools are disabled in configuration")
            return []

        try:
            # Load tools from MCP server
            tools = _load_mcp_tools_sync(mcp_config)

            # Apply tool filter from configuration
            tool_filter = mcp_config.get("tool_filter", [])
            if tool_filter:
                tools = _filter_tools(tools, tool_filter)

            # Cache results
            _mcp_tools_cache = tools
            self._tools_cache = tools

            logger.info(f"MCP GitHub tools initialized: {len(tools)} tools available")

            if tools:
                tool_names = [t.name for t in tools]
                logger.info(f"Available MCP GitHub tools: {tool_names}")

            return tools

        except Exception as e:
            logger.error(f"Failed to initialize MCP GitHub tools: {e}")
            return []

    def invalidate_cache(self):
        """Invalidate the tools cache to force reloading on next request."""
        global _mcp_tools_cache

        self._tools_cache = None
        _mcp_tools_cache = None

        logger.info("MCP GitHub tools cache invalidated")

    def get_connection_info(self) -> Dict[str, Any]:
        """Get MCP connection information for debugging."""
        config = _get_mcp_github_config()
        return {
            "provider": "mcp",
            "transport": config.get("transport", "stdio"),
            "command": config.get("command"),
            "url": config.get("url"),
            "enabled": config.get("enabled", False),
            "cached_tools": len(_mcp_tools_cache) if _mcp_tools_cache else 0,
        }
