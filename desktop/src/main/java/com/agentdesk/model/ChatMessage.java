package com.agentdesk.model;

import java.time.LocalDateTime;
import java.util.UUID;

public class ChatMessage {

    public enum Role { USER, ASSISTANT }

    private final String id;
    private final Role role;
    private String content;
    private final LocalDateTime timestamp;

    public ChatMessage(Role role, String content) {
        this.id = UUID.randomUUID().toString();
        this.role = role;
        this.content = content;
        this.timestamp = LocalDateTime.now();
    }

    public String getId() { return id; }
    public Role getRole() { return role; }
    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }
    public LocalDateTime getTimestamp() { return timestamp; }
    public boolean isUser() { return role == Role.USER; }
}
