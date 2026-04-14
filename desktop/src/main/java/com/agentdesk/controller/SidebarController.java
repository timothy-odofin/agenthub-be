package com.agentdesk.controller;

import com.agentdesk.component.MaterialDialog;
import com.agentdesk.component.ShareDialog;
import com.agentdesk.config.TokenStore;
import com.agentdesk.model.Conversation;
import com.agentdesk.service.ConversationService;
import javafx.fxml.FXML;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.geometry.Side;
import javafx.scene.control.*;
import javafx.scene.input.KeyCode;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.StackPane;
import javafx.stage.Window;
import javafx.animation.RotateTransition;
import javafx.util.Duration;
import org.kordamp.ikonli.feather.Feather;
import org.kordamp.ikonli.javafx.FontIcon;
import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Component;

import java.util.function.Consumer;

@Component
@Scope("prototype")
public class SidebarController {

    @FXML private TextField searchField;
    @FXML private ListView<Conversation> conversationList;
    @FXML private Button settingsBtn;
    @FXML private Button logoutBtn;
    @FXML private Button reloadSessionsBtn;
    @FXML private Label profileNameLabel;
    @FXML private Label userAvatarLabel;

    private final ConversationService conversationService;
    private final TokenStore tokenStore;
    private Consumer<Conversation> onConversationSelected;
    private Runnable onNewChat;
    private Runnable onLogout;

    public SidebarController(ConversationService conversationService, TokenStore tokenStore) {
        this.conversationService = conversationService;
        this.tokenStore = tokenStore;
    }

    @FXML
    public void initialize() {
        conversationList.setItems(conversationService.getFilteredConversations());
        conversationList.setCellFactory(lv -> new ConversationCell());

        conversationList.getSelectionModel().selectedItemProperty().addListener((obs, old, selected) -> {
            if (selected != null && onConversationSelected != null) {
                onConversationSelected.accept(selected);
            }
        });

        searchField.textProperty().addListener((obs, old, query) ->
            conversationService.filterByQuery(query)
        );

        // Populate the profile section with the logged-in user's name.
        final String name = tokenStore.getUsername();
        if (name != null && !name.isBlank()) {
            if (profileNameLabel != null) {
                profileNameLabel.setText(name);
            }
            if (userAvatarLabel != null) {
                // Show the first character of the name as the avatar initial.
                userAvatarLabel.setText(String.valueOf(name.charAt(0)).toUpperCase());
            }
        }

        if (logoutBtn != null) {
            FontIcon logoutIcon = new FontIcon(Feather.LOG_OUT);
            logoutIcon.setIconSize(16);
            logoutIcon.getStyleClass().add("icon-btn-icon");
            logoutBtn.setGraphic(logoutIcon);
        }

        if (reloadSessionsBtn != null) {
            FontIcon refreshIcon = new FontIcon(Feather.REFRESH_CW);
            refreshIcon.setIconSize(13);
            refreshIcon.getStyleClass().add("reload-sessions-icon");
            reloadSessionsBtn.setGraphic(refreshIcon);
        }
    }

    @FXML
    private void handleReloadSessions() {
        if (reloadSessionsBtn == null) return;

        // Spin the icon while loading
        FontIcon refreshIcon = (FontIcon) reloadSessionsBtn.getGraphic();
        RotateTransition spin = new RotateTransition(Duration.millis(600), refreshIcon);
        spin.setByAngle(360);
        spin.setCycleCount(RotateTransition.INDEFINITE);
        spin.play();
        reloadSessionsBtn.setDisable(true);

        Runnable stopSpin = () -> {
            spin.stop();
            refreshIcon.setRotate(0);
            reloadSessionsBtn.setDisable(false);
        };

        conversationService.loadSessions(stopSpin, errorMsg -> stopSpin.run());
    }

    @FXML
    private void handleNewChat() {
        if (onNewChat != null) {
            onNewChat.run();
        }
    }

    @FXML
    private void handleSettings() {
        var scene = settingsBtn.getScene();
        if (scene == null) return;

        var stylesheets = scene.getStylesheets();
        String darkTheme = getClass().getResource("/css/dark-theme.css").toExternalForm();

        if (stylesheets.contains(darkTheme)) {
            stylesheets.remove(darkTheme);
        } else {
            stylesheets.add(darkTheme);
        }
    }

    public void setOnConversationSelected(Consumer<Conversation> handler) {
        this.onConversationSelected = handler;
    }

    public void setOnNewChat(Runnable handler) {
        this.onNewChat = handler;
    }

    public void setOnLogout(Runnable handler) {
        this.onLogout = handler;
    }

    @FXML
    private void handleLogout() {
        if (onLogout != null) {
            onLogout.run();
        }
    }

    public void selectConversation(Conversation conversation) {
        conversationList.getSelectionModel().select(conversation);
    }

    /**
     * Returns the currently selected conversation, or {@code null} if none is selected.
     */
    @org.springframework.lang.Nullable
    public Conversation getSelectedConversation() {
        return conversationList.getSelectionModel().getSelectedItem();
    }

    private class ConversationCell extends ListCell<Conversation> {

        private final HBox      row;
        private final Label     icon;
        private final Label     titleLabel;
        private final TextField titleField;
        private final StackPane titleStack;
        private final Button    moreBtn;
        private final ContextMenu moreMenu;

        /** True while the inline rename field is visible. */
        private boolean editing = false;

        ConversationCell() {
            row = new HBox(8);
            row.setAlignment(Pos.CENTER_LEFT);
            row.setPadding(new Insets(6, 4, 6, 8));
            row.getStyleClass().add("conversation-cell-row");

            icon = new Label();
            FontIcon chatIcon = new FontIcon(Feather.MESSAGE_CIRCLE);
            chatIcon.setIconSize(14);
            chatIcon.getStyleClass().add("conv-cell-icon");
            icon.setGraphic(chatIcon);

            // ---- title label (normal display) ----
            titleLabel = new Label();
            titleLabel.getStyleClass().add("conversation-cell-title");
            titleLabel.setMaxWidth(Double.MAX_VALUE);
            titleLabel.setEllipsisString("...");

            // ---- inline rename field ----
            titleField = new TextField();
            titleField.getStyleClass().add("conv-rename-field");
            titleField.setVisible(false);
            titleField.setManaged(false);
            titleField.setMaxWidth(Double.MAX_VALUE);

            // Commit on Enter, cancel on Escape.
            titleField.setOnKeyPressed(e -> {
                if (e.getCode() == KeyCode.ENTER) {
                    e.consume();
                    commitRename();
                } else if (e.getCode() == KeyCode.ESCAPE) {
                    e.consume();
                    cancelRename();
                }
            });

            // Commit when focus leaves the field (e.g. click elsewhere).
            titleField.focusedProperty().addListener((obs, wasFocused, isFocused) -> {
                if (wasFocused && !isFocused && editing) {
                    commitRename();
                }
            });

            // Stack label and field in the same slot so layout doesn't shift.
            titleStack = new StackPane(titleLabel, titleField);
            titleStack.setAlignment(Pos.CENTER_LEFT);
            HBox.setHgrow(titleStack, Priority.ALWAYS);

            FontIcon dotsIcon = new FontIcon(Feather.MORE_HORIZONTAL);
            dotsIcon.setIconSize(14);
            dotsIcon.getStyleClass().add("conv-more-icon");

            moreBtn = new Button();
            moreBtn.setGraphic(dotsIcon);
            moreBtn.getStyleClass().add("conv-more-btn");
            moreBtn.setVisible(false);
            moreBtn.setTooltip(new Tooltip("More options"));

            moreMenu = buildMoreMenu();
            moreBtn.setOnAction(e -> {
                e.consume();
                moreMenu.show(moreBtn, Side.BOTTOM, 0, 4);
            });

            row.getChildren().addAll(icon, titleStack, moreBtn);

            row.setOnMouseEntered(e -> {
                if (!editing) moreBtn.setVisible(true);
            });
            row.setOnMouseExited(e -> {
                if (!moreMenu.isShowing() && !editing) {
                    moreBtn.setVisible(false);
                }
            });
            moreMenu.setOnHidden(e -> {
                if (!row.isHover() && !editing) {
                    moreBtn.setVisible(false);
                }
            });

            selectedProperty().addListener((obs, was, now) -> updateIconVisibility());
        }

        // ---- inline rename helpers ----------------------------------------

        private void startRename() {
            Conversation item = getItem();
            if (item == null) return;
            editing = true;

            titleField.setText(item.getTitle());
            titleField.setVisible(true);
            titleField.setManaged(true);
            titleLabel.setVisible(false);
            titleLabel.setManaged(false);
            moreBtn.setVisible(false);

            // Ensure cell gets focus and text is fully selected for easy overwrite.
            titleField.requestFocus();
            titleField.selectAll();
        }

        private void commitRename() {
            if (!editing) return;
            editing = false;

            String newTitle = titleField.getText().trim();
            Conversation item = getItem();
            if (item != null && !newTitle.isEmpty() && !newTitle.equals(item.getTitle())) {
                conversationService.renameConversation(item, newTitle);
            }
            exitEditMode();
        }

        private void cancelRename() {
            editing = false;
            exitEditMode();
        }

        private void exitEditMode() {
            titleField.setVisible(false);
            titleField.setManaged(false);
            titleLabel.setVisible(true);
            titleLabel.setManaged(true);
            moreBtn.setVisible(false);
        }

        // ---- existing helpers ---------------------------------------------

        private void updateIconVisibility() {
            boolean show = getItem() != null && !isEmpty() && isSelected();
            icon.setVisible(show);
            icon.setManaged(show);
        }

        private ContextMenu buildMoreMenu() {
            ContextMenu menu = new ContextMenu();
            menu.getStyleClass().add("conv-context-menu");

            FontIcon renameIcon = new FontIcon(Feather.EDIT_2);
            renameIcon.setIconSize(14);
            MenuItem renameItem = new MenuItem("Rename");
            renameItem.setGraphic(renameIcon);
            renameItem.setOnAction(e -> startRename());

            FontIcon shareIcon = new FontIcon(Feather.SHARE_2);
            shareIcon.setIconSize(14);
            MenuItem shareItem = new MenuItem("Share");
            shareItem.setGraphic(shareIcon);
            shareItem.setOnAction(e -> handleShare());

            SeparatorMenuItem separator = new SeparatorMenuItem();

            FontIcon deleteIcon = new FontIcon(Feather.TRASH_2);
            deleteIcon.setIconSize(14);
            deleteIcon.getStyleClass().add("conv-delete-icon");
            MenuItem deleteItem = new MenuItem("Delete");
            deleteItem.setGraphic(deleteIcon);
            deleteItem.getStyleClass().add("conv-delete-item");
            deleteItem.setOnAction(e -> handleDelete());

            menu.getItems().addAll(renameItem, shareItem, separator, deleteItem);
            return menu;
        }

        @Override
        protected void updateItem(Conversation item, boolean empty) {
            super.updateItem(item, empty);
            if (empty || item == null) {
                setGraphic(null);
                setText(null);
                // Make sure a recycled cell isn't stuck in edit mode.
                cancelRename();
            } else {
                titleLabel.setText(item.getTitle());
                setGraphic(row);
                setText(null);
                updateIconVisibility();
            }
        }

        private Window getOwnerWindow() {
            return getScene() != null ? getScene().getWindow() : null;
        }

        private void handleShare() {
            Conversation item = getItem();
            if (item == null) return;
            ShareDialog.show(getOwnerWindow(), item.getTitle());
        }

        private void handleDelete() {
            Conversation item = getItem();
            if (item == null) return;
            boolean confirmed = MaterialDialog.showDeleteDialog(getOwnerWindow(), item.getTitle());
            if (confirmed) {
                conversationService.deleteConversation(item);
            }
        }
    }
}
