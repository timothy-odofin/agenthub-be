package com.agentdesk.service;

import com.agentdesk.api.ApiClient;
import com.agentdesk.api.ApiExceptionMapper;
import com.agentdesk.model.McpServer;
import com.agentdesk.model.McpServer.ServerCategory;
import com.agentdesk.model.McpTool;
import com.agentdesk.model.dto.McpGroupDto;
import com.agentdesk.model.dto.McpServerDto;
import com.agentdesk.model.dto.McpToolDto;
import com.agentdesk.model.dto.McpToolsResponse;
import javafx.application.Platform;
import org.kordamp.ikonli.feather.Feather;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;

/**
 * Provides the list of available MCP servers populated from the AgentHub backend.
 *
 * <h3>Startup sequence</h3>
 * <ol>
 *   <li>The registry is created with an empty server list.</li>
 *   <li>After login, call {@link #refresh(Consumer)} to fetch from
 *       {@code GET /api/v1/tools/mcp}.</li>
 *   <li>If the backend is unreachable the registry falls back to the built-in static
 *       catalogue so the picker UI is never empty.</li>
 * </ol>
 *
 * <h3>Threading contract</h3>
 * Reads of {@link #getAllServers()} and {@link #getGroupedServers()} are safe from any thread.
 * The internal list is replaced atomically using {@link CopyOnWriteArrayList}.
 */
@Service
public final class McpServerRegistry {

    private static final Logger log = LoggerFactory.getLogger(McpServerRegistry.class);

    private static final String MCP_PATH = "/api/v1/tools/mcp";

    private final ApiClient            apiClient;
    private final ApiExceptionMapper   exceptionMapper;
    private final CategoryIconResolver iconResolver;

    /**
     * Thread-safe list of loaded servers.  Replaced atomically on each {@link #refresh} call.
     */
    private volatile List<McpServer> servers;

    public McpServerRegistry(
            ApiClient            apiClient,
            ApiExceptionMapper   exceptionMapper,
            CategoryIconResolver iconResolver) {
        this.apiClient       = apiClient;
        this.exceptionMapper = exceptionMapper;
        this.iconResolver    = iconResolver;
        this.servers         = buildFallbackServers();
    }

    // -------------------------------------------------------------------------
    // Public API
    // -------------------------------------------------------------------------

    /**
     * Returns all registered MCP servers in the order they were loaded from the backend
     * (or the static fallback order if the backend has not responded yet).
     *
     * @return an unmodifiable snapshot of the current server list
     */
    public List<McpServer> getAllServers() {
        return List.copyOf(servers);
    }

    /**
     * Returns the servers grouped by category label, preserving insertion order.
     *
     * @return an ordered, unmodifiable map of {@code "Category Label" → servers}
     */
    public Map<String, List<McpServer>> getGroupedServers() {
        final Map<String, List<McpServer>> grouped = new LinkedHashMap<>();
        for (final McpServer server : servers) {
            final String label = server.getCategory().getLabel();
            grouped.computeIfAbsent(label, k -> new ArrayList<>()).add(server);
        }
        return grouped;
    }

    /**
     * Fetches the MCP server catalogue from the backend and replaces the local list.
     *
     * <p>If the request fails the existing list is left intact (usually the fallback)
     * and the {@code onError} callback is invoked on the JavaFX thread.
     *
     * @param onError called on the JavaFX thread with a user-facing message if the call fails;
     *                may be {@code null} if the caller does not care about errors
     */
    public void refresh(Consumer<String> onError) {
        log.debug("Refreshing MCP server catalogue from backend");
        apiClient.getAsync(MCP_PATH, McpToolsResponse.class)
                .whenComplete((response, throwable) -> {
                    if (throwable != null) {
                        final String msg = exceptionMapper.toUserMessage(throwable);
                        log.warn("Failed to load MCP tools — using fallback catalogue: {}", msg);
                        if (onError != null) {
                            Platform.runLater(() -> onError.accept(msg));
                        }
                        return;
                    }
                    if (!response.success() || response.groups() == null) {
                        log.warn("Backend returned success=false for MCP tools — using fallback catalogue");
                        return;
                    }
                    final List<McpServer> loaded = mapFromResponse(response);
                    servers = loaded;
                    log.info("Loaded {} MCP servers from backend", loaded.size());
                });
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    private List<McpServer> mapFromResponse(McpToolsResponse response) {
        final List<McpServer> result = new ArrayList<>();
        for (final McpGroupDto group : response.groups()) {
            final ServerCategory category = resolveCategoryEnum(group.category(), group.label());
            if (group.servers() == null) continue;
            for (final McpServerDto dto : group.servers()) {
                final Feather icon = iconResolver.forServer(dto.id(), group.category());
                final List<McpTool> tools = mapTools(dto.tools());
                result.add(new McpServer(dto.id(), dto.name(), dto.description(), category, icon, tools));
            }
        }
        return result;
    }

    private static List<McpTool> mapTools(List<McpToolDto> dtos) {
        if (dtos == null) return List.of();
        return dtos.stream()
                .map(d -> new McpTool(d.name(), d.description(), Feather.TOOL))
                .toList();
    }

    /**
     * Maps a backend category string to a {@link ServerCategory} enum value.
     * Uses the {@code label} as a secondary hint when the key alone does not match.
     */
    private static ServerCategory resolveCategoryEnum(String key, String label) {
        if (key == null) return ServerCategory.KNOWLEDGE;
        return switch (key.toLowerCase()) {
            case "code"         -> ServerCategory.CODE;
            case "integration"  -> ServerCategory.INTEGRATION;
            case "analysis"     -> ServerCategory.ANALYSIS;
            default             -> {
                // Try a loose match against enum labels.
                if (label != null) {
                    final String lowerLabel = label.toLowerCase();
                    for (final ServerCategory cat : ServerCategory.values()) {
                        if (lowerLabel.contains(cat.getLabel().toLowerCase())) {
                            yield cat;
                        }
                    }
                }
                yield ServerCategory.KNOWLEDGE;
            }
        };
    }

    // -------------------------------------------------------------------------
    // Static fallback catalogue
    // -------------------------------------------------------------------------

    private List<McpServer> buildFallbackServers() {
        final List<McpServer> list = new ArrayList<>();

        list.add(new McpServer("web-search", "Web Search", "Search the web for real-time information",
                ServerCategory.KNOWLEDGE, Feather.SEARCH, List.of(
                new McpTool("search",       "Search the web with a query",              Feather.SEARCH),
                new McpTool("fetch_url",    "Fetch and extract content from a URL",     Feather.LINK),
                new McpTool("news_search",  "Search for recent news articles",          Feather.GLOBE)
        )));

        list.add(new McpServer("knowledge-base", "Knowledge Base", "Access internal documentation and FAQs",
                ServerCategory.KNOWLEDGE, Feather.BOOK_OPEN, List.of(
                new McpTool("query_docs",       "Query the documentation index",          Feather.FILE_TEXT),
                new McpTool("search_faq",       "Search frequently asked questions",      Feather.HELP_CIRCLE),
                new McpTool("get_article",      "Retrieve a specific article by ID",      Feather.BOOKMARK),
                new McpTool("list_categories",  "List all documentation categories",      Feather.LIST)
        )));

        list.add(new McpServer("file-manager", "File Manager", "Read and manage local files and directories",
                ServerCategory.KNOWLEDGE, Feather.FOLDER, List.of(
                new McpTool("read_file",  "Read the contents of a file",   Feather.FILE),
                new McpTool("write_file", "Write content to a file",       Feather.EDIT),
                new McpTool("list_dir",   "List directory contents",       Feather.FOLDER)
        )));

        list.add(new McpServer("code-interpreter", "Code Interpreter", "Execute code in a sandboxed environment",
                ServerCategory.CODE, Feather.CODE, List.of(
                new McpTool("run_python",       "Execute Python code",                  Feather.PLAY),
                new McpTool("run_javascript",   "Execute JavaScript code",              Feather.PLAY_CIRCLE),
                new McpTool("install_package",  "Install a package in the sandbox",     Feather.PACKAGE),
                new McpTool("get_output",       "Get execution output and logs",        Feather.TERMINAL),
                new McpTool("list_files",       "List files in the sandbox",            Feather.FOLDER)
        )));

        list.add(new McpServer("terminal", "Terminal", "Run shell commands and scripts",
                ServerCategory.CODE, Feather.TERMINAL, List.of(
                new McpTool("exec_command",  "Execute a shell command",       Feather.CHEVRON_RIGHT),
                new McpTool("read_output",   "Read command output",           Feather.FILE_TEXT),
                new McpTool("kill_process",  "Terminate a running process",   Feather.X_CIRCLE)
        )));

        list.add(new McpServer("git", "Git", "Git repository operations and version control",
                ServerCategory.CODE, Feather.GIT_BRANCH, List.of(
                new McpTool("git_status",  "Show working tree status",          Feather.INFO),
                new McpTool("git_diff",    "Show changes between commits",      Feather.FILE_MINUS),
                new McpTool("git_log",     "Show commit logs",                  Feather.LIST),
                new McpTool("git_commit",  "Record changes to the repository",  Feather.CHECK),
                new McpTool("git_branch",  "List or create branches",           Feather.GIT_BRANCH),
                new McpTool("git_push",    "Push commits to remote",            Feather.UPLOAD)
        )));

        list.add(new McpServer("api-connector", "API Connector", "Make HTTP requests to external APIs",
                ServerCategory.INTEGRATION, Feather.ZAP, List.of(
                new McpTool("http_get",    "Send a GET request",    Feather.ARROW_DOWN),
                new McpTool("http_post",   "Send a POST request",   Feather.ARROW_UP),
                new McpTool("http_put",    "Send a PUT request",    Feather.EDIT),
                new McpTool("http_delete", "Send a DELETE request", Feather.TRASH)
        )));

        list.add(new McpServer("database", "Database", "Query and manage relational databases",
                ServerCategory.INTEGRATION, Feather.DATABASE, List.of(
                new McpTool("run_query",        "Execute a SQL query",            Feather.PLAY),
                new McpTool("list_tables",      "List all database tables",       Feather.LIST),
                new McpTool("describe_table",   "Get table schema",               Feather.INFO),
                new McpTool("insert_row",       "Insert a new row",               Feather.PLUS),
                new McpTool("export_csv",       "Export query results to CSV",    Feather.DOWNLOAD)
        )));

        list.add(new McpServer("slack", "Slack", "Send messages and manage Slack channels",
                ServerCategory.INTEGRATION, Feather.MESSAGE_SQUARE, List.of(
                new McpTool("send_message",  "Send a message to a channel",  Feather.SEND),
                new McpTool("list_channels", "List available channels",      Feather.HASH)
        )));

        list.add(new McpServer("chart-generator", "Chart Generator", "Create charts and data visualizations",
                ServerCategory.ANALYSIS, Feather.BAR_CHART_2, List.of(
                new McpTool("bar_chart",  "Create a bar chart",  Feather.BAR_CHART),
                new McpTool("line_chart", "Create a line chart", Feather.TRENDING_UP),
                new McpTool("pie_chart",  "Create a pie chart",  Feather.PIE_CHART)
        )));

        list.add(new McpServer("pdf-export", "PDF Export", "Generate PDF documents from content",
                ServerCategory.ANALYSIS, Feather.FILE_TEXT, List.of(
                new McpTool("create_pdf",  "Generate a PDF from text/HTML",   Feather.FILE_PLUS),
                new McpTool("merge_pdfs",  "Merge multiple PDFs into one",    Feather.LAYERS)
        )));

        list.add(new McpServer("data-transform", "Data Transform", "Transform, clean, and analyze datasets",
                ServerCategory.ANALYSIS, Feather.SHUFFLE, List.of(
                new McpTool("parse_csv",        "Parse CSV data into records",                Feather.FILE_TEXT),
                new McpTool("parse_json",       "Parse and validate JSON data",               Feather.CODE),
                new McpTool("filter_rows",      "Filter rows by condition",                   Feather.FILTER),
                new McpTool("sort_data",        "Sort dataset by column",                     Feather.ARROW_UP),
                new McpTool("aggregate",        "Compute aggregates (sum, avg, count)",       Feather.HASH),
                new McpTool("join_datasets",    "Join two datasets on a key",                 Feather.LINK),
                new McpTool("pivot_table",      "Create a pivot table",                       Feather.GRID),
                new McpTool("deduplicate",      "Remove duplicate records",                   Feather.COPY),
                new McpTool("normalize",        "Normalize column values",                    Feather.SLIDERS),
                new McpTool("export_result",    "Export transformed data",                    Feather.DOWNLOAD),
                new McpTool("validate_schema",  "Validate data against a schema",             Feather.CHECK_CIRCLE),
                new McpTool("compute_stats",    "Compute summary statistics",                 Feather.ACTIVITY)
        )));

        return list;
    }
}
