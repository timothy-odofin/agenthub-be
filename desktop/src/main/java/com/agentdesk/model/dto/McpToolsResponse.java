package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * Response envelope for {@code GET /api/v1/tools/mcp}.
 */
public record McpToolsResponse(
        @JsonProperty("success") boolean success,
        @JsonProperty("groups")  List<McpGroupDto> groups
) {}
