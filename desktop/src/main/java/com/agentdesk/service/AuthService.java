package com.agentdesk.service;

import com.agentdesk.api.ApiClient;
import com.agentdesk.api.ApiExceptionMapper;
import com.agentdesk.config.TokenStore;
import com.agentdesk.model.dto.LoginRequest;
import com.agentdesk.model.dto.LoginResponse;
import com.agentdesk.model.dto.RefreshRequest;
import com.agentdesk.model.dto.RefreshResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.concurrent.CompletableFuture;

/**
 * Handles user authentication against the AgentHub backend.
 *
 * <h3>Endpoints consumed</h3>
 * <ul>
 *   <li>{@code POST /api/v1/auth/login}   — password-based login</li>
 *   <li>{@code POST /api/v1/auth/refresh} — silent token refresh</li>
 *   <li>{@code POST /api/v1/auth/logout}  — server-side session revocation</li>
 * </ul>
 *
 * <h3>Threading contract</h3>
 * All public methods return a {@link CompletableFuture} and must be awaited off the
 * JavaFX Application Thread.  The caller is responsible for dispatching UI updates via
 * {@code Platform.runLater()}.
 *
 * <h3>Token lifecycle</h3>
 * On a successful login or refresh the returned tokens are stored atomically in
 * {@link TokenStore}.  On logout or on any 401 response the store is cleared so that
 * subsequent requests do not send a stale credential.
 */
@Service
public final class AuthService {

    private static final Logger log = LoggerFactory.getLogger(AuthService.class);

    private static final String LOGIN_PATH   = "/api/v1/auth/login";
    private static final String REFRESH_PATH = "/api/v1/auth/refresh";
    private static final String LOGOUT_PATH  = "/api/v1/auth/logout";

    private final ApiClient          apiClient;
    private final TokenStore         tokenStore;
    private final ApiExceptionMapper exceptionMapper;

    public AuthService(
            ApiClient          apiClient,
            TokenStore         tokenStore,
            ApiExceptionMapper exceptionMapper) {
        this.apiClient       = apiClient;
        this.tokenStore      = tokenStore;
        this.exceptionMapper = exceptionMapper;
    }

    // -------------------------------------------------------------------------
    // Public API
    // -------------------------------------------------------------------------

    /**
     * Authenticates the user with email/username and password.
     *
     * <p>On success the access and refresh tokens are persisted in {@link TokenStore};
     * the caller should navigate to the main view.  On failure the store is left
     * unchanged and the returned future completes exceptionally — inspect the cause
     * with {@link ApiExceptionMapper#toUserMessage(Throwable)} to obtain a message
     * suitable for display in the UI.
     *
     * @param identifier the user's email address or username
     * @param password   the plain-text password (transmitted only over HTTPS in production)
     * @return a future that resolves to the server response; never {@code null}
     */
    public CompletableFuture<LoginResponse> login(String identifier, String password) {
        final LoginRequest body = new LoginRequest(identifier, password);
        log.debug("Attempting login for identifier='{}'", identifier);

        return apiClient.postAsync(LOGIN_PATH, body, LoginResponse.class)
                .thenApply(response -> {
                    if (response.success()
                            && response.accessToken()  != null
                            && response.refreshToken() != null) {
                        tokenStore.setTokens(response.accessToken(), response.refreshToken());
                        tokenStore.setUsername(response.displayName());
                        log.info("Login successful for identifier='{}'", identifier);
                    } else {
                        log.warn("Login responded success=false for identifier='{}'", identifier);
                    }
                    return response;
                })
                .exceptionally(throwable -> {
                    log.error("Login failed for identifier='{}': {}", identifier,
                            exceptionMapper.toUserMessage(throwable));
                    throw asUnchecked(throwable);
                });
    }

    /**
     * Silently refreshes the access token using the stored refresh token.
     *
     * <p>If the token store holds no refresh token this method completes immediately
     * with a failed future so the caller can redirect to login.
     *
     * @return a future resolving to the server response; never {@code null}
     */
    public CompletableFuture<RefreshResponse> refresh() {
        final String refreshToken = tokenStore.getRefreshToken();
        if (refreshToken == null) {
            log.warn("Attempted token refresh but no refresh token is present in TokenStore");
            return CompletableFuture.failedFuture(
                    new IllegalStateException("No refresh token available — please sign in again."));
        }

        final RefreshRequest body = new RefreshRequest(refreshToken);
        log.debug("Refreshing access token");

        return apiClient.postAsync(REFRESH_PATH, body, RefreshResponse.class)
                .thenApply(response -> {
                    if (response.success()
                            && response.accessToken()  != null
                            && response.refreshToken() != null) {
                        tokenStore.setTokens(response.accessToken(), response.refreshToken());
                        log.info("Token refresh successful");
                    } else {
                        log.warn("Token refresh responded success=false; clearing token store");
                        tokenStore.clear();
                    }
                    return response;
                })
                .exceptionally(throwable -> {
                    // CompletableFuture wraps causes in CompletionException; unwrap first.
                    final Throwable cause = throwable.getCause() != null ? throwable.getCause() : throwable;
                    if (exceptionMapper.isUnauthorized(cause)) {
                        log.warn("Refresh token rejected by server — clearing token store");
                        tokenStore.clear();
                    } else {
                        log.error("Token refresh failed: {}", exceptionMapper.toUserMessage(cause));
                    }
                    throw asUnchecked(throwable);
                });
    }

    /**
     * Signs the current user out.
     *
     * <p>The local {@link TokenStore} is cleared regardless of whether the server-side
     * call succeeds, so the application always ends up in an unauthenticated state.
     *
     * @return a future that resolves when the logout request completes; never {@code null}
     */
    public CompletableFuture<Void> logout() {
        log.debug("Signing out");
        return apiClient.deleteAsync(LOGOUT_PATH)
                .handle((ignored, throwable) -> {
                    tokenStore.clear();
                    if (throwable != null) {
                        log.warn("Server-side logout call failed (tokens cleared locally): {}",
                                exceptionMapper.toUserMessage(throwable));
                    } else {
                        log.info("Logout successful");
                    }
                    return (Void) null;
                });
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    /**
     * Re-throws the throwable unchecked.  {@link CompletableFuture} wraps checked exceptions
     * in {@link java.util.concurrent.ExecutionException}; this helper avoids that wrapping
     * inside {@code exceptionally()} handlers.
     */
    @SuppressWarnings("unchecked")
    private static <T extends Throwable> RuntimeException asUnchecked(Throwable t) throws T {
        throw (T) t;
    }
}
