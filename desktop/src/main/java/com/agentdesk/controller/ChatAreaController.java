package com.agentdesk.controller;

import com.agentdesk.component.MaterialDialog;
import com.agentdesk.component.MessageBubble;
import com.agentdesk.component.SearchablePickerPopup;
import com.agentdesk.component.SelectionBadge;
import com.agentdesk.component.ShareDialog;
import com.agentdesk.component.ToolInspectorPopup;
import com.agentdesk.config.SpringFXMLLoader;
import com.agentdesk.config.TokenStore;
import com.agentdesk.model.Artifact;
import com.agentdesk.model.ChatMessage;
import com.agentdesk.model.Conversation;
import com.agentdesk.model.McpServer;
import com.agentdesk.model.dto.SendMessageResponse;
import com.agentdesk.service.ChatService;
import com.agentdesk.service.ConversationService;
import com.agentdesk.service.McpServerRegistry;
import com.agentdesk.service.ProviderService;
import com.agentdesk.service.SpeechToTextService;
import javafx.animation.FadeTransition;
import javafx.animation.KeyFrame;
import javafx.animation.KeyValue;
import javafx.animation.Timeline;
import javafx.concurrent.Task;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.geometry.Pos;
import javafx.scene.Node;
import javafx.scene.Parent;
import javafx.scene.control.Button;
import javafx.scene.control.ComboBox;
import javafx.scene.control.Label;
import javafx.scene.control.ScrollPane;
import javafx.scene.control.SplitPane;
import javafx.scene.control.TextArea;
import javafx.scene.input.KeyCode;
import javafx.scene.input.KeyEvent;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.FlowPane;
import javafx.scene.layout.StackPane;
import javafx.scene.layout.VBox;
import javafx.util.Duration;
import org.kordamp.ikonli.feather.Feather;
import org.kordamp.ikonli.javafx.FontIcon;
import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import javafx.stage.FileChooser;
import javafx.stage.Window;

@Component
@Scope("prototype")
public class ChatAreaController {

    @FXML private VBox welcomeView;
    @FXML private SplitPane chatSplitPane;
    @FXML private BorderPane chatView;

    @FXML private Label greetingLabel;
    @FXML private TextArea welcomeInputArea;
    @FXML private Button welcomeAttachBtn;
    @FXML private Button welcomeMicBtn;
    @FXML private ComboBox<String> welcomeModelSelector;
    @FXML private FlowPane quickActionsPane;

    @FXML private ScrollPane scrollPane;
    @FXML private VBox messagesContainer;
    @FXML private TextArea chatInputArea;
    @FXML private Button chatAttachBtn;
    @FXML private Button chatMicBtn;
    @FXML private Button sendButton;
    @FXML private Button chatShareBtn;
    @FXML private Button chatDownloadBtn;
    @FXML private ComboBox<String> chatModelSelector;

    private final ChatService chatService;
    private final SpringFXMLLoader fxmlLoader;
    private final McpServerRegistry mcpServerRegistry;
    private final SpeechToTextService speechToTextService;
    private final ConversationService conversationService;
    private final ProviderService providerService;
    private final TokenStore tokenStore;
    private Conversation currentConversation;
    private Task<?> currentStreamTask;
    private MessageBubble streamingBubble;
    private boolean isStreaming = false;

    private ArtifactPanelController artifactPanelController;
    private Node artifactPanelRoot;
    private boolean artifactPanelLoaded = false;

    private final Set<McpServer> selectedServers = new HashSet<>();
    private SelectionBadge welcomeBadge;
    private SelectionBadge chatBadge;
    private Node toolInspectorDrawer;

    /** Which input was used when the current STT session started (for UI toggle). */
    private boolean sttFromChat;

    public ChatAreaController(ChatService chatService, SpringFXMLLoader fxmlLoader,
                              McpServerRegistry mcpServerRegistry,
                              SpeechToTextService speechToTextService,
                              ConversationService conversationService,
                              ProviderService providerService,
                              TokenStore tokenStore) {
        this.chatService = chatService;
        this.fxmlLoader = fxmlLoader;
        this.mcpServerRegistry = mcpServerRegistry;
        this.speechToTextService = speechToTextService;
        this.conversationService = conversationService;
        this.providerService = providerService;
        this.tokenStore = tokenStore;
    }

    @FXML
    public void initialize() {
        // Seed the model selectors with whatever is already known (fallback or prior load).
        populateModelSelectors(providerService.getModelNamesFlat());

        // Refresh from backend; selectors update when the response arrives.
        providerService.refresh(this::populateModelSelectors, err ->
                System.err.println("[ChatArea] Could not load providers: " + err));

        // Refresh the MCP server catalogue from the backend (GET /api/v1/tools/mcp).
        // Falls back to the built-in static catalogue when the backend is unreachable.
        mcpServerRegistry.refresh(err ->
                System.err.println("[ChatArea] Could not load MCP tools: " + err));

        greetingLabel.setText(buildGreeting());

        FontIcon micIcon = new FontIcon(Feather.MIC);
        micIcon.setIconSize(16);
        micIcon.getStyleClass().add("mic-icon");
        welcomeMicBtn.setGraphic(micIcon);

        if (chatMicBtn != null) {
            FontIcon chatMicIcon = new FontIcon(Feather.MIC);
            chatMicIcon.setIconSize(16);
            chatMicIcon.getStyleClass().add("mic-icon");
            chatMicBtn.setGraphic(chatMicIcon);
        }

        welcomeMicBtn.setOnAction(e -> toggleMic(false));
        if (chatMicBtn != null) {
            chatMicBtn.setOnAction(e -> toggleMic(true));
        }

        welcomeInputArea.addEventFilter(KeyEvent.KEY_PRESSED, event -> {
            if (event.getCode() == KeyCode.ENTER && !event.isShiftDown()) {
                event.consume();
                handleSendFromWelcome();
            }
        });
        autoGrow(welcomeInputArea, 120);

        autoGrow(chatInputArea, 160);

        chatInputArea.addEventFilter(KeyEvent.KEY_PRESSED, event -> {
            if (event.getCode() == KeyCode.ENTER && !event.isShiftDown()) {
                event.consume();
                handleSendFromChat();
            }
        });

        for (var node : quickActionsPane.getChildren()) {
            if (node instanceof Button chip) {
                chip.setOnAction(e -> {
                    welcomeInputArea.setText(chip.getText());
                    welcomeInputArea.requestFocus();
                    welcomeInputArea.positionCaret(chip.getText().length());
                });
            }
        }

        welcomeBadge = new SelectionBadge();
        chatBadge = new SelectionBadge();
        attachBadgeToButton(welcomeAttachBtn, welcomeBadge);
        attachBadgeToButton(chatAttachBtn, chatBadge);

        if (chatShareBtn != null) {
            FontIcon shareIcon = new FontIcon(Feather.SHARE_2);
            shareIcon.setIconSize(16);
            chatShareBtn.setGraphic(shareIcon);
        }
        if (chatDownloadBtn != null) {
            FontIcon dlIcon = new FontIcon(Feather.DOWNLOAD);
            dlIcon.setIconSize(16);
            chatDownloadBtn.setGraphic(dlIcon);
        }
    }

    private void toggleMic(boolean fromChat) {
        if (speechToTextService.isListening() && sttFromChat == fromChat) {
            speechToTextService.stopListening();
            return;
        }
        if (speechToTextService.isListening()) {
            speechToTextService.stopListening();
        }
        if (!speechToTextService.isAvailable()) {
            Window w = getChatWindow();
            String hint = speechToTextService.getUnavailableSetupHint();
            MaterialDialog.showInfoDialog(w, "Speech to text",
                hint != null ? hint
                    : "Speech-to-text is not available. See README (STT section).");
            return;
        }

        TextArea target = fromChat ? chatInputArea : welcomeInputArea;
        String prefix = target.getText();
        sttFromChat = fromChat;
        final boolean ctx = fromChat;
        setMicListeningStyle(ctx, true);
        speechToTextService.startListening(
            prefix,
            target::setText,
            err -> MaterialDialog.showInfoDialog(getChatWindow(), "Speech to text", err),
            () -> setMicListeningStyle(ctx, false)
        );
    }

    private void setMicListeningStyle(boolean fromChat, boolean listening) {
        Button b = fromChat ? chatMicBtn : welcomeMicBtn;
        if (b == null) {
            return;
        }
        if (listening) {
            if (!b.getStyleClass().contains("mic-listening")) {
                b.getStyleClass().add("mic-listening");
            }
        } else {
            b.getStyleClass().remove("mic-listening");
        }
    }

    private Window getChatWindow() {
        if (chatInputArea != null && chatInputArea.getScene() != null) {
            return chatInputArea.getScene().getWindow();
        }
        return null;
    }

    /**
     * Makes a {@link TextArea} grow vertically as the user types, up to {@code maxHeight} px,
     * then scroll internally. Works correctly for both explicit newlines and soft word-wrap.
     */
    private void autoGrow(TextArea area, double maxHeight) {
        // Use a lookup on the internal Text node to get the real rendered height.
        // We defer the initial measurement until the node is in the scene graph.
        area.textProperty().addListener((obs, oldVal, newVal) -> resizeTextArea(area, maxHeight));
        area.widthProperty().addListener((obs, oldVal, newVal) -> resizeTextArea(area, maxHeight));
        area.sceneProperty().addListener((obs, oldScene, newScene) -> {
            if (newScene != null) {
                resizeTextArea(area, maxHeight);
            }
        });
    }

    private void resizeTextArea(TextArea area, double maxHeight) {
        // text-area > content > .scroll-pane > .viewport > .scroll-pane-content > Text
        javafx.scene.Node textNode = area.lookup(".text");
        if (textNode == null) {
            return;
        }
        // The Text node's layoutBounds gives the actual rendered content height.
        double contentHeight = textNode.getBoundsInLocal().getHeight();
        // Add vertical padding/insets (approx. top+bottom padding inside the TextArea skin)
        double padding = 20;
        double desired = contentHeight + padding;
        double newPref = Math.max(36, Math.min(desired, maxHeight));
        area.setPrefHeight(newPref);
        area.setMaxHeight(maxHeight);
    }

    private void attachBadgeToButton(Button button, SelectionBadge badge) {
        if (button.getParent() instanceof StackPane parentStack) {
            StackPane.setAlignment(badge, Pos.TOP_RIGHT);
            badge.setTranslateX(4);
            badge.setTranslateY(-4);
            parentStack.getChildren().add(badge);
        }
    }

    @FXML
    private void handleAttach() {
        Button anchor = (chatSplitPane.isVisible() && chatSplitPane.isManaged())
                ? chatAttachBtn : welcomeAttachBtn;

        SearchablePickerPopup popup = new SearchablePickerPopup(
                mcpServerRegistry.getGroupedServers(),
                this::handleInspectServer
        );

        popup.preselectServers(selectedServers);
        popup.setOnApply(selected -> {
            selectedServers.clear();
            selectedServers.addAll(selected);
            updateBadges();
        });

        popup.showRelativeTo(anchor);
    }

    private void handleInspectServer(McpServer server) {
        if (server.getToolCount() >= 10) {
            showToolInspectorDrawer(server);
        } else {
            ToolInspectorPopup inspectorPopup = new ToolInspectorPopup(server);
            Button anchor = (chatSplitPane.isVisible() && chatSplitPane.isManaged())
                    ? chatAttachBtn : welcomeAttachBtn;
            inspectorPopup.showRelativeTo(anchor);
        }
    }

    private void showToolInspectorDrawer(McpServer server) {
        closeToolInspectorDrawer();
        toolInspectorDrawer = ToolInspectorPopup.buildDrawerPanel(server, this::closeToolInspectorDrawer);
        if (!chatSplitPane.getItems().contains(toolInspectorDrawer)) {
            chatSplitPane.getItems().add(toolInspectorDrawer);
            chatSplitPane.setDividerPosition(chatSplitPane.getDividerPositions().length - 1, 0.6);
        }
    }

    private void closeToolInspectorDrawer() {
        if (toolInspectorDrawer != null && chatSplitPane.getItems().contains(toolInspectorDrawer)) {
            chatSplitPane.getItems().remove(toolInspectorDrawer);
            toolInspectorDrawer = null;
        }
    }

    private void updateBadges() {
        int count = selectedServers.size();
        welcomeBadge.setCount(count);
        chatBadge.setCount(count);
    }

    private void populateModelSelectors(java.util.List<String> models) {
        final String currentWelcome = welcomeModelSelector.getValue();
        final String currentChat    = chatModelSelector.getValue();

        welcomeModelSelector.getItems().setAll(models);
        chatModelSelector.getItems().setAll(models);

        final String firstModel = models.isEmpty() ? null : models.get(0);
        welcomeModelSelector.setValue(
                currentWelcome != null && models.contains(currentWelcome) ? currentWelcome : firstModel);
        chatModelSelector.setValue(
                currentChat != null && models.contains(currentChat) ? currentChat : firstModel);
    }

    private String buildGreeting() {
        int hour = LocalTime.now().getHour();
        String timeOfDay;
        if (hour < 12) timeOfDay = "Good morning";
        else if (hour < 17) timeOfDay = "Good afternoon";
        else timeOfDay = "Good evening";
        final String name = tokenStore.getUsername();
        return timeOfDay + (name != null && !name.isBlank() ? ", " + name : "");
    }

    private void handleSendFromWelcome() {
        String text = welcomeInputArea.getText().trim();
        if (text.isEmpty() || isStreaming) return;
        if (currentConversation == null) return;

        welcomeInputArea.clear();
        welcomeInputArea.setPrefHeight(36);
        transitionToChat();
        sendMessage(text);
    }

    @FXML
    private void handleSendFromChat() {
        String text = chatInputArea.getText().trim();
        if (text.isEmpty() || isStreaming) return;
        if (currentConversation == null) return;

        chatInputArea.clear();
        chatInputArea.setPrefHeight(36);
        sendMessage(text);
    }

    private void editUserMessage(String originalText, String newText) {
        if (isStreaming || currentConversation == null) return;

        var messages = currentConversation.getMessages();
        var children = messagesContainer.getChildren();

        int userIdx = -1;
        for (int i = messages.size() - 1; i >= 0; i--) {
            if (messages.get(i).isUser() && messages.get(i).getContent().equals(originalText)) {
                userIdx = i;
                break;
            }
        }
        if (userIdx < 0) return;

        int removeCount = messages.size() - userIdx;
        for (int i = 0; i < removeCount; i++) {
            messages.removeLast();
            if (!children.isEmpty()) children.removeLast();
        }

        sendMessage(newText);
    }

    private void retryUserMessage(String userText) {
        if (isStreaming || currentConversation == null) return;

        var messages = currentConversation.getMessages();
        var children = messagesContainer.getChildren();

        int userIdx = -1;
        for (int i = messages.size() - 1; i >= 0; i--) {
            if (messages.get(i).isUser() && messages.get(i).getContent().equals(userText)) {
                userIdx = i;
                break;
            }
        }
        if (userIdx < 0) return;

        int removeCount = messages.size() - userIdx;
        for (int i = 0; i < removeCount; i++) {
            messages.removeLast();
            if (!children.isEmpty()) children.removeLast();
        }

        sendMessage(userText);
    }

    private MessageBubble addUserBubble(ChatMessage msg) {
        MessageBubble bubble = MessageBubble.createUserBubble(msg);
        bubble.showActionButtons(true);
        bubble.setOnEdit(this::editUserMessage);
        bubble.setOnRetry(this::retryUserMessage);
        messagesContainer.getChildren().add(bubble.getRoot());
        return bubble;
    }

    private void sendMessage(String text) {
        if (currentConversation.getMessages().isEmpty()) {
            String autoTitle = text.length() > 40 ? text.substring(0, 40) + "..." : text;
            currentConversation.setTitle(autoTitle);
        }

        ChatMessage userMsg = new ChatMessage(ChatMessage.Role.USER, text);
        currentConversation.addMessage(userMsg);
        addUserBubble(userMsg);

        ChatMessage assistantMsg = new ChatMessage(ChatMessage.Role.ASSISTANT, "");
        currentConversation.addMessage(assistantMsg);
        streamingBubble = MessageBubble.createAssistantBubble(assistantMsg);
        streamingBubble.showTypingIndicator(true);
        streamingBubble.setOnRetry(content -> retryLastMessage());
        messagesContainer.getChildren().add(streamingBubble.getRoot());

        scrollToBottom();
        isStreaming = true;
        sendButton.setDisable(true);
        sendButton.setText("\u25FC");

        final String sessionId    = currentConversation.getServerSessionId();
        final String selectedModel = chatSplitPane.isVisible() && chatSplitPane.isManaged()
                ? chatModelSelector.getValue() : welcomeModelSelector.getValue();
        final List<McpServer> serversForRequest = new ArrayList<>(selectedServers);

        currentStreamTask = chatService.streamResponse(
            text,
            sessionId,
            null,           // provider — Phase 7 will wire this from ProviderService
            selectedModel,
            serversForRequest,
            chunk -> {
                streamingBubble.showTypingIndicator(false);
                assistantMsg.setContent(chunk);
                streamingBubble.updateText(chunk);
                scrollToBottom();
            },
            response -> {
                isStreaming = false;
                sendButton.setDisable(false);
                sendButton.setText("\u2191");
                if (streamingBubble != null) {
                    streamingBubble.renderMarkdown();
                    streamingBubble.showActionButtons(true);
                }
                streamingBubble = null;

                // Capture the server-assigned session id on the first message.
                if (response.sessionId() != null
                        && !response.sessionId().isBlank()
                        && !response.sessionId().equals(currentConversation.getServerSessionId())) {
                    currentConversation.setServerSessionId(response.sessionId());
                }
            }
        );
    }

    private void retryLastMessage() {
        if (isStreaming || currentConversation == null) return;

        var messages = currentConversation.getMessages();
        if (messages.size() < 2) return;

        String lastUserText = null;
        for (int i = messages.size() - 1; i >= 0; i--) {
            if (messages.get(i).isUser()) {
                lastUserText = messages.get(i).getContent();
                break;
            }
        }
        if (lastUserText == null) return;

        messages.removeLast();
        if (!messagesContainer.getChildren().isEmpty()) {
            messagesContainer.getChildren().removeLast();
        }

        ChatMessage assistantMsg = new ChatMessage(ChatMessage.Role.ASSISTANT, "");
        currentConversation.addMessage(assistantMsg);
        streamingBubble = MessageBubble.createAssistantBubble(assistantMsg);
        streamingBubble.showTypingIndicator(true);
        streamingBubble.setOnRetry(content -> retryLastMessage());
        messagesContainer.getChildren().add(streamingBubble.getRoot());

        scrollToBottom();
        isStreaming = true;
        sendButton.setDisable(true);
        sendButton.setText("\u25FC");

        String userInput = lastUserText;
        List<McpServer> serversForRetry = new ArrayList<>(selectedServers);
        final String retrySessionId    = currentConversation.getServerSessionId();
        final String retryModel = chatSplitPane.isVisible() && chatSplitPane.isManaged()
                ? chatModelSelector.getValue() : welcomeModelSelector.getValue();

        currentStreamTask = chatService.streamResponse(
            userInput,
            retrySessionId,
            null,
            retryModel,
            serversForRetry,
            chunk -> {
                streamingBubble.showTypingIndicator(false);
                assistantMsg.setContent(chunk);
                streamingBubble.updateText(chunk);
                scrollToBottom();
            },
            response -> {
                isStreaming = false;
                sendButton.setDisable(false);
                sendButton.setText("\u2191");
                if (streamingBubble != null) {
                    streamingBubble.renderMarkdown();
                    streamingBubble.showActionButtons(true);
                }
                streamingBubble = null;

                if (response.sessionId() != null
                        && !response.sessionId().isBlank()
                        && !response.sessionId().equals(currentConversation.getServerSessionId())) {
                    currentConversation.setServerSessionId(response.sessionId());
                }
            }
        );
    }

    @FXML
    private void handleShareChat() {
        if (currentConversation == null) return;
        Window owner = chatShareBtn != null && chatShareBtn.getScene() != null
                ? chatShareBtn.getScene().getWindow() : null;
        ShareDialog.show(owner, currentConversation.getTitle());
    }

    @FXML
    private void handleDownloadChat() {
        if (currentConversation == null || currentConversation.getMessages().isEmpty()) return;

        Window owner = chatDownloadBtn != null && chatDownloadBtn.getScene() != null
                ? chatDownloadBtn.getScene().getWindow() : null;

        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Download Chat");
        fileChooser.setInitialFileName(currentConversation.getTitle().replaceAll("[^a-zA-Z0-9 ]", "") + ".md");
        fileChooser.getExtensionFilters().add(
            new FileChooser.ExtensionFilter("Markdown Files", "*.md")
        );

        File file = fileChooser.showSaveDialog(owner);
        if (file != null) {
            try (PrintWriter writer = new PrintWriter(file)) {
                writer.println("# " + currentConversation.getTitle());
                writer.println();
                for (ChatMessage msg : currentConversation.getMessages()) {
                    String role = msg.isUser() ? "**You**" : "**Assistant**";
                    writer.println(role);
                    writer.println();
                    writer.println(msg.getContent());
                    writer.println();
                    writer.println("---");
                    writer.println();
                }
            } catch (IOException e) {
                System.err.println("Failed to save chat: " + e.getMessage());
            }
        }
    }

    private void transitionToChat() {
        FadeTransition fadeOut = new FadeTransition(Duration.millis(200), welcomeView);
        fadeOut.setFromValue(1.0);
        fadeOut.setToValue(0.0);
        fadeOut.setOnFinished(e -> {
            welcomeView.setVisible(false);
            welcomeView.setManaged(false);
            chatSplitPane.setVisible(true);
            chatSplitPane.setManaged(true);
            chatSplitPane.setOpacity(0);

            FadeTransition fadeIn = new FadeTransition(Duration.millis(250), chatSplitPane);
            fadeIn.setFromValue(0.0);
            fadeIn.setToValue(1.0);
            fadeIn.play();

            chatInputArea.requestFocus();
        });
        fadeOut.play();
    }

    private void showWelcomeView() {
        welcomeView.setVisible(true);
        welcomeView.setManaged(true);
        welcomeView.setOpacity(1.0);
        chatSplitPane.setVisible(false);
        chatSplitPane.setManaged(false);
        closeArtifact();

        greetingLabel.setText(buildGreeting());
        welcomeInputArea.clear();
    }

    private void showChatView() {
        welcomeView.setVisible(false);
        welcomeView.setManaged(false);
        chatSplitPane.setVisible(true);
        chatSplitPane.setManaged(true);
        chatSplitPane.setOpacity(1.0);
    }

    private void scrollToBottom() {
        Timeline timeline = new Timeline(
            new KeyFrame(Duration.millis(50),
                new KeyValue(scrollPane.vvalueProperty(), 1.0))
        );
        timeline.play();
    }

    public void loadConversation(Conversation conversation) {
        this.currentConversation = conversation;
        messagesContainer.getChildren().clear();
        closeArtifact();
        closeToolInspectorDrawer();
        selectedServers.clear();
        updateBadges();

        if (conversation.isSynced()) {
            // Always re-fetch from the server so the view is never stale.
            showChatView();
            showHistoryLoading();
            conversationService.loadHistory(
                conversation,
                () -> {
                    // onComplete — called on the JAT after the list is populated.
                    messagesContainer.getChildren().clear();
                    if (conversation.getMessages().isEmpty()) {
                        // Synced session with no messages yet — ready to type.
                        chatInputArea.requestFocus();
                    } else {
                        renderMessages(conversation);
                        scrollToBottom();
                        chatInputArea.requestFocus();
                    }
                },
                errorMsg -> {
                    // onError — called on the JAT if the fetch fails.
                    messagesContainer.getChildren().clear();
                    Label errLabel = new Label("Could not load history: " + errorMsg);
                    errLabel.getStyleClass().add("history-error-label");
                    messagesContainer.getChildren().add(errLabel);
                }
            );

        } else if (!conversation.getMessages().isEmpty()) {
            // Brand-new local conversation that already has in-memory messages (mid-session).
            showChatView();
            renderMessages(conversation);
            chatInputArea.requestFocus();

        } else {
            // Brand-new local conversation with no messages yet — show the welcome view.
            showWelcomeView();
        }
    }

    /**
     * Adds a centred spinner to the messages container while history is being fetched.
     */
    private void showHistoryLoading() {
        javafx.scene.control.ProgressIndicator spinner =
                new javafx.scene.control.ProgressIndicator();
        spinner.setPrefSize(40, 40);
        spinner.getStyleClass().add("history-loading-spinner");
        javafx.scene.layout.StackPane centred = new javafx.scene.layout.StackPane(spinner);
        centred.setPrefHeight(200);
        messagesContainer.getChildren().add(centred);
    }

    /**
     * Renders all messages currently in {@code conversation} into the
     * {@code messagesContainer}.  Caller must ensure this runs on the JAT.
     */
    private void renderMessages(Conversation conversation) {
        for (ChatMessage msg : conversation.getMessages()) {
            if (msg.isUser()) {
                addUserBubble(msg);
            } else {
                MessageBubble bubble = MessageBubble.createAssistantBubble(msg);
                bubble.renderMarkdown();
                bubble.showActionButtons(true);
                bubble.setOnRetry(content -> retryLastMessage());
                messagesContainer.getChildren().add(bubble.getRoot());
            }
        }
    }

    public void showArtifact(Artifact artifact) {
        ensureArtifactPanelLoaded();
        if (artifactPanelRoot == null) return;

        if (!chatSplitPane.getItems().contains(artifactPanelRoot)) {
            chatSplitPane.getItems().add(artifactPanelRoot);
        }

        chatSplitPane.setDividerPosition(0, 0.55);
        artifactPanelController.showArtifact(artifact);
    }

    public void closeArtifact() {
        if (artifactPanelRoot != null && chatSplitPane.getItems().contains(artifactPanelRoot)) {
            chatSplitPane.getItems().remove(artifactPanelRoot);
        }
    }

    private void ensureArtifactPanelLoaded() {
        if (artifactPanelLoaded) return;
        try {
            FXMLLoader loader = fxmlLoader.getLoader("fxml/artifact-panel.fxml");
            Parent root = loader.load();
            artifactPanelController = loader.getController();
            artifactPanelRoot = root;
            artifactPanelController.setOnClose(this::closeArtifact);
            artifactPanelLoaded = true;
        } catch (IOException e) {
            System.err.println("Failed to load artifact panel: " + e.getMessage());
        }
    }

    public Conversation getCurrentConversation() {
        return currentConversation;
    }
}
