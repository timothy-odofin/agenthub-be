package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Request body for {@code POST /api/v1/auth/refresh}.
 */
public record RefreshRequest(
        @JsonProperty("refresh_token") String refreshToken
) {}
