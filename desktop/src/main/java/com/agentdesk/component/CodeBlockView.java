package com.agentdesk.component;

import javafx.animation.KeyFrame;
import javafx.animation.Timeline;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.ScrollPane;
import javafx.scene.control.TextArea;
import javafx.scene.input.Clipboard;
import javafx.scene.input.ClipboardContent;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.Region;
import javafx.scene.layout.VBox;
import javafx.util.Duration;
import org.kordamp.ikonli.feather.Feather;
import org.kordamp.ikonli.javafx.FontIcon;

public class CodeBlockView extends VBox {

    private final String code;

    public CodeBlockView(String code, String language) {
        this.code = code != null ? code.stripTrailing() : "";
        getStyleClass().add("md-code-block");

        HBox header = new HBox(8);
        header.getStyleClass().add("md-code-header");
        header.setAlignment(Pos.CENTER_LEFT);
        header.setPadding(new Insets(6, 12, 6, 14));

        Label langLabel = new Label(language != null && !language.isBlank() ? language : "code");
        langLabel.getStyleClass().add("md-code-language");

        Region spacer = new Region();
        HBox.setHgrow(spacer, Priority.ALWAYS);

        FontIcon copyIcon = new FontIcon(Feather.COPY);
        copyIcon.setIconSize(13);
        copyIcon.getStyleClass().add("md-code-copy-icon");

        Button copyBtn = new Button("Copy");
        copyBtn.setGraphic(copyIcon);
        copyBtn.getStyleClass().add("md-code-copy");
        copyBtn.setOnAction(e -> {
            ClipboardContent content = new ClipboardContent();
            content.putString(this.code);
            Clipboard.getSystemClipboard().setContent(content);

            FontIcon checkIcon = new FontIcon(Feather.CHECK);
            checkIcon.setIconSize(13);
            checkIcon.getStyleClass().add("md-code-copy-icon");
            copyBtn.setGraphic(checkIcon);
            copyBtn.setText("Copied!");

            new Timeline(new KeyFrame(Duration.seconds(2), ev -> {
                FontIcon resetIcon = new FontIcon(Feather.COPY);
                resetIcon.setIconSize(13);
                resetIcon.getStyleClass().add("md-code-copy-icon");
                copyBtn.setGraphic(resetIcon);
                copyBtn.setText("Copy");
            })).play();
        });

        header.getChildren().addAll(langLabel, spacer, copyBtn);

        TextArea codeArea = new TextArea(this.code);
        codeArea.getStyleClass().add("md-code-area");
        codeArea.setEditable(false);
        codeArea.setWrapText(false);

        int lineCount = this.code.split("\n", -1).length;
        double estimatedHeight = Math.min(lineCount * 20 + 24, 400);
        codeArea.setPrefHeight(estimatedHeight);
        codeArea.setMaxHeight(400);

        ScrollPane scrollPane = new ScrollPane(codeArea);
        scrollPane.getStyleClass().add("md-code-scroll");
        scrollPane.setFitToWidth(true);
        scrollPane.setFitToHeight(true);
        scrollPane.setMaxHeight(400);
        VBox.setVgrow(scrollPane, Priority.ALWAYS);

        getChildren().addAll(header, scrollPane);
    }
}
