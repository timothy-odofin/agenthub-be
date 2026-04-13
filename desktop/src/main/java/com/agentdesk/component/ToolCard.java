package com.agentdesk.component;

import com.agentdesk.model.McpTool;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.Label;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.StackPane;
import javafx.scene.layout.VBox;
import org.kordamp.ikonli.javafx.FontIcon;

public class ToolCard extends HBox {

    public ToolCard(McpTool tool) {
        getStyleClass().add("tool-card");
        setAlignment(Pos.CENTER_LEFT);
        setSpacing(12);
        setPadding(new Insets(10, 14, 10, 14));

        FontIcon toolIcon = new FontIcon(tool.getIcon());
        toolIcon.setIconSize(16);
        toolIcon.getStyleClass().add("tool-card-icon");

        StackPane iconContainer = new StackPane(toolIcon);
        iconContainer.getStyleClass().add("tool-card-icon-container");
        iconContainer.setMinSize(30, 30);
        iconContainer.setMaxSize(30, 30);

        Label nameLabel = new Label(tool.getName());
        nameLabel.getStyleClass().add("tool-card-name");

        Label descLabel = new Label(tool.getDescription());
        descLabel.getStyleClass().add("tool-card-desc");
        descLabel.setWrapText(false);

        VBox textBox = new VBox(2, nameLabel, descLabel);
        textBox.setAlignment(Pos.CENTER_LEFT);
        HBox.setHgrow(textBox, Priority.ALWAYS);

        getChildren().addAll(iconContainer, textBox);
    }

    public boolean matchesFilter(String filter) {
        if (filter == null || filter.isBlank()) return true;
        String lower = filter.toLowerCase();
        for (var child : ((VBox) getChildren().get(1)).getChildren()) {
            if (child instanceof Label label && label.getText().toLowerCase().contains(lower)) {
                return true;
            }
        }
        return false;
    }
}
