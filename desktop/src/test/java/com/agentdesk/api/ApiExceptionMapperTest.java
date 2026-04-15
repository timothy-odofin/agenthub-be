package com.agentdesk.api;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.net.ConnectException;
import java.net.SocketTimeoutException;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ApiExceptionMapperTest {

    private ApiExceptionMapper mapper;

    @BeforeEach
    void setUp() {
        mapper = new ApiExceptionMapper();
    }

    // ---- isUnauthorized -------------------------------------------------

    @Test
    void isUnauthorized_returnsTrueFor401() {
        final ApiException ex = new ApiException(401, "Unauthorized", new RuntimeException());
        assertTrue(mapper.isUnauthorized(ex));
    }

    @Test
    void isUnauthorized_returnsFalseFor403() {
        final ApiException ex = new ApiException(403, "Forbidden", new RuntimeException());
        assertFalse(mapper.isUnauthorized(ex));
    }

    @Test
    void isUnauthorized_returnsFalseForNonApiException() {
        assertFalse(mapper.isUnauthorized(new RuntimeException("oops")));
    }

    // ---- toUserMessage — ApiException -----------------------------------

    @Test
    void toUserMessage_401_returnsCredentialsMessage() {
        final String msg = mapper.toUserMessage(new ApiException(401, null, new RuntimeException()));
        assertTrue(msg.toLowerCase().contains("credentials") || msg.toLowerCase().contains("sign in"),
                "Expected a credentials-related message, got: " + msg);
    }

    @Test
    void toUserMessage_403_returnsForbiddenMessage() {
        final String msg = mapper.toUserMessage(new ApiException(403, null, new RuntimeException()));
        assertTrue(msg.toLowerCase().contains("permission"),
                "Expected a permission message, got: " + msg);
    }

    @Test
    void toUserMessage_404_returnsNotFoundMessage() {
        final String msg = mapper.toUserMessage(new ApiException(404, null, new RuntimeException()));
        assertTrue(msg.toLowerCase().contains("not found"),
                "Expected a not-found message, got: " + msg);
    }

    @Test
    void toUserMessage_500_returnsServerErrorMessage() {
        final String msg = mapper.toUserMessage(new ApiException(500, "Internal", new RuntimeException()));
        assertTrue(msg.toLowerCase().contains("server"),
                "Expected a server-error message, got: " + msg);
    }

    @Test
    void toUserMessage_429_returnsTooManyRequestsMessage() {
        final String msg = mapper.toUserMessage(new ApiException(429, null, new RuntimeException()));
        assertTrue(msg.toLowerCase().contains("many") || msg.toLowerCase().contains("wait"),
                "Expected a rate-limit message, got: " + msg);
    }

    // ---- toUserMessage — connectivity -----------------------------------

    @Test
    void toUserMessage_connectException_returnsNetworkMessage() {
        final String msg = mapper.toUserMessage(new ConnectException("Connection refused"));
        assertTrue(msg.toLowerCase().contains("server") || msg.toLowerCase().contains("network"),
                "Expected a network message, got: " + msg);
    }

    @Test
    void toUserMessage_socketTimeoutException_returnsTimeoutMessage() {
        final String msg = mapper.toUserMessage(new SocketTimeoutException("timed out"));
        assertTrue(msg.toLowerCase().contains("timeout") || msg.toLowerCase().contains("timed out"),
                "Expected a timeout message, got: " + msg);
    }

    // ---- toUserMessage — wrapped exceptions ----------------------------

    @Test
    void toUserMessage_wrappedApiException_unwrapsToApiMessage() {
        final ApiException cause = new ApiException(422, "Unprocessable", new RuntimeException());
        final RuntimeException wrapper = new RuntimeException("wrapper", cause);
        final String msg = mapper.toUserMessage(wrapper);
        assertTrue(msg.toLowerCase().contains("server") || msg.toLowerCase().contains("request"),
                "Expected mapped message for 422, got: " + msg);
    }
}
