package com.agentdesk.component;

import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.Button;
import javafx.scene.control.TextField;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.StackPane;
import org.kordamp.ikonli.feather.Feather;
import org.kordamp.ikonli.javafx.FontIcon;

import java.util.function.Consumer;

public class SearchField extends HBox {

    private final TextField textField;
    private final Button clearButton;

    public SearchField(String placeholder, Consumer<String> onFilterChanged) {
        getStyleClass().add("picker-search-field");
        setAlignment(Pos.CENTER_LEFT);
        setSpacing(0);

        FontIcon searchIcon = new FontIcon(Feather.SEARCH);
        searchIcon.setIconSize(14);
        searchIcon.getStyleClass().add("picker-search-icon");

        StackPane iconWrapper = new StackPane(searchIcon);
        iconWrapper.setPadding(new Insets(0, 8, 0, 12));

        textField = new TextField();
        textField.setPromptText(placeholder);
        textField.getStyleClass().add("picker-search-input");
        HBox.setHgrow(textField, Priority.ALWAYS);

        FontIcon clearIcon = new FontIcon(Feather.X);
        clearIcon.setIconSize(12);
        clearIcon.getStyleClass().add("picker-search-clear-icon");

        clearButton = new Button();
        clearButton.setGraphic(clearIcon);
        clearButton.getStyleClass().add("picker-search-clear");
        clearButton.setVisible(false);
        clearButton.setManaged(false);
        clearButton.setOnAction(e -> {
            textField.clear();
            textField.requestFocus();
        });

        textField.textProperty().addListener((obs, old, text) -> {
            boolean hasText = text != null && !text.isEmpty();
            clearButton.setVisible(hasText);
            clearButton.setManaged(hasText);
            if (onFilterChanged != null) {
                onFilterChanged.accept(text != null ? text : "");
            }
        });

        getChildren().addAll(iconWrapper, textField, clearButton);
    }

    public String getText() {
        return textField.getText();
    }

    public void clear() {
        textField.clear();
    }

    public void requestSearchFocus() {
        textField.requestFocus();
    }
}
