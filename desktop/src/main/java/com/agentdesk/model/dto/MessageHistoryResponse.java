package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * Response envelope for {@code GET /api/v1/chat/sessions/{session_id}/history}.
 */
public record MessageHistoryResponse(
        @JsonProperty("success")    boolean success,
        @JsonProperty("session_id") String sessionId,
        @JsonProperty("messages")   List<MessageItem> messages
) {}
