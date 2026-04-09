# Navigation Tools

> **LLM-driven voice/text navigation with auto-synced routes**

---

## Overview

Navigation tools enable the AI agent to navigate users to pages and trigger UI actions via voice or text commands. Unlike traditional navigation, there are **no hardcoded route aliases** — the LLM reads available routes dynamically and decides the best match.

**Category:** `navigation`
**Provider:** `NavigationTools`
**Location:** `src/app/agent/tools/navigation/navigation_tools.py`

---

## Available Tools

### `navigate_to_route`

Navigate the user to a page or trigger a UI action.

**When the LLM should use this tool:**
- User wants to go to a page ("go to dashboard", "take me to signup")
- User wants to perform an action ("start new chat", "delete this session", "log out")
- User wants both ("go to dashboard and start a new chat")

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `route_path` | string | Yes | Route path (e.g., `/main-dashboard`) |
| `action_name` | string | No | Action to perform (e.g., `DELETE`, `NEW_CHAT`) |
| `action_params` | object | No | Parameters for the action (e.g., `{ session_id: "abc" }`) |
| `reason` | string | No | Why this navigation/action was chosen |

**Returns:** JSON with `action_type` (`NAVIGATE`, `UI_ACTION`, or `ERROR`), `action` details, and `message`.

**Example invocations:**

```
User: "go to the dashboard"
→ navigate_to_route(route_path="/main-dashboard")
→ { action_type: "NAVIGATE", action: { route: "/main-dashboard", ... } }

User: "delete this chat"
→ navigate_to_route(route_path="/main-dashboard", action_name="DELETE")
→ { action_type: "UI_ACTION", action: { name: "DELETE", ... } }

User: "rename this chat to My Project"
→ navigate_to_route(route_path="/main-dashboard", action_name="RENAME",
                     action_params={ new_title: "My Project" })
```

---

### `list_available_routes`

List all available pages and UI actions in the application.

**When the LLM should use this tool:**
- User asks "where can I go?"
- User asks "what can I do?"
- User asks "what pages are available?"

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by `protected` or `public` |

**Returns:** JSON with list of routes and their actions.

---

## How Routes Are Synced

Routes are **not hardcoded** in the backend. The frontend pushes its route registry on every app startup:

1. Frontend defines routes in `routes/registry.ts`
2. `useRouteSync()` hook runs on app mount
3. Hook GETs current backend routes, compares with local registry
4. If different, POSTs the full registry to `/api/v1/routes/sync`
5. Backend stores in `routes.json` via `FileStorageService`
6. Navigation tool reads `routes.json` at call-time

**To add a new route:** Just update `routes/registry.ts` — no backend changes needed.

---

## Configuration

Navigation tools are configured in `resources/application-tools.yaml`:

```yaml
tools:
  navigation:
    enabled: true
    available_tools:
      navigate_to_route:
        enabled: true
      list_available_routes:
        enabled: true
```

---

## Intent Classification

The intent classifier automatically includes `ToolCategory.NAVIGATION` when it detects navigation patterns:

- "go to", "take me", "navigate", "open", "switch to"
- "dashboard", "login", "signup", "sign out", "log out"
- "page", "screen", "route", "view"

Navigation is also in the `_ALWAYS_INCLUDE` set, so it's loaded alongside any other matched category.

---

## Testing

```bash
# Direct tool tests (10 tests, deterministic, no LLM)
pytest tests/integration/test_navigation_routing.py::TestNavigationToolDirect -v

# LLM integration tests (7 tests, real LLM)
pytest tests/integration/test_navigation_routing.py::TestNavigationRouting -v
```

---

## Related Documentation

- [Voice & Navigation Architecture](../../architecture/VOICE-NAVIGATION-ARCHITECTURE.md) — Full architecture overview
- [Confirmation Workflow](./confirmation-workflow.md) — For mutating actions
- [Tools README](./README.md) — All tool integrations
