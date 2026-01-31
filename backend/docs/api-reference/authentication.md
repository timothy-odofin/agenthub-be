# Authentication API

> **User registration, login, and token management**

## Overview

The Authentication API provides secure user account management using JWT tokens. Supports both traditional REST and conversational (chatbot-style) signup.

**Base Path**: `/api/v1/auth/`

---

## Endpoints

### POST /signup

Create a new user account with all information at once.

**Authentication**: Not required

**Request Body**:
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecureP@ss123",
  "firstname": "John",
  "lastname": "Doe"
}
```

**Field Requirements**:

| Field | Type | Requirements | Example |
|-------|------|--------------|---------|
| `email` | string | Valid email format, unique | `user@example.com` |
| `username` | string | 3-30 chars, alphanumeric + underscore, unique | `john_doe` |
| `password` | string | 8-72 chars, uppercase + lowercase + number | `SecureP@ss123` |
| `firstname` | string | 1-50 chars | `John` |
| `lastname` | string | 1-50 chars | `Doe` |

**Success Response** (201 Created):
```json
{
  "success": true,
  "message": "User registered successfully",
  "user_id": "507f1f77bcf86cd799439011",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses**:

```json
// Validation Error (422)
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}

// Duplicate Email (400)
{
  "success": false,
  "message": "Email already registered"
}

// Duplicate Username (400)
{
  "success": false,
  "message": "Username already taken"
}

// Weak Password (400)
{
  "success": false,
  "message": "Password must contain uppercase, lowercase, and number"
}
```

**Example Request**:

```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "username": "johndoe",
    "password": "SecureP@ss123",
    "firstname": "John",
    "lastname": "Doe"
  }'
```

**Example Code**:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/signup",
    json={
        "email": "john.doe@example.com",
        "username": "johndoe",
        "password": "SecureP@ss123",
        "firstname": "John",
        "lastname": "Doe"
    }
)

if response.status_code == 201:
    data = response.json()
    access_token = data["access_token"]
    print(f"Signup successful! User ID: {data['user_id']}")
else:
    print(f"Signup failed: {response.json()}")
```

---

### POST /login

Authenticate a user and receive JWT tokens.

**Authentication**: Not required

**Request Body**:
```json
{
  "identifier": "johndoe",
  "password": "SecureP@ss123"
}
```

**Field Requirements**:

| Field | Type | Requirements | Example |
|-------|------|--------------|---------|
| `identifier` | string | Email or username | `johndoe` or `user@example.com` |
| `password` | string | User's password | `SecureP@ss123` |

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "507f1f77bcf86cd799439011",
  "username": "johndoe",
  "email": "john.doe@example.com"
}
```

**Error Responses**:

```json
// Invalid Credentials (401)
{
  "success": false,
  "message": "Invalid credentials"
}

// User Not Found (404)
{
  "success": false,
  "message": "User not found"
}
```

**Example Request**:

```bash
# Login with username
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "johndoe",
    "password": "SecureP@ss123"
  }'

# Login with email
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "john.doe@example.com",
    "password": "SecureP@ss123"
  }'
```

**Example Code**:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "identifier": "johndoe",  # Can be username or email
        "password": "SecureP@ss123"
    }
)

if response.status_code == 200:
    data = response.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    
    # Store tokens securely
    # Use access_token for subsequent requests
    print(f"Login successful! User: {data['username']}")
else:
    print(f"Login failed: {response.json()}")
```

---

### POST /refresh

Obtain a new access token using a valid refresh token.

**Authentication**: Not required (but needs valid refresh token)

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Token refreshed successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses**:

```json
// Invalid Token (401)
{
  "success": false,
  "message": "Invalid refresh token"
}

// Expired Token (401)
{
  "success": false,
  "message": "Refresh token has expired"
}
```

**Example Request**:

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Example Code**:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/refresh",
    json={
        "refresh_token": stored_refresh_token
    }
)

if response.status_code == 200:
    data = response.json()
    new_access_token = data["access_token"]
    new_refresh_token = data["refresh_token"]
    
    # Update stored tokens
    print("Tokens refreshed successfully")
else:
    print("Token refresh failed - user needs to login again")
```

---

## Token Management

### Access Token

**Lifetime**: 15 minutes  
**Purpose**: Authenticate API requests  
**Storage**: Memory or secure cookie

**Usage**:
```bash
curl http://localhost:8000/api/v1/chat/message \
  -H "Authorization: Bearer eyJhbGci..."
```

### Refresh Token

**Lifetime**: 7 days  
**Purpose**: Obtain new access tokens  
**Storage**: Secure HTTP-only cookie (recommended) or encrypted storage

**When to Refresh**:
- Access token expires (401 error)
- Proactively before expiration (recommended)

---

## Authentication Flow

### Complete Flow Example

```python
import requests
from datetime import datetime, timedelta

class AuthClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
    
    def signup(self, email, username, password, firstname, lastname):
        """Register a new user."""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/signup",
            json={
                "email": email,
                "username": username,
                "password": password,
                "firstname": firstname,
                "lastname": lastname
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            self._store_tokens(data)
            return data
        else:
            raise Exception(f"Signup failed: {response.json()}")
    
    def login(self, identifier, password):
        """Login with username or email."""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={
                "identifier": identifier,
                "password": password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self._store_tokens(data)
            return data
        else:
            raise Exception(f"Login failed: {response.json()}")
    
    def refresh(self):
        """Refresh the access token."""
        if not self.refresh_token:
            raise Exception("No refresh token available")
        
        response = requests.post(
            f"{self.base_url}/api/v1/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            self._store_tokens(data)
            return data
        else:
            raise Exception(f"Token refresh failed: {response.json()}")
    
    def _store_tokens(self, data):
        """Store tokens and set expiry."""
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")
        # Access token expires in 15 minutes
        self.token_expiry = datetime.now() + timedelta(minutes=15)
    
    def get_headers(self):
        """Get authorization headers, refreshing if needed."""
        # Refresh if token expires in less than 1 minute
        if self.token_expiry and datetime.now() >= self.token_expiry - timedelta(minutes=1):
            self.refresh()
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

# Usage
auth = AuthClient()

# Signup
auth.signup(
    email="user@example.com",
    username="johndoe",
    password="SecureP@ss123",
    firstname="John",
    lastname="Doe"
)

# Make authenticated request
response = requests.post(
    "http://localhost:8000/api/v1/chat/message",
    headers=auth.get_headers(),
    json={"message": "Hello!"}
)
```

---

## Security Best Practices

### Password Requirements

**Required**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number

**Recommended**:
- Use special characters
- Avoid common passwords
- Don't reuse passwords

### Token Storage

**Frontend (Browser)**:
```javascript
// GOOD - Secure HTTP-only cookie (set by backend)
// Access token in memory
let accessToken = null;

// BAD - localStorage (vulnerable to XSS)
localStorage.setItem('token', token);

// BAD - sessionStorage (vulnerable to XSS)
sessionStorage.setItem('token', token);
```

**Mobile/Desktop App**:
```python
# GOOD - Encrypted secure storage
from keyring import set_password, get_password

set_password("agenthub", "access_token", token)
token = get_password("agenthub", "access_token")

# BAD - Plain text file
with open('tokens.txt', 'w') as f:
    f.write(token)
```

### HTTPS Required

**Always use HTTPS in production** to prevent token interception.

```python
# Production
base_url = "https://api.yourdomain.com"

# Development only
base_url = "http://localhost:8000"
```

---

## Rate Limiting

**Current Status**: Not implemented  
**Planned**:
- 5 signup attempts per hour per IP
- 10 login attempts per hour per IP
- 20 refresh requests per hour per user

---

## Error Reference

| Status | Error | Cause | Solution |
|--------|-------|-------|----------|
| 400 | Duplicate email | Email already exists | Use different email or login |
| 400 | Duplicate username | Username taken | Choose different username |
| 400 | Weak password | Password too simple | Add uppercase, lowercase, numbers |
| 401 | Invalid credentials | Wrong password/user | Check credentials |
| 401 | Invalid token | Token expired/invalid | Refresh or login again |
| 422 | Validation error | Invalid field format | Check field requirements |
| 503 | Service unavailable | Database down | Retry later |

---

## Testing with Swagger

1. Visit http://localhost:8000/docs
2. Find "Authentication" section
3. Click "Try it out" on `/auth/signup`
4. Fill in the request body
5. Click "Execute"
6. Copy the `access_token` from response
7. Click "Authorize" button (top right)
8. Paste token: `Bearer <access_token>`
9. Now you can test protected endpoints!

---

## Related Documentation

- **[Conversational Auth API](./conversational-auth.md)** - Alternative signup flow
- **[Chat API](./chat.md)** - Using authenticated endpoints
- **[Schemas Guide](../guides/schemas/README.md)** - Request/response models

---

**Last Updated**: January 10, 2026  
**Status**: Production Ready

---
