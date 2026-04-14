package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.springframework.lang.Nullable;

import java.util.List;

/**
 * Request body for {@code POST /api/v1/chat/message}.
 *
 * <p>The {@code sessionId} field is optional on the first message of a brand-new session;
 * the backend will assign one and return it in {@link SendMessageResponse#sessionId()}.
 * On subsequent messages in the same session it must be present.
 */
public record SendMessageRequest(
        @JsonProperty("message")    String message,
        @JsonProperty("session_id") @Nullable String sessionId,
        @JsonProperty("provider")   @Nullable String provider,
        @JsonProperty("model")      @Nullable String model,
        @JsonProperty("mcp_servers") @Nullable List<String> mcpServers
) {}
