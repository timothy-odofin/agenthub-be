# Chat API

> 💬 **Conversational AI with session management and message history**

## Overview

The Chat API enables real-time conversations with AI agents, persistent session management, and full conversation history tracking.

**Base Path**: `/api/v1/chat/`  
**Authentication**: Required (JWT Bearer token)

---

## Endpoints

### POST /message

Send a message to the AI agent and receive a response.

**Authentication**: Required

**Request Headers**:
```
Authorization: Bearer eyJhbGci...
Content-Type: application/json
```

**Request Body**:
```json
{
  "message": "What is Python?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Field Requirements**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | ✅ Yes | User's message (min 1 char) |
| `session_id` | string (UUID) | ❌ No | Existing session ID (creates new if null) |

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Python is a high-level programming language...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "507f1f77bcf86cd799439011",
  "timestamp": "2026-01-10T14:30:00Z",
  "processing_time_ms": 245.3,
  "tools_used": ["web_search", "code_analyzer"],
  "errors": null,
  "metadata": {
    "model": "gpt-4",
    "tokens_used": 150,
    "confidence": 0.95
  }
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether request was successful |
| `message` | string | Agent's response text |
| `session_id` | string | Session ID (new or existing) |
| `user_id` | string | User's ID |
| `timestamp` | string | Response timestamp (ISO 8601) |
| `processing_time_ms` | float | Time taken to process |
| `tools_used` | array | Tools invoked (e.g., web_search) |
| `errors` | array | Any errors encountered |
| `metadata` | object | Additional context (model, tokens) |

**Example Requests**:

```bash
# New conversation
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is Python?"
  }'

# Continue conversation
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you explain decorators?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Example Code**:

```python
import requests

class ChatClient:
    def __init__(self, access_token):
        self.base_url = "http://localhost:8000"
        self.access_token = access_token
        self.session_id = None
    
    def send_message(self, message):
        """Send a message and maintain session."""
        payload = {"message": message}
        if self.session_id:
            payload["session_id"] = self.session_id
        
        response = requests.post(
            f"{self.base_url}/api/v1/chat/message",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            self.session_id = data["session_id"]
            return data
        else:
            raise Exception(f"Chat failed: {response.json()}")

# Usage
chat = ChatClient(access_token="your_token_here")

# Start conversation
response1 = chat.send_message("What is Python?")
print(response1["message"])

# Continue conversation (uses stored session_id)
response2 = chat.send_message("Can you show me an example?")
print(response2["message"])
```

---

### POST /sessions

Create a new chat session.

**Authentication**: Required

**Request Body**:
```json
{
  "title": "Python Learning Session"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Python Learning Session",
  "created_at": "2026-01-10T14:30:00Z"
}
```

**Example Request**:

```bash
curl -X POST http://localhost:8000/api/v1/chat/sessions \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Learning Session"
  }'
```

---

### GET /sessions

List all user's chat sessions with pagination.

**Authentication**: Required

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `page_size` | integer | 20 | Items per page (max: 100) |

**Success Response** (200 OK):
```json
{
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Python Learning Session",
      "created_at": "2026-01-10T14:00:00Z",
      "last_message_at": "2026-01-10T14:30:00Z",
      "message_count": 8,
      "preview": "What is Python? Python is a..."
    },
    {
      "session_id": "661f2c88-f39c-52e5-b827-557766551111",
      "title": "JavaScript Questions",
      "created_at": "2026-01-09T10:15:00Z",
      "last_message_at": "2026-01-09T11:20:00Z",
      "message_count": 12,
      "preview": "Explain async/await..."
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20,
  "has_more": false
}
```

**Example Request**:

```bash
# First page
curl http://localhost:8000/api/v1/chat/sessions \
  -H "Authorization: Bearer eyJhbGci..."

# Second page with custom size
curl "http://localhost:8000/api/v1/chat/sessions?page=2&page_size=10" \
  -H "Authorization: Bearer eyJhbGci..."
```

**Example Code**:

```python
def get_all_sessions(access_token):
    """Fetch all sessions with pagination."""
    base_url = "http://localhost:8000"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    all_sessions = []
    page = 1
    
    while True:
        response = requests.get(
            f"{base_url}/api/v1/chat/sessions?page={page}&page_size=20",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            all_sessions.extend(data["sessions"])
            
            if not data["has_more"]:
                break
            page += 1
        else:
            raise Exception(f"Failed to fetch sessions: {response.json()}")
    
    return all_sessions
```

---

### GET /sessions/{session_id}/messages

Retrieve message history for a specific session.

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string (UUID) | Session identifier |

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Max messages to return |

**Success Response** (200 OK):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "507f1f77bcf86cd799439011",
  "message_count": 4,
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "What is Python?",
      "timestamp": "2026-01-10T14:25:00Z"
    },
    {
      "id": "msg-2",
      "role": "assistant",
      "content": "Python is a high-level programming language...",
      "timestamp": "2026-01-10T14:25:02Z"
    },
    {
      "id": "msg-3",
      "role": "user",
      "content": "Can you show me an example?",
      "timestamp": "2026-01-10T14:26:00Z"
    },
    {
      "id": "msg-4",
      "role": "assistant",
      "content": "Here's a simple Python example:\n```python\nprint('Hello, World!')\n```",
      "timestamp": "2026-01-10T14:26:03Z"
    }
  ]
}
```

**Message Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Message identifier |
| `role` | string | `user` or `assistant` |
| `content` | string | Message text |
| `timestamp` | string | When message was sent (ISO 8601) |

**Example Request**:

```bash
# Get last 50 messages (default)
curl http://localhost:8000/api/v1/chat/sessions/550e8400-e29b-41d4-a716-446655440000/messages \
  -H "Authorization: Bearer eyJhbGci..."

# Get last 100 messages
curl "http://localhost:8000/api/v1/chat/sessions/550e8400-e29b-41d4-a716-446655440000/messages?limit=100" \
  -H "Authorization: Bearer eyJhbGci..."
```

**Example Code**:

```python
def get_session_history(access_token, session_id, limit=50):
    """Retrieve conversation history."""
    response = requests.get(
        f"http://localhost:8000/api/v1/chat/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"limit": limit}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # Format conversation
        for msg in data["messages"]:
            role = "You" if msg["role"] == "user" else "AI"
            print(f"{role}: {msg['content']}\n")
        
        return data
    else:
        raise Exception(f"Failed to fetch history: {response.json()}")
```

---

## Complete Chat Flow Example

```python
import requests
from datetime import datetime

class AgentHubChat:
    def __init__(self, access_token):
        self.base_url = "http://localhost:8000"
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self.current_session = None
    
    def create_session(self, title=None):
        """Create a new chat session."""
        response = requests.post(
            f"{self.base_url}/api/v1/chat/sessions",
            headers=self.headers,
            json={"title": title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.current_session = data["session_id"]
            return data
        else:
            raise Exception(f"Session creation failed: {response.json()}")
    
    def send(self, message):
        """Send a message in the current session."""
        payload = {"message": message}
        if self.current_session:
            payload["session_id"] = self.current_session
        
        response = requests.post(
            f"{self.base_url}/api/v1/chat/message",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            self.current_session = data["session_id"]
            return data
        else:
            raise Exception(f"Message failed: {response.json()}")
    
    def get_history(self, limit=50):
        """Get current session history."""
        if not self.current_session:
            raise Exception("No active session")
        
        response = requests.get(
            f"{self.base_url}/api/v1/chat/sessions/{self.current_session}/messages",
            headers=self.headers,
            params={"limit": limit}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"History fetch failed: {response.json()}")
    
    def list_sessions(self, page=1, page_size=20):
        """List all user sessions."""
        response = requests.get(
            f"{self.base_url}/api/v1/chat/sessions",
            headers=self.headers,
            params={"page": page, "page_size": page_size}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Session list failed: {response.json()}")
    
    def switch_session(self, session_id):
        """Switch to an existing session."""
        self.current_session = session_id

# Usage Example
chat = AgentHubChat(access_token="your_token_here")

# Create new session
session = chat.create_session(title="Python Learning")
print(f"Created session: {session['session_id']}")

# Send messages
response1 = chat.send("What is Python?")
print(f"AI: {response1['message']}")

response2 = chat.send("Can you show me examples?")
print(f"AI: {response2['message']}")

# Get conversation history
history = chat.get_history()
print(f"\nConversation has {history['message_count']} messages")

# List all sessions
sessions = chat.list_sessions()
print(f"\nYou have {sessions['total']} total sessions")

# Switch to different session
if sessions['sessions']:
    old_session = sessions['sessions'][0]['session_id']
    chat.switch_session(old_session)
    chat.send("Continuing our previous conversation...")
```

---

## Tools and Capabilities

The AI agent can invoke various tools during conversation:

| Tool | Purpose | Example Use Case |
|------|---------|------------------|
| `web_search` | Search the internet | "What's the weather in NYC?" |
| `code_analyzer` | Analyze code snippets | "Review this Python function" |
| `documentation_search` | Search docs | "Find NumPy array info" |
| `calculator` | Perform calculations | "What's 15% of 250?" |
| `jira_integration` | Access Jira tickets | "Show my open tickets" |
| `confluence_search` | Search Confluence | "Find API documentation" |

**Tool Usage Example**:

```json
{
  "message": "The weather in NYC is currently 72°F and sunny.",
  "tools_used": ["web_search"],
  "metadata": {
    "tools_data": {
      "web_search": {
        "query": "weather NYC",
        "sources": ["weather.com"]
      }
    }
  }
}
```

---

## Error Handling

### Common Errors

```json
// Missing Authorization (401)
{
  "detail": "Not authenticated"
}

// Invalid Session (404)
{
  "success": false,
  "message": "Session not found",
  "session_id": "invalid-id"
}

// Empty Message (422)
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "ensure this value has at least 1 character",
      "type": "value_error.any_str.min_length"
    }
  ]
}

// LLM Unavailable (503)
{
  "success": false,
  "message": "AI service temporarily unavailable",
  "errors": ["OpenAI API timeout"],
  "retry_after": 60
}
```

---

## Best Practices

### 1. Session Management

```python
# ✅ GOOD - Maintain session across messages
session_id = response["session_id"]
next_request = {"message": "...", "session_id": session_id}

# ❌ BAD - Create new session each time
# This loses conversation context
requests.post("/chat/message", json={"message": "..."})
```

### 2. Error Handling

```python
# ✅ GOOD - Handle errors gracefully
try:
    response = chat.send("Hello")
except Exception as e:
    if "503" in str(e):
        print("AI service down, retrying in 60s...")
        time.sleep(60)
        response = chat.send("Hello")
    else:
        print(f"Error: {e}")
```

### 3. Pagination

```python
# ✅ GOOD - Fetch all sessions properly
def get_all_sessions():
    sessions = []
    page = 1
    while True:
        data = fetch_page(page)
        sessions.extend(data["sessions"])
        if not data["has_more"]:
            break
        page += 1
    return sessions

# ❌ BAD - Only get first page
sessions = fetch_page(1)["sessions"]
```

---

## Rate Limiting

**Current Status**: Not implemented  
**Planned**:
- 60 messages per minute per user
- 100 session creations per hour per user

---

## WebSocket Support

**Status**: Coming soon

**Planned Endpoint**:
```
ws://localhost:8000/api/v1/chat/ws/{session_id}
```

**Features**:
- Real-time streaming responses
- Typing indicators
- Instant message delivery

---

## Related Documentation

- **[Authentication API](./authentication.md)** - Get access tokens
- **[Conversational Auth API](./conversational-auth.md)** - Alternative signup
- **[Schemas Guide](../guides/schemas/README.md)** - Message schemas

---

**Last Updated**: January 10, 2026  
**Status**: Production Ready

---
