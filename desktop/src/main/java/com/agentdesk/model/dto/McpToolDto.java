package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * A single tool within an MCP server, as returned by {@code GET /api/v1/tools/mcp}.
 */
public record McpToolDto(
        @JsonProperty("name")        String name,
        @JsonProperty("description") String description
) {}
