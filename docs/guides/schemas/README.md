# API Schemas & Data Models

> 📋 **Type-safe API contracts** with Pydantic for authentication, chat operations, and structured LLM outputs

## Table of Contents

### Overview
- [What are Schemas?](#what-are-schemas)
- [Schema Categories](#schema-categories)
- [Key Features](#key-features)

### Authentication Schemas
- [Signup](#signup-schemas)
  - [SignupRequest](#signuprequest)
  - [SignupResponse](#signupresponse)
- [Login](#login-schemas)
  - [LoginRequest](#loginrequest)
  - [LoginResponse](#loginresponse)
- [Token Refresh](#token-refresh-schemas)

### Chat & Session Schemas
- [Chat Operations](#chat-schemas)
  - [ChatRequest](#chatrequest)
  - [ChatResponse](#chatresponse)
- [Session Management](#session-schemas)
  - [CreateSessionRequest](#createsessionrequest)
  - [SessionMessage](#sessionmessage)
  - [SessionHistoryResponse](#sessionhistoryresponse)
  - [SessionListResponse](#sessionlistresponse)

### Conversational Authentication
- [Conversational Signup](#conversational-signup-flow)
  - [SignupStep Enum](#signupstep-enum)
  - [ConversationalSignupRequest](#conversationalsignuprequest)
  - [ConversationalSignupResponse](#conversationalsignupresponse)
- [Server-Side Session Management](#server-side-session-management)
- [Flow Examples](#conversational-flow-examples)

### Structured LLM Outputs
- [Base Models](#llm-output-base)
- [Agent Thinking](#agentthinking)
- [Chat Agent Response](#chatagentresponse)
- [Ingestion Analysis](#ingestionanalysis)
- [Data Source Processing](#datasourceprocessing)
- [System Diagnostics](#systemdiagnostics)
- [Session Analysis](#sessionanalysis)
- [Structured Response Wrapper](#structuredllmresponse)

### Usage Patterns
- [Request/Response Pattern](#requestresponse-pattern)
- [Validation](#validation)
- [Error Handling](#error-handling)
- [Serialization](#serialization)

### Extending Schemas
- [Creating Custom Schemas](#creating-custom-schemas)
- [Validation Rules](#custom-validation-rules)
- [Best Practices](#best-practices)

### Reference
- [Pydantic Features](#pydantic-features)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## What are Schemas?

Schemas in AgentHub are **Pydantic models** that define the structure and validation rules for API requests and responses. They provide:

- **Type Safety** - Automatic type checking and validation
- **API Contracts** - Clear interface definitions
- **Documentation** - Auto-generated OpenAPI docs
- **Serialization** - JSON conversion
- **Validation** - Field constraints and business rules

### Schema Categories

| Category | Location | Purpose |
|----------|----------|---------|
| **Authentication** | `schemas/auth.py` | User signup, login, token refresh |
| **Chat** | `schemas/chat.py` | Chat messages, session management |
| **Conversational Auth** | `schemas/conversational_auth.py` | Chatbot-style signup |
| **LLM Outputs** | `schemas/llm_output.py` | Structured LLM responses |

### Key Features

- ✅ **Pydantic BaseModel** - All schemas inherit from BaseModel
- ✅ **Field Validation** - Min/max length, regex patterns, custom validators
- ✅ **Type Hints** - Full Python type support
- ✅ **JSON Schema** - Auto-generated schemas
- ✅ **Examples** - Inline documentation
- ✅ **Optional Fields** - Default values and None support

---

## Authentication Schemas

**Location**: `src/app/schemas/auth.py`

### Signup Schemas

#### SignupRequest

User registration request:

```python
from pydantic import BaseModel, EmailStr, Field

class SignupRequest(BaseModel):
    """Schema for user signup requests."""
    
    email: EmailStr = Field(
        ..., 
        description="User's email address",
        example="user@example.com"
    )
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50,
        description="Unique username",
        example="john_doe"
    )
    password: str = Field(
        ..., 
        min_length=8,
        description="User password (min 8 characters)",
        example="SecureP@ss123"
    )
    firstname: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="User's first name",
        example="John"
    )
    lastname: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="User's last name",
        example="Doe"
    )
```

**Usage**:
```python
# In API endpoint
@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest):
    # Pydantic validates automatically
    user = await create_user(
        email=request.email,
        username=request.username,
        password=request.password,
        firstname=request.firstname,
        lastname=request.lastname
    )
    return SignupResponse(...)
```

#### SignupResponse

Successful signup response:

```python
class SignupResponse(BaseModel):
    """Schema for signup responses."""
    
    success: bool = Field(
        ..., 
        description="Whether signup was successful"
    )
    message: str = Field(
        ..., 
        description="Success or error message"
    )
    user_id: Optional[str] = Field(
        None, 
        description="Created user ID"
    )
    access_token: Optional[str] = Field(
        None, 
        description="JWT access token"
    )
    refresh_token: Optional[str] = Field(
        None, 
        description="JWT refresh token"
    )
```

**Example Response**:
```json
{
  "success": true,
  "message": "User registered successfully",
  "user_id": "507f1f77bcf86cd799439011",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### Login Schemas

#### LoginRequest

User authentication request:

```python
class LoginRequest(BaseModel):
    """Schema for login requests."""
    
    identifier: str = Field(
        ..., 
        description="Username or email address",
        example="john_doe"
    )
    password: str = Field(
        ..., 
        description="User password",
        example="SecureP@ss123"
    )
```

**Features**:
- ✅ Accepts email **OR** username
- ✅ Backend determines which type
- ✅ Simple single-field authentication

#### LoginResponse

Successful login response:

```python
class LoginResponse(BaseModel):
    """Schema for login responses."""
    
    success: bool = Field(..., description="Login success status")
    message: str = Field(..., description="Success or error message")
    access_token: Optional[str] = Field(None, description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    user_id: Optional[str] = Field(None, description="User ID")
    username: Optional[str] = Field(None, description="Username")
    email: Optional[str] = Field(None, description="User email")
```

**Example Response**:
```json
{
  "success": true,
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "507f1f77bcf86cd799439011",
  "username": "john_doe",
  "email": "user@example.com"
}
```

---

### Token Refresh Schemas

```python
class RefreshTokenRequest(BaseModel):
    """Schema for token refresh requests."""
    refresh_token: str = Field(..., description="JWT refresh token")

class RefreshTokenResponse(BaseModel):
    """Schema for token refresh responses."""
    success: bool = Field(..., description="Refresh success status")
    message: str = Field(..., description="Success or error message")
    access_token: Optional[str] = Field(None, description="New access token")
    refresh_token: Optional[str] = Field(None, description="New refresh token")
```

---

## Chat & Session Schemas

**Location**: `src/app/schemas/chat.py`

### Chat Schemas

#### ChatRequest

Send message to agent:

```python
class ChatRequest(BaseModel):
    """Schema for chat requests."""
    
    message: str = Field(
        ..., 
        min_length=1,
        description="User's message to the agent",
        example="What is the weather today?"
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID for conversation context",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
```

**Usage**:
```python
# New conversation
request = ChatRequest(
    message="Hello, I need help with Python"
)

# Continue conversation
request = ChatRequest(
    message="Can you explain decorators?",
    session_id="existing-session-id"
)
```

#### ChatResponse

Agent response with metadata:

```python
class ChatResponse(BaseModel):
    """Schema for chat responses."""
    
    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Agent's response message")
    session_id: str = Field(..., description="Conversation session ID")
    user_id: str = Field(..., description="User ID")
    timestamp: datetime = Field(..., description="Response timestamp")
    processing_time_ms: Optional[float] = Field(None, description="Processing time")
    tools_used: Optional[List[str]] = Field(None, description="Tools invoked")
    errors: Optional[List[str]] = Field(None, description="Any errors encountered")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
```

**Example Response**:
```json
{
  "success": true,
  "message": "Python decorators are a powerful feature that...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "507f1f77bcf86cd799439011",
  "timestamp": "2025-01-10T14:30:00Z",
  "processing_time_ms": 245.3,
  "tools_used": ["web_search", "code_analyzer"],
  "errors": null,
  "metadata": {
    "model": "gpt-4",
    "tokens_used": 150
  }
}
```

---

### Session Schemas

#### CreateSessionRequest

Start new conversation:

```python
class CreateSessionRequest(BaseModel):
    """Schema for creating a new session."""
    
    user_id: str = Field(..., description="User ID")
    initial_message: Optional[str] = Field(
        None, 
        description="First message in session"
    )
```

#### SessionMessage

Individual message in conversation:

```python
class SessionMessage(BaseModel):
    """Schema for individual messages in a session."""
    
    role: str = Field(
        ..., 
        description="Message role: 'user' or 'assistant'",
        example="user"
    )
    content: str = Field(
        ..., 
        description="Message content",
        example="Tell me about Python"
    )
    timestamp: datetime = Field(
        ..., 
        description="Message timestamp"
    )
    id: Optional[str] = Field(
        None, 
        description="Message ID"
    )
```

#### SessionHistoryResponse

Retrieve conversation history:

```python
class SessionHistoryResponse(BaseModel):
    """Schema for session history responses."""
    
    messages: List[SessionMessage] = Field(
        ..., 
        description="List of messages in the session"
    )
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    message_count: int = Field(..., description="Total message count")
```

**Example**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "507f1f77bcf86cd799439011",
  "message_count": 4,
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "Hello",
      "timestamp": "2025-01-10T14:25:00Z"
    },
    {
      "id": "msg-2",
      "role": "assistant",
      "content": "Hi! How can I help?",
      "timestamp": "2025-01-10T14:25:01Z"
    }
  ]
}
```

#### SessionListResponse

List user's sessions with pagination:

```python
class SessionListResponse(BaseModel):
    """Schema for listing user sessions."""
    
    sessions: List[dict] = Field(
        ..., 
        description="List of session summaries"
    )
    total: int = Field(..., description="Total session count")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="More pages available")
```

**Example**:
```json
{
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-01-10T14:00:00Z",
      "last_message_at": "2025-01-10T14:30:00Z",
      "message_count": 8,
      "preview": "Hello, I need help with..."
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 10,
  "has_more": true
}
```

---

## Conversational Authentication

**Location**: `src/app/schemas/conversational_auth.py`

### Conversational Signup Flow

A sophisticated **chatbot-style signup** where the agent guides users through registration step-by-step.

#### Key Features

- ✅ **Progressive Disclosure** - One field at a time
- ✅ **Natural Conversation** - Users respond in plain text
- ✅ **Server-Side Validation** - Real-time feedback
- ✅ **Secure** - Passwords stored server-side, never sent to client
- ✅ **Session Management** - Redis-based session storage

---

### SignupStep Enum

```python
from enum import Enum

class SignupStep(str, Enum):
    """Enumeration of signup steps in conversational flow."""
    
    START = "start"                # Initial step
    EMAIL = "email"                # Collecting email
    USERNAME = "username"          # Collecting username
    PASSWORD = "password"          # Collecting password (secure)
    FIRSTNAME = "firstname"        # Collecting first name
    LASTNAME = "lastname"          # Collecting last name
    COMPLETE = "complete"          # Signup finished
```

**Flow Order**:
```
START → EMAIL → USERNAME → PASSWORD → FIRSTNAME → LASTNAME → COMPLETE
```

---

### ConversationalSignupRequest

```python
class ConversationalSignupRequest(BaseModel):
    """
    Request schema for conversational signup.
    
    The agent guides users through signup one step at a time.
    Each request contains the user's response to the previous prompt.
    """
    
    message: str = Field(
        ...,
        description="User's response to the current signup step",
        example="john.doe@example.com"
    )
    
    session_id: Optional[str] = Field(
        None,
        description="Session ID tracking the signup process (null for START)",
        example="signup_550e8400-e29b-41d4-a716-446655440000"
    )
    
    current_step: SignupStep = Field(
        ...,
        description="Current step in the signup flow",
        example=SignupStep.EMAIL
    )
```

**Important**: 
- `current_step` must match the `next_step` from previous response
- Server validates and stores data server-side
- Passwords **never** sent to client

---

### ConversationalSignupResponse

```python
class ConversationalSignupResponse(BaseModel):
    """
    Response schema for conversational signup.
    
    Guides user to next step with validation feedback.
    """
    
    success: bool = Field(
        ...,
        description="Whether the current step was successful"
    )
    
    message: str = Field(
        ...,
        description="Agent's response guiding to next step",
        example="Great! Now, please choose a username."
    )
    
    next_step: SignupStep = Field(
        ...,
        description="Next step in the signup flow"
    )
    
    session_id: str = Field(
        ...,
        description="Session ID for tracking"
    )
    
    validation_errors: Optional[List[str]] = Field(
        None,
        description="Validation errors for current input"
    )
    
    progress: Optional[dict] = Field(
        None,
        description="Progress tracking information",
        example={
            "current_step": 2,
            "total_steps": 6,
            "percentage": 33
        }
    )
    
    # Only populated when complete
    user_id: Optional[str] = Field(None, description="Created user ID")
    access_token: Optional[str] = Field(None, description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
```

---

### Server-Side Session Management

**Session Storage**: Redis

**Session Data Structure**:
```python
{
    "session_id": "signup_550e8400-e29b-41d4-a716-446655440000",
    "current_step": "email",
    "collected_data": {
        "email": "john.doe@example.com",
        "username": null,
        "password": null,  # Hashed server-side
        "firstname": null,
        "lastname": null
    },
    "created_at": "2025-01-10T14:00:00Z",
    "expires_at": "2025-01-10T15:00:00Z"  # 1 hour TTL
}
```

**Security Benefits**:
- ✅ Passwords hashed immediately
- ✅ Client never sees sensitive data
- ✅ Session expires automatically
- ✅ Validation before storage

---

### Conversational Flow Examples

#### Example 1: Starting Signup

**Request**:
```json
{
  "message": "I want to sign up",
  "session_id": null,
  "current_step": "start"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Welcome! Let's get you set up. First, what's your email address?",
  "next_step": "email",
  "session_id": "signup_550e8400-e29b-41d4-a716-446655440000",
  "validation_errors": null,
  "progress": {
    "current_step": 0,
    "total_steps": 6,
    "percentage": 0
  }
}
```

---

#### Example 2: Providing Email

**Request**:
```json
{
  "message": "john.doe@example.com",
  "session_id": "signup_550e8400-e29b-41d4-a716-446655440000",
  "current_step": "email"
}
```

**Response (Success)**:
```json
{
  "success": true,
  "message": "Perfect! Now, please choose a unique username.",
  "next_step": "username",
  "session_id": "signup_550e8400-e29b-41d4-a716-446655440000",
  "validation_errors": null,
  "progress": {
    "current_step": 1,
    "total_steps": 6,
    "percentage": 17
  }
}
```

**Response (Validation Error)**:
```json
{
  "success": false,
  "message": "That doesn't look like a valid email. Please provide a valid email address.",
  "next_step": "email",
  "session_id": "signup_550e8400-e29b-41d4-a716-446655440000",
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

#### Example 3: Completing Signup

**Request (Last Step)**:
```json
{
  "message": "Doe",
  "session_id": "signup_550e8400-e29b-41d4-a716-446655440000",
  "current_step": "lastname"
}
```

**Response (Complete)**:
```json
{
  "success": true,
  "message": "Congratulations! Your account has been created successfully.",
  "next_step": "complete",
  "session_id": "signup_550e8400-e29b-41d4-a716-446655440000",
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

## Structured LLM Outputs

**Location**: `src/app/schemas/llm_output.py`

### LLM Output Base

Base class for all structured outputs:

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class LLMOutputBase(BaseModel):
    """Base class for all LLM output schemas."""
    
    success: bool = Field(
        ..., 
        description="Whether the operation was successful"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence score (0.0 to 1.0)"
    )
    reasoning: str = Field(
        ..., 
        description="Explanation of the decision/output"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional context and metadata"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this output was generated"
    )
```

---

### AgentThinking

Agent's internal reasoning process:

```python
class AgentThinking(LLMOutputBase):
    """
    Captures the agent's thought process and decision-making.
    
    Used for transparency and debugging agent behavior.
    """
    
    thought_process: str = Field(
        ..., 
        description="Agent's internal reasoning",
        example="User is asking about Python decorators. I should explain with examples."
    )
    
    selected_action: str = Field(
        ..., 
        description="Action the agent decided to take",
        example="provide_code_example"
    )
    
    confidence_level: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence in selected action"
    )
    
    tool_selection: Optional[List[str]] = Field(
        None,
        description="Tools the agent plans to use",
        example=["code_analyzer", "documentation_search"]
    )
    
    risk_assessment: Optional[str] = Field(
        None,
        description="Potential risks or concerns",
        example="User's question is ambiguous; may need clarification"
    )
    
    fallback_plan: Optional[str] = Field(
        None,
        description="Alternative approach if primary fails",
        example="If code example fails, provide conceptual explanation"
    )
```

**Usage**:
```python
thinking = AgentThinking(
    success=True,
    confidence=0.92,
    reasoning="Clear technical question requiring code demonstration",
    thought_process="User wants to understand decorators...",
    selected_action="provide_code_example",
    confidence_level=0.92,
    tool_selection=["code_analyzer"],
    risk_assessment="None - straightforward request",
    fallback_plan="Link to documentation if example unclear"
)
```

---

### ChatAgentResponse

Structured chat response with metadata:

```python
class ChatAgentResponse(LLMOutputBase):
    """
    Structured response from chat agent.
    
    Includes response text, tools used, and follow-up suggestions.
    """
    
    response_text: str = Field(
        ..., 
        description="The agent's text response to the user"
    )
    
    response_type: str = Field(
        ..., 
        description="Type of response",
        example="informational"  # or "question", "action", "error"
    )
    
    session_context_used: bool = Field(
        ..., 
        description="Whether previous conversation context was used"
    )
    
    tools_invoked: Optional[List[str]] = Field(
        None,
        description="Tools that were actually used",
        example=["web_search", "calculator"]
    )
    
    follow_up_suggestions: Optional[List[str]] = Field(
        None,
        description="Suggested follow-up questions",
        example=[
            "Would you like to see more examples?",
            "Should I explain error handling?"
        ]
    )
    
    sentiment: Optional[str] = Field(
        None,
        description="Detected user sentiment",
        example="curious"  # or "frustrated", "satisfied", etc.
    )
```

---

### IngestionAnalysis

Analysis of ingested documents:

```python
class IngestionAnalysis(LLMOutputBase):
    """
    Analysis of ingested content for RAG systems.
    
    Helps optimize chunking and retrieval strategies.
    """
    
    content_type: str = Field(
        ..., 
        description="Type of content",
        example="technical_documentation"
    )
    
    quality_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Content quality assessment"
    )
    
    key_topics: List[str] = Field(
        ..., 
        description="Main topics identified",
        example=["python", "decorators", "metaprogramming"]
    )
    
    document_summary: str = Field(
        ..., 
        description="Brief summary of content"
    )
    
    chunk_strategy: str = Field(
        ..., 
        description="Recommended chunking strategy",
        example="semantic_with_overlap"
    )
    
    complexity_level: str = Field(
        ..., 
        description="Content complexity",
        example="intermediate"  # beginner, intermediate, advanced
    )
    
    recommended_chunk_size: Optional[int] = Field(
        None,
        description="Optimal chunk size in characters",
        example=1000
    )
    
    language_detected: Optional[str] = Field(
        None,
        description="Primary language",
        example="en"
    )
```

---

### DataSourceProcessing

Processing status for data sources:

```python
class DataSourceProcessing(LLMOutputBase):
    """
    Status and results of data source processing.
    
    Used for tracking batch ingestion operations.
    """
    
    source_type: str = Field(
        ..., 
        description="Type of data source",
        example="pdf_files"
    )
    
    processed_items: int = Field(
        ..., 
        description="Number of items processed"
    )
    
    success_rate: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Percentage of successful processing"
    )
    
    extraction_method: str = Field(
        ..., 
        description="Method used for extraction",
        example="pypdf"
    )
    
    preprocessing_steps: List[str] = Field(
        ..., 
        description="Steps applied during preprocessing",
        example=["text_cleaning", "deduplication", "chunking"]
    )
    
    failed_items: Optional[List[str]] = Field(
        None,
        description="List of failed item identifiers"
    )
    
    processing_time_seconds: Optional[float] = Field(
        None,
        description="Total processing time"
    )
```

---

### SystemDiagnostics

System health and performance monitoring:

```python
class SystemDiagnostics(LLMOutputBase):
    """
    System health diagnostics and monitoring.
    
    Used for health checks and performance monitoring.
    """
    
    component_status: Dict[str, str] = Field(
        ..., 
        description="Status of each system component",
        example={
            "database": "healthy",
            "redis": "healthy",
            "celery": "healthy",
            "vector_db": "degraded"
        }
    )
    
    performance_metrics: Dict[str, float] = Field(
        ..., 
        description="Performance measurements",
        example={
            "response_time_ms": 120.5,
            "cpu_usage": 45.2,
            "memory_usage": 68.9
        }
    )
    
    alert_level: str = Field(
        ..., 
        description="Overall alert level",
        example="ok"  # ok, warning, critical
    )
    
    resource_usage: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed resource usage",
        example={
            "memory_mb": 512,
            "disk_gb": 10.5,
            "connections": 25
        }
    )
    
    bottlenecks: Optional[List[str]] = Field(
        None,
        description="Identified performance bottlenecks",
        example=["vector_db_slow_query", "high_memory_usage"]
    )
    
    recommendations: Optional[List[str]] = Field(
        None,
        description="Recommended actions",
        example=["Scale vector DB", "Clear Redis cache"]
    )
```

---

### SessionAnalysis

Analysis of conversation sessions:

```python
class SessionAnalysis(LLMOutputBase):
    """
    Analysis of user conversation sessions.
    
    Used for understanding conversation quality and outcomes.
    """
    
    session_summary: str = Field(
        ..., 
        description="Summary of the conversation"
    )
    
    conversation_topics: List[str] = Field(
        ..., 
        description="Topics discussed in the session",
        example=["python_basics", "decorators", "async_programming"]
    )
    
    user_satisfaction: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Estimated user satisfaction score"
    )
    
    resolution_status: str = Field(
        ..., 
        description="Whether user's needs were met",
        example="resolved"  # resolved, partial, unresolved
    )
    
    interaction_quality: Optional[str] = Field(
        None,
        description="Quality of agent-user interaction",
        example="excellent"  # poor, fair, good, excellent
    )
    
    key_insights: Optional[List[str]] = Field(
        None,
        description="Important insights from the conversation"
    )
    
    suggested_improvements: Optional[List[str]] = Field(
        None,
        description="Ways to improve similar interactions"
    )
```

---

### StructuredLLMResponse

Wrapper for all structured outputs:

```python
class StructuredLLMResponse(BaseModel):
    """
    Wrapper for structured LLM responses.
    
    Provides unified interface for all output types.
    """
    
    content: str = Field(
        ..., 
        description="Raw text response from LLM"
    )
    
    structured_output: Optional[Dict[str, Any]] = Field(
        None,
        description="Parsed structured data (JSON)"
    )
    
    output_type: str = Field(
        ..., 
        description="Type of structured output",
        example="agent_thinking"
    )
    
    usage: Optional[Dict[str, int]] = Field(
        None,
        description="Token usage statistics",
        example={
            "prompt_tokens": 150,
            "completion_tokens": 200,
            "total_tokens": 350
        }
    )
    
    model_name: str = Field(
        ..., 
        description="LLM model used",
        example="gpt-4"
    )
    
    provider: str = Field(
        ..., 
        description="LLM provider",
        example="openai"
    )
    
    processing_time_ms: Optional[float] = Field(
        None,
        description="Time taken to process"
    )
```

---

## Request/Response Pattern

### Standard Pattern

```python
# 1. Define request schema
class MyRequest(BaseModel):
    field1: str
    field2: int

# 2. Define response schema
class MyResponse(BaseModel):
    success: bool
    data: dict

# 3. Use in API endpoint
@router.post("/endpoint", response_model=MyResponse)
async def my_endpoint(request: MyRequest):
    # Pydantic validates automatically
    result = await process(request.field1, request.field2)
    return MyResponse(success=True, data=result)
```

---

## Validation

### Field Validation

```python
from pydantic import Field, validator

class UserSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    age: int = Field(..., ge=18, le=120)  # Greater/equal, less/equal
    email: EmailStr  # Built-in email validation
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """Ensure username is alphanumeric."""
        assert v.isalnum(), 'must be alphanumeric'
        return v
```

### Custom Validators

```python
class PasswordSchema(BaseModel):
    password: str
    confirm_password: str
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain a number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain uppercase letter')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Ensure passwords match."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
```

---

## Error Handling

### Validation Errors

```python
from fastapi import HTTPException
from pydantic import ValidationError

try:
    user = UserSchema(**data)
except ValidationError as e:
    # Pydantic provides detailed error messages
    raise HTTPException(
        status_code=422,
        detail=e.errors()
    )
```

**Error Response**:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    },
    {
      "loc": ["body", "username"],
      "msg": "ensure this value has at least 3 characters",
      "type": "value_error.any_str.min_length",
      "ctx": {"limit_value": 3}
    }
  ]
}
```

---

## Serialization

### JSON Conversion

```python
# Schema to JSON
user = UserSchema(username="john", email="john@example.com", age=25)
json_str = user.json()  # '{"username":"john","email":"john@example.com","age":25}'

# JSON to Schema
data = '{"username":"jane","email":"jane@example.com","age":30}'
user = UserSchema.parse_raw(data)

# Dict conversion
user_dict = user.dict()  # {"username": "john", ...}
user = UserSchema(**user_dict)
```

### Exclude Fields

```python
# Exclude password from response
class UserResponse(BaseModel):
    username: str
    email: str
    
    class Config:
        exclude = {'password'}

# Or use exclude on serialization
user_dict = user.dict(exclude={'password', 'internal_id'})
```

---

## Creating Custom Schemas

### Step-by-Step Guide

#### 1. Define Schema

```python
# In schemas/my_feature.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MyFeatureRequest(BaseModel):
    """Request schema for my feature."""
    
    name: str = Field(
        ..., 
        min_length=1,
        max_length=100,
        description="Feature name"
    )
    options: Optional[List[str]] = Field(
        None,
        description="Optional configuration"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "name": "example_feature",
                "options": ["option1", "option2"]
            }
        }

class MyFeatureResponse(BaseModel):
    """Response schema for my feature."""
    
    success: bool
    feature_id: str
    created_at: datetime
    metadata: Optional[dict] = None
```

#### 2. Use in API

```python
# In api/v1/my_feature.py
from fastapi import APIRouter
from app.schemas.my_feature import MyFeatureRequest, MyFeatureResponse

router = APIRouter()

@router.post("/feature", response_model=MyFeatureResponse)
async def create_feature(request: MyFeatureRequest):
    """Create a new feature."""
    # Automatic validation
    feature_id = await create_feature_in_db(request.name, request.options)
    
    return MyFeatureResponse(
        success=True,
        feature_id=feature_id,
        created_at=datetime.utcnow()
    )
```

---

## Custom Validation Rules

### Pattern 1: Cross-Field Validation

```python
class DateRangeSchema(BaseModel):
    start_date: datetime
    end_date: datetime
    
    @validator('end_date')
    def end_after_start(cls, v, values):
        """Ensure end date is after start date."""
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
```

### Pattern 2: List Validation

```python
class ItemListSchema(BaseModel):
    items: List[str]
    
    @validator('items')
    def unique_items(cls, v):
        """Ensure all items are unique."""
        if len(v) != len(set(v)):
            raise ValueError('items must be unique')
        return v
```

### Pattern 3: Conditional Fields

```python
class ConditionalSchema(BaseModel):
    type: str
    value: Optional[int] = None
    text: Optional[str] = None
    
    @validator('value')
    def value_required_for_numeric(cls, v, values):
        """value required when type is 'numeric'."""
        if values.get('type') == 'numeric' and v is None:
            raise ValueError('value required for numeric type')
        return v
```

---

## Best Practices

### 1. Use Descriptive Field Names

```python
# ✅ GOOD - Clear and descriptive
class UserRequest(BaseModel):
    email_address: EmailStr
    first_name: str
    last_name: str
    date_of_birth: datetime

# ❌ BAD - Ambiguous names
class UserRequest(BaseModel):
    email: str
    name1: str
    name2: str
    dob: str
```

### 2. Provide Examples

```python
# ✅ GOOD - Includes examples
class ProductRequest(BaseModel):
    name: str = Field(..., example="Laptop")
    price: float = Field(..., ge=0, example=999.99)
    category: str = Field(..., example="Electronics")

# ❌ BAD - No examples
class ProductRequest(BaseModel):
    name: str
    price: float
    category: str
```

### 3. Use Type Hints

```python
# ✅ GOOD - Explicit types
from typing import List, Optional, Dict

class DataSchema(BaseModel):
    items: List[str]
    metadata: Optional[Dict[str, Any]]
    count: int

# ❌ BAD - Missing types
class DataSchema(BaseModel):
    items: list
    metadata: dict
    count: int
```

### 4. Document Schemas

```python
# ✅ GOOD - Clear documentation
class ChatRequest(BaseModel):
    """
    Request schema for chat endpoint.
    
    Accepts user message and optional session ID for
    continuing conversations.
    """
    message: str = Field(..., description="User's message")
    session_id: Optional[str] = Field(None, description="Session ID")

# ❌ BAD - No documentation
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str]
```

### 5. Separate Request/Response Schemas

```python
# ✅ GOOD - Separate schemas
class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime
    # No password field

# ❌ BAD - Same schema for both
class User(BaseModel):
    email: EmailStr
    password: str  # Exposed in responses!
```

---

## Pydantic Features

### Config Class

```python
class MySchema(BaseModel):
    field1: str
    field2: int
    
    class Config:
        # Allow extra fields
        extra = "allow"  # or "forbid", "ignore"
        
        # Validate on assignment
        validate_assignment = True
        
        # Use enum values
        use_enum_values = True
        
        # JSON encoders
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### Aliases

```python
class APISchema(BaseModel):
    user_name: str = Field(..., alias="userName")
    user_id: int = Field(..., alias="userId")
    
    class Config:
        allow_population_by_field_name = True  # Allow both names
```

### Inheritance

```python
class BaseResponse(BaseModel):
    success: bool
    message: str

class UserResponse(BaseResponse):
    user_id: str
    # Inherits success and message
```

---

## Common Patterns

### Pattern 1: Pagination

```python
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Items per page")
    
class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int
    has_more: bool
```

### Pattern 2: Search Filters

```python
class SearchFilters(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    sort_by: Optional[str] = Field("relevance", regex="^(relevance|price|date)$")
```

### Pattern 3: Enum Fields

```python
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class UserSchema(BaseModel):
    username: str
    role: UserRole = UserRole.USER
```

---

## Troubleshooting

### Issue 1: Validation Not Working

**Problem**: Fields accept invalid values

**Solution**:
```python
# Ensure validators are defined correctly
@validator('field_name')  # Must match field name
def validate_field(cls, v):
    # Validation logic
    return v
```

### Issue 2: Circular Dependencies

**Problem**: `TypeError: 'type' object is not subscriptable`

**Solution**:
```python
from __future__ import annotations  # Add at top of file
from typing import List, Optional

class Parent(BaseModel):
    children: List['Child']  # Forward reference

class Child(BaseModel):
    parent: Optional['Parent']

# Update forward references
Parent.update_forward_refs()
```

### Issue 3: Date/Time Serialization

**Problem**: Datetime not JSON serializable

**Solution**:
```python
class MySchema(BaseModel):
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

---

## Related Documentation

- **[API Documentation](../../api/README.md)** - API endpoint usage
- **[Authentication Guide](../authentication/README.md)** - Auth implementation
- **[Database Guide](../database/README.md)** - Data persistence

---

**Last Updated**: January 10, 2026  
**Version**: 1.0  
**Related**: Pydantic, FastAPI, Type Safety, Validation

---

Thank you for using AgentHub's schema system! 📋
