package com.agentdesk.component;

import javafx.animation.KeyFrame;
import javafx.animation.Timeline;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.input.Clipboard;
import javafx.scene.input.ClipboardContent;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Region;
import javafx.scene.layout.StackPane;
import javafx.scene.layout.VBox;
import javafx.stage.Modality;
import javafx.stage.Stage;
import javafx.stage.StageStyle;
import javafx.stage.Window;
import javafx.util.Duration;
import org.kordamp.ikonli.feather.Feather;
import org.kordamp.ikonli.javafx.FontIcon;

import java.awt.Desktop;
import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

public class ShareDialog {

    public static void show(Window owner, String conversationTitle) {
        Stage dialog = new Stage(StageStyle.TRANSPARENT);
        dialog.initModality(Modality.WINDOW_MODAL);
        dialog.initOwner(owner);

        String shareUrl = "https://agentdesk.app/share/" + conversationTitle.hashCode();
        String shareText = "Check out this conversation: " + conversationTitle;

        VBox card = new VBox(10);
        card.getStyleClass().addAll("dialog-card", "share-dialog-card");
        card.setPadding(new Insets(18, 22, 18, 22));
        card.setMaxWidth(380);
        card.setMaxSize(Region.USE_PREF_SIZE, Region.USE_PREF_SIZE);

        HBox header = new HBox(12);
        header.setAlignment(Pos.CENTER_LEFT);

        FontIcon shareIcon = new FontIcon(Feather.SHARE_2);
        shareIcon.setIconSize(20);
        shareIcon.getStyleClass().add("dialog-header-icon");

        Label title = new Label("Share conversation");
        title.getStyleClass().add("dialog-title");

        Region spacer = new Region();
        spacer.setMaxWidth(Double.MAX_VALUE);
        HBox.setHgrow(spacer, javafx.scene.layout.Priority.ALWAYS);

        Button closeBtn = new Button();
        FontIcon closeIcon = new FontIcon(Feather.X);
        closeIcon.setIconSize(16);
        closeIcon.getStyleClass().add("dialog-header-icon");
        closeBtn.setGraphic(closeIcon);
        closeBtn.getStyleClass().add("artifact-close-btn");
        closeBtn.setOnAction(e -> dialog.close());

        header.getChildren().addAll(shareIcon, title, spacer, closeBtn);

        Label subtitle = new Label("Share \"" + conversationTitle + "\" via:");
        subtitle.getStyleClass().add("dialog-subtitle");
        subtitle.setWrapText(true);

        HBox row1 = new HBox(8);
        row1.setAlignment(Pos.CENTER);
        row1.getChildren().addAll(
            createOption("🔗", "Copy link", () -> {
                ClipboardContent content = new ClipboardContent();
                content.putString(shareUrl);
                Clipboard.getSystemClipboard().setContent(content);
                subtitle.setText("Link copied to clipboard!");
                new Timeline(new KeyFrame(Duration.seconds(2),
                    ev -> subtitle.setText("Share \"" + conversationTitle + "\" via:"))).play();
            }),
            createOption("📧", "Email", () -> {
                openUrl("mailto:?subject=" + encode(shareText) + "&body=" + encode(shareUrl));
                dialog.close();
            }),
            createOption("💬", "WhatsApp", () -> {
                openUrl("https://wa.me/?text=" + encode(shareText + " " + shareUrl));
                dialog.close();
            })
        );

        HBox row2 = new HBox(8);
        row2.setAlignment(Pos.CENTER);
        row2.getChildren().addAll(
            createOption("📋", "Teams", () -> {
                openUrl("https://teams.microsoft.com/share?msgText=" + encode(shareText + " " + shareUrl));
                dialog.close();
            }),
            createOption("💼", "Slack", () -> {
                ClipboardContent content = new ClipboardContent();
                content.putString(shareUrl);
                Clipboard.getSystemClipboard().setContent(content);
                subtitle.setText("Link copied! Paste in Slack.");
                new Timeline(new KeyFrame(Duration.seconds(2),
                    ev -> subtitle.setText("Share \"" + conversationTitle + "\" via:"))).play();
            })
        );

        VBox optionsBlock = new VBox(8);
        optionsBlock.setAlignment(Pos.CENTER);
        optionsBlock.setMaxHeight(Region.USE_PREF_SIZE);
        optionsBlock.getChildren().addAll(row1, row2);

        card.getChildren().addAll(header, subtitle, optionsBlock);

        StackPane backdrop = new StackPane(card);
        backdrop.getStyleClass().add("dialog-backdrop");
        backdrop.setAlignment(Pos.CENTER);
        backdrop.setOnMouseClicked(e -> {
            if (e.getTarget() == backdrop) dialog.close();
        });

        Scene scene = new Scene(backdrop);
        scene.setFill(null);

        if (owner != null && owner.getScene() != null) {
            scene.getStylesheets().addAll(owner.getScene().getStylesheets());
        }

        dialog.setScene(scene);

        if (owner != null) {
            double ownerX = owner.getX();
            double ownerY = owner.getY();
            double ownerW = owner.getWidth();
            double ownerH = owner.getHeight();
            dialog.setX(ownerX);
            dialog.setY(ownerY);
            dialog.setWidth(ownerW);
            dialog.setHeight(ownerH);
        } else {
            dialog.sizeToScene();
        }

        dialog.show();
    }

    private static VBox createOption(String icon, String label, Runnable action) {
        VBox card = new VBox(4);
        card.getStyleClass().add("share-option-card");
        card.setAlignment(Pos.CENTER);
        card.setPadding(new Insets(10, 12, 10, 12));
        card.setMinWidth(Region.USE_PREF_SIZE);
        card.setPrefWidth(100);
        card.setMaxWidth(110);
        card.setMaxHeight(Region.USE_PREF_SIZE);

        Label iconLabel = new Label(icon);
        iconLabel.getStyleClass().add("share-option-icon");

        Label nameLabel = new Label(label);
        nameLabel.getStyleClass().add("share-option-label");

        card.getChildren().addAll(iconLabel, nameLabel);
        card.setOnMouseClicked(e -> action.run());
        return card;
    }

    private static String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }

    private static void openUrl(String url) {
        try {
            if (Desktop.isDesktopSupported() && Desktop.getDesktop().isSupported(Desktop.Action.BROWSE)) {
                Desktop.getDesktop().browse(new URI(url));
            }
        } catch (Exception ignored) {
        }
    }
}
