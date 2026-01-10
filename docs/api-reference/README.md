# API Reference

> 📡 **Complete REST API documentation** for AgentHub backend services

## Table of Contents

### Overview
- [Introduction](#introduction)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)

### API Endpoints
- [Authentication API](./authentication.md) - User signup, login, token refresh
- [Chat API](./chat.md) - Chat messages and session management
- [Conversational Auth API](./conversational-auth.md) - Chatbot-style signup
- [Ingestion API](./ingestion.md) - File and data ingestion
- [Health API](./health.md) - System health checks
- [External Services API](./external-services.md) - Jira, Confluence integration

### Standards
- [Common Patterns](#common-patterns)
- [Response Format](#response-format)
- [Pagination](#pagination)
- [Versioning](#versioning)

---

## Introduction

AgentHub provides a RESTful API for building AI-powered applications with:

- **Authentication** - JWT-based user authentication
- **Chat Interface** - Conversational AI with session management
- **RAG Pipeline** - Document ingestion and retrieval
- **External Tools** - Integration with Jira, Confluence, and more
- **Flexible Configuration** - YAML-based settings

### Key Features

| Feature | Description |
|---------|-------------|
| **REST API** | Standard HTTP methods (GET, POST, PUT, DELETE) |
| **JSON Format** | All requests and responses use JSON |
| **JWT Auth** | Secure token-based authentication |
| **WebSocket Support** | Real-time chat (coming soon) |
| **OpenAPI Docs** | Auto-generated Swagger/ReDoc documentation |

---

## Base URL

### Development
```
http://localhost:8000
```

### Production
```
https://your-domain.com
```

### API Versions

All endpoints are versioned under `/api/v1/`:

```
http://localhost:8000/api/v1/{endpoint}
```

**Example**:
```bash
curl http://localhost:8000/api/v1/auth/login
```

---

## Authentication

AgentHub uses **JWT (JSON Web Tokens)** for authentication.

### Authentication Flow

```
1. User signs up or logs in
   POST /api/v1/auth/signup or /api/v1/auth/login
   
2. Server returns tokens
   {
     "access_token": "eyJhbGci...",
     "refresh_token": "eyJhbGci..."
   }
   
3. Client includes token in requests
   Authorization: Bearer eyJhbGci...
   
4. Token expires (15 minutes)
   Client refreshes using refresh token
   POST /api/v1/auth/refresh
```

### Token Types

| Token Type | Lifetime | Purpose |
|------------|----------|---------|
| **Access Token** | 15 minutes | API requests |
| **Refresh Token** | 7 days | Obtain new access token |

### Using Authentication

#### Standard REST Signup/Login

```bash
# 1. Signup
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecureP@ss123",
    "firstname": "John",
    "lastname": "Doe"
  }'

# Response:
{
  "success": true,
  "message": "User registered successfully",
  "user_id": "507f1f77bcf86cd799439011",
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci..."
}

# 2. Use access token
curl http://localhost:8000/api/v1/chat/message \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# 3. Refresh token when expired
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGci..."}'
```

#### Conversational Signup (Chatbot-Style)

```bash
# Step 1: Start conversation
curl -X POST http://localhost:8000/api/v1/auth/signup/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "message": "",
    "current_step": "start"
  }'

# Response:
{
  "success": true,
  "message": "Welcome! What's your email address?",
  "next_step": "email",
  "session_id": "signup_abc-123"
}

# Step 2: Provide email
curl -X POST http://localhost:8000/api/v1/auth/signup/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "message": "user@example.com",
    "current_step": "email",
    "session_id": "signup_abc-123"
  }'

# Continue until complete...
```

See [Conversational Auth API](./conversational-auth.md) for full flow.

---

## Rate Limiting

**Current Status**: Not implemented (planned for future)

**Planned Limits**:
- **Authentication**: 5 requests/minute per IP
- **Chat**: 20 requests/minute per user
- **Ingestion**: 10 requests/hour per user

**Rate Limit Headers** (when implemented):
```
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 1609459200
```

---

## Error Handling

### Standard Error Response

```json
{
  "detail": {
    "error_code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "timestamp": "2026-01-10T14:30:00Z",
    "path": "/api/v1/auth/signup"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| **200** | OK | Successful GET/POST |
| **201** | Created | User signup success |
| **400** | Bad Request | Invalid request data |
| **401** | Unauthorized | Missing/invalid token |
| **403** | Forbidden | Insufficient permissions |
| **404** | Not Found | Resource doesn't exist |
| **422** | Validation Error | Pydantic validation failed |
| **429** | Too Many Requests | Rate limit exceeded |
| **500** | Internal Error | Server error |
| **503** | Service Unavailable | Database/LLM down |

### Common Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `AUTHENTICATION_ERROR` | 401 | Invalid credentials |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `NOT_FOUND_ERROR` | 404 | Resource not found |
| `DUPLICATE_ERROR` | 400 | Resource already exists |
| `LLM_ERROR` | 503 | LLM service unavailable |
| `DATABASE_ERROR` | 503 | Database connection failed |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

### Example Error Responses

#### Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    },
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

#### Authentication Error (401)

```json
{
  "detail": {
    "error_code": "AUTHENTICATION_ERROR",
    "message": "Invalid credentials",
    "timestamp": "2026-01-10T14:30:00Z"
  }
}
```

#### Service Unavailable (503)

```json
{
  "detail": {
    "error_code": "LLM_ERROR",
    "message": "OpenAI API is currently unavailable",
    "timestamp": "2026-01-10T14:30:00Z",
    "retry_after": 60
  }
}
```

---

## Common Patterns

### Request Headers

```http
Content-Type: application/json
Authorization: Bearer eyJhbGci...
Accept: application/json
```

### Timestamps

All timestamps use **ISO 8601 format** in UTC:

```json
{
  "timestamp": "2026-01-10T14:30:00Z",
  "created_at": "2026-01-10T14:30:00.123456Z"
}
```

### Identifiers

- **User IDs**: MongoDB ObjectId (24 hex characters)
- **Session IDs**: UUID v4 format
- **Task IDs**: Celery task ID format

**Examples**:
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "a4f3c2e1-5d6a-4b8c-9e2f-1a3b5c7d9e1f"
}
```

---

## Response Format

### Success Response

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    // Response data
  },
  "metadata": {
    "timestamp": "2026-01-10T14:30:00Z",
    "processing_time_ms": 123.45
  }
}
```

### Error Response

```json
{
  "success": false,
  "message": "Operation failed",
  "error": {
    "code": "ERROR_CODE",
    "details": "Detailed error message"
  }
}
```

---

## Pagination

### Query Parameters

```
?page=1&page_size=20
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `page_size` | integer | 20 | Items per page (max: 100) |

### Paginated Response

```json
{
  "items": [
    // Array of items
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "has_more": true,
  "total_pages": 8
}
```

### Example Request

```bash
curl "http://localhost:8000/api/v1/chat/sessions?page=2&page_size=10" \
  -H "Authorization: Bearer eyJhbGci..."
```

---

## Versioning

### Current Version: v1

All endpoints are under `/api/v1/`:

```
/api/v1/auth/login
/api/v1/chat/message
/api/v1/health
```

### Version Compatibility

- **v1**: Current stable version
- **v2**: Planned (breaking changes will be introduced here)

### Deprecation Policy

- **30 days notice** before deprecating endpoints
- **90 days support** for deprecated endpoints
- **Migration guide** provided for breaking changes

---

## Interactive Documentation

### Swagger UI

```
http://localhost:8000/docs
```

**Features**:
- ✅ Try out API endpoints
- ✅ See request/response schemas
- ✅ Test authentication flow
- ✅ View all available endpoints

### ReDoc

```
http://localhost:8000/redoc
```

**Features**:
- ✅ Clean, readable documentation
- ✅ Better for documentation reading
- ✅ Download OpenAPI spec

### OpenAPI Schema

```
http://localhost:8000/openapi.json
```

Download the raw OpenAPI 3.0 specification.

---

## Quick Reference

### Endpoint Overview

| Endpoint | Method | Auth Required | Purpose |
|----------|--------|---------------|---------|
| `/auth/signup` | POST | ❌ | Create account |
| `/auth/login` | POST | ❌ | Login |
| `/auth/refresh` | POST | ❌ | Refresh token |
| `/auth/signup/conversation` | POST | ❌ | Conversational signup |
| `/chat/message` | POST | ✅ | Send message |
| `/chat/sessions` | GET | ✅ | List sessions |
| `/chat/sessions/{id}/messages` | GET | ✅ | Get history |
| `/ingest/load/{source}` | POST | ✅ | Ingest data |
| `/health` | GET | ❌ | Health check |
| `/health/test-celery` | GET | ❌ | Test workers |

---

## Code Examples

### Python (requests)

```python
import requests

# Signup
response = requests.post(
    "http://localhost:8000/api/v1/auth/signup",
    json={
        "email": "user@example.com",
        "username": "johndoe",
        "password": "SecureP@ss123",
        "firstname": "John",
        "lastname": "Doe"
    }
)
tokens = response.json()

# Chat
response = requests.post(
    "http://localhost:8000/api/v1/chat/message",
    headers={"Authorization": f"Bearer {tokens['access_token']}"},
    json={"message": "Hello, AI!"}
)
print(response.json()["message"])
```

### JavaScript (fetch)

```javascript
// Signup
const response = await fetch('http://localhost:8000/api/v1/auth/signup', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    username: 'johndoe',
    password: 'SecureP@ss123',
    firstname: 'John',
    lastname: 'Doe'
  })
});
const tokens = await response.json();

// Chat
const chatResponse = await fetch('http://localhost:8000/api/v1/chat/message', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${tokens.access_token}`
  },
  body: JSON.stringify({ message: 'Hello, AI!' })
});
const chat = await chatResponse.json();
console.log(chat.message);
```

### cURL

```bash
# Signup
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecureP@ss123",
    "firstname": "John",
    "lastname": "Doe"
  }'

# Chat (replace TOKEN with actual token)
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, AI!"}'
```

---

## Next Steps

Explore detailed documentation for each API:

1. **[Authentication API](./authentication.md)** - Start here to create an account
2. **[Chat API](./chat.md)** - Learn about conversational AI
3. **[Conversational Auth API](./conversational-auth.md)** - Alternative signup flow
4. **[Ingestion API](./ingestion.md)** - Upload and process documents
5. **[Health API](./health.md)** - Monitor system status

---

## Support

- **Swagger UI**: http://localhost:8000/docs
- **GitHub Issues**: [Report bugs](https://github.com/timothy-odofin/agenthub-be/issues)
- **Documentation**: [Full docs](../../README.md)

---

**Last Updated**: January 10, 2026  
**API Version**: v1  
**Status**: Production Ready

---

Thank you for using AgentHub! 🚀
