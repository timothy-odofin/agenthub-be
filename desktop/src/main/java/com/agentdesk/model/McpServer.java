package com.agentdesk.model;

import org.kordamp.ikonli.feather.Feather;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class McpServer {

    public enum ServerCategory {
        KNOWLEDGE("Knowledge & Data"),
        CODE("Code & Dev"),
        INTEGRATION("Integrations"),
        ANALYSIS("Analysis & Output");

        private final String label;

        ServerCategory(String label) { this.label = label; }

        public String getLabel() { return label; }
    }

    private final String id;
    private final String name;
    private final String description;
    private final ServerCategory category;
    private final Feather icon;
    private final List<McpTool> tools;

    public McpServer(String id, String name, String description,
                     ServerCategory category, Feather icon, List<McpTool> tools) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.category = category;
        this.icon = icon;
        this.tools = tools != null ? new ArrayList<>(tools) : new ArrayList<>();
    }

    public String getId() { return id; }
    public String getName() { return name; }
    public String getDescription() { return description; }
    public ServerCategory getCategory() { return category; }
    public Feather getIcon() { return icon; }
    public List<McpTool> getTools() { return Collections.unmodifiableList(tools); }
    public int getToolCount() { return tools.size(); }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        McpServer that = (McpServer) o;
        return Objects.equals(id, that.id);
    }

    @Override
    public int hashCode() { return Objects.hash(id); }

    @Override
    public String toString() { return name; }
}
