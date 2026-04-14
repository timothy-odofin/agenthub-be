package com.agentdesk.config;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class TokenStoreTest {

    private TokenStore store;

    @BeforeEach
    void setUp() {
        store = new TokenStore();
    }

    @Test
    void isAuthenticated_returnsFalse_whenEmpty() {
        assertFalse(store.isAuthenticated());
    }

    @Test
    void isAuthenticated_returnsTrue_afterSetTokens() {
        store.setTokens("access", "refresh");
        assertTrue(store.isAuthenticated());
    }

    @Test
    void getAccessToken_returnsNull_beforeSet() {
        assertNull(store.getAccessToken());
    }

    @Test
    void getAccessToken_returnsValue_afterSet() {
        store.setTokens("my-access", "my-refresh");
        assertEquals("my-access", store.getAccessToken());
    }

    @Test
    void getRefreshToken_returnsValue_afterSet() {
        store.setTokens("a", "my-refresh");
        assertEquals("my-refresh", store.getRefreshToken());
    }

    @Test
    void clear_resetsAllTokens() {
        store.setTokens("a", "r");
        store.clear();

        assertFalse(store.isAuthenticated());
        assertNull(store.getAccessToken());
        assertNull(store.getRefreshToken());
    }

    @Test
    void setTokens_overwritesPreviousValue() {
        store.setTokens("old-access", "old-refresh");
        store.setTokens("new-access", "new-refresh");

        assertEquals("new-access",   store.getAccessToken());
        assertEquals("new-refresh",  store.getRefreshToken());
    }
}
