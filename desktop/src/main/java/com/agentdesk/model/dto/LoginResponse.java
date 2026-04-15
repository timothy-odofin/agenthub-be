package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.springframework.lang.Nullable;

import java.util.Map;

/**
 * Response from {@code POST /api/v1/auth/login}.
 *
 * <p>On success {@code success} is {@code true}, both token fields are populated,
 * and {@code user} contains user profile info (id, username, email, etc.).
 * On failure {@code success} is {@code false} and {@code message} carries the error.
 */
public record LoginResponse(
        @JsonProperty("success")       boolean success,
        @JsonProperty("access_token")  @Nullable String accessToken,
        @JsonProperty("refresh_token") @Nullable String refreshToken,
        @JsonProperty("token_type")    @Nullable String tokenType,
        @JsonProperty("message")       @Nullable String message,
        @JsonProperty("user")          @Nullable Map<String, Object> user
) {
    /** Convenience: extracts the username from the nested {@code user} map. */
    @Nullable
    public String username() {
        if (user == null) return null;
        final Object u = user.get("username");
        return u instanceof String s ? s : null;
    }

    /**
     * Convenience: returns the friendliest available display name.
     * Priority: firstname → firstname + lastname → username.
     */
    @Nullable
    public String displayName() {
        if (user == null) return null;
        final Object first = user.get("firstname");
        final Object last  = user.get("lastname");
        if (first instanceof String fn && !fn.isBlank()) {
            if (last instanceof String ln && !ln.isBlank()) {
                return fn + " " + ln;
            }
            return fn;
        }
        // Fall back to the "name" field (some backends use this), then username.
        final Object n = user.get("name");
        if (n instanceof String s && !s.isBlank()) return s;
        return username();
    }
}
