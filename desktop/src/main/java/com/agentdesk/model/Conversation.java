package com.agentdesk.model;

import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import org.springframework.lang.Nullable;

import java.time.LocalDateTime;
import java.util.UUID;

public class Conversation {

    private final String id;
    private String title;
    private final ObservableList<ChatMessage> messages;
    private final LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    /**
     * The session ID assigned by the backend after the first message in this conversation
     * is sent (or after an explicit {@code POST /api/v1/chat/sessions} call).
     *
     * <p>When {@code null} the conversation has not yet been synchronised with the server
     * (i.e. it is a brand-new, unsent conversation).
     */
    @Nullable
    private String serverSessionId;

    public Conversation(String title) {
        this.id = UUID.randomUUID().toString();
        this.title = title;
        this.messages = FXCollections.observableArrayList();
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * Convenience constructor used when hydrating conversations loaded from the server.
     *
     * @param serverSessionId the session ID already assigned by the backend
     * @param title           the session title
     */
    public Conversation(String serverSessionId, String title) {
        this(title);
        this.serverSessionId = serverSessionId;
    }

    public void addMessage(ChatMessage message) {
        messages.add(message);
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * Returns {@code true} when this conversation has a {@code serverSessionId} and can
     * therefore be used in API calls without first creating a session.
     */
    public boolean isSynced() {
        return serverSessionId != null;
    }

    // -------------------------------------------------------------------------
    // Accessors
    // -------------------------------------------------------------------------

    public String getId() { return id; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public ObservableList<ChatMessage> getMessages() { return messages; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }

    @Nullable
    public String getServerSessionId() { return serverSessionId; }

    public void setServerSessionId(String serverSessionId) {
        this.serverSessionId = serverSessionId;
    }

    @Override
    public String toString() { return title; }
}

