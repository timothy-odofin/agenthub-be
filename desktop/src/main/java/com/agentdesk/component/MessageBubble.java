package com.agentdesk.component;

import com.agentdesk.model.ChatMessage;
import javafx.animation.Animation;
import javafx.animation.KeyFrame;
import javafx.animation.Timeline;
import javafx.fxml.FXMLLoader;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Node;
import javafx.scene.control.Button;
import javafx.scene.control.TextArea;
import javafx.scene.input.Clipboard;
import javafx.scene.input.ClipboardContent;
import javafx.scene.input.KeyCode;
import javafx.scene.layout.HBox;
import javafx.scene.layout.StackPane;
import javafx.scene.layout.VBox;
import javafx.scene.text.Text;
import javafx.scene.text.TextFlow;
import javafx.util.Duration;
import org.kordamp.ikonli.feather.Feather;
import org.kordamp.ikonli.javafx.FontIcon;

import java.io.IOException;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

public class MessageBubble {

    private final Node root;
    private final Text messageText;
    private HBox typingIndicator;
    private HBox actionButtons;
    private Timeline typingAnimation;
    private Consumer<String> onRetry;
    private BiConsumer<String, String> onEdit;

    private TextFlow textFlow;
    private VBox contentContainer;
    private String rawText = "";
    private boolean isEditing = false;

    private MessageBubble(Node root, Text messageText, HBox typingIndicator, HBox actionButtons) {
        this.root = root;
        this.messageText = messageText;
        this.typingIndicator = typingIndicator;
        this.actionButtons = actionButtons;
    }

    public static MessageBubble createUserBubble(ChatMessage message) {
        try {
            FXMLLoader loader = new FXMLLoader(
                MessageBubble.class.getResource("/fxml/user-message.fxml")
            );
            Node root = loader.load();
            Text text = (Text) root.lookup("#messageText");
            HBox actions = (HBox) root.lookup("#userActionButtons");
            TextFlow flow = (TextFlow) root.lookup("#textFlow");

            if (text != null) {
                text.setText(message.getContent());
            }

            MessageBubble bubble = new MessageBubble(root, text, null, actions);
            bubble.textFlow = flow;
            bubble.wireUserActionButtons();
            return bubble;
        } catch (IOException e) {
            throw new RuntimeException("Failed to load user-message.fxml", e);
        }
    }

    public static MessageBubble createAssistantBubble(ChatMessage message) {
        try {
            FXMLLoader loader = new FXMLLoader(
                MessageBubble.class.getResource("/fxml/assistant-message.fxml")
            );
            Node root = loader.load();
            Text text = (Text) root.lookup("#messageText");
            HBox typing = (HBox) root.lookup("#typingIndicator");
            HBox actions = (HBox) root.lookup("#actionButtons");
            VBox container = (VBox) root.lookup("#contentContainer");

            if (text != null) {
                text.setText(message.getContent());
            }

            MessageBubble bubble = new MessageBubble(root, text, typing, actions);
            bubble.contentContainer = container;
            bubble.rawText = message.getContent() != null ? message.getContent() : "";
            bubble.wireAssistantActionButtons();
            return bubble;
        } catch (IOException e) {
            throw new RuntimeException("Failed to load assistant-message.fxml", e);
        }
    }

    private FontIcon createIcon(Feather icon, int size) {
        FontIcon fi = new FontIcon(icon);
        fi.setIconSize(size);
        fi.getStyleClass().add("msg-action-icon");
        return fi;
    }

    private void wireUserActionButtons() {
        if (actionButtons == null) return;

        Button editBtn = (Button) actionButtons.lookup("#editBtn");
        Button retryBtn = (Button) actionButtons.lookup("#retryUserBtn");

        if (editBtn != null) {
            editBtn.setGraphic(createIcon(Feather.EDIT_2, 14));
            editBtn.setOnAction(e -> enterEditMode());
        }

        if (retryBtn != null) {
            retryBtn.setGraphic(createIcon(Feather.REFRESH_CW, 14));
            retryBtn.setOnAction(e -> {
                if (onRetry != null && messageText != null) {
                    onRetry.accept(messageText.getText());
                }
            });
        }
    }

    private void enterEditMode() {
        if (isEditing || textFlow == null || messageText == null) return;
        if (!(root instanceof VBox rootBox)) return;

        isEditing = true;
        String originalText = messageText.getText();

        textFlow.setVisible(false);
        textFlow.setManaged(false);
        if (actionButtons != null) {
            actionButtons.setVisible(false);
            actionButtons.setManaged(false);
        }

        TextArea editArea = new TextArea(originalText);
        editArea.getStyleClass().add("inline-edit-area");
        editArea.setWrapText(true);
        editArea.setPrefRowCount(Math.min(originalText.split("\n", -1).length + 1, 8));
        editArea.setMaxWidth(560);

        FontIcon sendIcon = new FontIcon(Feather.ARROW_UP);
        sendIcon.setIconSize(14);
        sendIcon.getStyleClass().add("inline-edit-send-icon");

        Button saveBtn = new Button();
        saveBtn.setGraphic(sendIcon);
        saveBtn.getStyleClass().addAll("inline-edit-btn", "inline-edit-btn-save");

        Button cancelBtn = new Button("Cancel");
        cancelBtn.getStyleClass().addAll("inline-edit-btn", "inline-edit-btn-cancel");

        HBox btnRow = new HBox(8, cancelBtn, saveBtn);
        btnRow.setAlignment(Pos.CENTER_RIGHT);
        btnRow.setMaxWidth(560);

        VBox editContainer = new VBox(8, editArea, btnRow);
        editContainer.setAlignment(Pos.TOP_RIGHT);
        editContainer.getStyleClass().add("inline-edit-container");
        editContainer.setMaxWidth(560);

        int insertIdx = rootBox.getChildren().indexOf(textFlow);
        rootBox.getChildren().add(insertIdx + 1, editContainer);

        editArea.requestFocus();
        editArea.positionCaret(originalText.length());

        saveBtn.setOnAction(ev -> {
            String newText = editArea.getText().trim();
            exitEditMode(rootBox, editContainer);
            if (!newText.isEmpty() && !newText.equals(originalText) && onEdit != null) {
                onEdit.accept(originalText, newText);
            }
        });

        cancelBtn.setOnAction(ev -> exitEditMode(rootBox, editContainer));

        editArea.addEventFilter(javafx.scene.input.KeyEvent.KEY_PRESSED, ev -> {
            if (ev.getCode() == KeyCode.ESCAPE) {
                ev.consume();
                exitEditMode(rootBox, editContainer);
            } else if (ev.getCode() == KeyCode.ENTER && !ev.isShiftDown()) {
                ev.consume();
                String newText = editArea.getText().trim();
                exitEditMode(rootBox, editContainer);
                if (!newText.isEmpty() && !newText.equals(originalText) && onEdit != null) {
                    onEdit.accept(originalText, newText);
                }
            }
        });
    }

    private void exitEditMode(VBox rootBox, VBox editContainer) {
        isEditing = false;
        rootBox.getChildren().remove(editContainer);

        textFlow.setVisible(true);
        textFlow.setManaged(true);
        if (actionButtons != null) {
            actionButtons.setVisible(true);
            actionButtons.setManaged(true);
        }
    }

    private void wireAssistantActionButtons() {
        if (actionButtons == null) return;

        Button copyBtn = (Button) actionButtons.lookup("#copyBtn");
        Button thumbsUpBtn = (Button) actionButtons.lookup("#thumbsUpBtn");
        Button thumbsDownBtn = (Button) actionButtons.lookup("#thumbsDownBtn");
        Button retryBtn = (Button) actionButtons.lookup("#retryBtn");

        if (copyBtn != null) {
            copyBtn.setGraphic(createIcon(Feather.COPY, 14));
            copyBtn.setOnAction(e -> {
                if (rawText != null && !rawText.isEmpty()) {
                    ClipboardContent content = new ClipboardContent();
                    content.putString(rawText);
                    Clipboard.getSystemClipboard().setContent(content);
                    copyBtn.setGraphic(createIcon(Feather.CHECK, 14));
                    Timeline reset = new Timeline(new KeyFrame(
                        Duration.seconds(2), ev -> copyBtn.setGraphic(createIcon(Feather.COPY, 14))
                    ));
                    reset.play();
                }
            });
        }

        if (thumbsUpBtn != null) {
            thumbsUpBtn.setGraphic(createIcon(Feather.THUMBS_UP, 14));
            thumbsUpBtn.setOnAction(e -> {
                thumbsUpBtn.getStyleClass().add("msg-action-active");
                if (thumbsDownBtn != null) thumbsDownBtn.getStyleClass().remove("msg-action-active");
            });
        }

        if (thumbsDownBtn != null) {
            thumbsDownBtn.setGraphic(createIcon(Feather.THUMBS_DOWN, 14));
            thumbsDownBtn.setOnAction(e -> {
                thumbsDownBtn.getStyleClass().add("msg-action-active");
                if (thumbsUpBtn != null) thumbsUpBtn.getStyleClass().remove("msg-action-active");
            });
        }

        if (retryBtn != null) {
            retryBtn.setGraphic(createIcon(Feather.REFRESH_CW, 14));
            retryBtn.setOnAction(e -> {
                if (onRetry != null && messageText != null) {
                    onRetry.accept(messageText.getText());
                }
            });
        }
    }

    public void showActionButtons(boolean show) {
        if (actionButtons == null) return;
        actionButtons.setVisible(show);
        actionButtons.setManaged(show);
    }

    public void setOnRetry(Consumer<String> handler) {
        this.onRetry = handler;
    }

    public void setOnEdit(BiConsumer<String, String> handler) {
        this.onEdit = handler;
    }

    public void showTypingIndicator(boolean show) {
        if (typingIndicator == null) return;
        typingIndicator.setVisible(show);
        typingIndicator.setManaged(show);

        if (show) {
            startTypingAnimation();
            showActionButtons(false);
        } else {
            stopTypingAnimation();
        }
    }

    private void startTypingAnimation() {
        if (typingAnimation != null) return;
        if (typingIndicator == null) return;

        var dots = typingIndicator.getChildren();
        typingAnimation = new Timeline();
        typingAnimation.setCycleCount(Animation.INDEFINITE);

        for (int i = 0; i < dots.size(); i++) {
            Node dot = dots.get(i);
            int delay = i * 200;
            typingAnimation.getKeyFrames().addAll(
                new KeyFrame(Duration.millis(delay), e -> dot.setOpacity(0.3)),
                new KeyFrame(Duration.millis(delay + 300), e -> dot.setOpacity(1.0)),
                new KeyFrame(Duration.millis(delay + 600), e -> dot.setOpacity(0.3))
            );
        }
        typingAnimation.getKeyFrames().add(new KeyFrame(Duration.millis(900)));
        typingAnimation.play();
    }

    private void stopTypingAnimation() {
        if (typingAnimation != null) {
            typingAnimation.stop();
            typingAnimation = null;
        }
    }

    public void updateText(String newContent) {
        rawText = newContent != null ? newContent : "";
        if (messageText != null) {
            messageText.setText(rawText);
        }
    }

    public void renderMarkdown() {
        if (contentContainer == null || rawText == null || rawText.isBlank()) return;

        try {
            VBox rendered = MarkdownRenderer.render(rawText);
            contentContainer.getChildren().clear();
            contentContainer.getChildren().add(rendered);
        } catch (Exception e) {
            System.err.println("Markdown render failed, keeping plain text: " + e.getMessage());
        }
    }

    public String getRawText() {
        return rawText;
    }

    public Node getRoot() {
        return root;
    }
}
