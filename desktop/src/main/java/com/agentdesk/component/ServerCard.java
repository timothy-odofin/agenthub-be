package com.agentdesk.component;

import com.agentdesk.model.McpServer;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.Tooltip;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.Region;
import javafx.scene.layout.StackPane;
import javafx.scene.layout.VBox;
import org.kordamp.ikonli.feather.Feather;
import org.kordamp.ikonli.javafx.FontIcon;

import java.util.function.Consumer;

public class ServerCard extends HBox {

    private final McpServer server;
    private boolean selected;
    private final FontIcon checkIcon;
    private final StackPane checkBadge;

    public ServerCard(McpServer server, Consumer<McpServer> onInspect) {
        this.server = server;
        this.selected = false;

        getStyleClass().add("server-card");
        setAlignment(Pos.CENTER_LEFT);
        setSpacing(12);
        setPadding(new Insets(12, 14, 12, 14));
        setPrefWidth(200);
        setMaxWidth(Double.MAX_VALUE);

        FontIcon serverIcon = new FontIcon(server.getIcon());
        serverIcon.setIconSize(20);
        serverIcon.getStyleClass().add("server-card-icon");

        StackPane iconContainer = new StackPane(serverIcon);
        iconContainer.getStyleClass().add("server-card-icon-container");
        iconContainer.setMinSize(36, 36);
        iconContainer.setMaxSize(36, 36);

        Label nameLabel = new Label(server.getName());
        nameLabel.getStyleClass().add("server-card-name");

        Label descLabel = new Label(server.getDescription());
        descLabel.getStyleClass().add("server-card-desc");
        descLabel.setWrapText(true);

        Label toolCountLabel = new Label(server.getToolCount() + " tools");
        toolCountLabel.getStyleClass().add("server-card-tool-count");

        VBox textBox = new VBox(2, nameLabel, descLabel, toolCountLabel);
        textBox.setAlignment(Pos.CENTER_LEFT);
        HBox.setHgrow(textBox, Priority.ALWAYS);

        Region spacer = new Region();
        HBox.setHgrow(spacer, Priority.SOMETIMES);

        VBox rightBox = new VBox(4);
        rightBox.setAlignment(Pos.CENTER_RIGHT);

        checkIcon = new FontIcon(Feather.CHECK);
        checkIcon.setIconSize(12);
        checkIcon.getStyleClass().add("server-card-check-icon");

        checkBadge = new StackPane(checkIcon);
        checkBadge.getStyleClass().add("server-card-check");
        checkBadge.setMinSize(22, 22);
        checkBadge.setMaxSize(22, 22);
        checkBadge.setVisible(false);
        checkBadge.setManaged(false);

        if (onInspect != null) {
            FontIcon eyeIcon = new FontIcon(Feather.EYE);
            eyeIcon.setIconSize(14);
            eyeIcon.getStyleClass().add("server-card-action-icon");

            Button inspectBtn = new Button();
            inspectBtn.setGraphic(eyeIcon);
            inspectBtn.getStyleClass().add("server-card-action");
            inspectBtn.setTooltip(new Tooltip("View tools"));
            inspectBtn.setOnAction(e -> {
                e.consume();
                onInspect.accept(server);
            });
            rightBox.getChildren().addAll(checkBadge, inspectBtn);
        } else {
            rightBox.getChildren().add(checkBadge);
        }

        setOnMouseClicked(e -> {
            if (e.getTarget() instanceof Button) return;
            toggleSelected();
        });

        getChildren().addAll(iconContainer, textBox, rightBox);
    }

    public void toggleSelected() {
        setSelected(!selected);
    }

    public void setSelected(boolean selected) {
        this.selected = selected;
        checkBadge.setVisible(selected);
        checkBadge.setManaged(selected);
        if (selected) {
            if (!getStyleClass().contains("server-card-selected")) {
                getStyleClass().add("server-card-selected");
            }
        } else {
            getStyleClass().remove("server-card-selected");
        }
    }

    public boolean isSelected() { return selected; }
    public McpServer getServer() { return server; }

    public boolean matchesFilter(String filter) {
        if (filter == null || filter.isBlank()) return true;
        String lower = filter.toLowerCase();
        return server.getName().toLowerCase().contains(lower)
                || server.getDescription().toLowerCase().contains(lower);
    }
}
