package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Request body for {@code POST /api/v1/auth/login}.
 *
 * <p>The backend accepts either an email address or a username as the
 * {@code identifier} value.
 */
public record LoginRequest(
        @JsonProperty("identifier") String identifier,
        @JsonProperty("password")   String password
) {}
