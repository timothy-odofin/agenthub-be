package com.agentdesk.service;

import com.agentdesk.config.SttProperties;
import com.agentdesk.stt.VoskSpeechToTextEngine;
import javafx.application.Platform;
import org.springframework.stereotype.Service;

import java.util.function.Consumer;

/**
 * Facade over the Vosk speech-to-text engine.
 */
@Service
public class SpeechToTextService {

    private final SttProperties sttProperties;
    private final VoskSpeechToTextEngine voskEngine;

    public SpeechToTextService(SttProperties sttProperties, VoskSpeechToTextEngine voskEngine) {
        this.sttProperties = sttProperties;
        this.voskEngine = voskEngine;
    }

    public boolean isEnabled() {
        return sttProperties.isEnabled();
    }

    /**
     * True when a Vosk model directory exists at the configured path.
     */
    public boolean isModelPresent() {
        return voskEngine.isModelPresent();
    }

    public boolean isAvailable() {
        if (!sttProperties.isEnabled()) {
            return false;
        }
        return voskEngine.isAvailable();
    }

    /**
     * User-facing setup message when {@link #isAvailable()} is false (mic button dialog).
     */
    public String getUnavailableSetupHint() {
        if (!sttProperties.isEnabled()) {
            return "Speech-to-text is disabled (app.stt.enabled).";
        }
        if (voskEngine.isAvailable()) {
            return null;
        }
        return voskEngine.getUnavailableSetupHint();
    }

    public boolean isListening() {
        return voskEngine.isListening();
    }

    public void startListening(
        String prefix,
        Consumer<String> onDisplayUpdate,
        Consumer<String> onError,
        Runnable onEnded
    ) {
        if (!voskEngine.isAvailable()) {
            onError.accept(voskEngine.getUnavailableSetupHint());
            Platform.runLater(onEnded);
            return;
        }
        voskEngine.startListening(prefix, onDisplayUpdate, onError, onEnded);
    }

    public void stopListening() {
        voskEngine.stopListening();
    }

    /**
     * Releases the Vosk model (optional explicit call; bean also shuts down on context stop).
     */
    public void closeModel() {
        voskEngine.shutdown();
    }
}

