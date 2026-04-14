package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.springframework.lang.Nullable;

/**
 * Response from {@code DELETE /api/v1/chat/sessions/{session_id}}.
 */
public record DeleteSessionResponse(
        @JsonProperty("success") boolean success,
        @JsonProperty("message") @Nullable String message
) {}
