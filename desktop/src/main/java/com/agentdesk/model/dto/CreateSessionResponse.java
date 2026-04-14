package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.springframework.lang.Nullable;

/**
 * Response from {@code POST /api/v1/chat/sessions} (create a new session).
 */
public record CreateSessionResponse(
        @JsonProperty("success")    boolean success,
        @JsonProperty("session_id") @Nullable String sessionId,
        @JsonProperty("title")      @Nullable String title,
        @JsonProperty("message")    @Nullable String message
) {}
