package com.agentdesk.component;

import javafx.geometry.Pos;
import javafx.scene.Node;
import javafx.scene.control.Label;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.VBox;

public class ListItemView extends HBox {

    private final VBox contentBox;

    public ListItemView(String bullet) {
        getStyleClass().add("md-list-item");
        setAlignment(Pos.TOP_LEFT);
        setSpacing(6);

        Label bulletLabel = new Label(bullet);
        bulletLabel.getStyleClass().add("md-list-bullet");
        bulletLabel.setMinWidth(20);
        bulletLabel.setMaxWidth(20);
        bulletLabel.setAlignment(Pos.TOP_RIGHT);

        contentBox = new VBox(2);
        contentBox.setAlignment(Pos.TOP_LEFT);
        HBox.setHgrow(contentBox, Priority.ALWAYS);

        getChildren().addAll(bulletLabel, contentBox);
    }

    public void addContent(Node node) {
        contentBox.getChildren().add(node);
    }

    public VBox getContentBox() {
        return contentBox;
    }
}
