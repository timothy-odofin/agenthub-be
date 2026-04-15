package com.agentdesk.service;

import com.agentdesk.api.ApiClient;
import com.agentdesk.api.ApiException;
import com.agentdesk.api.ApiExceptionMapper;
import com.agentdesk.config.TokenStore;
import com.agentdesk.model.dto.LoginRequest;
import com.agentdesk.model.dto.LoginResponse;
import com.agentdesk.model.dto.RefreshResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.contains;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock private ApiClient          apiClient;
    @Mock private ApiExceptionMapper exceptionMapper;

    private TokenStore  tokenStore;
    private AuthService authService;

    @BeforeEach
    void setUp() {
        tokenStore  = new TokenStore();
        authService = new AuthService(apiClient, tokenStore, exceptionMapper);
    }

    // ---- login ----------------------------------------------------------

    @Test
    void login_success_storesTokens() throws Exception {
        final LoginResponse response =
                new LoginResponse(true, "access-token", "refresh-token", "Bearer", null, null);
        when(apiClient.postAsync(contains("login"), any(LoginRequest.class), eq(LoginResponse.class)))
                .thenReturn(CompletableFuture.completedFuture(response));

        final LoginResponse result = authService.login("user@test.com", "secret").get();

        assertTrue(result.success());
        assertEquals("access-token",  tokenStore.getAccessToken());
        assertEquals("refresh-token", tokenStore.getRefreshToken());
    }

    @Test
    void login_successFalse_doesNotStoreTokens() throws Exception {
        final LoginResponse response =
                new LoginResponse(false, null, null, null, "Bad credentials", null);
        when(apiClient.postAsync(contains("login"), any(), eq(LoginResponse.class)))
                .thenReturn(CompletableFuture.completedFuture(response));

        authService.login("u", "p").get();

        assertFalse(tokenStore.isAuthenticated());
    }

    @Test
    void login_apiFailure_futureCompletesExceptionally() {
        final ApiException cause = new ApiException(401, "Unauthorized", new RuntimeException());
        when(apiClient.postAsync(contains("login"), any(), eq(LoginResponse.class)))
                .thenReturn(CompletableFuture.failedFuture(cause));
        when(exceptionMapper.toUserMessage(cause)).thenReturn("Invalid credentials.");

        final CompletableFuture<LoginResponse> future = authService.login("u", "bad");

        assertThrows(ExecutionException.class, future::get);
        assertFalse(tokenStore.isAuthenticated());
    }

    // ---- refresh --------------------------------------------------------

    @Test
    void refresh_noRefreshToken_failsWithoutCallingApi() {
        // TokenStore is empty — no refresh token.
        final CompletableFuture<RefreshResponse> future = authService.refresh();

        assertThrows(ExecutionException.class, future::get);
        verify(apiClient, never()).postAsync(any(), any(), any());
    }

    @Test
    void refresh_success_updatesTokens() throws Exception {
        tokenStore.setTokens("old-access", "old-refresh");
        final RefreshResponse response =
                new RefreshResponse(true, "new-access", "new-refresh", "Bearer", null);
        when(apiClient.postAsync(contains("refresh"), any(), eq(RefreshResponse.class)))
                .thenReturn(CompletableFuture.completedFuture(response));

        authService.refresh().get();

        assertEquals("new-access",  tokenStore.getAccessToken());
        assertEquals("new-refresh", tokenStore.getRefreshToken());
    }

    @Test
    void refresh_unauthorized_clearsTokenStore() {
        tokenStore.setTokens("access", "refresh");
        final ApiException cause = new ApiException(401, "Unauthorized", new RuntimeException());
        when(apiClient.postAsync(contains("refresh"), any(), eq(RefreshResponse.class)))
                .thenReturn(CompletableFuture.failedFuture(cause));
        when(exceptionMapper.isUnauthorized(any())).thenReturn(true);

        assertThrows(ExecutionException.class, () -> authService.refresh().get());
        assertFalse(tokenStore.isAuthenticated());
    }

    // ---- logout ---------------------------------------------------------

    @Test
    void logout_clearsTokensEvenOnServerError() throws Exception {
        tokenStore.setTokens("access", "refresh");
        when(apiClient.deleteAsync(contains("logout")))
                .thenReturn(CompletableFuture.failedFuture(new RuntimeException("network down")));
        when(exceptionMapper.toUserMessage(any())).thenReturn("Network error.");

        authService.logout().get(); // should not throw

        assertFalse(tokenStore.isAuthenticated());
    }

    @Test
    void logout_success_clearsTokens() throws Exception {
        tokenStore.setTokens("access", "refresh");
        when(apiClient.deleteAsync(contains("logout")))
                .thenReturn(CompletableFuture.completedFuture(null));

        authService.logout().get();

        assertFalse(tokenStore.isAuthenticated());
    }
}
