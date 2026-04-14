package com.agentdesk.service;

import com.agentdesk.api.ApiClient;
import com.agentdesk.api.ApiExceptionMapper;
import com.agentdesk.model.Conversation;
import com.agentdesk.model.ChatMessage;
import com.agentdesk.model.dto.CreateSessionResponse;
import com.agentdesk.model.dto.DeleteSessionResponse;
import com.agentdesk.model.dto.MessageHistoryResponse;
import com.agentdesk.model.dto.MessageItem;
import com.agentdesk.model.dto.SessionItem;
import com.agentdesk.model.dto.SessionListResponse;
import com.agentdesk.model.dto.UpdateTitleResponse;
import javafx.application.Platform;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.collections.transformation.FilteredList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;

/**
 * Manages the list of chat sessions, backed by the AgentHub backend.
 *
 * <h3>Session lifecycle</h3>
 * <ol>
 *   <li>On app start (after login) call {@link #loadSessions(Consumer)} to populate the list.</li>
 *   <li>New conversations are created locally and then registered with the server via
 *       {@link #createConversation(String)}.</li>
 *   <li>Rename and delete are applied optimistically locally and confirmed by the server.</li>
 * </ol>
 *
 * <h3>Threading contract</h3>
 * The {@link ObservableList} is always mutated on the JavaFX Application Thread.
 * All server calls are submitted asynchronously and results are dispatched via
 * {@code Platform.runLater()}.
 */
@Service
public final class ConversationService {

    private static final Logger log = LoggerFactory.getLogger(ConversationService.class);

    private static final String SESSIONS_PATH        = "/api/v1/chat/sessions?page=0&limit=20";
    private static final String SESSION_TITLE_PATH   = "/api/v1/chat/sessions/%s/title";
    private static final String SESSION_HISTORY_PATH = "/api/v1/chat/sessions/%s/messages";
    private static final String SESSION_DELETE_PATH  = "/api/v1/chat/sessions/%s";

    private final ApiClient          apiClient;
    private final ApiExceptionMapper exceptionMapper;

    private final ObservableList<Conversation> conversations    = FXCollections.observableArrayList();
    private final FilteredList<Conversation>   filteredConversations =
            new FilteredList<>(conversations, p -> true);

    public ConversationService(ApiClient apiClient, ApiExceptionMapper exceptionMapper) {
        this.apiClient       = apiClient;
        this.exceptionMapper = exceptionMapper;
    }

    // -------------------------------------------------------------------------
    // Observable accessors
    // -------------------------------------------------------------------------

    public ObservableList<Conversation> getConversations() {
        return conversations;
    }

    public FilteredList<Conversation> getFilteredConversations() {
        return filteredConversations;
    }

    // -------------------------------------------------------------------------
    // Session loading
    // -------------------------------------------------------------------------

    /**
     * Loads all sessions from the server and replaces the local list.
     *
     * <p>The list is refreshed on the JavaFX Application Thread. If the call fails the
     * {@code onError} callback receives a user-facing message string.
     *
     * @param onError called on the JavaFX thread with a display message if the load fails
     */
    public void loadSessions(Consumer<String> onError) {
        loadSessions(null, onError);
    }

    /**
     * Loads all sessions from the server and replaces the local list.
     *
     * @param onSuccess called on the JavaFX thread after the list is updated successfully; may be {@code null}
     * @param onError   called on the JavaFX thread with a display message if the load fails; may be {@code null}
     */
    public void loadSessions(Runnable onSuccess, Consumer<String> onError) {
        log.debug("Loading chat sessions from server");
        apiClient.getAsync(SESSIONS_PATH, SessionListResponse.class)
                .whenComplete((response, throwable) -> Platform.runLater(() -> {
                    if (throwable != null) {
                        final String msg = exceptionMapper.toUserMessage(throwable);
                        log.warn("Failed to load sessions: {}", msg);
                        if (onError != null) {
                            onError.accept(msg);
                        }
                        return;
                    }
                    conversations.clear();
                    if (response.sessions() != null) {
                        for (SessionItem item : response.sessions()) {
                            final String title = item.title() != null && !item.title().isBlank()
                                    ? item.title()
                                    : "Untitled";
                            conversations.add(new Conversation(item.sessionId(), title));
                        }
                    }
                    log.info("Loaded {} sessions from server", conversations.size());
                    if (onSuccess != null) {
                        onSuccess.run();
                    }
                }));
    }

    // -------------------------------------------------------------------------
    // CRUD
    // -------------------------------------------------------------------------

    /**
     * Creates a new conversation locally and registers it with the server.
     *
     * <p>The local {@link Conversation} object is returned immediately so the caller can
     * navigate to it.  The {@code serverSessionId} on the returned object will be {@code null}
     * until the server responds; {@link ChatService} will assign it on the first message send.
     *
     * @param title the initial title for the new conversation
     * @return the newly created local conversation; never {@code null}
     */
    public Conversation createConversation(String title) {
        final Conversation conversation = new Conversation(title);
        conversations.add(0, conversation);
        log.debug("Created local conversation '{}' — will obtain serverSessionId on first message", title);
        return conversation;
    }

    /**
     * Associates an existing server session with a local {@link Conversation} and adds it
     * to the front of the list (used after a session is implicitly created by the first
     * chat message).
     *
     * @param serverSessionId the session ID returned by the backend
     * @param title           the initial title
     * @return the hydrated conversation
     */
    public Conversation adoptSession(String serverSessionId, String title) {
        final Conversation conversation = new Conversation(serverSessionId, title);
        Platform.runLater(() -> conversations.add(0, conversation));
        return conversation;
    }

    /**
     * Deletes the conversation locally and fires a server-side delete in the background.
     * If the server-side call fails a warning is logged; the local removal is not reversed
     * (the next {@link #loadSessions} will re-sync the server state).
     *
     * @param conversation the conversation to remove
     */
    public void deleteConversation(Conversation conversation) {
        conversations.remove(conversation);

        if (!conversation.isSynced()) {
            log.debug("Deleted local-only conversation '{}' (no server record)", conversation.getTitle());
            return;
        }

        final String path = String.format(SESSION_DELETE_PATH, conversation.getServerSessionId());
        apiClient.deleteAsync(path)
                .whenComplete((ignored, throwable) -> {
                    if (throwable != null) {
                        log.warn("Server delete failed for session '{}': {}",
                                conversation.getServerSessionId(),
                                exceptionMapper.toUserMessage(throwable));
                    } else {
                        log.info("Deleted server session '{}'", conversation.getServerSessionId());
                    }
                });
    }

    /**
     * Renames the conversation locally and persists the change to the server.
     *
     * @param conversation the conversation to rename
     * @param newTitle     the new display title
     */
    public void renameConversation(Conversation conversation, String newTitle) {
        conversation.setTitle(newTitle);
        final int idx = conversations.indexOf(conversation);
        if (idx >= 0) {
            conversations.set(idx, conversation);
        }

        if (!conversation.isSynced()) {
            log.debug("Renamed local-only conversation to '{}' (no server record)", newTitle);
            return;
        }

        final String path = String.format(SESSION_TITLE_PATH, conversation.getServerSessionId());
        final Map<String, String> body = Map.of("title", newTitle);

        apiClient.putAsync(path, body, UpdateTitleResponse.class)
                .whenComplete((response, throwable) -> {
                    if (throwable != null) {
                        log.warn("Server rename failed for session '{}': {}",
                                conversation.getServerSessionId(),
                                exceptionMapper.toUserMessage(throwable));
                    } else {
                        log.info("Renamed session '{}' → '{}'",
                                conversation.getServerSessionId(), newTitle);
                    }
                });
    }

    // -------------------------------------------------------------------------
    // Message history
    // -------------------------------------------------------------------------

    /**
     * Loads full message history for a session and populates the given conversation's
     * message list on the JavaFX thread.
     *
     * <p>All messages are added in a single {@code addAll()} call so that observers
     * see exactly one change event containing the full history.
     *
     * @param conversation the conversation whose messages should be refreshed
     * @param onComplete   called on the JavaFX thread after the list is populated
     *                     (even when the session has zero messages)
     * @param onError      called on the JavaFX thread with a display message on failure
     */
    public void loadHistory(Conversation conversation, Runnable onComplete, Consumer<String> onError) {
        if (!conversation.isSynced()) {
            log.debug("Skipping history load for unsynced conversation '{}'", conversation.getTitle());
            return;
        }

        final String path = String.format(SESSION_HISTORY_PATH, conversation.getServerSessionId());
        log.debug("Loading history for session '{}'", conversation.getServerSessionId());

        apiClient.getAsync(path, MessageHistoryResponse.class)
                .whenComplete((response, throwable) -> Platform.runLater(() -> {
                    if (throwable != null) {
                        final String msg = exceptionMapper.toUserMessage(throwable);
                        log.warn("Failed to load history for session '{}': {}",
                                conversation.getServerSessionId(), msg);
                        if (onError != null) {
                            onError.accept(msg);
                        }
                        return;
                    }
                    // Build the full list first, then add everything in one addAll() call.
                    // This ensures a single ObservableList change event with all messages.
                    final java.util.List<ChatMessage> batch = new java.util.ArrayList<>();
                    if (response.messages() != null) {
                        for (MessageItem item : response.messages()) {
                            final ChatMessage.Role role = "user".equalsIgnoreCase(item.role())
                                    ? ChatMessage.Role.USER
                                    : ChatMessage.Role.ASSISTANT;
                            batch.add(new ChatMessage(role, item.content()));
                        }
                    }
                    conversation.getMessages().clear();
                    if (!batch.isEmpty()) {
                        conversation.getMessages().addAll(batch);
                    }
                    log.debug("Loaded {} messages for session '{}'",
                            conversation.getMessages().size(), conversation.getServerSessionId());
                    if (onComplete != null) {
                        onComplete.run();
                    }
                }));
    }

    // -------------------------------------------------------------------------
    // Filter
    // -------------------------------------------------------------------------

    public void filterByQuery(String query) {
        if (query == null || query.isBlank()) {
            filteredConversations.setPredicate(p -> true);
        } else {
            final String lower = query.toLowerCase();
            filteredConversations.setPredicate(c ->
                    c.getTitle().toLowerCase().contains(lower));
        }
    }
}

