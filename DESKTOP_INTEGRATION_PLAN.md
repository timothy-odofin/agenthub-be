# Desktop Client Integration Plan

**Branch:** `feature/desktop-client-integration`  
**Author:** AgentHub Contributors  
**Status:** Approved — Ready for Implementation  
**Last Updated:** 2026-04-13

---

## Table of Contents

1. [Objective](#1-objective)
2. [Current State Assessment](#2-current-state-assessment)
3. [Architecture Principles](#3-architecture-principles)
4. [API Contract Reference](#4-api-contract-reference)
5. [Backend Work — Phase 1](#5-backend-work--phase-1-mcp-tools-endpoint)
6. [Desktop Work — Phase 2](#6-desktop-work--phase-2-token-management)
7. [Desktop Work — Phase 3](#7-desktop-work--phase-3-authentication)
8. [Desktop Work — Phase 4](#8-desktop-work--phase-4-session-management)
9. [Desktop Work — Phase 5](#9-desktop-work--phase-5-real-chat-service)
10. [Desktop Work — Phase 6](#10-desktop-work--phase-6-mcp-server-registry)
11. [Desktop Work — Phase 7](#11-desktop-work--phase-7-llm-provider-service)
12. [Desktop Work — Phase 8](#12-desktop-work--phase-8-configuration)
13. [Testing Strategy](#13-testing-strategy)
14. [File Change Manifest](#14-file-change-manifest)
15. [Non-Goals (Future Work)](#15-non-goals-future-work)

---

## 1. Objective

Replace all mock/stubbed service implementations in the JavaFX desktop client
(`desktop/`) with real HTTP calls to the existing FastAPI backend (`backend/`),
producing feature parity with the React frontend for the following user flows:

- **Login** — authenticate and obtain JWT tokens
- **New Chat** — send first message, receive real AI response, persist session
- **Load Session** — restore full message history for an existing conversation
- **Continue Chat** — send subsequent messages within a session
- **Session Management** — rename and delete sessions from the sidebar
- **MCP Tool Picker** — display live tool providers and their tools from the
  backend's `ToolRegistry`

The desktop is a **Spring Boot + JavaFX** application running on Java 21. The
HTTP layer (`ApiClient` / `RestClientApiClient`) is already fully implemented and
production-ready. What is missing is its use.

---

## 2. Current State Assessment

### What is working and production-quality

| Component | File | Status |
|---|---|---|
| HTTP client facade | `api/ApiClient.java` | ✅ Complete |
| Spring `RestClient` impl | `api/RestClientApiClient.java` | ✅ Complete |
| Thread pool executor | `config/HttpClientConfig.java` | ✅ Complete |
| API configuration binding | `config/ApiProperties.java` | ✅ Complete |
| UI controllers (FXML wiring) | `controller/*.java` | ✅ Complete |
| Markdown rendering | `component/MessageBubble.java` | ✅ Complete |
| MCP picker UI | `component/SearchablePickerPopup.java` | ✅ Complete |
| STT (Vosk) service | `service/SpeechToTextService.java` | ✅ Complete |
| Stage / login transition | `config/StageInitializer.java` | ✅ Complete |

### What is stubbed and must be replaced

| Component | File | Problem |
|---|---|---|
| Login | `controller/LoginController.java` | Calls `onLoginSuccess()` immediately — no HTTP |
| Chat service | `service/ChatService.java` | Returns hardcoded lorem-ipsum with word-delay simulation |
| Conversation service | `service/ConversationService.java` | Seeds 6 fake conversations in memory; no persistence |
| MCP registry | `service/McpServerRegistry.java` | Fully hardcoded sample servers and tools |
| Auth token | `config/HttpClientConfig.java` | Static `defaultAuthorization` from YAML — never set at runtime |
| Base URL | `resources/application.yml` | Points to `https://api.example.com` |

### Backend endpoints that already exist

All endpoints below are live and tested in `backend/src/app/api/v1/`:

```
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/chat/message
POST   /api/v1/chat/sessions
GET    /api/v1/chat/sessions
GET    /api/v1/chat/sessions/{session_id}/messages
PUT    /api/v1/chat/sessions/{session_id}/title
DELETE /api/v1/chat/sessions/{session_id}
GET    /api/v1/llm/providers
GET    /api/v1/chat/capabilities         (public — no auth required)
```

### What must be added to the backend

```
GET    /api/v1/tools/mcp                 (authenticated)
```

---

## 3. Architecture Principles

These principles are non-negotiable and govern every file in this feature
branch. They reflect the expectations of an experienced engineering team
maintaining an open-source project.

### 3.1 Separation of Concerns

The existing codebase already follows this cleanly. We must not break it:

- **Model layer** — pure data; no Spring, no JavaFX, no Jackson annotations
  inside `model/`. DTOs for API I/O live in `model/dto/` and are the only
  classes that carry Jackson/JSON annotations.
- **Service layer** — business logic and HTTP orchestration. Services do not
  know about FXML nodes, JavaFX controls, or scene graphs.
- **Controller layer** — binds service results to JavaFX nodes via
  `Platform.runLater()`. Controllers do not call `RestClient` directly.
- **Config layer** — Spring beans, property bindings, and application wiring
  only. No business logic.

### 3.2 No Lazy Imports

Every import must appear at the top of the file. The pattern
`import X; // inside a method` is forbidden. The only acceptable deferred
loading is Spring's `@Lazy` annotation when circular bean construction
genuinely cannot be resolved otherwise — and that must be documented with
a comment explaining the cycle.

### 3.3 Explicit Dependencies via Constructor Injection

All Spring-managed beans use **constructor injection** exclusively. Field
injection (`@Autowired` on a field) and setter injection are not permitted.
This makes dependencies visible, testable without a container, and
immutable after construction.

```java
// Correct
@Service
public class AuthService {
    private final ApiClient apiClient;
    private final TokenStore tokenStore;

    public AuthService(ApiClient apiClient, TokenStore tokenStore) {
        this.apiClient = apiClient;
        this.tokenStore = tokenStore;
    }
}

// Forbidden
@Service
public class AuthService {
    @Autowired private ApiClient apiClient;   // ❌
}
```

### 3.4 Thread Safety and the JavaFX Thread Contract

The JavaFX Application Thread (JAT) must never block on I/O.

- All `ApiClient` calls use the `*Async()` variants, which run on the
  `apiClientExecutor` thread pool.
- Results are applied to the UI exclusively via `Platform.runLater()`.
- `CompletableFuture` chains must terminate with either
  `thenAcceptAsync(..., Platform::runLater)` or an explicit
  `.whenComplete((r, ex) -> Platform.runLater(...))`.
- No `Thread.sleep()`, no `Future.get()` with a timeout, and no
  `CountDownLatch` on the JAT.

### 3.5 Error Handling is a First-Class Citizen

Every `CompletableFuture` chain that reaches the UI must handle both the
happy path and the error path. Unhandled `exceptionally()` clauses that
silently swallow exceptions are a defect.

```java
apiClient.postAsync(path, body, ResponseType.class)
    .thenAccept(response -> Platform.runLater(() -> onSuccess(response)))
    .exceptionally(ex -> {
        Platform.runLater(() -> showError(ApiExceptionMapper.toMessage(ex)));
        return null;
    });
```

A dedicated `ApiExceptionMapper` utility class will translate `ApiException`
status codes to user-facing messages.

### 3.6 Immutability and Value Objects

DTO classes are **records** (Java 21). They are immutable, require no
boilerplate getters/setters, and make defensive copies unnecessary.

```java
// Correct — Java record
public record SessionItem(
    String sessionId,
    String title,
    String createdAt,
    String lastMessageAt
) {}
```

The existing domain models (`Conversation`, `ChatMessage`, `McpServer`, etc.)
keep their current mutable form because JavaFX `ObservableList` and property
bindings require mutability. DTOs and domain models must not be conflated.

### 3.7 Open/Closed for Extension

New capabilities (e.g., SSE streaming, OAuth, WebSocket) must be addable
without modifying existing service contracts. The `ApiClient` interface
already models this correctly. Services must be coded to interfaces where
extension is anticipated.

### 3.8 Null Safety

- All method parameters that accept `null` are annotated `@Nullable`
  (Spring's `org.springframework.lang.Nullable`).
- All parameters that must not be `null` are annotated `@NonNull` or use
  `Objects.requireNonNull()` at the top of the constructor.
- `Optional<T>` is used for optional return values, never returning `null`
  from a public method without annotation.

### 3.9 Logging

Use SLF4J (`LoggerFactory.getLogger(Foo.class)`). Log levels:

- `DEBUG` — internal state useful during development
- `INFO` — significant lifecycle events (service started, session created)
- `WARN` — recoverable problems (token refresh attempted)
- `ERROR` — unrecoverable failures with the full exception object

Never log credentials, tokens, or full request bodies.

---

## 4. API Contract Reference

This section is the single source of truth for the HTTP interface.  
The backend schema source of record is `backend/src/app/schemas/`.

### 4.1 POST `/api/v1/auth/login`

**Request:**
```json
{ "identifier": "user@example.com", "password": "..." }
```
**Response (200):**
```json
{
  "success": true,
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "...", "email": "...", "name": "..." }
}
```
**Error (401):** `{ "success": false, "message": "Invalid credentials" }`

### 4.2 POST `/api/v1/auth/refresh`

**Request:** `{ "refresh_token": "eyJ..." }`  
**Response (200):** `{ "access_token": "eyJ...", "token_type": "bearer" }`

### 4.3 POST `/api/v1/chat/message`

**Request:**
```json
{
  "message": "Hello",
  "session_id": null,
  "provider": "anthropic",
  "model": "claude-sonnet-4-6"
}
```
**Response (200):**
```json
{
  "success": true,
  "message": "Hello! How can I help you?",
  "session_id": "uuid-string",
  "user_id": "...",
  "timestamp": "2026-04-13T10:00:00Z",
  "processing_time_ms": 1234.5,
  "tools_used": [],
  "errors": [],
  "metadata": {}
}
```

### 4.4 GET `/api/v1/chat/sessions`

**Query params:** `page=0&limit=20`  
**Response:** `{ "success": true, "sessions": [...], "total": N, "has_more": false }`

### 4.5 GET `/api/v1/chat/sessions/{id}/messages`

**Query params:** `limit=50`  
**Response:** `{ "success": true, "session_id": "...", "messages": [...], "count": N }`

### 4.6 PUT `/api/v1/chat/sessions/{id}/title`

**Request:** `{ "title": "New Title" }`  
**Response:** `{ "success": true, "session_id": "...", "title": "New Title" }`

### 4.7 DELETE `/api/v1/chat/sessions/{id}`

**Response:** `{ "success": true, "session_id": "...", "deleted_at": "..." }`

### 4.8 GET `/api/v1/llm/providers`

**Response:**
```json
{
  "success": true,
  "providers": [
    {
      "name": "anthropic",
      "display_name": "Anthropic (Claude)",
      "model_versions": ["claude-sonnet-4-6", "claude-opus-4-5"],
      "default_model": "claude-sonnet-4-6",
      "is_default": true
    }
  ],
  "total": 1
}
```

### 4.9 GET `/api/v1/tools/mcp` *(new — see Phase 1)*

**Response:**
```json
{
  "success": true,
  "groups": [
    {
      "category": "github",
      "label": "GitHub",
      "servers": [
        {
          "id": "github",
          "name": "GitHub",
          "description": "GitHub repository operations via MCP",
          "tool_count": 10,
          "tools": [
            { "name": "search_code",       "description": "Full-text search across all files in a repo" },
            { "name": "list_issues",        "description": "List issues in a repository" }
          ]
        }
      ]
    },
    {
      "category": "jira",
      "label": "Jira",
      "servers": [ ... ]
    }
  ]
}
```

---

## 5. Backend Work — Phase 1: MCP Tools Endpoint

### 5.1 Why

The desktop's `McpServerRegistry` currently hardcodes 12+ server entries with
their tools. The backend's `ToolRegistry` is the authoritative source of truth
for which tools are enabled, filtered, and configured. Exposing this via an
endpoint gives the desktop — and any future client — a live, consistent view.

### 5.2 New file: `backend/src/app/schemas/tools.py`

Define three Pydantic models using explicit field definitions. No `model_config`
shortcuts that obscure the schema shape.

```python
# backend/src/app/schemas/tools.py

from typing import List
from pydantic import BaseModel


class McpToolInfo(BaseModel):
    name: str
    description: str


class McpServerInfo(BaseModel):
    id: str
    name: str
    description: str
    tool_count: int
    tools: List[McpToolInfo]


class McpGroupInfo(BaseModel):
    category: str
    label: str
    servers: List[McpServerInfo]


class McpToolsResponse(BaseModel):
    success: bool
    groups: List[McpGroupInfo]
```

### 5.3 New file: `backend/src/app/api/v1/tools.py`

```python
# backend/src/app/api/v1/tools.py

from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.db.models.user import UserInDB
from app.agent.tools.base.registry import ToolRegistry
from app.schemas.tools import McpGroupInfo, McpServerInfo, McpToolInfo, McpToolsResponse
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Human-readable labels for known registry categories.
# Add new entries here as new tool packages are registered.
_CATEGORY_LABELS: dict[str, str] = {
    "github":     "GitHub",
    "jira":       "Jira",
    "confluence": "Confluence",
    "datadog":    "Datadog",
    "vector":     "Knowledge Base",
    "web":        "Web",
    "navigation": "Navigation",
}


@router.get("/mcp", response_model=McpToolsResponse)
async def list_mcp_tools(
    current_user: UserInDB = Depends(get_current_user),
) -> McpToolsResponse:
    """
    Return all enabled MCP tool providers grouped by category.

    Each group contains one or more server entries, and each server lists
    the tools it exposes. This endpoint allows desktop and other thick
    clients to display the live tool picker without hardcoding tool names.

    Requires authentication — tools reflect the server's live configuration.
    """
    groups: list[McpGroupInfo] = []

    for category in ToolRegistry.get_categories():
        tool_classes = ToolRegistry.get_tools_by_category(category)
        if not tool_classes:
            continue

        servers: list[McpServerInfo] = []

        for tool_class in tool_classes:
            try:
                provider = tool_class()
                langchain_tools = provider.get_tools()
            except Exception:
                logger.warning(
                    "Could not instantiate provider %s for category '%s'",
                    getattr(tool_class, "__name__", repr(tool_class)),
                    category,
                )
                continue

            if not langchain_tools:
                continue

            tool_infos = [
                McpToolInfo(name=t.name, description=t.description or "")
                for t in langchain_tools
            ]

            provider_name = getattr(tool_class, "__name__", category)
            servers.append(
                McpServerInfo(
                    id=category,
                    name=_CATEGORY_LABELS.get(category, provider_name),
                    description=f"{_CATEGORY_LABELS.get(category, provider_name)} tools",
                    tool_count=len(tool_infos),
                    tools=tool_infos,
                )
            )

        if servers:
            groups.append(
                McpGroupInfo(
                    category=category,
                    label=_CATEGORY_LABELS.get(category, category.title()),
                    servers=servers,
                )
            )

    return McpToolsResponse(success=True, groups=groups)
```

### 5.4 Modify: `backend/src/app/main.py`

Add the new router import alongside the existing ones and register it:

```python
# In the APPLICATION IMPORTS block — add alongside existing imports:
from app.api.v1 import auth, chat, conversational_auth, health
from app.api.v1 import ingest_data as ingest
from app.api.v1 import llm, resilience, routes, tools   # ← add tools

# In the router registration block — add after the llm router:
app.include_router(tools.router, prefix="/api/v1/tools", tags=["Tools"])
```

---

## 6. Desktop Work — Phase 2: Token Management

### 6.1 Problem

`HttpClientConfig` sets a static `Authorization` header from YAML at bean
construction time. That value is empty until overwritten, and the bean is
a singleton — so there is no mechanism to swap the token after login.

### 6.2 New class: `config/TokenStore.java`

A Spring singleton (`@Component`) that holds the runtime JWT state. It is the
single source of truth for authentication state in the application.

```java
package com.agentdesk.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.lang.NonNull;
import org.springframework.lang.Nullable;
import org.springframework.stereotype.Component;

import java.util.Objects;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Thread-safe, in-memory store for the current user's JWT tokens.
 *
 * <p>Tokens are held only for the lifetime of the application process.
 * No persistence to disk is performed — on restart the user must log in again.
 *
 * <p>This class is the single gatekeeper for authentication state. Every
 * component that needs to know "is the user logged in?" or "what is the
 * current bearer token?" reads from here.
 */
@Component
public class TokenStore {

    private static final Logger log = LoggerFactory.getLogger(TokenStore.class);

    private final AtomicReference<String> accessToken  = new AtomicReference<>();
    private final AtomicReference<String> refreshToken = new AtomicReference<>();

    /**
     * Store a new token pair after successful login or token refresh.
     *
     * @param accessToken  JWT access token — must not be null or blank
     * @param refreshToken JWT refresh token — must not be null or blank
     */
    public void setTokens(@NonNull String accessToken, @NonNull String refreshToken) {
        Objects.requireNonNull(accessToken,  "accessToken must not be null");
        Objects.requireNonNull(refreshToken, "refreshToken must not be null");
        this.accessToken.set(accessToken);
        this.refreshToken.set(refreshToken);
        log.info("Tokens updated — access token stored");
    }

    /**
     * Returns the current access token, or {@code null} if the user is not
     * authenticated.
     */
    @Nullable
    public String getAccessToken() {
        return accessToken.get();
    }

    /**
     * Returns the current refresh token, or {@code null} if the user is not
     * authenticated.
     */
    @Nullable
    public String getRefreshToken() {
        return refreshToken.get();
    }

    /**
     * Returns {@code true} if a non-null access token is currently held.
     */
    public boolean isAuthenticated() {
        return accessToken.get() != null;
    }

    /**
     * Clears both tokens. Call this on logout.
     */
    public void clear() {
        accessToken.set(null);
        refreshToken.set(null);
        log.info("Token store cleared — user logged out");
    }
}
```

### 6.3 Modify: `config/HttpClientConfig.java`

Replace the static `defaultRequest` header with a per-request interceptor that
reads the current token from `TokenStore` at call time.

- Add `TokenStore` as a constructor parameter on `HttpClientConfig`
- Remove the `defaultAuthorization` block from the `RestClient` builder
- Add a `ClientHttpRequestInterceptor` that injects `Authorization: Bearer <token>`
  only when `tokenStore.getAccessToken()` is non-null

```java
// Key change in restClient() bean method:
RestClient.Builder builder = RestClient.builder()
    .baseUrl(apiProperties.getBaseUrl())
    .requestFactory(factory)
    .requestInterceptor((request, body, execution) -> {
        String token = tokenStore.getAccessToken();
        if (token != null && !token.isBlank()) {
            request.getHeaders().setBearerAuth(token);
        }
        return execution.execute(request, body);
    });
// Remove the old: if (auth != null ...) builder.defaultRequest(...)
```

---

## 7. Desktop Work — Phase 3: Authentication

### 7.1 New record: `model/dto/LoginRequest.java`

```java
package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Request body for {@code POST /api/v1/auth/login}.
 * The backend accepts either an email address or a username as the identifier.
 */
public record LoginRequest(
    @JsonProperty("identifier") String identifier,
    @JsonProperty("password")   String password
) {}
```

### 7.2 New record: `model/dto/LoginResponse.java`

```java
package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Response from {@code POST /api/v1/auth/login}.
 */
public record LoginResponse(
    @JsonProperty("success")       boolean success,
    @JsonProperty("access_token")  String  accessToken,
    @JsonProperty("refresh_token") String  refreshToken,
    @JsonProperty("token_type")    String  tokenType,
    @JsonProperty("message")       String  message
) {}
```

### 7.3 New record: `model/dto/RefreshRequest.java`

```java
package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record RefreshRequest(
    @JsonProperty("refresh_token") String refreshToken
) {}
```

### 7.4 New record: `model/dto/RefreshResponse.java`

```java
package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record RefreshResponse(
    @JsonProperty("access_token") String accessToken,
    @JsonProperty("token_type")   String tokenType
) {}
```

### 7.5 New class: `service/AuthService.java`

Owns the login and token-refresh flows. Does not touch any JavaFX node.

```java
package com.agentdesk.service;

import com.agentdesk.api.ApiClient;
import com.agentdesk.api.ApiException;
import com.agentdesk.config.TokenStore;
import com.agentdesk.model.dto.LoginRequest;
import com.agentdesk.model.dto.LoginResponse;
import com.agentdesk.model.dto.RefreshRequest;
import com.agentdesk.model.dto.RefreshResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Service;

import java.util.Objects;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;

/**
 * Handles authentication against {@code /api/v1/auth/*}.
 *
 * <p>All network calls are dispatched on the background executor via
 * {@link ApiClient#postAsync}. Callers must apply results on the
 * JavaFX Application Thread via {@code Platform.runLater()}.
 */
@Service
public class AuthService {

    private static final Logger log = LoggerFactory.getLogger(AuthService.class);

    private static final String LOGIN_PATH   = "/api/v1/auth/login";
    private static final String REFRESH_PATH = "/api/v1/auth/refresh";

    private final ApiClient   apiClient;
    private final TokenStore  tokenStore;

    public AuthService(@NonNull ApiClient apiClient,
                       @NonNull TokenStore tokenStore) {
        this.apiClient  = Objects.requireNonNull(apiClient,  "apiClient");
        this.tokenStore = Objects.requireNonNull(tokenStore, "tokenStore");
    }

    /**
     * Attempt login with the supplied credentials.
     *
     * @param identifier email or username
     * @param password   plaintext password (transport-layer encrypted via TLS)
     * @param onSuccess  callback invoked on success with the parsed response
     * @param onFailure  callback invoked on failure with a human-readable message
     * @return the {@link CompletableFuture} representing the in-flight request
     */
    public CompletableFuture<Void> login(
            @NonNull String identifier,
            @NonNull String password,
            @NonNull Consumer<LoginResponse> onSuccess,
            @NonNull Consumer<String> onFailure) {

        Objects.requireNonNull(identifier, "identifier");
        Objects.requireNonNull(password,   "password");
        Objects.requireNonNull(onSuccess,  "onSuccess");
        Objects.requireNonNull(onFailure,  "onFailure");

        LoginRequest request = new LoginRequest(identifier, password);

        return apiClient
            .postAsync(LOGIN_PATH, request, LoginResponse.class)
            .thenAccept(response -> {
                if (response != null && response.success()) {
                    tokenStore.setTokens(response.accessToken(), response.refreshToken());
                    log.info("Login succeeded for identifier '{}'", identifier);
                    onSuccess.accept(response);
                } else {
                    String msg = response != null ? response.message() : "Login failed";
                    log.warn("Login rejected: {}", msg);
                    onFailure.accept(msg);
                }
            })
            .exceptionally(ex -> {
                String msg = ApiExceptionMapper.toMessage(ex);
                log.error("Login request failed", ex);
                onFailure.accept(msg);
                return null;
            });
    }

    /**
     * Exchange the stored refresh token for a new access token.
     * Stores the new token automatically on success.
     *
     * @param onSuccess called with the new access token string
     * @param onFailure called with an error message if refresh fails
     */
    public CompletableFuture<Void> refreshToken(
            @NonNull Consumer<String> onSuccess,
            @NonNull Consumer<String> onFailure) {

        String stored = tokenStore.getRefreshToken();
        if (stored == null || stored.isBlank()) {
            onFailure.accept("No refresh token available — please log in again");
            return CompletableFuture.completedFuture(null);
        }

        return apiClient
            .postAsync(REFRESH_PATH, new RefreshRequest(stored), RefreshResponse.class)
            .thenAccept(response -> {
                if (response != null && response.accessToken() != null) {
                    tokenStore.setTokens(response.accessToken(), stored);
                    log.info("Access token refreshed successfully");
                    onSuccess.accept(response.accessToken());
                } else {
                    onFailure.accept("Token refresh returned an empty response");
                }
            })
            .exceptionally(ex -> {
                log.error("Token refresh failed", ex);
                onFailure.accept(ApiExceptionMapper.toMessage(ex));
                return null;
            });
    }

    /** Clears stored tokens. Call on logout. */
    public void logout() {
        tokenStore.clear();
        log.info("User logged out — tokens cleared");
    }
}
```

### 7.6 New utility: `api/ApiExceptionMapper.java`

Translates raw `ApiException` or `CompletionException` to user-friendly strings.

```java
package com.agentdesk.api;

import org.springframework.lang.NonNull;

import java.util.concurrent.CompletionException;

/**
 * Maps exceptions from the HTTP layer to human-readable error messages
 * suitable for display in the UI.
 */
public final class ApiExceptionMapper {

    private ApiExceptionMapper() {}

    @NonNull
    public static String toMessage(@NonNull Throwable ex) {
        Throwable cause = ex instanceof CompletionException ? ex.getCause() : ex;

        if (cause instanceof ApiException apiEx) {
            return switch (apiEx.getStatusCode()) {
                case 401 -> "Invalid credentials. Please check your email and password.";
                case 403 -> "You do not have permission to perform this action.";
                case 404 -> "The requested resource was not found.";
                case 429 -> "Too many requests. Please wait a moment and try again.";
                case 500, 502, 503 -> "The server encountered an error. Please try again later.";
                default  -> apiEx.getResponseBody() != null
                            ? apiEx.getResponseBody()
                            : "An unexpected error occurred (HTTP " + apiEx.getStatusCode() + ")";
            };
        }

        return cause != null ? cause.getMessage() : "An unexpected error occurred.";
    }
}
```

### 7.7 Modify: `controller/LoginController.java`

Wire `AuthService`, add an error `Label`, and replace the no-op `doLogin()`
with a real async call. Show a spinner while in flight. The FXML must have
matching `fx:id` values for the two new nodes.

```java
// Constructor — receive AuthService via Spring DI
public LoginController(AuthService authService) {
    this.authService = Objects.requireNonNull(authService, "authService");
}

private void doLogin() {
    String id  = emailField.getText().trim();
    String pwd = passwordField.getText();

    if (id.isBlank() || pwd.isBlank()) {
        showError("Email and password are required.");
        return;
    }

    setLoading(true);

    authService.login(
        id, pwd,
        response -> Platform.runLater(() -> {
            setLoading(false);
            if (onLoginSuccess != null) onLoginSuccess.run();
        }),
        message -> Platform.runLater(() -> {
            setLoading(false);
            showError(message);
        })
    );
}
```

---

## 8. Desktop Work — Phase 4: Session Management

### 8.1 New DTOs

**`model/dto/SessionItem.java`**
```java
public record SessionItem(
    @JsonProperty("session_id")      String sessionId,
    @JsonProperty("title")           String title,
    @JsonProperty("created_at")      @Nullable String createdAt,
    @JsonProperty("last_message_at") @Nullable String lastMessageAt,
    @JsonProperty("message_count")   @Nullable Integer messageCount
) {}
```

**`model/dto/SessionListResponse.java`**
```java
public record SessionListResponse(
    @JsonProperty("success")  boolean         success,
    @JsonProperty("sessions") List<SessionItem> sessions,
    @JsonProperty("total")    int             total,
    @JsonProperty("has_more") boolean         hasMore
) {}
```

**`model/dto/MessageItem.java`**
```java
public record MessageItem(
    @JsonProperty("role")      String role,
    @JsonProperty("content")   String content,
    @JsonProperty("timestamp") @Nullable String timestamp,
    @JsonProperty("id")        @Nullable String id
) {}
```

**`model/dto/MessageHistoryResponse.java`**
```java
public record MessageHistoryResponse(
    @JsonProperty("success")    boolean           success,
    @JsonProperty("session_id") String            sessionId,
    @JsonProperty("messages")   List<MessageItem> messages,
    @JsonProperty("count")      int               count
) {}
```

**`model/dto/CreateSessionResponse.java`**
```java
public record CreateSessionResponse(
    @JsonProperty("success")    boolean success,
    @JsonProperty("session_id") String  sessionId,
    @JsonProperty("title")      String  title,
    @JsonProperty("created_at") String  createdAt
) {}
```

**`model/dto/UpdateTitleResponse.java`**
```java
public record UpdateTitleResponse(
    @JsonProperty("success")    boolean success,
    @JsonProperty("session_id") String  sessionId,
    @JsonProperty("title")      String  title,
    @JsonProperty("message")    @Nullable String message
) {}
```

**`model/dto/DeleteSessionResponse.java`**
```java
public record DeleteSessionResponse(
    @JsonProperty("success")    boolean success,
    @JsonProperty("session_id") String  sessionId,
    @JsonProperty("message")    String  message,
    @JsonProperty("deleted_at") String  deletedAt
) {}
```

### 8.2 Modify domain model: `model/Conversation.java`

Add a `serverSessionId` field — the UUID returned by the backend. This is
distinct from the local `id` field (used by JavaFX for list identity).

```java
// Add alongside existing fields:
private String serverSessionId;   // null until first message is sent or session is loaded

public String getServerSessionId() { return serverSessionId; }
public void setServerSessionId(String serverSessionId) { this.serverSessionId = serverSessionId; }
public boolean isSynced() { return serverSessionId != null; }
```

### 8.3 Rewrite: `service/ConversationService.java`

Remove the `seedSampleConversations()` method entirely. All data flows from
the API.

**Key API methods:**

| Method | Endpoint |
|---|---|
| `loadSessions()` | `GET /api/v1/chat/sessions?page=0&limit=20` |
| `createSession(title)` | `POST /api/v1/chat/sessions` |
| `loadMessages(serverSessionId)` | `GET /api/v1/chat/sessions/{id}/messages?limit=50` |
| `renameConversation(conv, title)` | `PUT /api/v1/chat/sessions/{id}/title` |
| `deleteConversation(conv)` | `DELETE /api/v1/chat/sessions/{id}` |

**Design rules:**
- All calls use `ApiClient.*Async()` — never block the JAT.
- `ObservableList<Conversation>` is updated on `Platform.runLater()`.
- `loadSessions()` is called once at startup (after login) and on `CompletableFuture`
  completion — no polling.
- A `Consumer<String>` error callback is accepted by each mutating method so
  the controller can surface errors to the user.

### 8.4 Modify: `controller/SidebarController.java`

Add a `Runnable onSessionLoadError` callback. Replace the
`seedSampleConversations()` startup data with a `conversationService.loadSessions()`
call triggered from `MainController.initialize()` after the stage is ready.

---

## 9. Desktop Work — Phase 5: Real Chat Service

### 9.1 New DTOs

**`model/dto/SendMessageRequest.java`**
```java
public record SendMessageRequest(
    @JsonProperty("message")    String          message,
    @JsonProperty("session_id") @Nullable String sessionId,
    @JsonProperty("provider")   @Nullable String provider,
    @JsonProperty("model")      @Nullable String model
) {}
```

**`model/dto/SendMessageResponse.java`**
```java
public record SendMessageResponse(
    @JsonProperty("success")            boolean         success,
    @JsonProperty("message")            String          message,
    @JsonProperty("session_id")         String          sessionId,
    @JsonProperty("user_id")            String          userId,
    @JsonProperty("timestamp")          String          timestamp,
    @JsonProperty("processing_time_ms") double          processingTimeMs,
    @JsonProperty("tools_used")         List<String>    toolsUsed,
    @JsonProperty("errors")             List<String>    errors,
    @JsonProperty("metadata")           Map<String, Object> metadata
) {}
```

### 9.2 Rewrite: `service/ChatService.java`

The new `ChatService` does exactly one thing: call `POST /api/v1/chat/message`
and return the response asynchronously.

**The streaming UX is preserved without SSE:** The real API response text is
fed to the existing word-by-word reveal animation. From the user's perspective,
the experience is identical to today — the words appear progressively. The only
change is that the words come from the real LLM rather than a lorem-ipsum list.

**Sequence:**
1. Caller invokes `streamResponse(text, sessionId, provider, model, onChunk, onDone)`
2. Service posts `SendMessageRequest` via `apiClient.postAsync()`
3. On response: the full `message` string is chunked and replayed through
   `onChunk` using a background `Task` — identical animation to the current mock
4. `onDone` is called with the `SendMessageResponse` so the caller can capture
   the `sessionId` (important on first message)
5. On API error: `onDone` is called with `null` and the error is propagated
   via an `onError` consumer

**Signature change:**
```java
public Task<Void> streamResponse(
    String                       userMessage,
    @Nullable String             serverSessionId,
    @Nullable String             provider,
    @Nullable String             model,
    Consumer<String>             onChunk,
    Consumer<SendMessageResponse> onComplete,
    Consumer<String>             onError
)
```

`ChatAreaController` passes `currentConversation.getServerSessionId()` as
`serverSessionId` and stores the returned `sessionId` back on the conversation
in the `onComplete` handler.

---

## 10. Desktop Work — Phase 6: MCP Server Registry

### 10.1 New DTOs

**`model/dto/McpToolDto.java`**
```java
public record McpToolDto(
    @JsonProperty("name")        String name,
    @JsonProperty("description") String description
) {}
```

**`model/dto/McpServerDto.java`**
```java
public record McpServerDto(
    @JsonProperty("id")          String          id,
    @JsonProperty("name")        String          name,
    @JsonProperty("description") String          description,
    @JsonProperty("tool_count")  int             toolCount,
    @JsonProperty("tools")       List<McpToolDto> tools
) {}
```

**`model/dto/McpGroupDto.java`**
```java
public record McpGroupDto(
    @JsonProperty("category") String          category,
    @JsonProperty("label")    String          label,
    @JsonProperty("servers")  List<McpServerDto> servers
) {}
```

**`model/dto/McpToolsResponse.java`**
```java
public record McpToolsResponse(
    @JsonProperty("success") boolean          success,
    @JsonProperty("groups")  List<McpGroupDto> groups
) {}
```

### 10.2 Rewrite: `service/McpServerRegistry.java`

**Design:**

- On `refresh()` call (triggered post-login by `MainController`), fetch
  `GET /api/v1/tools/mcp` via `apiClient.getAsync()`.
- Map each `McpGroupDto` → `ServerCategory` + `McpServer` list.
- `McpTool` objects are created without a `Feather` icon (the icon is inferred
  from the category label using a `CategoryIconResolver` helper, keeping the
  domain model and HTTP DTOs independent).
- Fall back to the existing hardcoded list if the API call fails — this
  ensures the app is usable offline and in development without a running backend.
- Expose `getGroupedServers()` unchanged — callers in `ChatAreaController`
  need no modification.

**New helper: `service/CategoryIconResolver.java`**

A simple static lookup from category string → `Feather` icon constant.
This keeps icon-framework knowledge out of the registry and out of the DTOs.

```java
public final class CategoryIconResolver {
    private CategoryIconResolver() {}

    public static Feather iconFor(String category) {
        return switch (category.toLowerCase()) {
            case "github"     -> Feather.GITHUB;
            case "jira"       -> Feather.TRELLO;
            case "confluence" -> Feather.BOOK_OPEN;
            case "datadog"    -> Feather.ACTIVITY;
            case "vector"     -> Feather.DATABASE;
            case "web"        -> Feather.GLOBE;
            case "navigation" -> Feather.NAVIGATION;
            default           -> Feather.TOOL;
        };
    }
}
```

---

## 11. Desktop Work — Phase 7: LLM Provider Service

### 11.1 New DTOs

**`model/dto/ProviderInfo.java`**
```java
public record ProviderInfo(
    @JsonProperty("name")           String       name,
    @JsonProperty("display_name")   String       displayName,
    @JsonProperty("model_versions") List<String> modelVersions,
    @JsonProperty("default_model")  String       defaultModel,
    @JsonProperty("is_default")     boolean      isDefault
) {}
```

**`model/dto/ProvidersResponse.java`**
```java
public record ProvidersResponse(
    @JsonProperty("success")   boolean          success,
    @JsonProperty("providers") List<ProviderInfo> providers,
    @JsonProperty("total")     int              total
) {}
```

### 11.2 New class: `service/ProviderService.java`

Fetches `GET /api/v1/llm/providers` once after login and caches the result.
Exposes `getProviders()` and `getDefaultProvider()`.

### 11.3 Modify: `controller/ChatAreaController.java`

Replace the hardcoded `{"Sonnet 4.6", "Opus 4.5", "Haiku 4.5"}` array with
a call to `providerService.getProviders()`. Populate `welcomeModelSelector`
and `chatModelSelector` from the live list.

When sending a message, pass `selectedProvider` and `selectedModel` to
`chatService.streamResponse()`.

---

## 12. Desktop Work — Phase 8: Configuration

### 12.1 Update `resources/application.yml`

```yaml
app:
  api:
    base-url: ${AGENTDESK_API_URL:http://localhost:8000}
    connect-timeout: 10s
    read-timeout: 60s
    # default-authorization is intentionally absent — set dynamically by TokenStore
```

The `read-timeout` is raised to 60s from 30s because LLM inference on a cold
agent can take 30–55s (see backend warmup logs from 2026-04-07).

The base URL is overridable via an environment variable `AGENTDESK_API_URL`,
making it deployable without recompiling.

---

## 13. Testing Strategy

### 13.1 Backend — Unit tests (`pytest`)

| Test file | What to test |
|---|---|
| `tests/unit/api/test_tools_endpoint.py` | `GET /api/v1/tools/mcp` — authenticated, returns correct shape, empty groups handled, provider instantiation failure is graceful |
| `tests/unit/schemas/test_tools_schemas.py` | Pydantic model validation |

### 13.2 Desktop — Unit tests (`JUnit 5` + `Mockito`)

| Test class | What to test |
|---|---|
| `TokenStoreTest` | Thread safety, `setTokens` / `clear` / `isAuthenticated` |
| `ApiExceptionMapperTest` | Status code → message mappings for 401, 403, 404, 500, and unknown |
| `AuthServiceTest` | `login()` success path, 401 path, network failure path; `refreshToken()` success and no-stored-token path — mock `ApiClient` with `Mockito` |
| `ConversationServiceTest` | `loadSessions()` populates `ObservableList`; `deleteConversation()` removes correct entry; error callback invoked on failure |
| `ChatServiceTest` | `streamResponse()` invokes `onComplete` with correct session ID; `onError` invoked on `ApiException` |
| `McpServerRegistryTest` | `refresh()` maps DTO groups to `McpServer` list; falls back to hardcoded data on failure |
| `CategoryIconResolverTest` | Known categories return non-`TOOL` icons; unknown returns `TOOL` |

### 13.3 Integration — Manual checklist

A `DESKTOP_INTEGRATION_CHECKLIST.md` will be created alongside this plan
and used for PR review sign-off:

- [ ] Login with valid credentials succeeds and shows main view
- [ ] Login with invalid credentials shows error label, does not advance
- [ ] Session list loads from backend on first open
- [ ] "New chat" sends first message, URL-equivalent session ID is stored
- [ ] Subsequent messages in the same session include the session ID
- [ ] Existing session loads full message history
- [ ] Rename session persists across app restart
- [ ] Delete session removes it from the sidebar
- [ ] MCP picker shows live tools from backend
- [ ] Model selector shows live provider list from backend
- [ ] 401 mid-session triggers token refresh transparently
- [ ] Network failure shows user-facing error, does not crash

---

## 14. File Change Manifest

### Backend (Python)

| Action | File |
|---|---|
| **New** | `backend/src/app/api/v1/tools.py` |
| **New** | `backend/src/app/schemas/tools.py` |
| **Modify** | `backend/src/app/main.py` — add `tools` router import and registration |
| **New** | `backend/tests/unit/api/test_tools_endpoint.py` |

### Desktop (Java)

| Action | File |
|---|---|
| **New** | `desktop/src/main/java/com/agentdesk/config/TokenStore.java` |
| **Modify** | `desktop/src/main/java/com/agentdesk/config/HttpClientConfig.java` |
| **New** | `desktop/src/main/java/com/agentdesk/api/ApiExceptionMapper.java` |
| **New** | `desktop/src/main/java/com/agentdesk/service/AuthService.java` |
| **New** | `desktop/src/main/java/com/agentdesk/service/ProviderService.java` |
| **New** | `desktop/src/main/java/com/agentdesk/service/CategoryIconResolver.java` |
| **Rewrite** | `desktop/src/main/java/com/agentdesk/service/ConversationService.java` |
| **Rewrite** | `desktop/src/main/java/com/agentdesk/service/ChatService.java` |
| **Rewrite** | `desktop/src/main/java/com/agentdesk/service/McpServerRegistry.java` |
| **Modify** | `desktop/src/main/java/com/agentdesk/model/Conversation.java` |
| **Modify** | `desktop/src/main/java/com/agentdesk/controller/LoginController.java` |
| **Modify** | `desktop/src/main/java/com/agentdesk/controller/ChatAreaController.java` |
| **Modify** | `desktop/src/main/java/com/agentdesk/controller/MainController.java` |
| **Modify** | `desktop/src/main/resources/application.yml` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/LoginRequest.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/LoginResponse.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/RefreshRequest.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/RefreshResponse.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/SessionItem.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/SessionListResponse.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/MessageItem.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/MessageHistoryResponse.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/CreateSessionResponse.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/UpdateTitleResponse.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/DeleteSessionResponse.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/SendMessageRequest.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/SendMessageResponse.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/ProviderInfo.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/ProvidersResponse.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/McpToolDto.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/McpServerDto.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/McpGroupDto.java` |
| **New** | `desktop/src/main/java/com/agentdesk/model/dto/McpToolsResponse.java` |
| **New** | `desktop/src/test/java/com/agentdesk/config/TokenStoreTest.java` |
| **New** | `desktop/src/test/java/com/agentdesk/api/ApiExceptionMapperTest.java` |
| **New** | `desktop/src/test/java/com/agentdesk/service/AuthServiceTest.java` |
| **New** | `desktop/src/test/java/com/agentdesk/service/ConversationServiceTest.java` |
| **New** | `desktop/src/test/java/com/agentdesk/service/ChatServiceTest.java` |
| **New** | `desktop/src/test/java/com/agentdesk/service/McpServerRegistryTest.java` |
| **New** | `desktop/src/test/java/com/agentdesk/service/CategoryIconResolverTest.java` |

---

## 15. Non-Goals (Future Work)

The following are explicitly **out of scope** for this branch and should be
tracked as separate issues:

- **SSE / real-time streaming** — The backend can be extended to stream tokens
  via Server-Sent Events. The `ApiClient` interface has room for a
  `streamAsync()` method. This is a follow-on once the REST baseline is stable.
- **Passing selected MCP tools to the backend** — The picker UI exists. The
  `SendMessageRequest` DTO can be extended with a `tools: List<String>` field
  when the backend is ready to consume it.
- **Token persistence across restarts** — `TokenStore` is in-memory. Persisting
  to an OS keychain (e.g., macOS Keychain via JNA) is a follow-on.
- **OAuth / SSO login** — `LoginController` already has `handleSsoLogin()` and
  `handleGoogleLogin()` stubs. Wiring a system-browser OAuth flow is a
  follow-on issue.
- **Offline mode / local caching** — Persisting sessions and messages to a
  local SQLite database for offline access is a follow-on.
- **Auto-title generation** — The current desktop sets the conversation title
  from the first 40 characters of the first message. The backend's
  `SessionTitleService` generates better AI-derived titles. Switching to
  backend-side title generation is a follow-on.
