package com.agentdesk.stt;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.channels.FileChannel;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/**
 * Downloads and extracts the default English Vosk small model when missing from {@code app.stt.model-path}.
 */
public final class VoskModelDownloader {

    private static final Logger log = LoggerFactory.getLogger(VoskModelDownloader.class);

    private VoskModelDownloader() {
    }

    /**
     * True when the directory exists and contains Vosk {@code am} layout.
     */
    public static boolean isModelComplete(Path modelDir) {
        try {
            return Files.isDirectory(modelDir) && Files.exists(modelDir.resolve("am"));
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * Downloads {@code zipUrl} into a temp file under {@code parentDir}, extracts into {@code parentDir}, then removes the zip.
     */
    public static void downloadAndExtract(Path modelDir, URI zipUrl) throws IOException, InterruptedException {
        Path parent = modelDir.getParent();
        if (parent == null) {
            throw new IOException("model-path has no parent directory: " + modelDir);
        }
        Files.createDirectories(parent);

        Path lock = parent.resolve(".agentdesk-vosk-download.lock");
        try (FileChannel channel = FileChannel.open(lock, StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
            var flock = channel.tryLock();
            if (flock == null) {
                log.info("Another process holds the Vosk model download lock; skipping.");
                return;
            }
            try {
                if (isModelComplete(modelDir)) {
                    return;
                }
                Path zipPart = parent.resolve("vosk-model-download.zip.part");
                Path zipDone = parent.resolve("vosk-model-download.zip");

                HttpClient client = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(30))
                    .followRedirects(HttpClient.Redirect.NORMAL)
                    .build();
                HttpRequest request = HttpRequest.newBuilder()
                    .uri(zipUrl)
                    .timeout(Duration.ofMinutes(15))
                    .GET()
                    .build();

                log.info("Downloading Vosk English model from {} …", zipUrl);
                HttpResponse<InputStream> response = client.send(request, HttpResponse.BodyHandlers.ofInputStream());
                if (response.statusCode() / 100 != 2) {
                    throw new IOException("HTTP " + response.statusCode() + " for " + zipUrl);
                }

                long total = response.headers().firstValueAsLong("Content-Length").orElse(-1L);
                long written = 0L;
                long lastLog = 0L;
                try (InputStream in = response.body();
                     OutputStream out = Files.newOutputStream(zipPart)) {
                    byte[] buf = new byte[65536];
                    int n;
                    while ((n = in.read(buf)) >= 0) {
                        out.write(buf, 0, n);
                        written += n;
                        if (written - lastLog >= 5L * 1024 * 1024) {
                            lastLog = written;
                            if (total > 0) {
                                log.info("Vosk model download: {} / {} MB", written / (1024 * 1024), total / (1024 * 1024));
                            } else {
                                log.info("Vosk model download: {} MB …", written / (1024 * 1024));
                            }
                        }
                    }
                }
                try {
                    Files.move(zipPart, zipDone, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
                } catch (AtomicMoveNotSupportedException e) {
                    Files.move(zipPart, zipDone, StandardCopyOption.REPLACE_EXISTING);
                }

                log.info("Extracting Vosk model to {} …", parent);
                unzip(zipDone, parent);
                Files.deleteIfExists(zipDone);

                if (!isModelComplete(modelDir)) {
                    throw new IOException(
                        "After extract, model still incomplete at " + modelDir + " (expected am/).");
                }
                log.info("Vosk English model ready at {}", modelDir);
            } finally {
                flock.release();
            }
        }
    }

    private static void unzip(Path zipFile, Path targetDir) throws IOException {
        Files.createDirectories(targetDir);
        Path canonicalTarget = targetDir.toRealPath();
        try (InputStream fis = Files.newInputStream(zipFile);
             ZipInputStream zis = new ZipInputStream(fis)) {
            ZipEntry entry;
            byte[] buf = new byte[65536];
            while ((entry = zis.getNextEntry()) != null) {
                if (entry.isDirectory()) {
                    continue;
                }
                Path out = canonicalTarget.resolve(entry.getName()).normalize();
                if (!out.startsWith(canonicalTarget)) {
                    throw new IOException("Unsafe zip entry: " + entry.getName());
                }
                Files.createDirectories(out.getParent());
                try (OutputStream os = Files.newOutputStream(out)) {
                    int r;
                    while ((r = zis.read(buf)) >= 0) {
                        os.write(buf, 0, r);
                    }
                }
                zis.closeEntry();
            }
        }
    }
}
