package com.agentdesk.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.kordamp.ikonli.feather.Feather;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class CategoryIconResolverTest {

    private CategoryIconResolver resolver;

    @BeforeEach
    void setUp() {
        resolver = new CategoryIconResolver();
    }

    @Test
    void forCategory_null_returnsFallback() {
        assertEquals(Feather.PACKAGE, resolver.forCategory(null));
    }

    @Test
    void forCategory_unknown_returnsFallback() {
        assertEquals(Feather.PACKAGE, resolver.forCategory("unknown-xyz"));
    }

    @ParameterizedTest
    @CsvSource({
            "knowledge,  BOOK_OPEN",
            "code,       CODE",
            "integration, ZAP",
            "analysis,   BAR_CHART_2",
            "KNOWLEDGE,  BOOK_OPEN",  // case-insensitive
            "CODE,       CODE"
    })
    void forCategory_knownKeys_returnExpectedIcon(String key, String expectedName) {
        final Feather actual = resolver.forCategory(key.trim());
        assertNotNull(actual);
        assertEquals(expectedName.trim(), actual.name(),
                "Wrong icon for category key '" + key + "'");
    }

    @Test
    void forServer_knownServerId_returnServerSpecificIcon() {
        assertEquals(Feather.TERMINAL, resolver.forServer("terminal", "code"));
    }

    @Test
    void forServer_unknownServerId_fallsBackToCategory() {
        assertEquals(Feather.CODE, resolver.forServer("nonexistent-server", "code"));
    }

    @Test
    void forServer_nullServerId_fallsBackToCategory() {
        assertEquals(Feather.DATABASE, resolver.forServer(null, "data"));
    }
}
