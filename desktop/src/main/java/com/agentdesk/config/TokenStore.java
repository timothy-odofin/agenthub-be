package com.agentdesk.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.lang.NonNull;
import org.springframework.lang.Nullable;
import org.springframework.stereotype.Component;

import java.util.Objects;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Thread-safe, in-memory store for the current user's JWT tokens.
 *
 * <p>Tokens are held only for the lifetime of the application process.
 * No persistence to disk is performed — on restart the user must log in again.
 *
 * <p>This is the single source of truth for authentication state in the
 * desktop application. Every component that needs to know whether the user
 * is logged in, or what the current bearer token is, reads from here.
 *
 * <p>Thread safety: all reads and writes are mediated through
 * {@link AtomicReference} and are therefore safe for concurrent access from
 * both the JavaFX Application Thread and the background API executor pool.
 */
@Component
public class TokenStore {

    private static final Logger log = LoggerFactory.getLogger(TokenStore.class);

    private final AtomicReference<String> accessToken  = new AtomicReference<>();
    private final AtomicReference<String> refreshToken = new AtomicReference<>();
    private final AtomicReference<String> username     = new AtomicReference<>();

    /**
     * Store a new token pair after a successful login or token refresh.
     *
     * @param accessToken  JWT access token — must not be null or blank
     * @param refreshToken JWT refresh token — must not be null or blank
     */
    public void setTokens(@NonNull String accessToken, @NonNull String refreshToken) {
        Objects.requireNonNull(accessToken,  "accessToken must not be null");
        Objects.requireNonNull(refreshToken, "refreshToken must not be null");
        this.accessToken.set(accessToken);
        this.refreshToken.set(refreshToken);
        log.info("Token store updated — new access token stored");
    }

    /**
     * Stores the display name / username after a successful login.
     *
     * @param name the username or display name to show in the UI; may be {@code null}
     */
    public void setUsername(@Nullable String name) {
        this.username.set(name);
    }

    /**
     * Returns the stored username / display name, or {@code null} if not set.
     */
    @Nullable
    public String getUsername() {
        return username.get();
    }

    /**
     * Returns the current access token, or {@code null} if the user is not
     * authenticated.
     */
    @Nullable
    public String getAccessToken() {
        return accessToken.get();
    }

    /**
     * Returns the current refresh token, or {@code null} if the user is not
     * authenticated.
     */
    @Nullable
    public String getRefreshToken() {
        return refreshToken.get();
    }

    /**
     * Returns {@code true} if a non-null access token is currently held,
     * indicating that the user has completed the login flow in this session.
     */
    public boolean isAuthenticated() {
        return accessToken.get() != null;
    }

    /**
     * Clears both tokens and the username from memory.
     * Call this on explicit logout or when a token refresh fails.
     */
    public void clear() {
        accessToken.set(null);
        refreshToken.set(null);
        username.set(null);
        log.info("Token store cleared — user logged out");
    }
}
