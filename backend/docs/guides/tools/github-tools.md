# GitHub Tools (MCP Integration)

GitHub tools give agents real-time access to repositories, issues, pull requests, and code search via the **Model Context Protocol (MCP)**. The integration uses GitHub's official hosted MCP server instead of custom tool code, so authentication, pagination, and rate-limiting are all handled server-side.

---

## Overview

| Attribute | Value |
|-----------|-------|
| Provider | `MCPGitHubToolsProvider` |
| Registry category | `github` |
| Transport | Streamable HTTP (default) / SSE / stdio |
| MCP endpoint | `https://api.githubcopilot.com/mcp/` |
| Tool count exposed | **10** (filtered from ~34 available) |
| Auth | `GITHUB_TOKEN` (Personal Access Token or GitHub App token) |

### How it works

```
Agent
  └─► StructuredTool.func / coroutine
        └─► JSON-RPC 2.0 POST (httpx)
              └─► GitHub MCP Server (api.githubcopilot.com/mcp/)
                    └─► GitHub REST API
```

During **initialization** the provider connects to the MCP server once to discover tool schemas (name, description, input schema), then immediately disconnects. Each subsequent tool call opens a fresh connection, makes the call, and closes — no stale session state.

---

## Available Tools

These are the 10 tools exposed to the agent (filtered from all ~34 the MCP server offers):

| Tool | Type | Description |
|------|------|-------------|
| `search_code` | Read | **Start here for codebase questions.** Full-text search across all files in a repo |
| `search_repositories` | Read | Find repos by name or topic; returns owner/name slug |
| `get_file_contents` | Read | Read a specific file or list a directory (requires a known path) |
| `list_issues` | Read | List issues with optional filters (state, labels, assignee) |
| `get_issue` | Read | Get full details of a single issue by number |
| `list_pull_requests` | Read | List PRs with optional filters (state, base branch) |
| `get_pull_request` | Read | Get full details of a single PR |
| `create_pull_request` | **Mutating** | Create a PR — requires confirmation workflow |
| `create_issue` | **Mutating** | Create an issue — requires confirmation workflow |
| `add_issue_comment` | **Mutating** | Add a comment to an issue — requires confirmation workflow |

> **Why only 10?** The MCP server exposes ~34 tools. Exposing all of them floods the LLM with irrelevant choices (e.g. `update_gist`, `manage_repository_notification`) and wastes context tokens. A focused list improves planning accuracy and reduces iterations. See [Architecture Notes](#architecture-notes) below.

---

## Configuration

### Environment Variables

```bash
# Required — GitHub Personal Access Token or App token
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Optional — override transport (default: http)
GITHUB_MCP_TRANSPORT=http

# Optional — override MCP endpoint (default: GitHub's hosted endpoint)
GITHUB_MCP_URL=https://api.githubcopilot.com/mcp/

# Optional — override local stdio binary path
GITHUB_MCP_COMMAND=github-mcp-server
```

### `application-tools.yaml`

```yaml
github:
  enabled: true
  transport: "${GITHUB_MCP_TRANSPORT:http}"
  url: "${GITHUB_MCP_URL:https://api.githubcopilot.com/mcp/}"
  headers:
    Authorization: "Bearer ${GITHUB_TOKEN}"

  # Restrict which MCP tools the agent can see.
  # Empty list = expose all ~34 tools (not recommended).
  tool_filter:
    - search_code
    - search_repositories
    - get_file_contents
    - list_issues
    - get_issue
    - list_pull_requests
    - get_pull_request
    - create_pull_request
    - create_issue
    - add_issue_comment

  # Override MCP server descriptions with concise, agent-optimised text.
  # Stored here so they can be tuned without touching Python code.
  tool_descriptions:
    search_code: >-
      **START HERE for any codebase question.** Full-text search across all files in a
      GitHub repository. Use targeted queries like class names, function names, decorators,
      or patterns (e.g. "Factory", "@register", "BaseModel", "Abstract"). Returns matching
      file paths and snippets — far faster than browsing directories with get_file_contents.
      Always prefer this over get_file_contents when exploring or answering architecture questions.
    get_file_contents: >-
      Read a specific file or list a directory in a GitHub repository. Requires a known
      file path (e.g. "README.md", "src/app/main.py"). Do NOT use for exploring unknown
      structure — use search_code instead. Do NOT pass a git SHA as the path.
      Pass path="" or path="." to list the root directory.
    # ... (other overrides follow the same pattern)
```

### Transports

| Transport | When to use | Config |
|-----------|-------------|--------|
| `http` | **Default.** GitHub's hosted MCP endpoint | `GITHUB_MCP_TRANSPORT=http` |
| `sse` | Self-hosted MCP server with SSE | `GITHUB_MCP_TRANSPORT=sse` + `GITHUB_MCP_URL=<your-url>` |
| `stdio` | Local dev with `github-mcp-server` binary | `GITHUB_MCP_TRANSPORT=stdio` |

---

## Intent Classification

The intent classifier routes messages to the GitHub tool category when it detects:

| Pattern type | Examples |
|---|---|
| Explicit GitHub terms | `github`, `repo`, `repository`, `pull request`, `PR`, `branch`, `commit` |
| Code search | `source code`, `search code`, `file in repo` |
| Codebase exploration | `codebase`, `application code`, `source files` |
| Architecture questions | `design patterns`, `architecture`, `how is it structured` |
| Project structure | `folder structure`, `directory structure`, `project structure` |
| Pattern keywords | `Factory`, `Singleton`, `Registry`, `Abstract`, `decorator` |
| "How does X work?" | `how does ... work`, `how is ... implemented` |

**Important:** If none of these patterns match, the general fallback set is used which **excludes** GitHub tools (they are heavy to load and irrelevant for general conversation). GitHub tools are loaded on-demand only.

**File:** `src/app/services/intent_classifier.py`

---

## Usage Examples

### Answering a codebase / architecture question

**Efficient approach (≤ 3 tool calls):**

1. `search_code(query="Factory OR Registry OR Abstract OR BaseModel", repo="owner/repo")`
   → Returns file paths and snippets showing where patterns are implemented
2. `get_file_contents(owner="owner", repo="repo", path="README.md")`
   → Architecture overview
3. **Answer** — synthesise from results

**Do NOT do this (slow, burns iterations):**

```
get_file_contents(path="src")          # list directory
get_file_contents(path="src/app")      # list subdirectory
get_file_contents(path="src/app/main.py")  # open file
get_file_contents(path="src/app/core") # list another subdirectory
... (13+ calls to answer one question)
```

### Finding a repository

```
search_repositories(query="agenthub-be")
→ { "owner": "timothy-odofin", "repo": "agenthub-be", ... }
```

### Listing open issues

```
list_issues(owner="timothy-odofin", repo="agenthub-be", state="open")
```

### Creating an issue (confirmation required)

```
# Step 1 — prepare
prepare_action(
  tool_name="create_issue",
  tool_args={"owner": "...", "repo": "...", "title": "...", "body": "..."},
  risk_level="medium",
  user_id="...",
  session_id="..."
)
# → Shows preview to user, asks for confirmation

# Step 2 — user says "yes"
confirm_action(action_id="...", user_id="...")
# → Issue is created
```

---

## Known Pitfalls & Guardrails

### SHA passed as file path

The LLM occasionally passes a git commit SHA as the `path` parameter to `get_file_contents`. This returns a `422` error from the MCP server.

**Guardrail in code:** `_sanitize_github_args()` in `mcp_github_tools.py` detects any 7–40 character hex string in `path` and replaces it with `""` (which lists the root directory), then logs a warning.

**Guardrail in prompt:** The system prompt section `## GitHub Tool Usage Rules` explicitly states: *"NEVER use a commit SHA as a file path."*

### Tool errors return strings, not exceptions

When the MCP server returns `isError: true`, the tool returns `"Error: <message>"` as a string instead of raising a `RuntimeError`. This allows the agent to read the error and self-correct, rather than crashing.

### Redis reconnects on each web tool call

When the agent calls `read_url` from inside `AgentExecutor` (which runs tools in a `ThreadPoolExecutor`), the Redis connection's TCP transport is bound to the main event loop and appears closed in the thread's new loop.

**Fix:** `RedisConnectionManager.ensure_connected()` is overridden to perform a real async `PING` before every operation. If the ping fails, it reconnects transparently. A `WARNING` log line is emitted: `"Redis ping failed on existing client — reconnecting"`.

---

## Architecture Notes

### Why MCP instead of direct GitHub API calls?

| Aspect | Direct API | MCP |
|--------|-----------|-----|
| Auth complexity | Manual token handling | Handled by MCP server |
| Pagination | Manual | Handled by MCP server |
| New endpoints | Write new tool | Free automatically |
| Tool count | 5–8 focused | ~34 (filtered to 10) |
| Per-call latency | ~100–200 ms | ~400–800 ms (two hops) |
| Cold start | Fast | Schema discovery on first load (~2 s) |

MCP wins on **maintenance** — no custom tool code to write or maintain when GitHub adds new API endpoints. The trade-off is slightly higher per-call latency due to the extra hop through the MCP server.

### Why `tool_filter`?

Without filtering, the agent receives all ~34 GitHub tools in its context window. More tools means:
- More tokens consumed per request (larger function schema block)
- LLM takes more reasoning steps to decide which tool to use
- Higher chance of picking a suboptimal tool chain

Filtering to 10 tools keeps the agent focused and cuts GitHub's token footprint by ~65%.

### Why `tool_descriptions` overrides?

The MCP server's built-in descriptions are written as API documentation — accurate but verbose and not directive. Agent-optimised descriptions:
- Start with the most common correct action ("**START HERE for codebase questions**")
- Include explicit negative guidance ("Do NOT use for exploring unknown structure")
- Match the language users and the LLM naturally use

Descriptions are stored in `application-tools.yaml` (not Python code) so they can be tuned without a deployment.

### `max_iterations` and `max_execution_time`

`AgentExecutor` is now constructed with:
```python
AgentExecutor(
    max_iterations=15,          # from config, default 15
    max_execution_time=120,     # seconds, default 120
    ...
)
```

Previously `max_iterations` was defined in `AgentContext` but **never passed** to `AgentExecutor`, so LangChain's hardcoded default of 15 was used silently. Now it is explicitly set and configurable per-agent via `config["max_iterations"]`.

`early_stopping_method` was removed (deprecated in LangChain 0.3.x). When the iteration or time limit is reached, the executor now automatically returns whatever the agent has produced so far — the same behaviour `"generate"` previously provided explicitly.

---

## File Reference

| File | Purpose |
|------|---------|
| `src/app/agent/tools/mcp_github/mcp_github_tools.py` | Tool provider, schema discovery, HTTP transport, arg sanitisation |
| `src/app/services/intent_classifier.py` | Keyword patterns that route to GitHub category |
| `src/app/agent/frameworks/langchain_agent.py` | `AgentExecutor` construction with `max_iterations` |
| `resources/application-tools.yaml` | `tool_filter` and `tool_descriptions` overrides |
| `resources/application-prompt.yaml` | System prompt: GitHub rules + codebase question guidance |
| `tests/unit/agent/tools/test_mcp_github_tools.py` | 52 unit tests covering all guardrails |

---

## Testing

```bash
# Run all MCP GitHub tool tests
pytest tests/unit/agent/tools/test_mcp_github_tools.py -v

# Run a specific class
pytest tests/unit/agent/tools/test_mcp_github_tools.py::TestSanitizeGithubArgs -v
pytest tests/unit/agent/tools/test_mcp_github_tools.py::TestExtractJsonrpcToolResult -v
pytest tests/unit/agent/tools/test_mcp_github_tools.py::TestCallToolViaHTTP -v
```

**Test coverage:**
- `TestSanitizeGithubArgs` — SHA-as-path detection, None stripping, non-SHA paths left alone
- `TestExtractJsonrpcToolResult` — error returns string (not raises), single/multi-content
- `TestExtractTextFromResult` — MCP SDK result extraction
- `TestCallToolViaHTTP` — JSON-RPC success, error, SSE response paths
- `TestCallMCPTool` — transport routing, sanitisation applied before call
- `TestMCPGitHubToolsProvider` — disabled config, cache hit, filter applied

---

## Related Documentation

- [Architecture: MCP GitHub Integration (April 9, 2026)](../../architecture/MCP-GITHUB-INTEGRATION-2026-04-09.md)
- [Confirmation Workflow](./confirmation-workflow.md) — required for mutating tools
- [Web Tools](./web-tools.md) — `read_url` (do not use for GitHub code browsing)
- [Tools README](./README.md) — all tool integrations overview
- [Prompt Optimization (April 7, 2026)](../../architecture/PROMPT-OPTIMIZATION-2026-04-07.md)
