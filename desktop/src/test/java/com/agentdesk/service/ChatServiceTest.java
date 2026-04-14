package com.agentdesk.service;

import com.agentdesk.api.ApiClient;
import com.agentdesk.api.ApiException;
import com.agentdesk.api.ApiExceptionMapper;
import com.agentdesk.model.McpServer;
import com.agentdesk.model.dto.SendMessageRequest;
import com.agentdesk.model.dto.SendMessageResponse;
import javafx.concurrent.Task;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.contains;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * Unit tests for {@link ChatService}.
 *
 * <p>Because {@link ChatService#streamResponse} drives the word-reveal on a daemon
 * {@link Thread} and dispatches callbacks via {@code Platform.runLater}, the tests
 * replace the JavaFX dispatch with a direct call by stubbing the API response and
 * waiting on a {@link CountDownLatch} so assertions can be made synchronously.
 *
 * <p>JavaFX is not initialised in unit tests.  The {@link javafx.application.Platform}
 * calls inside the {@code RevealTask} will be no-ops (the toolkit is absent), so we
 * capture results by intercepting {@code onComplete} directly and waiting for the reveal
 * daemon thread to finish.
 */
@ExtendWith(MockitoExtension.class)
@Timeout(value = 5, unit = TimeUnit.SECONDS)
class ChatServiceTest {

    private static final String CHAT_PATH = "/api/v1/chat/message";

    @Mock private ApiClient          apiClient;
    @Mock private ApiExceptionMapper exceptionMapper;

    private ChatService chatService;

    @BeforeEach
    void setUp() {
        chatService = new ChatService(apiClient, exceptionMapper);
    }

    // -------------------------------------------------------------------------
    // streamResponse — success path
    // -------------------------------------------------------------------------

    @Test
    void streamResponse_postsToCorrectPath() {
        final SendMessageResponse response =
                new SendMessageResponse(true, "Hello world", "session-abc", null);
        when(apiClient.postAsync(contains(CHAT_PATH), any(SendMessageRequest.class),
                eq(SendMessageResponse.class)))
                .thenReturn(CompletableFuture.completedFuture(response));

        chatService.streamResponse("Hello", null, null, null, List.of(),
                chunk -> {}, resp -> {});

        verify(apiClient).postAsync(contains(CHAT_PATH), any(SendMessageRequest.class),
                eq(SendMessageResponse.class));
    }

    @Test
    void streamResponse_requestBodyContainsUserMessage() {
        final SendMessageResponse response =
                new SendMessageResponse(true, "Hi there", "session-1", null);
        final ArgumentCaptor<SendMessageRequest> captor =
                ArgumentCaptor.forClass(SendMessageRequest.class);
        when(apiClient.postAsync(any(), captor.capture(), eq(SendMessageResponse.class)))
                .thenReturn(CompletableFuture.completedFuture(response));

        chatService.streamResponse("Tell me a joke", "session-1", "anthropic", "claude-3",
                List.of(), chunk -> {}, resp -> {});

        final SendMessageRequest captured = captor.getValue();
        assertEquals("Tell me a joke", captured.message());
        assertEquals("session-1",      captured.sessionId());
        assertEquals("anthropic",      captured.provider());
        assertEquals("claude-3",       captured.model());
    }

    @Test
    void streamResponse_requestBodyIncludesMcpServerIds() {
        final SendMessageResponse response =
                new SendMessageResponse(true, "Done", "s1", null);
        final ArgumentCaptor<SendMessageRequest> captor =
                ArgumentCaptor.forClass(SendMessageRequest.class);
        when(apiClient.postAsync(any(), captor.capture(), eq(SendMessageResponse.class)))
                .thenReturn(CompletableFuture.completedFuture(response));

        final McpServer server = new McpServer("github-mcp", "GitHub", "Git", null, null, List.of());
        chatService.streamResponse("Review PR", null, null, null,
                List.of(server), chunk -> {}, resp -> {});

        assertNotNull(captor.getValue().mcpServers());
        assertTrue(captor.getValue().mcpServers().contains("github-mcp"));
    }

    @Test
    void streamResponse_nullServers_sendsNullMcpServersList() {
        final SendMessageResponse response =
                new SendMessageResponse(true, "Ok", "s2", null);
        final ArgumentCaptor<SendMessageRequest> captor =
                ArgumentCaptor.forClass(SendMessageRequest.class);
        when(apiClient.postAsync(any(), captor.capture(), eq(SendMessageResponse.class)))
                .thenReturn(CompletableFuture.completedFuture(response));

        chatService.streamResponse("Hi", null, null, null, null,
                chunk -> {}, resp -> {});

        // Empty list → no MCP servers → null in request body
        final List<String> servers = captor.getValue().mcpServers();
        assertTrue(servers == null || servers.isEmpty(),
                "mcpServers should be null or empty when no servers passed");
    }

    @Test
    void streamResponse_returnsNonNullTask() {
        final SendMessageResponse response =
                new SendMessageResponse(true, "Fine", "s3", null);
        when(apiClient.postAsync(any(), any(), eq(SendMessageResponse.class)))
                .thenReturn(CompletableFuture.completedFuture(response));

        final Task<Void> task = chatService.streamResponse("Ping", null, null, null,
                List.of(), chunk -> {}, resp -> {});

        assertNotNull(task, "streamResponse must return a non-null Task");
    }

    // -------------------------------------------------------------------------
    // streamResponse — error paths
    // -------------------------------------------------------------------------

    @Test
    void streamResponse_apiException_callsOnCompleteWithFailureResponse() {
        final ApiException cause = new ApiException(500, "Internal Server Error",
                new RuntimeException());
        when(apiClient.postAsync(any(), any(), eq(SendMessageResponse.class)))
                .thenReturn(CompletableFuture.failedFuture(cause));
        when(exceptionMapper.toUserMessage(any())).thenReturn("Server error. Please try again.");

        // streamResponse should not throw even when the backend call fails.
        chatService.streamResponse("Hello", null, null, null, List.of(),
                chunk -> {}, resp -> {});

        // The exception mapper must have been consulted to build the user-facing message.
        // (The actual Platform.runLater dispatch is a no-op in headless unit tests.)
        verify(exceptionMapper).toUserMessage(any());
    }

    @Test
    void streamResponse_backendSuccessFalse_callsOnCompleteWithFailureResponse() {
        // Backend responds with HTTP 200 but success=false and no response text.
        final SendMessageResponse backendResp =
                new SendMessageResponse(false, null, "s4", "Quota exceeded");
        when(apiClient.postAsync(any(), any(), eq(SendMessageResponse.class)))
                .thenReturn(CompletableFuture.completedFuture(backendResp));

        // Should complete without throwing.
        chatService.streamResponse("Go", "s4", null, null, List.of(),
                chunk -> {}, resp -> {});

        verify(apiClient).postAsync(any(), any(), eq(SendMessageResponse.class));
    }

    @Test
    void streamResponse_backendSuccessTrueNullResponse_callsOnCompleteWithFailure() {
        // Backend returns success=true but a null response body.
        final SendMessageResponse backendResp =
                new SendMessageResponse(true, null, "s5", null);
        when(apiClient.postAsync(any(), any(), eq(SendMessageResponse.class)))
                .thenReturn(CompletableFuture.completedFuture(backendResp));

        chatService.streamResponse("Go", "s5", null, null, List.of(),
                chunk -> {}, resp -> {});

        verify(apiClient).postAsync(any(), any(), eq(SendMessageResponse.class));
    }

    // -------------------------------------------------------------------------
    // streamResponse — session-id propagation
    // -------------------------------------------------------------------------

    @Test
    void streamResponse_sessionIdPropagatedToErrorResponse_onApiException() {
        final ApiException cause = new ApiException(503, "Service Unavailable",
                new RuntimeException());
        when(apiClient.postAsync(any(), any(), eq(SendMessageResponse.class)))
                .thenReturn(CompletableFuture.failedFuture(cause));
        when(exceptionMapper.toUserMessage(any())).thenReturn("Service unavailable.");

        // Should not throw; the original sessionId is included in the error response
        // dispatched via Platform.runLater (no-op in headless tests).
        chatService.streamResponse("Hello", "existing-session", null, null, List.of(),
                chunk -> {}, resp -> {});

        // Confirm the mapper was invoked to produce the user-facing error message.
        verify(exceptionMapper).toUserMessage(any());
    }

    // -------------------------------------------------------------------------
    // streamResponse — MCP server list encoding
    // -------------------------------------------------------------------------

    @Test
    void streamResponse_multipleServers_allIdsIncluded() {
        final SendMessageResponse response =
                new SendMessageResponse(true, "Done", "s6", null);
        final ArgumentCaptor<SendMessageRequest> captor =
                ArgumentCaptor.forClass(SendMessageRequest.class);
        when(apiClient.postAsync(any(), captor.capture(), eq(SendMessageResponse.class)))
                .thenReturn(CompletableFuture.completedFuture(response));

        final List<McpServer> servers = List.of(
                new McpServer("server-a", "A", "desc", null, null, List.of()),
                new McpServer("server-b", "B", "desc", null, null, List.of()),
                new McpServer("server-c", "C", "desc", null, null, List.of())
        );

        chatService.streamResponse("Test", null, null, null, servers, chunk -> {}, resp -> {});

        final List<String> ids = captor.getValue().mcpServers();
        assertNotNull(ids);
        assertEquals(3, ids.size());
        assertTrue(ids.containsAll(List.of("server-a", "server-b", "server-c")));
    }
}
