package com.agentdesk.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

import java.util.concurrent.Executor;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.atomic.AtomicInteger;

@Configuration
@EnableConfigurationProperties({ApiProperties.class, SttProperties.class})
public class HttpClientConfig {

    @Bean
    public RestClient restClient(ApiProperties apiProperties) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout((int) apiProperties.getConnectTimeout().toMillis());
        factory.setReadTimeout((int) apiProperties.getReadTimeout().toMillis());

        RestClient.Builder builder = RestClient.builder()
            .baseUrl(apiProperties.getBaseUrl())
            .requestFactory(factory);

        String auth = apiProperties.getDefaultAuthorization();
        if (auth != null && !auth.isBlank()) {
            builder.defaultRequest(headers -> headers.header(HttpHeaders.AUTHORIZATION, auth));
        }

        return builder.build();
    }

    /**
     * Background executor for {@link ApiClient} async methods; safe to use with JavaFX when chaining
     * {@link java.util.concurrent.CompletableFuture} and applying results with
     * {@link javafx.application.Platform#runLater}.
     */
    @Bean(name = "apiClientExecutor")
    public Executor apiClientExecutor() {
        ThreadFactory factory = new ThreadFactory() {
            private final AtomicInteger n = new AtomicInteger(1);

            @Override
            public Thread newThread(Runnable r) {
                Thread t = new Thread(r, "api-client-" + n.getAndIncrement());
                t.setDaemon(true);
                return t;
            }
        };
        return Executors.newFixedThreadPool(4, factory);
    }
}
