package com.agentdesk.stt;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Parses JSON lines returned by Vosk {@link org.vosk.Recognizer}.
 */
public final class VoskResultParser {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private VoskResultParser() {
    }

    public static String text(String json) {
        if (json == null || json.isBlank()) {
            return "";
        }
        try {
            JsonNode n = MAPPER.readTree(json);
            return n.path("text").asText("");
        } catch (Exception e) {
            return "";
        }
    }

    public static String partial(String json) {
        if (json == null || json.isBlank()) {
            return "";
        }
        try {
            JsonNode n = MAPPER.readTree(json);
            return n.path("partial").asText("");
        } catch (Exception e) {
            return "";
        }
    }
}
