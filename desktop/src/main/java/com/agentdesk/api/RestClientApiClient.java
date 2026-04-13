package com.agentdesk.api;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpHeaders;
import org.springframework.lang.Nullable;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.util.UriComponentsBuilder;

import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.function.Supplier;

/**
 * {@link ApiClient} backed by Spring {@link RestClient}.
 */
@Service
public class RestClientApiClient implements ApiClient {

    private final RestClient restClient;
    private final Executor apiClientExecutor;

    public RestClientApiClient(RestClient restClient,
                               @Qualifier("apiClientExecutor") Executor apiClientExecutor) {
        this.restClient = restClient;
        this.apiClientExecutor = apiClientExecutor;
    }

    @Override
    public <T> T get(String path, Class<T> bodyType) {
        return execute(() -> restClient.get().uri(normalizePath(path)).retrieve().body(bodyType));
    }

    @Override
    public <T> T get(String path, ParameterizedTypeReference<T> bodyType) {
        return execute(() -> restClient.get().uri(normalizePath(path)).retrieve().body(bodyType));
    }

    @Override
    public <T> T get(String path, Class<T> bodyType, HttpHeaders extraHeaders) {
        return execute(() -> restClient.get()
            .uri(normalizePath(path))
            .headers(h -> copyHeaders(h, extraHeaders))
            .retrieve()
            .body(bodyType));
    }

    @Override
    public <T> T get(String path, ParameterizedTypeReference<T> bodyType, HttpHeaders extraHeaders) {
        return execute(() -> restClient.get()
            .uri(normalizePath(path))
            .headers(h -> copyHeaders(h, extraHeaders))
            .retrieve()
            .body(bodyType));
    }

    @Override
    public <T> T get(String path, Map<String, String> queryParams, Class<T> bodyType) {
        String uri = buildPathWithQuery(path, queryParams);
        return execute(() -> restClient.get().uri(uri).retrieve().body(bodyType));
    }

    @Override
    public <T> T post(String path, @Nullable Object body, Class<T> responseType) {
        return execute(() -> restClient.post()
            .uri(normalizePath(path))
            .body(body != null ? body : "")
            .retrieve()
            .body(responseType));
    }

    @Override
    public <T> T post(String path, @Nullable Object body, Class<T> responseType, HttpHeaders extraHeaders) {
        return execute(() -> restClient.post()
            .uri(normalizePath(path))
            .headers(h -> copyHeaders(h, extraHeaders))
            .body(body != null ? body : "")
            .retrieve()
            .body(responseType));
    }

    @Override
    public <T> T post(String path, @Nullable Object body, ParameterizedTypeReference<T> responseType) {
        return execute(() -> restClient.post()
            .uri(normalizePath(path))
            .body(body != null ? body : "")
            .retrieve()
            .body(responseType));
    }

    @Override
    public void delete(String path) {
        executeVoid(() -> restClient.delete().uri(normalizePath(path)).retrieve().toBodilessEntity());
    }

    @Override
    public void delete(String path, HttpHeaders extraHeaders) {
        executeVoid(() -> restClient.delete()
            .uri(normalizePath(path))
            .headers(h -> copyHeaders(h, extraHeaders))
            .retrieve()
            .toBodilessEntity());
    }

    @Override
    public <T> T delete(String path, Class<T> responseType) {
        return execute(() -> restClient.delete().uri(normalizePath(path)).retrieve().body(responseType));
    }

    @Override
    public <T> CompletableFuture<T> getAsync(String path, Class<T> bodyType) {
        return CompletableFuture.supplyAsync(() -> get(path, bodyType), apiClientExecutor);
    }

    @Override
    public <T> CompletableFuture<T> postAsync(String path, @Nullable Object body, Class<T> responseType) {
        return CompletableFuture.supplyAsync(() -> post(path, body, responseType), apiClientExecutor);
    }

    @Override
    public CompletableFuture<Void> deleteAsync(String path) {
        return CompletableFuture.runAsync(() -> delete(path), apiClientExecutor);
    }

    private static String normalizePath(String path) {
        if (path == null || path.isEmpty()) {
            return "/";
        }
        return path.startsWith("/") ? path : "/" + path;
    }

    private static String buildPathWithQuery(String path, Map<String, String> queryParams) {
        UriComponentsBuilder b = UriComponentsBuilder.fromPath(normalizePath(path));
        if (queryParams != null && !queryParams.isEmpty()) {
            new TreeMap<>(queryParams).forEach(b::queryParam);
        }
        return b.build().encode().toUriString();
    }

    private static void copyHeaders(HttpHeaders target, @Nullable HttpHeaders extra) {
        if (extra != null && !extra.isEmpty()) {
            target.addAll(extra);
        }
    }

    private static <T> T execute(Supplier<T> supplier) {
        try {
            return supplier.get();
        } catch (RestClientResponseException e) {
            String body = e.getResponseBodyAsString(StandardCharsets.UTF_8);
            throw new ApiException(e.getStatusCode().value(), body, e);
        } catch (RestClientException e) {
            throw new ApiException(0, null, e);
        }
    }

    private static void executeVoid(Runnable runnable) {
        try {
            runnable.run();
        } catch (RestClientResponseException e) {
            String body = e.getResponseBodyAsString(StandardCharsets.UTF_8);
            throw new ApiException(e.getStatusCode().value(), body, e);
        } catch (RestClientException e) {
            throw new ApiException(0, null, e);
        }
    }
}
