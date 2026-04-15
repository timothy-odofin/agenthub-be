package com.agentdesk.stt;

import com.agentdesk.config.SttProperties;
import javafx.application.Platform;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.lang.Nullable;
import org.springframework.stereotype.Component;
import org.vosk.Model;
import org.vosk.Recognizer;

import javax.sound.sampled.AudioFormat;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.DataLine;
import javax.sound.sampled.LineUnavailableException;
import javax.sound.sampled.TargetDataLine;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;

/**
 * Offline STT using Vosk and the system microphone.
 * <p>
 * Do not reference {@link org.vosk.LibVosk} in a static initializer: it loads the native library
 * immediately and can crash startup on macOS when the bundled {@code libvosk.dylib} does not match
 * the Java bindings.
 */
@Component
public class VoskSpeechToTextEngine implements SpeechToTextEngine {

    private static final Logger log = LoggerFactory.getLogger(VoskSpeechToTextEngine.class);

    private final SttProperties sttProperties;

    private final AtomicBoolean listening = new AtomicBoolean(false);
    private volatile TargetDataLine audioLine;
    private volatile Thread captureThread;

    private Model voskModel;
    private final Object modelLock = new Object();

    private volatile boolean voskNativeFailed = false;

    private static final AtomicBoolean jnaConfigured = new AtomicBoolean(false);

    public VoskSpeechToTextEngine(SttProperties sttProperties) {
        this.sttProperties = sttProperties;
    }

    @Override
    public String getEngineId() {
        return "vosk";
    }

    @Override
    public boolean isAvailable() {
        return sttProperties.isEnabled() && isModelPresent() && !voskNativeFailed;
    }

    @Override
    public String getUnavailableSetupHint() {
        if (!sttProperties.isEnabled()) {
            return "Speech-to-text is disabled (app.stt.enabled).";
        }
        if (!isModelPresent()) {
            return "Download a Vosk model, extract it, and set app.stt.model-path in application.yml "
                + "(see README). Example: ~/.agentdesk/vosk-model-small-en-us-0.15";
        }
        if (voskNativeFailed) {
            return "Speech-to-text: Vosk native library failed to load. On macOS the bundled library "
                + "may be incompatible—set app.stt.native-library-path to a folder containing a "
                + "matching libvosk.dylib, or restart after fixing. See README.";
        }
        return "Speech-to-text (Vosk) unavailable.";
    }

    /**
     * True when a Vosk model directory exists at the configured path.
     */
    public boolean isModelPresent() {
        Path p = Path.of(sttProperties.getModelPath());
        return Files.isDirectory(p) && Files.exists(p.resolve("am"));
    }

    @Override
    public boolean isListening() {
        return listening.get();
    }

    @Override
    public void startListening(
        String prefix,
        Consumer<String> onDisplayUpdate,
        Consumer<String> onError,
        Runnable onEnded
    ) {
        if (!isAvailable()) {
            onError.accept(getUnavailableSetupHint());
            Platform.runLater(onEnded);
            return;
        }
        if (!listening.compareAndSet(false, true)) {
            return;
        }

        Runnable task = () -> {
            try {
                runCapture(prefix, onDisplayUpdate, onError, onEnded);
            } finally {
                listening.set(false);
                captureThread = null;
            }
        };
        Thread t = new Thread(task, "vosk-stt");
        t.setDaemon(true);
        captureThread = t;
        t.start();
    }

    @Override
    public void stopListening() {
        listening.set(false);
        closeAudioLine();
    }

    private void closeAudioLine() {
        TargetDataLine line = audioLine;
        audioLine = null;
        if (line != null) {
            try {
                line.stop();
                line.close();
            } catch (Exception e) {
                log.debug("Error closing audio line: {}", e.getMessage(), e);
            }
        }
    }

    private void configureJnaOnce() {
        if (!jnaConfigured.compareAndSet(false, true)) {
            return;
        }

        // If the user has explicitly provided a native library directory, honour it first.
        String userPath = sttProperties.getNativeLibraryPath();
        if (userPath != null && !userPath.isBlank()) {
            System.setProperty("jna.library.path", userPath.trim());
            log.info("Vosk native library path set from config: {}", userPath.trim());
            return;
        }

        // When running from a Spring Boot fat-JAR the Vosk JAR is nested inside BOOT-INF/lib/
        // and JNA cannot extract libvosk.dylib from a doubly-nested JAR. Extract it ourselves
        // to a temp directory so JNA can find it regardless of packaging.
        String nativeResource = getNativeLibraryResourcePath();
        if (nativeResource == null) {
            log.warn("Vosk: unsupported OS/arch combination - cannot locate bundled libvosk native library.");
            return;
        }

        try {
            InputStream in = VoskSpeechToTextEngine.class.getResourceAsStream(nativeResource);
            if (in == null) {
                log.error("Vosk native library resource not found in classpath: {}", nativeResource);
                return;
            }
            String fileName = nativeResource.substring(nativeResource.lastIndexOf('/') + 1);
            Path tmpDir = Files.createTempDirectory("vosk-native-");
            tmpDir.toFile().deleteOnExit();
            Path libFile = tmpDir.resolve(fileName);
            try (in) {
                Files.copy(in, libFile, StandardCopyOption.REPLACE_EXISTING);
            }
            libFile.toFile().deleteOnExit();
            System.setProperty("jna.library.path", tmpDir.toAbsolutePath().toString());
            log.info("Vosk native library extracted to: {}", libFile);
        } catch (IOException e) {
            log.error("Failed to extract Vosk native library: {}", e.getMessage(), e);
        }
    }

    /**
     * Returns the classpath resource path for the Vosk native library matching the current OS/arch,
     * or {@code null} when unsupported.
     */
    @Nullable
    private static String getNativeLibraryResourcePath() {
        String os = System.getProperty("os.name", "").toLowerCase();
        String arch = System.getProperty("os.arch", "").toLowerCase();
        if (os.contains("mac") || os.contains("darwin")) {
            return "/darwin/libvosk.dylib";
        } else if (os.contains("linux")) {
            return "/linux-x86-64/libvosk.so";
        } else if (os.contains("win")) {
            return "/win32-x86-64/libvosk.dll";
        }
        return null;
    }

    private void runCapture(
        String prefix,
        Consumer<String> onDisplayUpdate,
        Consumer<String> onError,
        Runnable onEnded
    ) {
        Recognizer recognizer = null;
        try {
            Model model = getOrLoadModel();
            if (model == null) {
                Platform.runLater(() -> onError.accept(
                    voskNativeFailed
                        ? getUnavailableSetupHint()
                        : "Could not load Vosk model."));
                return;
            }

            recognizer = new Recognizer(model, sttProperties.getSampleRate());
            TargetDataLine line = openMicrophoneLine();
            if (line == null) {
                Platform.runLater(() -> onError.accept("Microphone not available."));
                return;
            }
            this.audioLine = line;
            line.start();

            StringBuilder committed = new StringBuilder(prefix == null ? "" : prefix);
            if (!committed.isEmpty() && !Character.isWhitespace(committed.charAt(committed.length() - 1))) {
                committed.append(' ');
            }

            byte[] buffer = new byte[4096];
            while (listening.get()) {
                int n = line.read(buffer, 0, buffer.length);
                if (n < 0) {
                    break;
                }
                if (recognizer.acceptWaveForm(buffer, n)) {
                    String chunk = VoskResultParser.text(recognizer.getResult());
                    if (!chunk.isEmpty()) {
                        committed.append(chunk).append(' ');
                    }
                    String out = committed.toString().trim();
                    String snapshot = out;
                    Platform.runLater(() -> onDisplayUpdate.accept(snapshot));
                } else {
                    String partial = VoskResultParser.partial(recognizer.getPartialResult());
                    String base = committed.toString().trim();
                    String display = partial.isEmpty() ? base : (base.isEmpty() ? partial : base + " " + partial);
                    String snap = display;
                    Platform.runLater(() -> onDisplayUpdate.accept(snap));
                }
            }

            String finalJson = recognizer.getFinalResult();
            String tail = VoskResultParser.text(finalJson);
            if (!tail.isEmpty()) {
                String cur = committed.toString().trim();
                if (cur.isEmpty()) {
                    committed.append(tail);
                } else if (!cur.endsWith(tail)) {
                    committed.append(' ').append(tail);
                }
            }
            String done = committed.toString().trim();
            Platform.runLater(() -> onDisplayUpdate.accept(done));

        } catch (Throwable e) {
            if (isNativeFailure(e)) {
                voskNativeFailed = true;
                log.error("Vosk native failure during capture: {}", e.getMessage(), e);
            } else {
                log.error("Vosk STT capture error: {}", e.getMessage(), e);
            }
            String msg = e.getMessage() != null ? e.getMessage() : e.toString();
            Platform.runLater(() -> onError.accept(msg));
        } finally {
            closeAudioLine();
            if (recognizer != null) {
                recognizer.close();
            }
            Platform.runLater(onEnded);
        }
    }

    private static boolean isNativeFailure(Throwable e) {
        if (e instanceof UnsatisfiedLinkError) {
            return true;
        }
        if (e instanceof ExceptionInInitializerError initializerError) {
            return initializerError.getCause() instanceof UnsatisfiedLinkError;
        }
        Throwable c = e.getCause();
        return c != null && isNativeFailure(c);
    }

    @Nullable
    private Model getOrLoadModel() {
        synchronized (modelLock) {
            if (voskModel != null) {
                return voskModel;
            }
            try {
                configureJnaOnce();
                log.info("Loading Vosk model from: {}", sttProperties.getModelPath());
                voskModel = new Model(sttProperties.getModelPath());
                log.info("Vosk model loaded successfully.");
                return voskModel;
            } catch (Throwable e) {
                if (isNativeFailure(e)) {
                    voskNativeFailed = true;
                    log.error("Vosk native library failed to load. Full error: {}", e.getMessage(), e);
                } else {
                    log.error("Failed to load Vosk model from '{}': {}", sttProperties.getModelPath(), e.getMessage(), e);
                }
                return null;
            }
        }
    }

    @Nullable
    private TargetDataLine openMicrophoneLine() throws LineUnavailableException {
        float rate = sttProperties.getSampleRate();
        AudioFormat format = new AudioFormat(
            AudioFormat.Encoding.PCM_SIGNED,
            rate,
            16,
            1,
            2,
            rate,
            false
        );
        DataLine.Info info = new DataLine.Info(TargetDataLine.class, format);
        if (!AudioSystem.isLineSupported(info)) {
            return null;
        }
        TargetDataLine line = (TargetDataLine) AudioSystem.getLine(info);
        line.open(format);
        return line;
    }

    @PreDestroy
    @Override
    public void shutdown() {
        stopListening();
        synchronized (modelLock) {
            if (voskModel != null) {
                voskModel.close();
                voskModel = null;
            }
        }
    }
}
