package com.agentdesk.stt;

import java.util.function.Consumer;

/**
 * Pluggable speech-to-text backend (OS native, Vosk, etc.). Recognition callbacks may originate
 * from background threads; implementations should marshal UI updates to the JavaFX thread.
 */
public interface SpeechToTextEngine {

    /**
     * Stable id for logging and configuration (e.g. {@code os}, {@code vosk}).
     */
    String getEngineId();

    /**
     * Whether this engine can run in the current environment (OS support, native library, model, permissions).
     */
    boolean isAvailable();

    /**
     * User-facing explanation when {@link #isAvailable()} is false (mic button help dialog).
     */
    String getUnavailableSetupHint();

    boolean isListening();

    /**
     * Start streaming recognition. {@code onDisplayUpdate} receives the full text for the input field
     * (prefix plus recognized speech). {@code onEnded} runs on the JavaFX thread when the session ends.
     */
    void startListening(
        String prefix,
        Consumer<String> onDisplayUpdate,
        Consumer<String> onError,
        Runnable onEnded
    );

    void stopListening();

    /**
     * Release resources (e.g. Vosk model); invoked on application shutdown.
     */
    default void shutdown() {
        stopListening();
    }
}
