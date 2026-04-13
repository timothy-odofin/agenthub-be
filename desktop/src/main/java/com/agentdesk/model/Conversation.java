package com.agentdesk.model;

import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import java.time.LocalDateTime;
import java.util.UUID;

public class Conversation {

    private final String id;
    private String title;
    private final ObservableList<ChatMessage> messages;
    private final LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public Conversation(String title) {
        this.id = UUID.randomUUID().toString();
        this.title = title;
        this.messages = FXCollections.observableArrayList();
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    public void addMessage(ChatMessage message) {
        messages.add(message);
        this.updatedAt = LocalDateTime.now();
    }

    public String getId() { return id; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public ObservableList<ChatMessage> getMessages() { return messages; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }

    @Override
    public String toString() { return title; }
}
