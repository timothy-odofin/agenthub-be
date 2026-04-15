package com.agentdesk.stt;

import com.agentdesk.config.SttProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.nio.file.Path;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executors;

/**
 * If the Vosk model is missing at {@link SttProperties#getModelPath()}, downloads the default
 * English small model in the background on first run.
 */
@Component
public class VoskModelBootstrap {

    private static final Logger log = LoggerFactory.getLogger(VoskModelBootstrap.class);

    private final SttProperties sttProperties;

    public VoskModelBootstrap(SttProperties sttProperties) {
        this.sttProperties = sttProperties;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void onApplicationReady() {
        if (!sttProperties.isEnabled()) {
            return;
        }
        if (!sttProperties.isAutoDownloadModel()) {
            return;
        }
        CompletableFuture.runAsync(this::downloadIfNeeded, Executors.newVirtualThreadPerTaskExecutor());
    }

    private void downloadIfNeeded() {
        try {
            Path modelDir = Path.of(sttProperties.getModelPath());
            if (VoskModelDownloader.isModelComplete(modelDir)) {
                log.info("Vosk model already present at {}", modelDir);
                return;
            }
            URI uri = URI.create(sttProperties.getAutoDownloadModelUrl().trim());
            if (!"https".equalsIgnoreCase(uri.getScheme())) {
                log.warn("Refusing Vosk auto-download: URL must use HTTPS (got {}).", uri.getScheme());
                return;
            }
            VoskModelDownloader.downloadAndExtract(modelDir, uri);
        } catch (Exception e) {
            log.warn("Vosk model auto-download failed (speech-to-text will be unavailable until a model is installed): {}",
                e.toString());
        }
    }
}
