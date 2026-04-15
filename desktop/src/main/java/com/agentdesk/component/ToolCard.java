package com.agentdesk.component;

import com.agentdesk.model.McpTool;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.Label;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.VBox;

public class ToolCard extends HBox {

    public ToolCard(McpTool tool) {
        getStyleClass().add("tool-card");
        setAlignment(Pos.CENTER_LEFT);
        setSpacing(12);
        setPadding(new Insets(10, 14, 10, 14));

        Label nameLabel = new Label(tool.getName());
        nameLabel.getStyleClass().add("tool-card-name");

        Label descLabel = new Label(tool.getDescription());
        descLabel.getStyleClass().add("tool-card-desc");
        descLabel.setWrapText(true);

        VBox textBox = new VBox(2, nameLabel, descLabel);
        textBox.setAlignment(Pos.CENTER_LEFT);
        HBox.setHgrow(textBox, Priority.ALWAYS);

        getChildren().add(textBox);
    }

    public boolean matchesFilter(String filter) {
        if (filter == null || filter.isBlank()) return true;
        String lower = filter.toLowerCase();
        for (var child : ((VBox) getChildren().get(0)).getChildren()) {
            if (child instanceof Label label && label.getText().toLowerCase().contains(lower)) {
                return true;
            }
        }
        return false;
    }
}
