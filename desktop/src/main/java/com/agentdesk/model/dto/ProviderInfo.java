package com.agentdesk.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.springframework.lang.Nullable;

import java.util.List;

/**
 * A single LLM provider entry as returned by {@code GET /api/v1/llm/providers}.
 *
 * <p>Field names match the backend schema exactly:
 * {@code name}, {@code display_name}, {@code model_versions}, {@code default_model},
 * {@code is_default}.
 */
public record ProviderInfo(
        @JsonProperty("name")           String name,
        @JsonProperty("display_name")   @Nullable String displayName,
        @JsonProperty("model_versions") @Nullable List<String> modelVersions,
        @JsonProperty("default_model")  @Nullable String defaultModel,
        @JsonProperty("is_default")     boolean isDefault
) {}
