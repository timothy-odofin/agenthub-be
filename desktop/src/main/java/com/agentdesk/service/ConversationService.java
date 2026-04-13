package com.agentdesk.service;

import com.agentdesk.model.Conversation;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.collections.transformation.FilteredList;
import org.springframework.stereotype.Service;

@Service
public class ConversationService {

    private final ObservableList<Conversation> conversations = FXCollections.observableArrayList();
    private final FilteredList<Conversation> filteredConversations = new FilteredList<>(conversations, p -> true);

    public ConversationService() {
        seedSampleConversations();
    }

    public ObservableList<Conversation> getConversations() {
        return conversations;
    }

    public FilteredList<Conversation> getFilteredConversations() {
        return filteredConversations;
    }

    public Conversation createConversation(String title) {
        Conversation conversation = new Conversation(title);
        conversations.add(0, conversation);
        return conversation;
    }

    public void deleteConversation(Conversation conversation) {
        conversations.remove(conversation);
    }

    public void renameConversation(Conversation conversation, String newTitle) {
        conversation.setTitle(newTitle);
        int idx = conversations.indexOf(conversation);
        if (idx >= 0) {
            conversations.set(idx, conversation);
        }
    }

    public void filterByQuery(String query) {
        if (query == null || query.isBlank()) {
            filteredConversations.setPredicate(p -> true);
        } else {
            String lower = query.toLowerCase();
            filteredConversations.setPredicate(c ->
                c.getTitle().toLowerCase().contains(lower)
            );
        }
    }

    private void seedSampleConversations() {
        conversations.add(new Conversation("JavaFX desktop app design"));
        conversations.add(new Conversation("Explain MCP and SSE"));
        conversations.add(new Conversation("MySQL MCP server setup"));
        conversations.add(new Conversation("Best UI frameworks 2025"));
        conversations.add(new Conversation("Help me write a cover letter"));
        conversations.add(new Conversation("Python data analysis tips"));
    }
}
