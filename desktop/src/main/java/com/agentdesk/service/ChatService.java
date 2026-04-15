package com.agentdesk.service;

import com.agentdesk.api.ApiClient;
import com.agentdesk.api.ApiExceptionMapper;
import com.agentdesk.model.McpServer;
import com.agentdesk.model.dto.SendMessageRequest;
import com.agentdesk.model.dto.SendMessageResponse;
import javafx.application.Platform;
import javafx.concurrent.Task;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Random;
import java.util.function.Consumer;

/**
 * Sends chat messages to the AgentHub backend and drives the word-by-word reveal
 * animation that gives the impression of a streaming response.
 *
 * <h3>Flow</h3>
 * <ol>
 *   <li>{@link #streamResponse} posts to {@code POST /api/v1/chat/message} on the
 *       {@link ApiClient}'s background thread pool.</li>
 *   <li>When the response arrives the full text is word-tokenised.</li>
 *   <li>A daemon {@link Thread} replays the tokens with human-like delays, dispatching
 *       each cumulative chunk via {@code Platform.runLater(onChunk)}.</li>
 *   <li>On completion {@code onComplete} is called on the JavaFX thread with the full
 *       {@link SendMessageResponse} so the caller can capture the {@code session_id}.</li>
 * </ol>
 *
 * <h3>Threading contract</h3>
 * {@code onChunk} and {@code onComplete} are always called on the JavaFX Application Thread.
 * The returned {@link Task} can be cancelled; the word-reveal loop will stop at the next
 * token boundary.
 */
@Service
public final class ChatService {

    private static final Logger log = LoggerFactory.getLogger(ChatService.class);

    private static final String CHAT_MESSAGE_PATH = "/api/v1/chat/message";

    private final ApiClient          apiClient;
    private final ApiExceptionMapper exceptionMapper;
    private final Random             random = new Random();

    public ChatService(ApiClient apiClient, ApiExceptionMapper exceptionMapper) {
        this.apiClient       = apiClient;
        this.exceptionMapper = exceptionMapper;
    }

    // -------------------------------------------------------------------------
    // Public API
    // -------------------------------------------------------------------------

    /**
     * Sends {@code userInput} to the backend and streams the response text token-by-token
     * to the caller via {@code onChunk}.
     *
     * @param userInput  the user's message text; must not be blank
     * @param sessionId  the current session identifier, or {@code null} for the first message
     * @param provider   the LLM provider key (e.g. {@code "anthropic"}), or {@code null} for default
     * @param model      the model identifier (e.g. {@code "claude-sonnet-4-5"}), or {@code null} for default
     * @param servers    the MCP servers to attach to this request; may be empty
     * @param onChunk    called on the JavaFX thread with each cumulative text chunk during reveal
     * @param onComplete called on the JavaFX thread with the full response once reveal finishes
     * @return a {@link Task} that can be cancelled to abort the reveal mid-stream
     */
    public Task<Void> streamResponse(
            String userInput,
            String sessionId,
            String provider,
            String model,
            List<McpServer> servers,
            Consumer<String> onChunk,
            Consumer<SendMessageResponse> onComplete) {

        final List<String> serverIds = servers == null
                ? List.of()
                : servers.stream().map(McpServer::getId).toList();

        final SendMessageRequest request = new SendMessageRequest(
                userInput, sessionId, provider, model,
                serverIds.isEmpty() ? null : serverIds);

        log.debug("Sending chat message to session='{}' provider='{}' model='{}' servers={}",
                sessionId, provider, model, serverIds);

        final Task<Void> revealTask = buildRevealTask(onChunk, onComplete);

        // Kick off the API call on the executor; once it responds start the reveal.
        apiClient.postAsync(CHAT_MESSAGE_PATH, request, SendMessageResponse.class)
                .whenComplete((response, throwable) -> {
                    if (throwable != null) {
                        final String msg = exceptionMapper.toUserMessage(throwable);
                        log.error("Chat message failed: {}", msg);
                        final SendMessageResponse errorResponse =
                                new SendMessageResponse(false, null, sessionId, msg);
                        Platform.runLater(() -> onComplete.accept(errorResponse));
                        return;
                    }
                    if (!response.success() || response.response() == null) {
                        final String detail = response.message() != null
                                ? response.message()
                                : "The assistant returned an empty response.";
                        log.warn("Backend reported failure: {}", detail);
                        final SendMessageResponse errorResponse =
                                new SendMessageResponse(false, null, response.sessionId(), detail);
                        Platform.runLater(() -> onComplete.accept(errorResponse));
                        return;
                    }
                    log.info("Received response for session='{}' ({} chars)",
                            response.sessionId(), response.response().length());
                    startReveal(revealTask, response);
                });

        return revealTask;
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    /**
     * Builds the {@link Task} that drives the word-reveal animation.
     * The response text and response object are injected later via
     * {@link RevealTask#setResponse(SendMessageResponse)}.
     */
    private Task<Void> buildRevealTask(
            Consumer<String> onChunk,
            Consumer<SendMessageResponse> onComplete) {
        return new RevealTask(onChunk, onComplete, random);
    }

    private void startReveal(Task<Void> task, SendMessageResponse response) {
        ((RevealTask) task).setResponse(response);
        final Thread thread = new Thread(task, "chat-reveal");
        thread.setDaemon(true);
        thread.start();
    }

    // -------------------------------------------------------------------------
    // Inner task
    // -------------------------------------------------------------------------

    /**
     * A {@link Task} that waits for the server response to be injected and then
     * replays the text word-by-word with human-like timing delays.
     */
    private static final class RevealTask extends Task<Void> {

        private final Consumer<String>             onChunk;
        private final Consumer<SendMessageResponse> onComplete;
        private final Random                        random;
        private volatile SendMessageResponse        response;

        private final Object latch = new Object();

        RevealTask(Consumer<String> onChunk,
                   Consumer<SendMessageResponse> onComplete,
                   Random random) {
            this.onChunk    = onChunk;
            this.onComplete = onComplete;
            this.random     = random;
        }

        void setResponse(SendMessageResponse response) {
            synchronized (latch) {
                this.response = response;
                latch.notifyAll();
            }
        }

        @Override
        protected Void call() throws Exception {
            // Wait until the API call populates the response.
            synchronized (latch) {
                while (response == null && !isCancelled()) {
                    latch.wait(50);
                }
            }
            if (isCancelled() || response == null) {
                return null;
            }

            final String text = response.response();
            if (text == null || text.isBlank()) {
                Platform.runLater(() -> onComplete.accept(response));
                return null;
            }

            // Tokenise on whitespace boundaries, preserving the whitespace tokens.
            final String[] tokens = text.split("(?<=\\s)|(?=\\s)");
            final StringBuilder built = new StringBuilder(text.length());

            for (final String token : tokens) {
                if (isCancelled()) break;
                built.append(token);
                final String chunk = built.toString();
                Platform.runLater(() -> onChunk.accept(chunk));

                int delayMs = 12 + random.nextInt(18);
                if (token.contains("\n"))                               delayMs += 40;
                if (token.contains(".") || token.contains("?") || token.contains("!")) delayMs += 20;
                Thread.sleep(delayMs);
            }

            final SendMessageResponse finalResponse = response;
            Platform.runLater(() -> onComplete.accept(finalResponse));
            return null;
        }
    }
}
