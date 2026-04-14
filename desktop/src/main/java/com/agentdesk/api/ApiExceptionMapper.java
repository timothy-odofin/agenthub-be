package com.agentdesk.api;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.net.ConnectException;
import java.net.SocketTimeoutException;
import java.util.concurrent.TimeoutException;

/**
 * Translates raw {@link Throwable} instances caught from {@link ApiClient} calls into
 * human-readable, user-facing error messages.
 *
 * <p>All public methods in this class are pure and stateless; the class is registered as a
 * Spring component solely for convenient injection.
 *
 * <h3>Mapping rules</h3>
 * <ul>
 *   <li>Connection refused / host unreachable → "Cannot reach the server. Check your network."</li>
 *   <li>Timeout ({@link SocketTimeoutException} / {@link TimeoutException}) → "The request timed out."</li>
 *   <li>{@link ApiException} with status 401 → "Invalid credentials."</li>
 *   <li>{@link ApiException} with status 403 → "Access denied."</li>
 *   <li>{@link ApiException} with status 404 → "Resource not found."</li>
 *   <li>{@link ApiException} with status 429 → "Too many requests. Please wait and try again."</li>
 *   <li>{@link ApiException} with status 5xx → "The server encountered an error. Try again later."</li>
 *   <li>Any other {@link ApiException} → generic message including the status code.</li>
 *   <li>Everything else → "An unexpected error occurred."</li>
 * </ul>
 */
@Component
public final class ApiExceptionMapper {

    private static final Logger log = LoggerFactory.getLogger(ApiExceptionMapper.class);

    /**
     * Returns a short, user-facing message for the given throwable.
     *
     * <p>The root cause is unwrapped one level when the top-level exception is a plain
     * {@link RuntimeException} wrapping a more specific type.
     *
     * @param throwable the exception to map; must not be {@code null}
     * @return a non-null, non-empty human-readable message
     */
    public String toUserMessage(Throwable throwable) {
        final Throwable effective = unwrap(throwable);

        if (isConnectFailure(effective)) {
            log.debug("API call failed — connection refused", effective);
            return "Cannot reach the server. Check your network connection.";
        }

        if (isTimeout(effective)) {
            log.debug("API call failed — timeout", effective);
            return "The request timed out. Please try again.";
        }

        if (effective instanceof ApiException ex) {
            return mapApiException(ex);
        }

        log.warn("Unexpected exception during API call", effective);
        return "An unexpected error occurred. Please try again.";
    }

    /**
     * Returns {@code true} if the status code of the given {@link ApiException} indicates
     * an authentication / authorisation error that should redirect the user to login.
     *
     * @param throwable the exception to test
     * @return {@code true} for 401 responses
     */
    public boolean isUnauthorized(Throwable throwable) {
        final Throwable effective = unwrap(throwable);
        return effective instanceof ApiException ex && ex.getStatusCode() == 401;
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    private static String mapApiException(ApiException ex) {
        return switch (ex.getStatusCode()) {
            case 400 -> "The request was invalid. Please check your input.";
            case 401 -> "Invalid credentials. Please sign in again.";
            case 403 -> "You do not have permission to perform this action.";
            case 404 -> "The requested resource was not found.";
            case 409 -> "A conflict occurred. The resource may already exist.";
            case 422 -> "The server could not process the request. Check your input.";
            case 429 -> "Too many requests. Please wait a moment and try again.";
            default  -> {
                if (ex.getStatusCode() >= 500) {
                    yield "The server encountered an error. Please try again later.";
                }
                yield "Request failed (HTTP " + ex.getStatusCode() + ").";
            }
        };
    }

    /**
     * Unwraps one layer of plain {@link RuntimeException} to surface the true cause.
     * Stops at {@link ApiException} since that is already specific.
     */
    private static Throwable unwrap(Throwable t) {
        if (t instanceof RuntimeException && !(t instanceof ApiException) && t.getCause() != null) {
            return t.getCause();
        }
        return t;
    }

    private static boolean isConnectFailure(Throwable t) {
        if (t instanceof ConnectException) {
            return true;
        }
        final String msg = t.getMessage();
        return msg != null && (msg.contains("Connection refused")
                || msg.contains("No route to host")
                || msg.contains("Connection reset"));
    }

    private static boolean isTimeout(Throwable t) {
        return t instanceof SocketTimeoutException || t instanceof TimeoutException;
    }
}
