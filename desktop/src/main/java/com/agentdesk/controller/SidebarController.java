package com.agentdesk.controller;

import com.agentdesk.component.MaterialDialog;
import com.agentdesk.component.ShareDialog;
import com.agentdesk.model.Conversation;
import com.agentdesk.service.ConversationService;
import javafx.fxml.FXML;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.geometry.Side;
import javafx.scene.control.*;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.Region;
import javafx.stage.Window;
import org.kordamp.ikonli.feather.Feather;
import org.kordamp.ikonli.javafx.FontIcon;
import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Component;

import java.util.Optional;
import java.util.function.Consumer;

@Component
@Scope("prototype")
public class SidebarController {

    @FXML private TextField searchField;
    @FXML private ListView<Conversation> conversationList;
    @FXML private Button settingsBtn;
    @FXML private Button logoutBtn;

    private final ConversationService conversationService;
    private Consumer<Conversation> onConversationSelected;
    private Runnable onNewChat;
    private Runnable onLogout;

    public SidebarController(ConversationService conversationService) {
        this.conversationService = conversationService;
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

        if (logoutBtn != null) {
            FontIcon logoutIcon = new FontIcon(Feather.LOG_OUT);
            logoutIcon.setIconSize(16);
            logoutIcon.getStyleClass().add("icon-btn-icon");
            logoutBtn.setGraphic(logoutIcon);
        }
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

    private class ConversationCell extends ListCell<Conversation> {

        private final HBox row;
        private final Label icon;
        private final Label title;
        private final Button moreBtn;
        private final ContextMenu moreMenu;

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

            title = new Label();
            title.getStyleClass().add("conversation-cell-title");
            title.setMaxWidth(140);
            title.setEllipsisString("...");
            HBox.setHgrow(title, Priority.ALWAYS);

            Region spacer = new Region();
            HBox.setHgrow(spacer, Priority.ALWAYS);

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

            row.getChildren().addAll(icon, title, spacer, moreBtn);

            row.setOnMouseEntered(e -> moreBtn.setVisible(true));
            row.setOnMouseExited(e -> {
                if (!moreMenu.isShowing()) {
                    moreBtn.setVisible(false);
                }
            });
            moreMenu.setOnHidden(e -> {
                if (!row.isHover()) {
                    moreBtn.setVisible(false);
                }
            });

            selectedProperty().addListener((obs, was, now) -> updateIconVisibility());
        }

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
            renameItem.setOnAction(e -> handleRename());

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
            } else {
                title.setText(item.getTitle());
                setGraphic(row);
                setText(null);
                updateIconVisibility();
            }
        }

        private Window getOwnerWindow() {
            return getScene() != null ? getScene().getWindow() : null;
        }

        private void handleRename() {
            Conversation item = getItem();
            if (item == null) return;

            Optional<String> result = MaterialDialog.showRenameDialog(getOwnerWindow(), item.getTitle());
            result.ifPresent(name -> conversationService.renameConversation(item, name));
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
