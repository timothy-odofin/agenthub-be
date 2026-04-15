package com.agentdesk.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Speech-to-text settings using the Vosk offline engine. Download a Vosk model from
 * <a href="https://alphacephei.com/vosk/models">models</a> or let the app auto-download it on
 * first run (see {@link #isAutoDownloadModel()}).
 */
@ConfigurationProperties(prefix = "app.stt")
public class SttProperties {

    public enum SttProvider {
        VOSK
    }

    private boolean enabled = true;

    /**
     * Engine selection: only {@code vosk} is supported.
     */
    private String provider = "vosk";

    /**
     * Path to the Vosk model directory (contains am/, conf/, etc.).
     * Defaults to a {@code models/vosk-model-small-en-us-0.15} folder next to the running JAR
     * (or the current working directory during development).
     */
    private String modelPath = System.getProperty("user.dir") + "/models/vosk-model-small-en-us-0.15";

    /**
     * Sample rate in Hz (must match the model; small models typically use 16000).
     */
    private float sampleRate = 16000f;

    /**
     * Optional directory containing a compatible {@code libvosk.dylib} / {@code libvosk.so} / {@code libvosk.dll}.
     * Use on macOS if the JAR-bundled native library fails to load (see README).
     */
    private String nativeLibraryPath;

    /**
     * When true and the Vosk model folder is missing, download the default English small model at startup
     * (skipped when {@link #getProvider()} is {@code os}, or when {@code auto} and macOS native STT is available).
     */
    private boolean autoDownloadModel = true;

    /**
     * HTTPS URL for the Vosk zip (default: small English US model).
     */
    private String autoDownloadModelUrl = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip";

    public boolean isEnabled() {
        return enabled;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }

    public SttProvider getProvider() {
        return SttProvider.VOSK;
    }

    public String getProviderRaw() {
        return provider;
    }

    public void setProvider(String provider) {
        this.provider = provider;
    }

    public String getModelPath() {
        return modelPath;
    }

    public void setModelPath(String modelPath) {
        this.modelPath = modelPath;
    }

    public float getSampleRate() {
        return sampleRate;
    }

    public void setSampleRate(float sampleRate) {
        this.sampleRate = sampleRate;
    }

    public String getNativeLibraryPath() {
        return nativeLibraryPath;
    }

    public void setNativeLibraryPath(String nativeLibraryPath) {
        this.nativeLibraryPath = nativeLibraryPath;
    }

    public boolean isAutoDownloadModel() {
        return autoDownloadModel;
    }

    public void setAutoDownloadModel(boolean autoDownloadModel) {
        this.autoDownloadModel = autoDownloadModel;
    }

    public String getAutoDownloadModelUrl() {
        return autoDownloadModelUrl;
    }

    public void setAutoDownloadModelUrl(String autoDownloadModelUrl) {
        this.autoDownloadModelUrl = autoDownloadModelUrl;
    }
}
