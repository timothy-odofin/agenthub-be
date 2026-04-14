package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * A category group of MCP servers, as returned by {@code GET /api/v1/tools/mcp}.
 */
public record McpGroupDto(
        @JsonProperty("category") String category,
        @JsonProperty("label")    String label,
        @JsonProperty("servers")  List<McpServerDto> servers
) {}
