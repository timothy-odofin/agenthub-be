package com.agentdesk.component;

import com.agentdesk.model.McpServer;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Node;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.ScrollPane;
import javafx.scene.layout.FlowPane;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.Region;
import javafx.scene.layout.VBox;
import javafx.stage.Popup;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;

public class SearchablePickerPopup extends Popup {

    private final VBox root;
    private final SearchField searchField;
    private final VBox groupsContainer;
    private final Label selectionCountLabel;
    private final Button applyButton;
    private final Map<String, List<ServerCard>> groupedCards = new LinkedHashMap<>();
    private final Map<String, GroupHeader> groupHeaders = new LinkedHashMap<>();
    private final Map<String, FlowPane> groupFlowPanes = new LinkedHashMap<>();
    private Consumer<List<McpServer>> onApply;
    private Consumer<McpServer> onInspect;

    public SearchablePickerPopup(Map<String, List<McpServer>> groupedServers,
                                  Consumer<McpServer> onInspect) {
        this.onInspect = onInspect;
        setAutoHide(true);

        root = new VBox(0);
        root.getStyleClass().add("tool-picker");
        root.setPrefWidth(460);
        root.setMaxWidth(460);
        root.setMaxHeight(440);

        searchField = new SearchField("Search servers...", this::applyFilter);
        HBox searchRow = new HBox(searchField);
        searchRow.getStyleClass().add("tool-picker-search-row");
        searchRow.setPadding(new Insets(16, 16, 8, 16));
        HBox.setHgrow(searchField, Priority.ALWAYS);

        groupsContainer = new VBox(4);
        groupsContainer.setPadding(new Insets(4, 16, 8, 16));

        buildGroups(groupedServers);

        ScrollPane scrollPane = new ScrollPane(groupsContainer);
        scrollPane.getStyleClass().add("tool-picker-scroll");
        scrollPane.setFitToWidth(true);
        scrollPane.setHbarPolicy(ScrollPane.ScrollBarPolicy.NEVER);
        scrollPane.setVbarPolicy(ScrollPane.ScrollBarPolicy.AS_NEEDED);
        scrollPane.setMaxHeight(320);
        VBox.setVgrow(scrollPane, Priority.ALWAYS);

        selectionCountLabel = new Label("0 servers selected");
        selectionCountLabel.getStyleClass().add("tool-picker-count");

        applyButton = new Button("Apply");
        applyButton.getStyleClass().add("tool-picker-apply");
        applyButton.setOnAction(e -> {
            if (onApply != null) {
                onApply.accept(getSelectedServers());
            }
            hide();
        });

        Region footerSpacer = new Region();
        HBox.setHgrow(footerSpacer, Priority.ALWAYS);

        HBox footer = new HBox(12, selectionCountLabel, footerSpacer, applyButton);
        footer.getStyleClass().add("tool-picker-footer");
        footer.setAlignment(Pos.CENTER_LEFT);
        footer.setPadding(new Insets(12, 16, 12, 16));

        root.getChildren().addAll(searchRow, scrollPane, footer);
        getContent().add(root);

        updateSelectionCount();
    }

    private void buildGroups(Map<String, List<McpServer>> groupedServers) {
        for (var entry : groupedServers.entrySet()) {
            String groupName = entry.getKey();
            List<McpServer> servers = entry.getValue();

            GroupHeader header = new GroupHeader(groupName, servers.size());
            groupHeaders.put(groupName, header);

            FlowPane flowPane = new FlowPane();
            flowPane.getStyleClass().add("tool-picker-card-flow");
            flowPane.setHgap(8);
            flowPane.setVgap(8);

            List<ServerCard> cards = new ArrayList<>();
            for (McpServer server : servers) {
                ServerCard card = new ServerCard(server, onInspect);
                card.setOnMouseClicked(e -> {
                    if (!(e.getTarget() instanceof Button)) {
                        card.toggleSelected();
                        updateSelectionCount();
                    }
                });
                cards.add(card);
                flowPane.getChildren().add(card);
            }

            groupedCards.put(groupName, cards);
            groupFlowPanes.put(groupName, flowPane);

            groupsContainer.getChildren().addAll(header, flowPane);
        }
    }

    private void applyFilter(String filter) {
        for (var entry : groupedCards.entrySet()) {
            String groupName = entry.getKey();
            List<ServerCard> cards = entry.getValue();
            GroupHeader header = groupHeaders.get(groupName);
            FlowPane flowPane = groupFlowPanes.get(groupName);

            int visibleCount = 0;
            for (ServerCard card : cards) {
                boolean matches = card.matchesFilter(filter);
                card.setVisible(matches);
                card.setManaged(matches);
                if (matches) visibleCount++;
            }

            boolean groupVisible = visibleCount > 0;
            header.setVisible(groupVisible);
            header.setManaged(groupVisible);
            flowPane.setVisible(groupVisible);
            flowPane.setManaged(groupVisible);
            header.updateCount(visibleCount);
        }
    }

    private void updateSelectionCount() {
        long count = groupedCards.values().stream()
                .flatMap(List::stream)
                .filter(ServerCard::isSelected)
                .count();
        selectionCountLabel.setText(count + (count == 1 ? " server selected" : " servers selected"));
    }

    public List<McpServer> getSelectedServers() {
        return groupedCards.values().stream()
                .flatMap(List::stream)
                .filter(ServerCard::isSelected)
                .map(ServerCard::getServer)
                .toList();
    }

    public void preselectServers(Set<McpServer> servers) {
        for (List<ServerCard> cards : groupedCards.values()) {
            for (ServerCard card : cards) {
                card.setSelected(servers.contains(card.getServer()));
            }
        }
        updateSelectionCount();
    }

    public void setOnApply(Consumer<List<McpServer>> onApply) {
        this.onApply = onApply;
    }

    public void showRelativeTo(Node anchor) {
        var bounds = anchor.localToScreen(anchor.getBoundsInLocal());
        if (bounds == null) return;

        double x = bounds.getMinX();
        double y = bounds.getMinY() - 450;
        if (y < 0) {
            y = bounds.getMaxY() + 8;
        }

        show(anchor, x, y);
        searchField.clear();
        searchField.requestSearchFocus();
    }
}
