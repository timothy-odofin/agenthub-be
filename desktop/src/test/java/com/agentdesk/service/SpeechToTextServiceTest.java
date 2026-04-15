package com.agentdesk.service;

import com.agentdesk.config.SttProperties;
import com.agentdesk.stt.VoskSpeechToTextEngine;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class SpeechToTextServiceTest {

    @Mock
    private VoskSpeechToTextEngine vosk;

    @Test
    void availableWhenVoskIsReady() {
        SttProperties p = new SttProperties();
        when(vosk.isAvailable()).thenReturn(true);

        SpeechToTextService svc = new SpeechToTextService(p, vosk);
        assertTrue(svc.isAvailable());
    }

    @Test
    void unavailableWhenVoskNotReady() {
        SttProperties p = new SttProperties();
        when(vosk.isAvailable()).thenReturn(false);

        SpeechToTextService svc = new SpeechToTextService(p, vosk);
        assertFalse(svc.isAvailable());
    }

    @Test
    void unavailableWhenSttDisabled() {
        SttProperties p = new SttProperties();
        p.setEnabled(false);

        SpeechToTextService svc = new SpeechToTextService(p, vosk);
        assertFalse(svc.isAvailable());
        verify(vosk, never()).isAvailable();
    }

    @Test
    void startListeningDelegatesToVosk() {
        SttProperties p = new SttProperties();
        when(vosk.isAvailable()).thenReturn(true);

        SpeechToTextService svc = new SpeechToTextService(p, vosk);
        svc.startListening("", s -> {}, e -> {}, () -> {});
        verify(vosk).startListening(any(), any(), any(), any());
    }

    @Test
    void startListeningDoesNotDelegateWhenUnavailable() {
        SttProperties p = new SttProperties();
        when(vosk.isAvailable()).thenReturn(false);
        when(vosk.getUnavailableSetupHint()).thenReturn("Model not found.");

        SpeechToTextService svc = new SpeechToTextService(p, vosk);
        // Pass a no-op onEnded to avoid Platform.runLater; we only assert vosk is never called
        try {
            svc.startListening("", s -> {}, e -> {}, () -> {});
        } catch (IllegalStateException ignored) {
            // JavaFX toolkit not initialised in unit tests; expected when hitting Platform.runLater
        }
        verify(vosk, never()).startListening(any(), any(), any(), any());
    }
}
