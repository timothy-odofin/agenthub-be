package com.agentdesk.stt;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class VoskModelDownloaderTest {

    @Test
    void modelCompleteWhenAmPresent(@TempDir Path dir) throws Exception {
        Path model = dir.resolve("vosk-model-small-en-us-0.15");
        Files.createDirectories(model.resolve("am"));
        assertTrue(VoskModelDownloader.isModelComplete(model));
    }

    @Test
    void modelIncompleteWhenMissing(@TempDir Path dir) {
        Path model = dir.resolve("empty");
        assertFalse(VoskModelDownloader.isModelComplete(model));
    }
}
