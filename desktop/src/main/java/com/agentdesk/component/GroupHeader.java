package com.agentdesk.component;

import javafx.geometry.Pos;
import javafx.scene.control.Label;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.Region;

public class GroupHeader extends HBox {

    private final Label titleLabel;
    private final Label countLabel;

    public GroupHeader(String title, int itemCount) {
        getStyleClass().add("picker-group-header");
        setAlignment(Pos.CENTER_LEFT);
        setSpacing(8);

        titleLabel = new Label(title.toUpperCase());
        titleLabel.getStyleClass().add("picker-group-title");

        Region spacer = new Region();
        HBox.setHgrow(spacer, Priority.ALWAYS);

        countLabel = new Label(String.valueOf(itemCount));
        countLabel.getStyleClass().add("picker-group-count");

        getChildren().addAll(titleLabel, spacer, countLabel);
    }

    public void updateCount(int visibleCount) {
        countLabel.setText(String.valueOf(visibleCount));
    }

    public String getTitle() {
        return titleLabel.getText();
    }
}
