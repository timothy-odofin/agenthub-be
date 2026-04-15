package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.springframework.lang.Nullable;

/**
 * Response from {@code POST /api/v1/auth/refresh}.
 *
 * <p>Mirrors {@link LoginResponse} because the backend returns the same
 * payload shape for both endpoints.
 */
public record RefreshResponse(
        @JsonProperty("success")       boolean success,
        @JsonProperty("access_token")  @Nullable String accessToken,
        @JsonProperty("refresh_token") @Nullable String refreshToken,
        @JsonProperty("token_type")    @Nullable String tokenType,
        @JsonProperty("message")       @Nullable String message
) {}
