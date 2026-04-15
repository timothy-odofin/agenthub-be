package com.agentdesk.controller;

import com.agentdesk.config.AppConfig;
import com.agentdesk.model.Conversation;
import com.agentdesk.service.ConversationService;
import javafx.fxml.FXML;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.SplitPane;
import javafx.scene.input.MouseButton;
import javafx.scene.input.MouseEvent;
import javafx.scene.layout.HBox;
import javafx.stage.Stage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Component;

@Component
@Scope("prototype")
public class MainController {

    private static final Logger log = LoggerFactory.getLogger(MainController.class);

    @FXML private HBox titleBar;
    @FXML private Label titleBarLabel;
    @FXML private Button minimizeBtn;
    @FXML private Button maximizeBtn;
    @FXML private Button closeBtn;
    @FXML private SplitPane splitPane;
    @FXML private SidebarController sidebarController;
    @FXML private ChatAreaController chatAreaController;

    private final ConversationService conversationService;
    private final AppConfig appConfig;
    private Stage stage;
    private double dragOffsetX;
    private double dragOffsetY;
    private boolean maximized = false;
    private double restoreX, restoreY, restoreW, restoreH;

    public MainController(ConversationService conversationService, AppConfig appConfig) {
        this.conversationService = conversationService;
        this.appConfig = appConfig;
    }

    @FXML
    public void initialize() {
        SplitPane.setResizableWithParent(splitPane.getItems().get(0), false);

        titleBarLabel.setText(appConfig.getTitle());

        sidebarController.setOnConversationSelected(this::loadConversation);
        sidebarController.setOnNewChat(this::createNewConversation);

        // Load sessions from the server; select the first one when the list arrives.
        conversationService.loadSessions(errorMsg -> {
            log.warn("Could not load sessions on startup: {}", errorMsg);
            // Show an empty sidebar — the user can still start a new conversation.
        });

        // When the server populates the list, auto-select the first entry.
        conversationService.getConversations().addListener(
                (javafx.collections.ListChangeListener<Conversation>) change -> {
                    if (!change.getList().isEmpty()
                            && sidebarController.getSelectedConversation() == null) {
                        final Conversation first = change.getList().get(0);
                        loadConversation(first);
                        sidebarController.selectConversation(first);
                    }
                });
    }

    private void loadConversation(Conversation conversation) {
        chatAreaController.loadConversation(conversation);
        updateTitleBar(conversation);
    }

    private void createNewConversation() {
        Conversation newConv = conversationService.createConversation("New conversation");
        loadConversation(newConv);
        sidebarController.selectConversation(newConv);
    }

    private void updateTitleBar(Conversation conversation) {
        if (titleBarLabel == null) return;
        String base = appConfig.getTitle();
        if (conversation != null && conversation.getTitle() != null && !conversation.getTitle().isBlank()) {
            titleBarLabel.setText(base + " — " + conversation.getTitle());
        } else {
            titleBarLabel.setText(base);
        }
    }

    public void onStageReady(Stage stage) {
        this.stage = stage;

        titleBar.setOnMousePressed(this::onTitleBarPressed);
        titleBar.setOnMouseDragged(this::onTitleBarDragged);
        titleBar.setOnMouseClicked(e -> {
            if (e.getButton() == MouseButton.PRIMARY && e.getClickCount() == 2) {
                toggleMaximize();
            }
        });
    }

    private void onTitleBarPressed(MouseEvent e) {
        if (maximized) return;
        dragOffsetX = e.getScreenX() - stage.getX();
        dragOffsetY = e.getScreenY() - stage.getY();
    }

    private void onTitleBarDragged(MouseEvent e) {
        if (maximized) {
            double relX = dragOffsetX / stage.getWidth();
            maximized = false;
            stage.setWidth(restoreW);
            stage.setHeight(restoreH);
            dragOffsetX = relX * restoreW;
            dragOffsetY = e.getScreenY() - stage.getY();
        }
        stage.setX(e.getScreenX() - dragOffsetX);
        stage.setY(e.getScreenY() - dragOffsetY);
    }

    private void toggleMaximize() {
        if (maximized) {
            stage.setX(restoreX);
            stage.setY(restoreY);
            stage.setWidth(restoreW);
            stage.setHeight(restoreH);
            maximized = false;
        } else {
            restoreX = stage.getX();
            restoreY = stage.getY();
            restoreW = stage.getWidth();
            restoreH = stage.getHeight();
            var screen = javafx.stage.Screen.getPrimary().getVisualBounds();
            stage.setX(screen.getMinX());
            stage.setY(screen.getMinY());
            stage.setWidth(screen.getWidth());
            stage.setHeight(screen.getHeight());
            maximized = true;
        }
    }

    @FXML
    private void handleMinimize() {
        if (stage != null) stage.setIconified(true);
    }

    @FXML
    private void handleMaximize() {
        if (stage != null) toggleMaximize();
    }

    @FXML
    private void handleClose() {
        if (stage != null) stage.close();
    }

    public void setOnLogout(Runnable logoutHandler) {
        sidebarController.setOnLogout(logoutHandler);
    }

    public Conversation getCurrentConversation() {
        return chatAreaController.getCurrentConversation();
    }
}
