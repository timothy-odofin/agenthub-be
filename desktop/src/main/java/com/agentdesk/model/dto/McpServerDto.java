package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * A single MCP server within a category group, as returned by {@code GET /api/v1/tools/mcp}.
 */
public record McpServerDto(
        @JsonProperty("id")          String id,
        @JsonProperty("name")        String name,
        @JsonProperty("description") String description,
        @JsonProperty("tool_count")  int toolCount,
        @JsonProperty("tools")       List<McpToolDto> tools
) {}
