package com.agentdesk.service;

import com.agentdesk.api.ApiClient;
import com.agentdesk.api.ApiExceptionMapper;
import com.agentdesk.model.dto.ProviderInfo;
import com.agentdesk.model.dto.ProvidersResponse;
import javafx.application.Platform;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.function.Consumer;

/**
 * Fetches the list of available LLM providers and their supported model identifiers
 * from the AgentHub backend ({@code GET /api/v1/llm/providers}).
 *
 * <h3>Startup sequence</h3>
 * <ol>
 *   <li>After login, call {@link #refresh(Consumer, Consumer)} to populate the registry.</li>
 *   <li>If the request fails the built-in static fallback list is used so the model
 *       selector is never empty.</li>
 * </ol>
 *
 * <h3>Threading contract</h3>
 * Reads of {@link #getProviders()} and {@link #getModelNamesFlat()} are safe from any thread.
 * The {@code onLoaded} / {@code onError} callbacks are dispatched on the JavaFX thread.
 */
@Service
public final class ProviderService {

    private static final Logger log = LoggerFactory.getLogger(ProviderService.class);

    private static final String PROVIDERS_PATH = "/api/v1/llm/providers";

    /** Shown when the backend is unreachable on first load. */
    private static final List<String> FALLBACK_MODELS = List.of(
            "claude-sonnet-4-5",
            "claude-opus-4-5",
            "claude-haiku-4-5",
            "gpt-4o",
            "gpt-4o-mini",
            "gemini-2.0-flash"
    );

    private final ApiClient          apiClient;
    private final ApiExceptionMapper exceptionMapper;

    private volatile List<ProviderInfo> providers = List.of();

    public ProviderService(ApiClient apiClient, ApiExceptionMapper exceptionMapper) {
        this.apiClient       = apiClient;
        this.exceptionMapper = exceptionMapper;
    }

    // -------------------------------------------------------------------------
    // Public API
    // -------------------------------------------------------------------------

    /**
     * Returns the currently loaded provider list.
     *
     * @return an unmodifiable snapshot; empty if {@link #refresh} has not been called yet
     */
    public List<ProviderInfo> getProviders() {
        return providers;
    }

    /**
     * Returns a flat list of all model identifiers across all providers.
     * Falls back to {@link #FALLBACK_MODELS} if no providers have been loaded.
     * Each provider's {@code model_versions} list is used; if empty the {@code default_model}
     * is included as a single entry.
     *
     * @return a non-null, non-empty list of model name strings
     */
    public List<String> getModelNamesFlat() {
        final List<ProviderInfo> current = providers;
        if (current.isEmpty()) {
            return FALLBACK_MODELS;
        }
        final List<String> models = current.stream()
                .flatMap(p -> {
                    if (p.modelVersions() != null && !p.modelVersions().isEmpty()) {
                        return p.modelVersions().stream();
                    } else if (p.defaultModel() != null) {
                        return java.util.stream.Stream.of(p.defaultModel());
                    }
                    return java.util.stream.Stream.empty();
                })
                .distinct()
                .toList();
        return models.isEmpty() ? FALLBACK_MODELS : models;
    }

    /**
     * Asynchronously refreshes the provider list from the backend.
     *
     * @param onLoaded called on the JavaFX thread with the new model name list on success
     * @param onError  called on the JavaFX thread with a user-facing message on failure;
     *                 may be {@code null}
     */
    public void refresh(Consumer<List<String>> onLoaded, Consumer<String> onError) {
        log.debug("Fetching LLM providers");
        apiClient.getAsync(PROVIDERS_PATH, ProvidersResponse.class)
                .whenComplete((response, throwable) -> {
                    if (throwable != null) {
                        final String msg = exceptionMapper.toUserMessage(throwable);
                        log.warn("Failed to load LLM providers — using fallback: {}", msg);
                        Platform.runLater(() -> {
                            if (onLoaded != null) {
                                onLoaded.accept(FALLBACK_MODELS);
                            }
                            if (onError != null) {
                                onError.accept(msg);
                            }
                        });
                        return;
                    }
                    if (!response.success() || response.providers() == null) {
                        log.warn("Backend returned success=false for providers — using fallback");
                        Platform.runLater(() -> {
                            if (onLoaded != null) {
                                onLoaded.accept(FALLBACK_MODELS);
                            }
                        });
                        return;
                    }
                    providers = response.providers();
                    final List<String> models = getModelNamesFlat();
                    log.info("Loaded {} providers, {} models total",
                            providers.size(), models.size());
                    Platform.runLater(() -> {
                        if (onLoaded != null) {
                            onLoaded.accept(models);
                        }
                    });
                });
    }
}
