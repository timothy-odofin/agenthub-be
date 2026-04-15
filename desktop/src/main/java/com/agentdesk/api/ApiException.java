package com.agentdesk.api;

import org.springframework.lang.Nullable;

/**
 * Thrown when an HTTP response indicates an error or when the request fails in a way that
 * maps to a remote status (see {@link #getStatusCode()}).
 */
public class ApiException extends RuntimeException {

    /** HTTP status, or 0 if not applicable (e.g. connection failure). */
    private final int statusCode;

    @Nullable
    private final String responseBody;

    public ApiException(int statusCode, @Nullable String responseBody, Throwable cause) {
        super(buildMessage(statusCode, responseBody), cause);
        this.statusCode = statusCode;
        this.responseBody = responseBody;
    }

    private static String buildMessage(int statusCode, @Nullable String responseBody) {
        if (responseBody == null || responseBody.isBlank()) {
            return statusCode > 0 ? "HTTP " + statusCode : "Request failed";
        }
        return "HTTP " + statusCode + ": " + responseBody;
    }

    public int getStatusCode() {
        return statusCode;
    }

    @Nullable
    public String getResponseBody() {
        return responseBody;
    }
}
