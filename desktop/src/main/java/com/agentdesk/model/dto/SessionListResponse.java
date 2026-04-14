package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * Response envelope for {@code GET /api/v1/chat/sessions}.
 */
public record SessionListResponse(
        @JsonProperty("success")  boolean success,
        @JsonProperty("sessions") List<SessionItem> sessions
) {}
