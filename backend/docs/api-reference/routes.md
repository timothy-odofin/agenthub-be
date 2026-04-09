# Route Sync API

> **Frontend ↔ Backend route synchronization for LLM-driven navigation**

**Base Path:** `/api/v1/routes/`

---

## Overview

The Route Sync API enables the frontend to push its route definitions to the backend. The backend stores them so the LLM navigation tool can read routes dynamically — no hardcoded routes needed.

**Why no auth for GET/sync?** Routes are public metadata (path, label, description). The sync happens before login during app startup.

---

## Endpoints

### GET /api/v1/routes

Get the currently synced routes from storage.

**Authentication:** Not required

**Success Response** (200 OK):

```json
{
  "success": true,
  "routes": [
    {
      "path": "/",
      "label": "Login",
      "description": "Sign in to your account",
      "protected": false,
      "actions": []
    },
    {
      "path": "/main-dashboard",
      "label": "Dashboard",
      "description": "Main chat dashboard...",
      "protected": true,
      "actions": ["NEW_CHAT", "DELETE", "SHARE", "RENAME", "LOAD_SESSION", "SHOW_CAPABILITIES", "LOGOUT"]
    }
  ],
  "total": 2
}
```

---

### POST /api/v1/routes/sync

Push routes from the frontend registry to backend storage.

**Authentication:** Not required

**Request Body:**

```json
{
  "routes": [
    {
      "path": "/",
      "label": "Login",
      "description": "Sign in to your account",
      "protected": false,
      "actions": []
    },
    {
      "path": "/signup",
      "label": "Sign Up",
      "description": "Create a new account via the conversational signup flow",
      "protected": false,
      "actions": []
    },
    {
      "path": "/main-dashboard",
      "label": "Dashboard",
      "description": "Main chat dashboard where you can chat with the AI agent, view sessions, manage conversations, share chats, and explore agent capabilities",
      "protected": true,
      "actions": ["NEW_CHAT", "DELETE", "SHARE", "RENAME", "LOAD_SESSION", "SHOW_CAPABILITIES", "LOGOUT"]
    }
  ]
}
```

**Route Definition Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | Yes | React Router path (e.g., `/main-dashboard`) |
| `label` | string | Yes | Human-readable name |
| `description` | string | Yes | What the page does — LLM uses this to match intent |
| `protected` | boolean | No | Whether auth is required (default: false) |
| `actions` | string[] | No | Available UI actions on this page |

**Success Response** (200 OK):

```json
{
  "success": true,
  "synced_count": 3,
  "message": "Successfully synced 3 routes"
}
```

---

### POST /api/v1/routes/action-completed

Notify the backend that the frontend has executed an action.

**Authentication:** Required (JWT Bearer token)

**Request Body:**

```json
{
  "action_type": "UI_ACTION",
  "action_name": "DELETE",
  "success": true,
  "result": { "deleted_session_id": "abc123" },
  "session_id": "abc123",
  "message": "Session deleted successfully"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action_type` | string | Yes | `NAVIGATE`, `UI_ACTION`, etc. |
| `action_name` | string | No | Specific action name (e.g., `DELETE`) |
| `success` | boolean | Yes | Whether the action completed |
| `result` | object | No | Any result data |
| `session_id` | string | No | Chat session ID for context |
| `message` | string | No | Human-readable summary |

**Success Response** (200 OK):

```json
{
  "success": true,
  "message": "Action 'DELETE' completion acknowledged"
}
```

---

## Schemas

All schemas are defined in `src/app/schemas/routes.py`:

- `RouteDefinition` — A single route
- `RouteSyncRequest` — POST /sync body
- `RouteSyncResponse` — Sync result
- `RouteListResponse` — GET response
- `ActionCompletedRequest` — POST /action-completed body
- `ActionCompletedResponse` — Acknowledgment

---

## Frontend Integration

The frontend auto-syncs routes on every app startup:

```typescript
// hooks/useRouteSync.ts
import { ROUTE_REGISTRY } from "@/routes/registry";
import { getRoutes, syncRoutes } from "@/api/routes";

// 1. GET current backend routes
// 2. Compare with local ROUTE_REGISTRY
// 3. POST if different
```

See [Voice & Navigation Architecture](../architecture/VOICE-NAVIGATION-ARCHITECTURE.md) for the full flow.

---

## Related

- [Chat API](./chat.md) — Chat responses may include an `action` field
- [Voice & Navigation Architecture](../architecture/VOICE-NAVIGATION-ARCHITECTURE.md)
- [Navigation Tools Guide](../guides/tools/navigation-tools.md)
