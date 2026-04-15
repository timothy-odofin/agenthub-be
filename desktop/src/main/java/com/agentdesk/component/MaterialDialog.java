package com.agentdesk.component;

import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.TextField;
import javafx.scene.input.KeyCode;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.StackPane;
import javafx.scene.layout.VBox;
import javafx.scene.paint.Color;
import javafx.stage.Modality;
import javafx.stage.Stage;
import javafx.stage.StageStyle;
import javafx.stage.Window;
import org.kordamp.ikonli.feather.Feather;
import org.kordamp.ikonli.javafx.FontIcon;

import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

public class MaterialDialog {

    public static Optional<String> showRenameDialog(Window owner, String currentName) {
        Stage dialog = createDialogStage(owner);
        AtomicReference<String> result = new AtomicReference<>(null);

        FontIcon icon = new FontIcon(Feather.EDIT_2);
        icon.setIconSize(20);
        icon.getStyleClass().add("dialog-header-icon");

        Label titleLabel = new Label("Rename conversation");
        titleLabel.getStyleClass().add("dialog-title");

        Label subtitleLabel = new Label("Enter a new name for this conversation");
        subtitleLabel.getStyleClass().add("dialog-subtitle");

        TextField input = new TextField(currentName);
        input.getStyleClass().add("dialog-input");
        input.setPromptText("Conversation name");
        input.selectAll();

        Button cancelBtn = new Button("Cancel");
        cancelBtn.getStyleClass().addAll("dialog-btn", "dialog-btn-secondary");
        cancelBtn.setOnAction(e -> dialog.close());

        Button confirmBtn = new Button("Rename");
        confirmBtn.getStyleClass().addAll("dialog-btn", "dialog-btn-primary");
        confirmBtn.setOnAction(e -> {
            String text = input.getText().trim();
            if (!text.isBlank()) {
                result.set(text);
            }
            dialog.close();
        });
        confirmBtn.setDefaultButton(true);

        input.setOnKeyPressed(e -> {
            if (e.getCode() == KeyCode.ESCAPE) dialog.close();
        });

        HBox buttons = new HBox(10, cancelBtn, confirmBtn);
        buttons.setAlignment(Pos.CENTER_RIGHT);

        VBox card = buildCard(icon, titleLabel, subtitleLabel, input, buttons);

        showDialog(dialog, owner, card);
        return Optional.ofNullable(result.get());
    }

    public static boolean showDeleteDialog(Window owner, String conversationTitle) {
        Stage dialog = createDialogStage(owner);
        AtomicBoolean confirmed = new AtomicBoolean(false);

        StackPane iconCircle = new StackPane();
        iconCircle.getStyleClass().add("dialog-icon-circle-danger");
        iconCircle.setMaxSize(44, 44);
        iconCircle.setMinSize(44, 44);
        FontIcon icon = new FontIcon(Feather.TRASH_2);
        icon.setIconSize(20);
        icon.getStyleClass().add("dialog-danger-icon");
        iconCircle.getChildren().add(icon);

        Label titleLabel = new Label("Delete conversation");
        titleLabel.getStyleClass().add("dialog-title");

        Label messageLabel = new Label(
            "Are you sure you want to delete \"" + conversationTitle + "\"? This action cannot be undone."
        );
        messageLabel.getStyleClass().add("dialog-message");
        messageLabel.setWrapText(true);

        Button cancelBtn = new Button("Cancel");
        cancelBtn.getStyleClass().addAll("dialog-btn", "dialog-btn-secondary");
        cancelBtn.setOnAction(e -> dialog.close());

        Button deleteBtn = new Button("Delete");
        deleteBtn.getStyleClass().addAll("dialog-btn", "dialog-btn-danger");
        deleteBtn.setOnAction(e -> {
            confirmed.set(true);
            dialog.close();
        });

        HBox buttons = new HBox(10, cancelBtn, deleteBtn);
        buttons.setAlignment(Pos.CENTER_RIGHT);

        VBox card = buildCard(iconCircle, titleLabel, null, messageLabel, buttons);

        showDialog(dialog, owner, card);
        return confirmed.get();
    }

    public static void showInfoDialog(Window owner, String title, String message) {
        Stage dialog = createDialogStage(owner);

        FontIcon icon = new FontIcon(Feather.CHECK_CIRCLE);
        icon.setIconSize(20);
        icon.getStyleClass().add("dialog-success-icon");

        Label titleLabel = new Label(title);
        titleLabel.getStyleClass().add("dialog-title");

        Label messageLabel = new Label(message);
        messageLabel.getStyleClass().add("dialog-message");
        messageLabel.setWrapText(true);

        Button okBtn = new Button("OK");
        okBtn.getStyleClass().addAll("dialog-btn", "dialog-btn-primary");
        okBtn.setOnAction(e -> dialog.close());
        okBtn.setDefaultButton(true);

        HBox buttons = new HBox(okBtn);
        buttons.setAlignment(Pos.CENTER_RIGHT);

        VBox card = buildCard(icon, titleLabel, null, messageLabel, buttons);

        showDialog(dialog, owner, card);
    }

    private static Stage createDialogStage(Window owner) {
        Stage dialog = new Stage(StageStyle.TRANSPARENT);
        dialog.initModality(Modality.APPLICATION_MODAL);
        if (owner != null) {
            dialog.initOwner(owner);
        }
        return dialog;
    }

    private static VBox buildCard(
            javafx.scene.Node iconNode,
            Label titleLabel,
            Label subtitleLabel,
            javafx.scene.Node contentNode,
            HBox buttons
    ) {
        VBox header = new VBox(6);
        header.setAlignment(Pos.CENTER_LEFT);
        header.getChildren().add(iconNode);
        header.getChildren().add(titleLabel);
        if (subtitleLabel != null) {
            header.getChildren().add(subtitleLabel);
        }

        VBox card = new VBox(20);
        card.getStyleClass().add("dialog-card");
        card.setMaxWidth(420);
        card.setMinWidth(380);
        card.setPadding(new Insets(28, 28, 24, 28));

        card.getChildren().add(header);
        if (contentNode != null) {
            VBox.setVgrow(contentNode, Priority.NEVER);
            card.getChildren().add(contentNode);
        }
        card.getChildren().add(buttons);

        return card;
    }

    private static void showDialog(Stage dialog, Window owner, VBox card) {
        Scene scene = new Scene(card);
        scene.setFill(Color.TRANSPARENT);

        if (owner != null && owner.getScene() != null) {
            scene.getStylesheets().addAll(owner.getScene().getStylesheets());
        }
        String themeUrl = MaterialDialog.class.getResource("/css/theme.css") != null
                ? MaterialDialog.class.getResource("/css/theme.css").toExternalForm()
                : null;
        if (themeUrl != null && !scene.getStylesheets().contains(themeUrl)) {
            scene.getStylesheets().add(0, themeUrl);
        }

        scene.setOnKeyPressed(e -> {
            if (e.getCode() == KeyCode.ESCAPE) dialog.close();
        });

        dialog.setScene(scene);
        dialog.sizeToScene();

        if (owner != null) {
            dialog.setOnShown(e -> {
                dialog.setX(owner.getX() + (owner.getWidth() - dialog.getWidth()) / 2);
                dialog.setY(owner.getY() + (owner.getHeight() - dialog.getHeight()) / 2);
            });
        } else {
            dialog.centerOnScreen();
        }

        dialog.showAndWait();
    }
}
