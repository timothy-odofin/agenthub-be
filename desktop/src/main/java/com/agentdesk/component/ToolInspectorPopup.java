package com.agentdesk.component;

import com.agentdesk.model.McpServer;
import com.agentdesk.model.McpTool;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Node;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.ScrollPane;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.Region;
import javafx.scene.layout.VBox;
import javafx.stage.Popup;
import org.kordamp.ikonli.feather.Feather;
import org.kordamp.ikonli.javafx.FontIcon;

import java.util.ArrayList;
import java.util.List;

public class ToolInspectorPopup extends Popup {

    private final VBox root;
    private final VBox toolsContainer;
    private final SearchField searchField;
    private final List<ToolCard> toolCards = new ArrayList<>();

    public ToolInspectorPopup(McpServer server) {
        setAutoHide(true);

        root = new VBox(0);
        root.getStyleClass().add("tool-inspector");
        root.setPrefWidth(380);
        root.setMaxWidth(380);
        root.setMaxHeight(420);

        // Header
        FontIcon serverIcon = new FontIcon(server.getIcon());
        serverIcon.setIconSize(18);
        serverIcon.getStyleClass().add("tool-inspector-header-icon");

        Label titleLabel = new Label(server.getName());
        titleLabel.getStyleClass().add("tool-inspector-title");

        Label subtitleLabel = new Label(server.getToolCount() + " tools available");
        subtitleLabel.getStyleClass().add("tool-inspector-subtitle");

        VBox titleBox = new VBox(2, titleLabel, subtitleLabel);
        titleBox.setAlignment(Pos.CENTER_LEFT);
        HBox.setHgrow(titleBox, Priority.ALWAYS);

        FontIcon closeIcon = new FontIcon(Feather.X);
        closeIcon.setIconSize(16);
        closeIcon.getStyleClass().add("tool-inspector-close-icon");

        Button closeBtn = new Button();
        closeBtn.setGraphic(closeIcon);
        closeBtn.getStyleClass().add("tool-inspector-close-btn");
        closeBtn.setOnAction(e -> hide());

        HBox header = new HBox(10, serverIcon, titleBox, closeBtn);
        header.getStyleClass().add("tool-inspector-header");
        header.setAlignment(Pos.CENTER_LEFT);
        header.setPadding(new Insets(14, 16, 10, 16));

        // Search
        searchField = new SearchField("Search tools...", this::applyFilter);
        HBox searchRow = new HBox(searchField);
        searchRow.setPadding(new Insets(0, 16, 8, 16));
        HBox.setHgrow(searchField, Priority.ALWAYS);

        // Tools list
        toolsContainer = new VBox(6);
        toolsContainer.setPadding(new Insets(4, 16, 12, 16));

        for (McpTool tool : server.getTools()) {
            ToolCard card = new ToolCard(tool);
            toolCards.add(card);
            toolsContainer.getChildren().add(card);
        }

        ScrollPane scrollPane = new ScrollPane(toolsContainer);
        scrollPane.getStyleClass().add("tool-inspector-scroll");
        scrollPane.setFitToWidth(true);
        scrollPane.setHbarPolicy(ScrollPane.ScrollBarPolicy.NEVER);
        scrollPane.setVbarPolicy(ScrollPane.ScrollBarPolicy.AS_NEEDED);
        scrollPane.setMaxHeight(300);
        VBox.setVgrow(scrollPane, Priority.ALWAYS);

        // Footer
        Label countLabel = new Label(server.getToolCount() + " tools total");
        countLabel.getStyleClass().add("tool-inspector-footer-count");

        Region footerSpacer = new Region();
        HBox.setHgrow(footerSpacer, Priority.ALWAYS);

        HBox footer = new HBox(12, countLabel, footerSpacer);
        footer.getStyleClass().add("tool-inspector-footer");
        footer.setAlignment(Pos.CENTER_LEFT);
        footer.setPadding(new Insets(10, 16, 10, 16));

        root.getChildren().addAll(header, searchRow, scrollPane, footer);
        getContent().add(root);
    }

    private void applyFilter(String filter) {
        for (ToolCard card : toolCards) {
            boolean matches = card.matchesFilter(filter);
            card.setVisible(matches);
            card.setManaged(matches);
        }
    }

    public void showRelativeTo(Node anchor) {
        var bounds = anchor.localToScreen(anchor.getBoundsInLocal());
        if (bounds == null) return;

        double x = bounds.getMaxX() + 8;
        double y = bounds.getMinY();

        show(anchor, x, y);
        searchField.clear();
        searchField.requestSearchFocus();
    }

    public VBox createDrawerContent(Runnable onClose) {
        VBox drawer = new VBox(0);
        drawer.getStyleClass().add("tool-inspector-drawer");

        FontIcon closeIcon = new FontIcon(Feather.X);
        closeIcon.setIconSize(16);
        closeIcon.getStyleClass().add("tool-inspector-close-icon");

        Button closeBtn = new Button();
        closeBtn.setGraphic(closeIcon);
        closeBtn.getStyleClass().add("tool-inspector-close-btn");
        closeBtn.setOnAction(e -> {
            if (onClose != null) onClose.run();
        });

        HBox header = (HBox) root.getChildren().get(0);
        HBox searchRow = (HBox) root.getChildren().get(1);
        ScrollPane scroll = (ScrollPane) root.getChildren().get(2);
        HBox footer = (HBox) root.getChildren().get(3);

        root.getChildren().clear();
        drawer.getChildren().addAll(header, searchRow, scroll, footer);
        VBox.setVgrow(scroll, Priority.ALWAYS);

        return drawer;
    }

    public static Node createForServer(McpServer server, Node anchor,
                                        javafx.scene.control.SplitPane splitPane,
                                        Runnable onCloseDrawer) {
        boolean useDrawer = server.getToolCount() >= 10;

        if (useDrawer) {
            return buildDrawerPanel(server, onCloseDrawer);
        } else {
            ToolInspectorPopup popup = new ToolInspectorPopup(server);
            popup.showRelativeTo(anchor);
            return null;
        }
    }

    public static VBox buildDrawerPanel(McpServer server, Runnable onClose) {
        VBox drawer = new VBox(0);
        drawer.getStyleClass().add("tool-inspector-drawer");
        drawer.setMinWidth(300);

        FontIcon serverIcon = new FontIcon(server.getIcon());
        serverIcon.setIconSize(18);
        serverIcon.getStyleClass().add("tool-inspector-header-icon");

        Label titleLabel = new Label(server.getName());
        titleLabel.getStyleClass().add("tool-inspector-title");

        Label subtitleLabel = new Label(server.getToolCount() + " tools available");
        subtitleLabel.getStyleClass().add("tool-inspector-subtitle");

        VBox titleBox = new VBox(2, titleLabel, subtitleLabel);
        titleBox.setAlignment(Pos.CENTER_LEFT);
        HBox.setHgrow(titleBox, Priority.ALWAYS);

        FontIcon closeIcon = new FontIcon(Feather.X);
        closeIcon.setIconSize(16);
        closeIcon.getStyleClass().add("tool-inspector-close-icon");

        Button closeBtn = new Button();
        closeBtn.setGraphic(closeIcon);
        closeBtn.getStyleClass().add("tool-inspector-close-btn");
        closeBtn.setOnAction(e -> {
            if (onClose != null) onClose.run();
        });

        HBox header = new HBox(10, serverIcon, titleBox, closeBtn);
        header.getStyleClass().add("tool-inspector-header");
        header.setAlignment(Pos.CENTER_LEFT);
        header.setPadding(new Insets(14, 16, 10, 16));

        List<ToolCard> toolCardList = new ArrayList<>();
        VBox toolsVBox = new VBox(6);
        toolsVBox.setPadding(new Insets(4, 16, 12, 16));

        for (McpTool tool : server.getTools()) {
            ToolCard card = new ToolCard(tool);
            toolCardList.add(card);
            toolsVBox.getChildren().add(card);
        }

        SearchField search = new SearchField("Search tools...", filter -> {
            for (ToolCard card : toolCardList) {
                boolean matches = card.matchesFilter(filter);
                card.setVisible(matches);
                card.setManaged(matches);
            }
        });

        HBox searchRow = new HBox(search);
        searchRow.setPadding(new Insets(0, 16, 8, 16));
        HBox.setHgrow(search, Priority.ALWAYS);

        ScrollPane scrollPane = new ScrollPane(toolsVBox);
        scrollPane.getStyleClass().add("tool-inspector-scroll");
        scrollPane.setFitToWidth(true);
        scrollPane.setHbarPolicy(ScrollPane.ScrollBarPolicy.NEVER);
        scrollPane.setVbarPolicy(ScrollPane.ScrollBarPolicy.AS_NEEDED);
        VBox.setVgrow(scrollPane, Priority.ALWAYS);

        Label countLabel = new Label(server.getToolCount() + " tools total");
        countLabel.getStyleClass().add("tool-inspector-footer-count");

        HBox footer = new HBox(countLabel);
        footer.getStyleClass().add("tool-inspector-footer");
        footer.setAlignment(Pos.CENTER_LEFT);
        footer.setPadding(new Insets(10, 16, 10, 16));

        drawer.getChildren().addAll(header, searchRow, scrollPane, footer);
        return drawer;
    }
}
