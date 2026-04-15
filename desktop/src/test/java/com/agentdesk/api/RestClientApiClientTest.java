package com.agentdesk.api;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import java.util.Map;
import java.util.concurrent.Executor;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withBadRequest;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;
import static org.springframework.http.HttpMethod.DELETE;
import static org.springframework.http.HttpMethod.GET;
import static org.springframework.http.HttpMethod.POST;

class RestClientApiClientTest {

    private MockRestServiceServer server;
    private RestClientApiClient client;

    @BeforeEach
    void setUp() {
        RestClient.Builder builder = RestClient.builder().baseUrl("https://api.example.com");
        server = MockRestServiceServer.bindTo(builder).build();
        RestClient restClient = builder.build();
        Executor sync = Runnable::run;
        client = new RestClientApiClient(restClient, sync);
    }

    @AfterEach
    void tearDown() {
        server.verify();
    }

    @Test
    void get_returnsBody() {
        server.expect(requestTo("https://api.example.com/v1/status"))
            .andExpect(method(GET))
            .andRespond(withSuccess("{\"ok\":true}", MediaType.APPLICATION_JSON));

        String body = client.get("/v1/status", String.class);
        assertEquals("{\"ok\":true}", body);
    }

    @Test
    void get_withQueryParams() {
        server.expect(requestTo("https://api.example.com/items?limit=10&q=a"))
            .andExpect(method(GET))
            .andRespond(withSuccess("[]", MediaType.APPLICATION_JSON));

        String body = client.get("/items", Map.of("q", "a", "limit", "10"), String.class);
        assertEquals("[]", body);
    }

    @Test
    void post_sendsJsonBody() {
        server.expect(requestTo("https://api.example.com/v1/messages"))
            .andExpect(method(POST))
            .andExpect(content().json("{\"text\":\"hi\"}"))
            .andRespond(withSuccess("{\"id\":1}", MediaType.APPLICATION_JSON));

        Map<String, String> req = Map.of("text", "hi");
        String out = client.post("/v1/messages", req, String.class);
        assertEquals("{\"id\":1}", out);
    }

    @Test
    void delete_succeeds() {
        server.expect(requestTo("https://api.example.com/v1/messages/5"))
            .andExpect(method(DELETE))
            .andRespond(withSuccess());

        client.delete("/v1/messages/5");
    }

    @Test
    void get_throwsApiExceptionOnError() {
        server.expect(requestTo("https://api.example.com/missing"))
            .andRespond(withBadRequest().body("no"));

        ApiException ex = assertThrows(ApiException.class, () -> client.get("/missing", String.class));
        assertEquals(400, ex.getStatusCode());
        assertEquals("no", ex.getResponseBody());
    }
}
