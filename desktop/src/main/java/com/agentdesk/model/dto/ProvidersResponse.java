package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * Response envelope for {@code GET /api/v1/llm/providers}.
 */
public record ProvidersResponse(
        @JsonProperty("success")   boolean success,
        @JsonProperty("providers") List<ProviderInfo> providers
) {}
