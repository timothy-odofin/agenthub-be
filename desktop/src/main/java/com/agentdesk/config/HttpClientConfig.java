package com.agentdesk.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

import java.util.Objects;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.atomic.AtomicInteger;

@Configuration
@EnableConfigurationProperties({ApiProperties.class, SttProperties.class})
public class HttpClientConfig {

    private final TokenStore tokenStore;

    public HttpClientConfig(TokenStore tokenStore) {
        this.tokenStore = Objects.requireNonNull(tokenStore, "tokenStore");
    }

    @Bean
    public RestClient restClient(ApiProperties apiProperties) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout((int) apiProperties.getConnectTimeout().toMillis());
        factory.setReadTimeout((int) apiProperties.getReadTimeout().toMillis());

        return RestClient.builder()
            .baseUrl(apiProperties.getBaseUrl())
            .requestFactory(factory)
            // Dynamic per-request interceptor: reads the current token from TokenStore
            // at call time rather than at bean construction time. This ensures that
            // every request made after login automatically carries the correct bearer token,
            // and that the token is updated transparently after a refresh.
            .requestInterceptor((request, body, execution) -> {
                String token = tokenStore.getAccessToken();
                if (token != null && !token.isBlank()) {
                    request.getHeaders().setBearerAuth(token);
                }
                return execution.execute(request, body);
            })
            .build();
    }

    /**
     * Background executor for {@link com.agentdesk.api.ApiClient} async methods.
     *
     * <p>Uses a cached thread pool (unbounded) so that long-running LLM chat calls
     * never block concurrent session-list, history, or rename requests.
     * All threads are daemon threads so they do not prevent JVM shutdown.
     */
    @Bean(name = "apiClientExecutor")
    public Executor apiClientExecutor() {
        AtomicInteger counter = new AtomicInteger(1);
        ThreadFactory factory = r -> {
            Thread t = new Thread(r, "api-client-" + counter.getAndIncrement());
            t.setDaemon(true);
            return t;
        };
        return Executors.newCachedThreadPool(factory);
    }
}

