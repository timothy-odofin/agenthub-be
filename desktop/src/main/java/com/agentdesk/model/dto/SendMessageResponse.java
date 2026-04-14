package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.springframework.lang.Nullable;

/**
 * Response from {@code POST /api/v1/chat/message}.
 */
public record SendMessageResponse(
        @JsonProperty("success")    boolean success,
        @JsonProperty("response")   @Nullable String response,
        @JsonProperty("session_id") @Nullable String sessionId,
        @JsonProperty("message")    @Nullable String message
) {}
