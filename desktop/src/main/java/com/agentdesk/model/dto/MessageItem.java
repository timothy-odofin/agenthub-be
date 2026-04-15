package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.springframework.lang.Nullable;

/**
 * A single message within a session history, as returned by
 * {@code GET /api/v1/chat/sessions/{session_id}/messages}.
 */
public record MessageItem(
        @JsonProperty("id")        @Nullable String id,
        @JsonProperty("role")      String role,
        @JsonProperty("content")   String content,
        @JsonProperty("timestamp") @Nullable String timestamp
) {}
