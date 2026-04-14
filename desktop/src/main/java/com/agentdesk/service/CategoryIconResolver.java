package com.agentdesk.service;

import org.kordamp.ikonli.feather.Feather;
import org.springframework.stereotype.Service;

import java.util.Map;

/**
 * Maps category key strings returned by the backend to a {@link Feather} icon constant
 * appropriate for display in the MCP server picker UI.
 *
 * <p>All mapping is performed by a static lookup table; unknown categories fall back to
 * {@link Feather#PACKAGE}.
 */
@Service
public final class CategoryIconResolver {

    private static final Map<String, Feather> ICON_BY_CATEGORY = Map.ofEntries(
            Map.entry("knowledge",    Feather.BOOK_OPEN),
            Map.entry("code",         Feather.CODE),
            Map.entry("integration",  Feather.ZAP),
            Map.entry("analysis",     Feather.BAR_CHART_2),
            Map.entry("data",         Feather.DATABASE),
            Map.entry("search",       Feather.SEARCH),
            Map.entry("file",         Feather.FOLDER),
            Map.entry("communication", Feather.MESSAGE_SQUARE),
            Map.entry("automation",   Feather.SETTINGS),
            Map.entry("web",          Feather.GLOBE)
    );

    private static final Map<String, Feather> ICON_BY_SERVER_ID = Map.ofEntries(
            Map.entry("web-search",       Feather.SEARCH),
            Map.entry("knowledge-base",   Feather.BOOK_OPEN),
            Map.entry("file-manager",     Feather.FOLDER),
            Map.entry("code-interpreter", Feather.CODE),
            Map.entry("terminal",         Feather.TERMINAL),
            Map.entry("git",              Feather.GIT_BRANCH),
            Map.entry("api-connector",    Feather.ZAP),
            Map.entry("database",         Feather.DATABASE),
            Map.entry("slack",            Feather.MESSAGE_SQUARE),
            Map.entry("chart-generator",  Feather.BAR_CHART_2),
            Map.entry("pdf-export",       Feather.FILE_TEXT),
            Map.entry("data-transform",   Feather.SHUFFLE)
    );

    /**
     * Resolves a {@link Feather} icon for a category key string.
     *
     * @param categoryKey the category key as returned by the backend (case-insensitive)
     * @return a non-null {@link Feather} icon constant
     */
    public Feather forCategory(String categoryKey) {
        if (categoryKey == null) {
            return Feather.PACKAGE;
        }
        return ICON_BY_CATEGORY.getOrDefault(categoryKey.toLowerCase(), Feather.PACKAGE);
    }

    /**
     * Resolves a {@link Feather} icon for a specific server ID string.
     * Falls back to {@link #forCategory(String)} when no server-specific icon is registered.
     *
     * @param serverId    the server identifier as returned by the backend
     * @param categoryKey the server's category key, used as the fallback
     * @return a non-null {@link Feather} icon constant
     */
    public Feather forServer(String serverId, String categoryKey) {
        if (serverId != null) {
            final Feather icon = ICON_BY_SERVER_ID.get(serverId.toLowerCase());
            if (icon != null) {
                return icon;
            }
        }
        return forCategory(categoryKey);
    }
}
