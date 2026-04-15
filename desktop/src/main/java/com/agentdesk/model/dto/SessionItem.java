package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.springframework.lang.Nullable;

/**
 * A single chat session as returned by {@code GET /api/v1/chat/sessions}.
 */
public record SessionItem(
        @JsonProperty("session_id") String sessionId,
        @JsonProperty("title")      @Nullable String title,
        @JsonProperty("created_at") @Nullable String createdAt,
        @JsonProperty("updated_at") @Nullable String updatedAt
) {}
