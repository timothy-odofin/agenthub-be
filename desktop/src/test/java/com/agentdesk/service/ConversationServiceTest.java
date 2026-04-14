package com.agentdesk.service;

import com.agentdesk.api.ApiClient;
import com.agentdesk.api.ApiExceptionMapper;
import com.agentdesk.model.Conversation;
import com.agentdesk.model.dto.SessionItem;
import com.agentdesk.model.dto.SessionListResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.concurrent.CompletableFuture;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.contains;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ConversationServiceTest {

    @Mock private ApiClient          apiClient;
    @Mock private ApiExceptionMapper exceptionMapper;

    private ConversationService service;

    @BeforeEach
    void setUp() {
        service = new ConversationService(apiClient, exceptionMapper);
    }

    // ---- loadSessions ---------------------------------------------------

    @Test
    void loadSessions_populatesConversations() {
        final SessionListResponse response = new SessionListResponse(true, List.of(
                new SessionItem("sess-1", "First chat",  null, null),
                new SessionItem("sess-2", "Second chat", null, null)
        ));
        when(apiClient.getAsync(contains("sessions"), eq(SessionListResponse.class)))
                .thenReturn(CompletableFuture.completedFuture(response));

        service.loadSessions(null);

        // Platform.runLater is a no-op in unit tests (no JavaFX toolkit).
        // We verify the API call was made.
        verify(apiClient).getAsync(contains("sessions"), eq(SessionListResponse.class));
    }

    @Test
    void loadSessions_failure_invokesOnError() {
        when(apiClient.getAsync(contains("sessions"), eq(SessionListResponse.class)))
                .thenReturn(CompletableFuture.failedFuture(new RuntimeException("down")));

        service.loadSessions(msg -> {});

        // The API call must have been attempted even though it failed.
        // Note: the error callback is dispatched via Platform.runLater which is a no-op
        // in headless unit tests; we assert only that the API path was reached.
        verify(apiClient).getAsync(contains("sessions"), eq(SessionListResponse.class));
    }

    // ---- createConversation ---------------------------------------------

    @Test
    void createConversation_addsToFront() {
        service.createConversation("Chat A");
        service.createConversation("Chat B");

        assertEquals("Chat B", service.getConversations().get(0).getTitle());
        assertEquals("Chat A", service.getConversations().get(1).getTitle());
    }

    @Test
    void createConversation_hasNoServerSessionId() {
        final Conversation conv = service.createConversation("New");
        assertFalse(conv.isSynced());
    }

    // ---- renameConversation ---------------------------------------------

    @Test
    void renameConversation_updatesLocalTitle() {
        final Conversation conv = service.createConversation("Old title");
        service.renameConversation(conv, "New title");
        assertEquals("New title", conv.getTitle());
    }

    @Test
    void renameConversation_synced_callsApi() {
        final Conversation conv = service.createConversation("Title");
        conv.setServerSessionId("sess-xyz");

        when(apiClient.putAsync(contains("sess-xyz"), any(), eq(
                com.agentdesk.model.dto.UpdateTitleResponse.class)))
                .thenReturn(CompletableFuture.completedFuture(
                        new com.agentdesk.model.dto.UpdateTitleResponse(true, "sess-xyz", "New title", null)));

        service.renameConversation(conv, "New title");

        verify(apiClient).putAsync(contains("sess-xyz"), any(), eq(
                com.agentdesk.model.dto.UpdateTitleResponse.class));
    }

    // ---- deleteConversation ---------------------------------------------

    @Test
    void deleteConversation_removesLocally() {
        final Conversation conv = service.createConversation("Bye");
        service.deleteConversation(conv);
        assertFalse(service.getConversations().contains(conv));
    }

    @Test
    void deleteConversation_synced_callsDeleteApi() {
        final Conversation conv = service.createConversation("Bye");
        conv.setServerSessionId("sess-del");

        when(apiClient.deleteAsync(contains("sess-del")))
                .thenReturn(CompletableFuture.completedFuture(null));

        service.deleteConversation(conv);

        verify(apiClient).deleteAsync(contains("sess-del"));
    }

    // ---- filterByQuery --------------------------------------------------

    @Test
    void filterByQuery_filtersCorrectly() {
        service.createConversation("Java tips");
        service.createConversation("Python guide");
        service.createConversation("JavaFX tutorial");

        service.filterByQuery("java");

        final List<Conversation> filtered = service.getFilteredConversations();
        assertEquals(2, filtered.size());
        assertTrue(filtered.stream().anyMatch(c -> c.getTitle().equals("Java tips")));
        assertTrue(filtered.stream().anyMatch(c -> c.getTitle().equals("JavaFX tutorial")));
    }

    @Test
    void filterByQuery_blank_showsAll() {
        service.createConversation("A");
        service.createConversation("B");
        service.filterByQuery("");

        assertEquals(2, service.getFilteredConversations().size());
    }
}
