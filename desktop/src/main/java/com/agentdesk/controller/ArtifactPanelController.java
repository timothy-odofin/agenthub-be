package com.agentdesk.controller;

import com.agentdesk.model.Artifact;
import javafx.animation.KeyFrame;
import javafx.animation.Timeline;
import javafx.fxml.FXML;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.ScrollPane;
import javafx.scene.control.TextArea;
import javafx.scene.input.Clipboard;
import javafx.scene.input.ClipboardContent;
import javafx.scene.layout.StackPane;
import javafx.scene.layout.VBox;
import javafx.scene.web.WebView;
import javafx.stage.FileChooser;
import javafx.util.Duration;
import org.kordamp.ikonli.feather.Feather;
import org.kordamp.ikonli.javafx.FontIcon;
import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;

@Component
@Scope("prototype")
public class ArtifactPanelController {

    @FXML private Label artifactTypeIcon;
    @FXML private Label artifactTitle;
    @FXML private Label artifactSubtitle;
    @FXML private Button closeBtn;
    @FXML private StackPane contentStack;

    @FXML private ScrollPane codeScrollPane;
    @FXML private TextArea codeArea;
    @FXML private WebView webView;
    @FXML private ScrollPane docScrollPane;
    @FXML private Label docContent;
    @FXML private VBox downloadCard;
    @FXML private Label downloadIcon;
    @FXML private Label downloadFilename;
    @FXML private Label downloadSize;

    @FXML private Button copyArtifactBtn;
    @FXML private Button downloadArtifactBtn;
    @FXML private Label footerStatus;

    private Artifact currentArtifact;
    private Runnable onClose;

    @FXML
    public void initialize() {
        FontIcon closeIcon = new FontIcon(Feather.X);
        closeIcon.setIconSize(16);
        closeIcon.getStyleClass().add("artifact-close-icon");
        closeBtn.setGraphic(closeIcon);

        FontIcon copyIcon = new FontIcon(Feather.COPY);
        copyIcon.setIconSize(14);
        copyIcon.getStyleClass().add("artifact-action-icon");
        copyArtifactBtn.setGraphic(copyIcon);

        FontIcon dlIcon = new FontIcon(Feather.DOWNLOAD);
        dlIcon.setIconSize(14);
        dlIcon.getStyleClass().add("artifact-action-icon");
        downloadArtifactBtn.setGraphic(dlIcon);
    }

    public void showArtifact(Artifact artifact) {
        this.currentArtifact = artifact;
        artifactTitle.setText(artifact.getTitle());
        hideAllViews();

        switch (artifact.getType()) {
            case CODE -> showCodeView(artifact);
            case HTML -> showHtmlView(artifact);
            case DOCUMENT -> showDocumentView(artifact);
            case DOWNLOAD -> showDownloadView(artifact);
        }
    }

    private void showCodeView(Artifact artifact) {
        FontIcon icon = new FontIcon(Feather.CODE);
        icon.setIconSize(16);
        icon.getStyleClass().add("artifact-type-feather-icon");
        artifactTypeIcon.setGraphic(icon);

        String lang = artifact.getLanguage() != null ? artifact.getLanguage() : "Code";
        artifactSubtitle.setText(lang.substring(0, 1).toUpperCase() + lang.substring(1));

        codeArea.setText(artifact.getContent());
        codeScrollPane.setVisible(true);
        codeScrollPane.setManaged(true);
    }

    private void showHtmlView(Artifact artifact) {
        FontIcon icon = new FontIcon(Feather.GLOBE);
        icon.setIconSize(16);
        icon.getStyleClass().add("artifact-type-feather-icon");
        artifactTypeIcon.setGraphic(icon);
        artifactSubtitle.setText("HTML Preview");

        webView.getEngine().loadContent(artifact.getContent());
        webView.setVisible(true);
        webView.setManaged(true);
    }

    private void showDocumentView(Artifact artifact) {
        FontIcon icon = new FontIcon(Feather.FILE_TEXT);
        icon.setIconSize(16);
        icon.getStyleClass().add("artifact-type-feather-icon");
        artifactTypeIcon.setGraphic(icon);
        artifactSubtitle.setText("Document");

        docContent.setText(artifact.getContent());
        docScrollPane.setVisible(true);
        docScrollPane.setManaged(true);
    }

    private void showDownloadView(Artifact artifact) {
        FontIcon icon = new FontIcon(Feather.DOWNLOAD);
        icon.setIconSize(16);
        icon.getStyleClass().add("artifact-type-feather-icon");
        artifactTypeIcon.setGraphic(icon);
        artifactSubtitle.setText("File");

        FontIcon fileIcon = new FontIcon(Feather.FILE);
        fileIcon.setIconSize(48);
        fileIcon.getStyleClass().add("artifact-download-file-icon");
        downloadIcon.setGraphic(fileIcon);

        downloadFilename.setText(artifact.getFilename() != null ? artifact.getFilename() : "file.txt");
        int size = artifact.getContent() != null ? artifact.getContent().length() : 0;
        downloadSize.setText(formatSize(size));

        downloadCard.setVisible(true);
        downloadCard.setManaged(true);
    }

    private void hideAllViews() {
        codeScrollPane.setVisible(false);
        codeScrollPane.setManaged(false);
        webView.setVisible(false);
        webView.setManaged(false);
        docScrollPane.setVisible(false);
        docScrollPane.setManaged(false);
        downloadCard.setVisible(false);
        downloadCard.setManaged(false);
        footerStatus.setText("");
    }

    @FXML
    private void handleClose() {
        if (onClose != null) onClose.run();
    }

    @FXML
    private void handleCopy() {
        if (currentArtifact == null || currentArtifact.getContent() == null) return;

        ClipboardContent cc = new ClipboardContent();
        cc.putString(currentArtifact.getContent());
        Clipboard.getSystemClipboard().setContent(cc);

        footerStatus.setText("Copied!");
        Timeline reset = new Timeline(new KeyFrame(Duration.seconds(2), e -> footerStatus.setText("")));
        reset.play();
    }

    @FXML
    private void handleDownload() {
        if (currentArtifact == null || currentArtifact.getContent() == null) return;

        FileChooser chooser = new FileChooser();
        String fname = currentArtifact.getFilename();
        if (fname == null || fname.isBlank()) {
            fname = switch (currentArtifact.getType()) {
                case CODE -> "code." + (currentArtifact.getLanguage() != null ? currentArtifact.getLanguage() : "txt");
                case HTML -> "preview.html";
                case DOCUMENT -> "document.txt";
                case DOWNLOAD -> "file.txt";
            };
        }
        chooser.setInitialFileName(fname);

        File file = chooser.showSaveDialog(contentStack.getScene().getWindow());
        if (file != null) {
            try {
                Files.writeString(file.toPath(), currentArtifact.getContent());
                footerStatus.setText("Saved!");
                Timeline reset = new Timeline(new KeyFrame(Duration.seconds(2), e -> footerStatus.setText("")));
                reset.play();
            } catch (IOException ex) {
                footerStatus.setText("Save failed");
            }
        }
    }

    public void setOnClose(Runnable handler) {
        this.onClose = handler;
    }

    private String formatSize(int bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return String.format("%.1f KB", bytes / 1024.0);
        return String.format("%.1f MB", bytes / (1024.0 * 1024));
    }
}
