package com.agentdesk.api;

import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpHeaders;
import org.springframework.lang.Nullable;

import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * Generic HTTP facade backed by Spring {@link org.springframework.web.client.RestClient}.
 * <p><b>JavaFX:</b> synchronous methods block the calling thread. Never call them from the
 * JavaFX {@link javafx.application.Application} UI thread; use {@link #getAsync}, {@link #postAsync},
 * {@link #deleteAsync}, or {@link javafx.concurrent.Task} / {@link CompletableFuture} with a
 * background {@link java.util.concurrent.Executor} instead.
 */
public interface ApiClient {

    <T> T get(String path, Class<T> bodyType);

    <T> T get(String path, ParameterizedTypeReference<T> bodyType);

    <T> T get(String path, Class<T> bodyType, HttpHeaders extraHeaders);

    <T> T get(String path, ParameterizedTypeReference<T> bodyType, HttpHeaders extraHeaders);

    <T> T get(String path, Map<String, String> queryParams, Class<T> bodyType);

    <T> T post(String path, @Nullable Object body, Class<T> responseType);

    <T> T post(String path, @Nullable Object body, Class<T> responseType, HttpHeaders extraHeaders);

    <T> T post(String path, @Nullable Object body, ParameterizedTypeReference<T> responseType);

    void delete(String path);

    void delete(String path, HttpHeaders extraHeaders);

    <T> T delete(String path, Class<T> responseType);

    <T> CompletableFuture<T> getAsync(String path, Class<T> bodyType);

    <T> CompletableFuture<T> postAsync(String path, @Nullable Object body, Class<T> responseType);

    <T> CompletableFuture<T> putAsync(String path, @Nullable Object body, Class<T> responseType);

    CompletableFuture<Void> deleteAsync(String path);
}
