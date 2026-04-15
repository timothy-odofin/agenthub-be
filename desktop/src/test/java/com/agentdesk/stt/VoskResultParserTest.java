package com.agentdesk.stt;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class VoskResultParserTest {

    @Test
    void parsesText() {
        assertEquals("hello world", VoskResultParser.text("{\"text\": \"hello world\"}"));
    }

    @Test
    void parsesPartial() {
        assertEquals("hel", VoskResultParser.partial("{\"partial\": \"hel\"}"));
    }

    @Test
    void emptyOnInvalidJson() {
        assertEquals("", VoskResultParser.text("not json"));
    }
}
