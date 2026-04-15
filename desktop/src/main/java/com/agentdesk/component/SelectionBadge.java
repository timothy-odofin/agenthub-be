package com.agentdesk.component;

import javafx.geometry.Pos;
import javafx.scene.control.Label;
import javafx.scene.layout.StackPane;

public class SelectionBadge extends StackPane {

    private final Label countLabel;

    public SelectionBadge() {
        getStyleClass().add("selection-badge");
        setAlignment(Pos.CENTER);
        setMinSize(18, 18);
        setMaxSize(18, 18);
        setPickOnBounds(false);
        setMouseTransparent(true);

        countLabel = new Label("0");
        countLabel.getStyleClass().add("selection-badge-label");

        getChildren().add(countLabel);

        setVisible(false);
        setManaged(false);
    }

    public void setCount(int count) {
        countLabel.setText(String.valueOf(count));
        setVisible(count > 0);
        setManaged(count > 0);
    }

    public int getCount() {
        try {
            return Integer.parseInt(countLabel.getText());
        } catch (NumberFormatException e) {
            return 0;
        }
    }
}
