package com.agentdesk.model;

import org.kordamp.ikonli.feather.Feather;

public class McpTool {

    private final String name;
    private final String description;
    private final Feather icon;

    public McpTool(String name, String description, Feather icon) {
        this.name = name;
        this.description = description;
        this.icon = icon;
    }

    public McpTool(String name, String description) {
        this(name, description, Feather.TOOL);
    }

    public String getName() { return name; }
    public String getDescription() { return description; }
    public Feather getIcon() { return icon; }

    @Override
    public String toString() { return name; }
}
