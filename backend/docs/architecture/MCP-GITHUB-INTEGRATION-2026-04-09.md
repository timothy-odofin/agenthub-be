# MCP GitHub Integration — April 9, 2026

> **GitHub tools via Model Context Protocol: guardrails, efficiency improvements, and agent optimisations**

**Branch:** `feature/github-mcp-integration`
**Status:** ✅ Implemented & Tested (52 tests passing)

---

## Table of Contents

- [Summary of Changes](#summary-of-changes)
- [Problem Analysis](#problem-analysis)
- [Changes Made](#changes-made)
  - [1. SHA-as-path guardrail](#1-sha-as-path-guardrail)
  - [2. Error handling — return strings not raise](#2-error-handling--return-strings-not-raise)
  - [3. Tool list reduced 14 → 10](#3-tool-list-reduced-14--10)
  - [4. Tool description overrides](#4-tool-description-overrides)
  - [5. Intent classifier — codebase patterns](#5-intent-classifier--codebase-patterns)
  - [6. AgentExecutor max_iterations wired up](#6-agentexecutor-max_iterations-wired-up)
  - [7. WebTools async sync wrapper](#7-webtools-async-sync-wrapper)
  - [8. Redis stale connection fix](#8-redis-stale-connection-fix)
  - [9. System prompt additions](#9-system-prompt-additions)
  - [10. Frontend MarkdownRenderer](#10-frontend-markdownrenderer)
- [Modified Files](#modified-files)
- [Test Results](#test-results)

---

## Summary of Changes

| Area | Problem | Fix |
|------|---------|-----|
| GitHub tools | LLM passes SHA as file path → `422` error | `_sanitize_github_args()` replaces SHA-in-path with `""` |
| GitHub tools | `isError: true` crashed agent with `RuntimeError` | All error paths return `"Error: ..."` string |
| GitHub tools | 14 tools exposed, LLM picks wrong ones | Filtered to 10; `search_code` listed first |
| GitHub tools | MCP server descriptions are API docs, not agent guidance | `tool_descriptions` overrides in YAML |
| Intent classifier | "design patterns" → general set (no GitHub tools) | Added codebase/architecture patterns to GitHub category |
| AgentExecutor | `max_iterations=10` defined but never passed to executor | Wired into `AgentExecutor(max_iterations=...)` |
| AgentExecutor | `early_stopping_method="generate"` unsupported in LangChain 0.3 | Removed (behaviour is now the default) |
| WebTools | `func=async_method` → "coroutine never awaited" warning | `_run_async()` helper + sync wrapper functions |
| Redis | `TCPTransport closed=True` in ThreadPoolExecutor threads | `ensure_connected()` override with real async PING |
| Frontend | Inline code rendered as dark terminal block | `MarkdownRenderer.tsx` split into `pre()` + `code()` components |
| Frontend | Code block text invisible (near-white on light background) | Removed `rehype-highlight` + dead `!important` CSS |

---

## Problem Analysis

### Agent hitting max iterations on codebase questions

When a user asked *"what are the major design patterns used for the application code?"*, the log showed:

```
Intent: general set (6 categories, excludes github)
→ web tools loaded, github tools NOT loaded
→ agent calls read_url("github.com/owner/repo/tree/main/src")  [1 iteration]
→ agent calls read_url("github.com/.../src/app")               [2 iterations]
→ agent calls read_url("github.com/.../src/app/main.py")       [3 iterations]
... 13 web URL fetches later ...
→ Agent stopped due to max iteration
```

**Root causes:**

1. `"design patterns"` matched no GitHub keywords → general fallback → no GitHub MCP tools
2. Agent used `read_url` (generic web scraper) to crawl GitHub HTML pages — each call takes ~2 s plus Redis reconnect overhead
3. `max_iterations` was set in `AgentContext` but silently ignored by `AgentExecutor`
4. MCP tool descriptions didn't guide the agent toward `search_code` for architecture questions

### SHA-as-path `422` error

The LLM called `get_file_contents` with `path=<40-char hex string>` (a commit SHA). The MCP server rejected it with HTTP 422 and `"path does not point to a file"`. The original code raised `RuntimeError`, crashing the agent.

### Coroutine never awaited (WebTools)

LangChain's `AgentExecutor.invoke()` calls tools synchronously via `tool.func(...)`. `WebTools` tools were constructed with `func=self._read_dynamic_url` (an `async` method). The sync path got back an unawaited coroutine, producing:

```
RuntimeWarning: coroutine 'WebTools._read_dynamic_url' was never awaited
```

### Redis TCPTransport closed

`AgentExecutor.invoke()` runs in a `ThreadPoolExecutor` thread via `asyncio.get_event_loop().run_in_executor(...)`. Inside that thread, tool wrappers call `asyncio.run(coro)`, which creates a **new event loop**. The shared Redis client's TCP transport was created on the main event loop and is therefore "closed" from the new loop's perspective.

The old `ensure_connected()` called `is_healthy()` — a sync no-op that just checked `if self._redis_client is not None` — and reused the stale client, producing:

```
RuntimeError: unable to perform operation on <TCPTransport closed=True>
```

---

## Changes Made

### 1. SHA-as-path guardrail

**File:** `src/app/agent/tools/mcp_github/mcp_github_tools.py`

Added `_SHA_PATTERN = re.compile(r"^[0-9a-f]{7,40}$", re.IGNORECASE)` and `_sanitize_github_args()`:

```python
def _sanitize_github_args(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Strip None values — MCP server rejects null for typed params
    args = {k: v for k, v in arguments.items() if v is not None}

    # 2. Replace SHA-as-path with "" (list repo root) instead of erroring
    if tool_name == "get_file_contents":
        path_val = args.get("path", "")
        if isinstance(path_val, str) and _SHA_PATTERN.match(path_val):
            logger.warning(f"SHA passed as path — replacing with '' to list root")
            args["path"] = ""

    return args
```

Replacing with `""` (not removing the key) is intentional: an absent `path` causes the server to return `"path does not point to a file"`, but `path=""` causes it to list the root directory — which is the most useful recovery action.

---

### 2. Error handling — return strings not raise

**File:** `src/app/agent/tools/mcp_github/mcp_github_tools.py`

All error paths (`_extract_jsonrpc_tool_result`, `_extract_text_from_result`, JSON-RPC level errors) now **return** `"Error: <message>"` instead of raising `RuntimeError`.

**Before:**
```python
if is_error:
    raise RuntimeError(f"MCP tool error: {message}")
```

**After:**
```python
if is_error:
    logger.warning(f"MCP tool returned an error: {message}")
    return f"Error: {message}"
```

This lets LangChain feed the error back to the LLM as an observation. The agent can read it and self-correct (e.g., try a different path) rather than crashing the entire request.

---

### 3. Tool list reduced 14 → 10

**File:** `resources/application-tools.yaml`

**Removed:**

| Tool | Reason |
|------|--------|
| `list_branches` | Rarely needed for Q&A queries |
| `create_branch` | Mutating op almost never needed for codebase questions |
| `get_commit` | LLM used it to retrieve SHAs, then passed them as paths |
| `list_commits` | Same SHA-retrieval anti-pattern as `get_commit` |

**Reordered:** `search_code` is now **first** in `tool_filter`. LangChain passes tools to the LLM in the order they appear — listing `search_code` first biases the model toward it for the most common query type.

---

### 4. Tool description overrides

**Files:** `resources/application-tools.yaml`, `src/app/agent/tools/mcp_github/mcp_github_tools.py`

Added a `tool_descriptions` map in YAML. `_load_mcp_tools_sync()` reads this map and passes each override to `_create_tool_wrapper()`, which uses it in place of the MCP server's description.

Key changes:
- `search_code` prefixed with `**START HERE for any codebase question.**`
- `get_file_contents` includes explicit `"Do NOT use for exploring unknown structure"` warning
- Descriptions are YAML-only — no code change needed to tune them

---

### 5. Intent classifier — codebase patterns

**File:** `src/app/services/intent_classifier.py`

Added patterns to `ToolCategory.GITHUB` to catch architecture and codebase questions:

```python
re.compile(r"\b(codebase|code\s*base|application\s*code|source\s*files?)\b", re.I),
re.compile(r"\b(design\s*patterns?|architecture|architectural|software\s*design)\b", re.I),
re.compile(r"\b(how\s+is\s+.*(structured|organized|built|implemented|designed))\b", re.I),
re.compile(r"\b(folder\s*structure|directory\s*structure|project\s*structure)\b", re.I),
re.compile(r"\b(class\s*diagram|module|package|layer|Factory|Singleton|Observer|Strategy)\b", re.I),
re.compile(r"\b(what\s+.*(pattern|patterns|approach)\s+.*(use|used|applied|implemented))\b", re.I),
```

**Impact:** *"What are the major design patterns used for the application code?"* now routes to GitHub tools instead of the general fallback, giving the agent `search_code` as its primary instrument.

---

### 6. AgentExecutor max_iterations wired up

**File:** `src/app/agent/frameworks/langchain_agent.py`

`AgentContext.max_iterations` was defined but `AgentExecutor` was built without it, silently using LangChain's own default.

**Before:**
```python
self.executor = AgentExecutor(
    agent=self.agent,
    tools=self.tools,
    verbose=self.verbose,
    return_intermediate_steps=True,
)
```

**After:**
```python
self.executor = AgentExecutor(
    agent=self.agent,
    tools=self.tools,
    verbose=self.verbose,
    return_intermediate_steps=True,
    max_iterations=self.config.get("max_iterations", 15),
    max_execution_time=self.config.get("max_execution_time", 120),
)
```

Applied to both `initialize()` and `reinitialize_with_tools()`.

`early_stopping_method="generate"` was also removed — it was deprecated and unsupported in LangChain 0.3.x (`"Got unsupported early_stopping_method 'generate'"`). In 0.3.x, the executor automatically returns the agent's current output when limits are hit.

---

### 7. WebTools async sync wrapper

**File:** `src/app/agent/tools/web/web_tools.py`

Added a module-level `_run_async()` helper and split each tool into a sync wrapper + async coroutine:

```python
def _run_async(coro) -> str:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=60)
    else:
        return asyncio.run(coro)
```

Each `StructuredTool` is created with:
```python
tool = StructuredTool(
    func=search_url_sync,       # sync wrapper calling _run_async(coro)
    coroutine=search_url_async, # native async for ainvoke() path
    ...
)
```

This ensures `AgentExecutor.invoke()` (sync path) never receives an unawaited coroutine.

---

### 8. Redis stale connection fix

**File:** `src/app/infrastructure/connections/database/redis_connection_manager.py`

Overrode `ensure_connected()` with a real async PING check:

```python
async def ensure_connected(self) -> Redis:
    if self._redis_client:
        try:
            await self._redis_client.ping()
            return self._redis_client
        except Exception:
            logger.warning(
                "Redis ping failed on existing client — reconnecting "
                "(connection may be bound to a different event loop)."
            )
            await self.disconnect()
    return await self.connect()
```

The base class `ensure_connected()` called `is_healthy()` — a sync method that just checks `if self._redis_client is not None`. It could not detect a stale TCP transport. The override replaces this with an actual async PING. If the PING fails (stale loop), it disconnects and reconnects transparently.

`is_healthy()` is also updated to check both `_redis_client` and `_connection_pool` are non-None, and its docstring clarifies it is a sync-only existence check — not a liveness check.

---

### 9. System prompt additions

**File:** `resources/application-prompt.yaml`

Added two new sections:

**`## GitHub Tool Usage Rules`** (existed, expanded):
- NEVER use a commit SHA as a file path
- NEVER pass SHA to `sha` parameter unless retrieved from a prior tool call
- Correct sequence to explore a repo (4-step guide)

**`## Codebase & Architecture Questions`** (new):
- Use GitHub MCP tools first (`search_code`, `get_file_contents`)
- Do NOT use `read_url` to crawl GitHub HTML pages
- Synthesise from ≤ 5 tool calls
- `search_code` is the power tool for pattern discovery
- Example efficient 3-call flow for "what design patterns are used?"

---

### 10. Frontend MarkdownRenderer

**Files:** `frontend/src/components/MarkdownRenderer.tsx`, `frontend/src/index.css`

**Problem 1 — Inline code shown as dark terminal block:**

`react-markdown` v10 removed the `inline` prop from its `code` component. Old code checked `!inline` to decide whether to render a terminal block; without the prop, `!inline` was always `true`, so even single backtick spans like `` `langchain-core` `` got rendered as dark terminal blocks.

**Fix:** Split into two components — `pre()` handles block code wrappers, `code()` detects inline vs block by inspecting `node.parent.tagName`:

```tsx
pre({ children }) {
  // block code — renders the dark/light container + copy button
},
code({ node, children, ...props }) {
  const isBlock = node?.parent?.type === 'element' && node?.parent?.tagName === 'pre';
  if (isBlock) {
    return <code className="bg-transparent text-inherit ...">{children}</code>;
  }
  // inline — pill styling
  return <code className="bg-gray-100 text-red-600 ...">{children}</code>;
}
```

**Problem 2 — Code block text invisible:**

`rehype-highlight` + `github-dark.css` were removed, but `index.css` still contained:

```css
.markdown-content pre code,
.markdown-content pre code * {
  color: #e6edf3 !important;  /* near-white */
}
```

This `!important` rule forced near-white text on the now light-gray (`bg-gray-100`) background — invisible in light mode.

**Fix:** Removed the entire `rehype-highlight`/`hljs-*` CSS block from `index.css`. Code blocks now use Tailwind classes only: `bg-gray-100 text-gray-800` (light mode) / `dark:bg-gray-800 dark:text-gray-100` (dark mode).

---

## Modified Files

| File | Change type |
|------|-------------|
| `src/app/agent/tools/mcp_github/mcp_github_tools.py` | Core — SHA guardrail, error handling, description overrides |
| `src/app/services/intent_classifier.py` | Added codebase/architecture patterns to GitHub category |
| `src/app/agent/frameworks/langchain_agent.py` | Wire `max_iterations` + `max_execution_time` into `AgentExecutor` |
| `src/app/agent/tools/web/web_tools.py` | `_run_async()` helper + sync/async tool split |
| `src/app/infrastructure/connections/database/redis_connection_manager.py` | Override `ensure_connected()` with real PING |
| `resources/application-tools.yaml` | `tool_filter` (14→10), `tool_descriptions` overrides map |
| `resources/application-prompt.yaml` | GitHub rules + codebase question guidance |
| `frontend/src/components/MarkdownRenderer.tsx` | Remove `rehype-highlight`, fix inline/block code detection |
| `frontend/src/index.css` | Remove dead `hljs-*` and `!important` colour overrides |
| `tests/unit/agent/tools/test_mcp_github_tools.py` | 52 tests covering all guardrails |

---

## Test Results

```
tests/unit/agent/tools/test_mcp_github_tools.py — 52 passed
```

Key test classes:
- `TestSanitizeGithubArgs` — SHA replaced with `""`, None values stripped, valid paths left alone
- `TestExtractJsonrpcToolResult` — `isError: true` returns `"Error: ..."` string (not raises)
- `TestExtractTextFromResult` — MCP SDK error returns string (not raises)
- `TestCallToolViaHTTP` — JSON-RPC error returns string, SSE parsing, success path
- `TestCallMCPTool` — transport routing, sanitisation applied pre-call
- `TestMCPGitHubToolsProvider` — disabled config, cache hit, `tool_filter` applied

---

## Related Documentation

- [GitHub Tools Guide](../guides/tools/github-tools.md)
- [Prompt Optimization (April 7, 2026)](./PROMPT-OPTIMIZATION-2026-04-07.md)
- [Cache Architecture](./CACHE-ARCHITECTURE-TWO-LAYER-DESIGN.md)
- [Web Tools Guide](../guides/tools/web-tools.md)
