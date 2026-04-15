package com.agentdesk.service;

import com.agentdesk.api.ApiClient;
import com.agentdesk.api.ApiExceptionMapper;
import com.agentdesk.model.McpServer;
import com.agentdesk.model.dto.McpGroupDto;
import com.agentdesk.model.dto.McpServerDto;
import com.agentdesk.model.dto.McpToolDto;
import com.agentdesk.model.dto.McpToolsResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.contains;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class McpServerRegistryTest {

    @Mock private ApiClient          apiClient;
    @Mock private ApiExceptionMapper exceptionMapper;

    private CategoryIconResolver iconResolver;
    private McpServerRegistry    registry;

    @BeforeEach
    void setUp() {
        iconResolver = new CategoryIconResolver();
        registry     = new McpServerRegistry(apiClient, exceptionMapper, iconResolver);
    }

    @Test
    void getAllServers_returnsNonEmptyFallbackOnInit() {
        assertFalse(registry.getAllServers().isEmpty(),
                "Fallback catalogue must be non-empty on construction");
    }

    @Test
    void getGroupedServers_keysMatchCategoryLabels() {
        final Map<String, List<McpServer>> grouped = registry.getGroupedServers();
        assertFalse(grouped.isEmpty());
        grouped.forEach((label, servers) -> {
            assertFalse(label.isBlank(), "Category label must not be blank");
            assertFalse(servers.isEmpty(), "Each group must have at least one server");
        });
    }

    @Test
    void refresh_success_replacesServerList() {
        final McpToolsResponse response = new McpToolsResponse(true, List.of(
                new McpGroupDto("code", "Code & Dev", List.of(
                        new McpServerDto("my-repl", "My REPL", "Run code", 2, List.of(
                                new McpToolDto("run", "Run code"),
                                new McpToolDto("stop", "Stop execution")
                        ))
                ))
        ));
        when(apiClient.getAsync(contains("mcp"), eq(McpToolsResponse.class)))
                .thenReturn(CompletableFuture.completedFuture(response));

        registry.refresh(null);

        verify(apiClient).getAsync(contains("mcp"), eq(McpToolsResponse.class));
        // After an async call the volatile field should be updated. We can only assert
        // this synchronously because CompletableFuture.completedFuture runs inline
        // when the whenComplete callback is registered.
        final List<McpServer> servers = registry.getAllServers();
        assertEquals(1, servers.size());
        assertEquals("my-repl", servers.get(0).getId());
        assertEquals(2, servers.get(0).getToolCount());
    }

    @Test
    void refresh_failure_keepsExistingList() {
        final int initialCount = registry.getAllServers().size();
        when(apiClient.getAsync(contains("mcp"), eq(McpToolsResponse.class)))
                .thenReturn(CompletableFuture.failedFuture(new RuntimeException("network")));
        when(exceptionMapper.toUserMessage(any())).thenReturn("Network error.");

        registry.refresh(null);

        assertEquals(initialCount, registry.getAllServers().size());
    }
}
