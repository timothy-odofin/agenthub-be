# Conversational Authentication API

> **Chatbot-style user signup** with natural language understanding and step-by-step guidance

## Overview

The Conversational Authentication API provides an alternative signup experience where users interact with an AI agent that guides them through account creation one field at a time.

**Base Path**: `/api/v1/auth/signup/` 
**Authentication**: Not required

**Key Features**:
- **Natural Language** - Users can type conversationally
- **Intelligent Extraction** - LLM extracts values from natural text
- **Real-time Validation** - Immediate feedback on each field
- **Progress Tracking** - Users see completion percentage
- **Server-Side Sessions** - Secure Redis-based session storage (5-minute TTL)
- **Intelligent START** - Answers questions before collecting data

---

## Endpoint

### POST /signup/conversation

Handle step-by-step conversational signup.

**Authentication**: Not required

**Request Body**:
```json
{
"message": "My email is john@example.com",
"session_id": "signup_abc-123-def",
"current_step": "email"
}
```

**Field Requirements**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | User's response (can be natural language) |
| `session_id` | string | No | Session ID (null for START step only) |
| `current_step` | enum | Yes | Current step in flow |

**Signup Steps Enum**:
```
start → email → username → password → firstname → lastname → complete
```

**Success Response** (200 OK):
```json
{
"success": true,
"message": "Great! Now choose a username (3-30 characters).",
"next_step": "username",
"session_id": "signup_abc-123-def",
"validation_errors": null,
"progress": {
"current_step": 1,
"total_steps": 6,
"percentage": 17
}
}
```

**Complete Response** (signup finished):
```json
{
"success": true,
"message": "Congratulations! Your account has been created successfully.",
"next_step": "complete",
"session_id": "signup_abc-123-def",
"validation_errors": null,
"progress": {
"current_step": 6,
"total_steps": 6,
"percentage": 100
},
"user_id": "507f1f77bcf86cd799439011",
"access_token": "eyJhbGci...",
"refresh_token": "eyJhbGci..."
}
```

---

## Complete Signup Flow

### Step 1: START (Intelligent Conversation)

Users can ask questions before starting:

**Request**:
```json
{
"message": "What do I need to sign up?",
"current_step": "start"
}
```

**Response**:
```json
{
"success": true,
"message": " Hello! I'm your signup assistant. I can help you create a new account.\n\nHere's what I'll need from you:\n Email address - Your unique login identifier\n Username - How you'll be known (3-30 characters)\nPassword - A secure password (min 8 characters, uppercase, lowercase, number)\n First name - Your given name\nLast name - Your family name\n\nThe whole process takes less than a minute! I'll guide you through each step.\n\nWould you like to proceed with creating an account?",
"next_step": "start",
"session_id": null
}
```

When ready to start:

**Request**:
```json
{
"message": "Yes, let's start",
"current_step": "start"
}
```

**Response**:
```json
{
"success": true,
"message": " Welcome! Let's create your account. What's your email address?",
"next_step": "email",
"session_id": "signup_abc-123-def",
"progress": {
"current_step": 0,
"total_steps": 6,
"percentage": 0
}
}
```

---

### Step 2: EMAIL

**Natural Language Accepted**:
```
"My email is john@example.com"
"john@example.com"
"You can reach me at john@example.com"
```

**Request**:
```json
{
"message": "My email is john@example.com",
"session_id": "signup_abc-123-def",
"current_step": "email"
}
```

**Success Response**:
```json
{
"success": true,
"message": "Perfect! Now choose a unique username (3-30 characters).",
"next_step": "username",
"session_id": "signup_abc-123-def",
"validation_errors": null,
"progress": {
"current_step": 1,
"total_steps": 6,
"percentage": 17
}
}
```

**Validation Error Response**:
```json
{
"success": false,
"message": "That doesn't look like a valid email. Please provide a valid email address.",
"next_step": "email",
"session_id": "signup_abc-123-def",
"validation_errors": [
"Email must be a valid email address"
],
"progress": {
"current_step": 1,
"total_steps": 6,
"percentage": 17
}
}
```

---

### Step 3: USERNAME

**Natural Language Accepted**:
```
"My username is johndoe"
"johndoe"
"You can call me johndoe"
```

**Request**:
```json
{
"message": "You can call me johndoe",
"session_id": "signup_abc-123-def",
"current_step": "username"
}
```

**Success Response**:
```json
{
"success": true,
"message": "Great choice! Now create a secure password (min 8 characters, must include uppercase, lowercase, and number).",
"next_step": "password",
"session_id": "signup_abc-123-def",
"validation_errors": null,
"progress": {
"current_step": 2,
"total_steps": 6,
"percentage": 33
}
}
```

**Validation Errors**:
```json
{
"success": false,
"message": "That username is already taken. Please choose a different username.",
"next_step": "username",
"session_id": "signup_abc-123-def",
"validation_errors": [
"Username 'johndoe' is already taken"
]
}
```

---

### Step 4: PASSWORD

**Security Note**: Password is hashed immediately server-side and never sent to client.

**Request**:
```json
{
"message": "MySecureP@ss123",
"session_id": "signup_abc-123-def",
"current_step": "password"
}
```

**Success Response**:
```json
{
"success": true,
"message": "Excellent! What's your first name?",
"next_step": "firstname",
"session_id": "signup_abc-123-def",
"validation_errors": null,
"progress": {
"current_step": 3,
"total_steps": 6,
"percentage": 50
}
}
```

**Weak Password Error**:
```json
{
"success": false,
"message": "Password is too weak. It must contain at least one uppercase letter, one lowercase letter, and one number.",
"next_step": "password",
"session_id": "signup_abc-123-def",
"validation_errors": [
"Password must contain uppercase letter",
"Password must contain number"
]
}
```

---

### Step 5: FIRSTNAME

**Request**:
```json
{
"message": "John",
"session_id": "signup_abc-123-def",
"current_step": "firstname"
}
```

**Response**:
```json
{
"success": true,
"message": "Almost done! What's your last name?",
"next_step": "lastname",
"session_id": "signup_abc-123-def",
"validation_errors": null,
"progress": {
"current_step": 4,
"total_steps": 6,
"percentage": 67
}
}
```

---

### Step 6: LASTNAME (Final Step)

**Request**:
```json
{
"message": "Doe",
"session_id": "signup_abc-123-def",
"current_step": "lastname"
}
```

**Complete Response**:
```json
{
"success": true,
"message": "Congratulations! Your account has been created successfully.\n\nYou can now:\nChat with AI agents\nCreate and manage sessions\nUpload and analyze documents\n\nYour account details:\n Email: john@example.com\n Username: johndoe\n Name: John Doe",
"next_step": "complete",
"session_id": "signup_abc-123-def",
"validation_errors": null,
"progress": {
"current_step": 6,
"total_steps": 6,
"percentage": 100
},
"user_id": "507f1f77bcf86cd799439011",
"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## Python Client Example

```python
import requests
from typing import Optional

class ConversationalSignup:
def __init__(self, base_url="http://localhost:8000"):
self.base_url = base_url
self.session_id = None
self.current_step = "start"

def send(self, message: str) -> dict:
"""Send message to conversational signup."""
response = requests.post(
f"{self.base_url}/api/v1/auth/signup/conversation",
json={
"message": message,
"session_id": self.session_id,
"current_step": self.current_step
}
)

if response.status_code == 200:
data = response.json()

# Update state
if data.get("session_id"):
self.session_id = data["session_id"]
self.current_step = data["next_step"]

return data
else:
raise Exception(f"Request failed: {response.json()}")

def is_complete(self) -> bool:
"""Check if signup is complete."""
return self.current_step == "complete"

# Interactive signup
def interactive_signup():
signup = ConversationalSignup()

print("Conversational Signup Bot\n")
print("Type your responses naturally. I'll guide you through!\n")

# Start conversation
response = signup.send("")
print(f"Bot: {response['message']}\n")

# Collect user inputs
while not signup.is_complete():
user_input = input("You: ")

response = signup.send(user_input)
print(f"\nBot: {response['message']}")

# Show progress
if response.get("progress"):
progress = response["progress"]
print(f"Progress: {progress['percentage']}% ({progress['current_step']}/{progress['total_steps']})")

# Show validation errors
if response.get("validation_errors"):
print(f"Errors: {', '.join(response['validation_errors'])}")

print()

# Signup complete
print(f"\nSignup complete!")
print(f"User ID: {response.get('user_id')}")
print(f"Access Token: {response.get('access_token')[:50]}...")

return response

# Run interactive signup
if __name__ == "__main__":
result = interactive_signup()
```

---

## JavaScript Client Example

```javascript
class ConversationalSignup {
constructor(baseUrl = 'http://localhost:8000') {
this.baseUrl = baseUrl;
this.sessionId = null;
this.currentStep = 'start';
}

async send(message) {
const response = await fetch(`${this.baseUrl}/api/v1/auth/signup/conversation`, {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({
message,
session_id: this.sessionId,
current_step: this.currentStep
})
});

if (response.ok) {
const data = await response.json();

// Update state
if (data.session_id) {
this.sessionId = data.session_id;
}
this.currentStep = data.next_step;

return data;
} else {
throw new Error(`Request failed: ${await response.text()}`);
}
}

isComplete() {
return this.currentStep === 'complete';
}
}

// Usage in React component
function ConversationalSignupForm() {
const [signup] = useState(() => new ConversationalSignup());
const [message, setMessage] = useState('');
const [response, setResponse] = useState(null);
const [loading, setLoading] = useState(false);

const handleSubmit = async (e) => {
e.preventDefault();
setLoading(true);

try {
const data = await signup.send(message);
setResponse(data);
setMessage('');

if (signup.isComplete()) {
// Store tokens and redirect
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token);
window.location.href = '/dashboard';
}
} catch (error) {
console.error('Signup error:', error);
} finally {
setLoading(false);
}
};

return (
<div className="conversational-signup">
{response && (
<div className="bot-message">
<p>{response.message}</p>
{response.progress && (
<div className="progress-bar">
<div style={{ width: `${response.progress.percentage}%` }} />
</div>
)}
{response.validation_errors && (
<ul className="errors">
{response.validation_errors.map((err, i) => (
<li key={i}>{err}</li>
))}
</ul>
)}
</div>
)}

<form onSubmit={handleSubmit}>
<input
type="text"
value={message}
onChange={(e) => setMessage(e.target.value)}
placeholder="Type your response..."
disabled={loading}
/>
<button type="submit" disabled={loading}>
{loading ? 'Sending...' : 'Send'}
</button>
</form>
</div>
);
}
```

---

## Server-Side Session Management

### Redis Session Storage

**Session Structure**:
```json
{
"session_id": "signup_abc-123-def",
"current_step": "email",
"collected_data": {
"email": "john@example.com",
"username": null,
"password_hash": "$2b$12$...",
"firstname": null,
"lastname": null
},
"created_at": "2026-01-10T14:00:00Z",
"expires_at": "2026-01-10T14:05:00Z"
}
```

**Security Features**:
- **5-minute TTL** - Sessions expire automatically
- **Server-side storage** - Client never sees collected data
- **Password hashing** - Passwords hashed immediately (bcrypt)
- **Validation** - Data validated before storage

---

## Natural Language Extraction

The system uses LLM to extract values from natural language:

### Examples

**Email Extraction**:
```
"My email is john@example.com" → john@example.com
"john@example.com" → john@example.com
"You can reach me at john@example.com" → john@example.com
```

**Username Extraction**:
```
"My username is johndoe" → johndoe
"johndoe" → johndoe
"Call me johndoe" → johndoe
```

**Name Extraction**:
```
"My name is John" → John
"John" → John
"I'm John" → John
```

---

## Error Handling

### Validation Errors

```json
{
"success": false,
"message": "Error message for user",
"next_step": "current_step",
"validation_errors": [
"Specific error 1",
"Specific error 2"
]
}
```

### Common Errors

| Error | Cause | Next Step |
|-------|-------|-----------|
| Invalid email format | Not a valid email | Stays on `email` |
| Email already exists | Duplicate email | Stays on `email` |
| Username too short | < 3 characters | Stays on `username` |
| Username taken | Duplicate username | Stays on `username` |
| Weak password | Missing requirements | Stays on `password` |
| Session expired | > 5 minutes idle | Returns to `start` |

---

## Best Practices

### 1. Handle Session Expiry

```python
# GOOD - Check for session expiry
response = signup.send(message)
if response.get("next_step") == "start" and signup.session_id:
print("Session expired, starting over")
signup.session_id = None
```

### 2. Show Progress

```python
# GOOD - Show visual progress
if response.get("progress"):
progress = response["progress"]
bar = "=" * int(progress["percentage"] / 5)
print(f"[{bar:20}] {progress['percentage']}%")
```

### 3. Store Tokens Securely

```javascript
// GOOD - Secure storage
if (data.access_token) {
// Use HTTP-only cookies (set by backend)
// Or secure storage in mobile apps
}

// BAD - Vulnerable to XSS
localStorage.setItem('token', data.access_token);
```

---

## Comparison: Traditional vs Conversational

| Feature | Traditional | Conversational |
|---------|-------------|----------------|
| **Fields shown** | All at once | One at a time |
| **User experience** | Form-based | Chat-based |
| **Validation** | Submit-time | Real-time |
| **Natural language** | No | Yes |
| **Progress tracking** | No | Yes |
| **Mobile-friendly** | Medium | High |
| **Accessibility** | Medium | High |

---

## Related Documentation

- **[Authentication API](./authentication.md)** - Traditional signup
- **[Chat API](./chat.md)** - Chat with AI agents
- **[Tutorials](../tutorials/conversational-auth.md)** - Frontend integration

---

**Last Updated**: January 10, 2026 
**Status**: Production Ready

---
