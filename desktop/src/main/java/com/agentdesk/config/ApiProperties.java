package com.agentdesk.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.time.Duration;

/**
 * HTTP client settings for Spring {@code RestClient} (see {@link HttpClientConfig}).
 */
@ConfigurationProperties(prefix = "app.api")
public class ApiProperties {

    /**
     * Base URL for all relative paths (e.g. https://api.example.com).
     */
    private String baseUrl = "http://localhost:8080";

    private Duration connectTimeout = Duration.ofSeconds(10);

    private Duration readTimeout = Duration.ofSeconds(30);

    /**
     * Optional {@code Authorization} header value (e.g. {@code Bearer &lt;token&gt;}).
     */
    private String defaultAuthorization;

    public String getBaseUrl() {
        return baseUrl;
    }

    public void setBaseUrl(String baseUrl) {
        this.baseUrl = baseUrl;
    }

    public Duration getConnectTimeout() {
        return connectTimeout;
    }

    public void setConnectTimeout(Duration connectTimeout) {
        this.connectTimeout = connectTimeout;
    }

    public Duration getReadTimeout() {
        return readTimeout;
    }

    public void setReadTimeout(Duration readTimeout) {
        this.readTimeout = readTimeout;
    }

    public String getDefaultAuthorization() {
        return defaultAuthorization;
    }

    public void setDefaultAuthorization(String defaultAuthorization) {
        this.defaultAuthorization = defaultAuthorization;
    }
}
