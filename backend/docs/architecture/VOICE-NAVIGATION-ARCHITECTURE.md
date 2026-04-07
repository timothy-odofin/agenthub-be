# Voice & Navigation Architecture

> **Auto-sync route navigation with voice/text-driven UI actions**

**Date:** April 7, 2026
**Branch:** `feature/voice-integration`
**Status:** ✅ Implemented & Tested

---

## Table of Contents

- [Overview](#overview)
- [Architecture Diagram](#architecture-diagram)
- [Components](#components)
  - [Frontend Route Registry](#1-frontend-route-registry)
  - [Route Sync Hook](#2-route-sync-hook)
  - [Route Sync API](#3-route-sync-api)
  - [File Storage Service](#4-file-storage-service)
  - [Navigation Tools](#5-navigation-tools)
  - [Action Executor](#6-action-executor)
- [Voice Input](#voice-input)
- [Action Types](#action-types)
- [Adding New Routes](#adding-new-routes)
- [Adding New Actions](#adding-new-actions)
- [Testing](#testing)

---

## Overview

AgentHub supports voice and text-driven navigation. Users can say "go to dashboard" or "delete this chat" and the AI agent translates intent into UI actions — no hardcoded aliases needed.

**Key design decisions:**

1. **No hardcoded routes in the backend** — all routes come from the frontend via auto-sync
2. **No aliases** — the LLM decides the best route/action match based on user intent
3. **Actions are per-route** — e.g., Dashboard has DELETE, SHARE, NEW_CHAT
4. **New pages are immediately available** after the next frontend app load

---

## Architecture Diagram

```
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
```

### Full Flow (e.g., "delete this chat")

```
1. User speaks "delete this chat"
     ↓
2. Web Speech API transcribes → text input
     ↓
3. POST /api/v1/chat/message { message: "delete this chat" }
     ↓
4. Intent classifier → ToolCategory.NAVIGATION matched
     ↓
5. Agent loads navigation tools (reads routes.json)
     ↓
6. LLM calls navigate_to_route(path="/main-dashboard", action="DELETE")
     ↓
7. Tool returns JSON: { action_type: "UI_ACTION", action: { name: "DELETE", ... } }
     ↓
8. Chat API extracts action from tool output → includes in response
     ↓
9. Frontend receives response with `action` field
     ↓
10. Action Executor runs: triggers delete confirmation modal
     ↓
11. Frontend POSTs /action-completed to notify backend
```

---

## Components

### 1. Frontend Route Registry

**File:** `frontend/src/routes/registry.ts`

The single source of truth for all navigable routes. Each entry includes:

| Field | Type | Description |
|-------|------|-------------|
| `path` | string | React Router path (e.g., `/main-dashboard`) |
| `label` | string | Human-readable name (e.g., "Dashboard") |
| `description` | string | What the page does — the LLM uses this to match intent |
| `protected` | boolean | Whether authentication is required |
| `actions` | string[] | Available UI actions on this page |

```typescript
export const ROUTE_REGISTRY: RouteRegistryEntry[] = [
  {
    path: "/",
    label: "Login",
    description: "Sign in to your account",
    protected: false,
    actions: [],
  },
  {
    path: "/main-dashboard",
    label: "Dashboard",
    description: "Main chat dashboard where you can chat with the AI agent...",
    protected: true,
    actions: ["NEW_CHAT", "DELETE", "SHARE", "RENAME", "LOAD_SESSION",
              "SHOW_CAPABILITIES", "LOGOUT"],
  },
];
```

### 2. Route Sync Hook

**File:** `frontend/src/hooks/useRouteSync.ts`

Runs automatically on app startup (in `App.tsx`):

1. GETs currently stored routes from the backend
2. Compares against `ROUTE_REGISTRY` (deep JSON comparison)
3. If different, POSTs the full registry to the backend
4. Prevents double-sync in React StrictMode via `useRef`

```typescript
// In App.tsx
function App() {
  useRouteSync(); // Auto-syncs on mount
  return <Outlet />;
}
```

### 3. Route Sync API

**File:** `backend/src/app/api/v1/routes.py`

Three endpoints for route management:

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/routes` | GET | No | Get currently synced routes |
| `/api/v1/routes/sync` | POST | No | Push routes from frontend |
| `/api/v1/routes/action-completed` | POST | Yes | Notify action was executed |

Routes are public metadata (path, label, description) — no auth needed for GET/sync.

### 4. File Storage Service

**File:** `backend/src/app/infrastructure/storage/file_storage_service.py`

Atomic, thread-safe JSON file persistence:

- **Atomic writes** — write-to-temp + `os.replace()` to prevent partial reads
- **Thread-safe** — `threading.Lock` protects concurrent access
- **Generic** — works with any JSON-serializable data

```python
from app.infrastructure.storage import FileStorageService

storage = FileStorageService("routes")
storage.save({"routes": [...]})   # Write
data = storage.load()              # Read
```

Storage location: `backend/src/app/infrastructure/storage/data/routes.json`

### 5. Navigation Tools

**File:** `backend/src/app/agent/tools/navigation/navigation_tools.py`

Two LangChain tools registered under the `navigation` category:

| Tool | Description |
|------|-------------|
| `navigate_to_route` | Navigate to a page or trigger a UI action |
| `list_available_routes` | List all available routes and actions |

The tools load routes dynamically from `routes.json` at call-time, so new pages are immediately available after the next frontend sync.

### 6. Action Executor

**File:** `frontend/src/lib/actions/action-executor.ts`

Processes structured action payloads from the backend and executes them:

```typescript
// In ChatLayout.tsx — after receiving a chat response
if (res.data.action) {
  setTimeout(() => {
    executeAction(res.data.action, actionHandlers());
  }, 800); // Small delay so user sees the AI message first
}
```

The executor handles auth checks (protected routes), navigation, and UI actions.

---

## Voice Input

**Files:**
- `frontend/src/components/chat/MainChatInput.tsx` — Main chat voice input
- `frontend/src/pages/ConversationalSignup.tsx` — Signup flow voice input
- `frontend/src/types/speech.d.ts` — Web Speech API type declarations

### How It Works

1. User clicks the 🎤 microphone button
2. `SpeechRecognition` API starts listening (browser-native, no external service)
3. Speech is transcribed to text in real-time
4. Transcript is placed in the input field
5. After 300ms, the message is auto-sent

### Design Decisions

- **No external API** — Uses the browser's built-in Web Speech API (free, no latency)
- **Feature detection** — Voice button only shown if `window.SpeechRecognition` is available
- **Password safety** — Voice input is disabled on the password step during signup
- **Auto-send** — Transcript is automatically submitted after a brief delay
- **Visual feedback** — Pulsing red indicator while listening, with cancel option
- **Typing cancels listening** — If user starts typing, voice recognition stops

---

## Action Types

### NAVIGATE

Pure page navigation. No in-page action.

```json
{
  "action_type": "NAVIGATE",
  "action": {
    "route": "/signup",
    "title": "Sign Up",
    "protected": false
  },
  "message": "Navigating to Sign Up (/signup)"
}
```

### UI_ACTION

In-page action with optional navigation.

```json
{
  "action_type": "UI_ACTION",
  "action": {
    "route": "/main-dashboard",
    "title": "Dashboard",
    "protected": true,
    "name": "DELETE",
    "params": { "session_id": "abc123" }
  },
  "message": "Deleting session abc123"
}
```

### Supported UI Actions

| Action | Params | Description |
|--------|--------|-------------|
| `NEW_CHAT` | — | Start a fresh chat session |
| `DELETE` | `session_id?` | Delete a chat session (defaults to current) |
| `SHARE` | `session_id?` | Open the share modal |
| `RENAME` | `session_id?`, `new_title` | Rename a session |
| `LOAD_SESSION` | `session_id` | Load a specific session |
| `SHOW_CAPABILITIES` | — | Show the capabilities view |
| `LOGOUT` | — | Clear tokens and redirect to login |

---

## Adding New Routes

When a new page is added to the frontend:

1. **Add the route to `routes/index.tsx`** (React Router)
2. **Add an entry to `ROUTE_REGISTRY`** in `routes/registry.ts`
3. **That's it** — the sync hook pushes it to the backend on next app load

No backend changes needed. The LLM will automatically see the new route.

### Example: Adding a Settings Page

```typescript
// 1. routes/index.tsx — add the React Router route
{
  path: "/settings",
  element: <ProtectedRoute><SettingsPage /></ProtectedRoute>,
}

// 2. routes/registry.ts — add registry entry
{
  path: "/settings",
  label: "Settings",
  description: "Account settings, preferences, and configuration",
  protected: true,
  actions: ["CHANGE_PASSWORD", "UPDATE_PROFILE", "MANAGE_NOTIFICATIONS"],
}
```

## Adding New Actions

To add a new UI action to an existing route:

1. **Add the action name to the route's `actions` array** in `registry.ts`
2. **Add a case to `handleUIAction`** in `action-executor.ts`
3. **Add a handler callback** to `ActionHandlers` interface

No backend changes needed.

---

## Testing

### Direct Tool Tests (Deterministic)

10 tests that call the navigation tool function directly — no LLM involved:

```bash
cd backend
pytest tests/integration/test_navigation_routing.py::TestNavigationToolDirect -v
```

Tests cover: navigate to each route, all action types, invalid routes, invalid actions, params, reason field.

### LLM Integration Tests

7 tests that verify the real LLM agent picks the right tool:

```bash
cd backend
pytest tests/integration/test_navigation_routing.py::TestNavigationRouting -v
```

Tests cover: "go to dashboard", "take me to signup", "go home", "start new chat", "delete this session", general question (should NOT trigger nav), "show capabilities".

---

## Related Documentation

- [Intent Classifier](#intent-classifier) — How navigation intent is detected
- [Prompt Optimization](./PROMPT-OPTIMIZATION-2026-04-07.md) — System prompt changes
- [Tools Guide](../guides/tools/README.md) — Tool integration patterns
- [Chat API](../api-reference/chat.md) — Chat message API with action field
