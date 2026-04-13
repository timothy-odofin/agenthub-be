package com.agentdesk.service;

import com.agentdesk.model.McpServer;
import com.agentdesk.model.McpServer.ServerCategory;
import com.agentdesk.model.McpTool;
import org.kordamp.ikonli.feather.Feather;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class McpServerRegistry {

    private final List<McpServer> servers;

    public McpServerRegistry() {
        this.servers = buildSampleServers();
    }

    public List<McpServer> getAllServers() {
        return servers;
    }

    public Map<String, List<McpServer>> getGroupedServers() {
        Map<String, List<McpServer>> grouped = new LinkedHashMap<>();
        for (ServerCategory cat : ServerCategory.values()) {
            List<McpServer> inCat = servers.stream()
                    .filter(s -> s.getCategory() == cat)
                    .toList();
            if (!inCat.isEmpty()) {
                grouped.put(cat.getLabel(), inCat);
            }
        }
        return grouped;
    }

    private List<McpServer> buildSampleServers() {
        List<McpServer> list = new ArrayList<>();

        // --- Knowledge & Data ---
        list.add(new McpServer("web-search", "Web Search", "Search the web for real-time information",
                ServerCategory.KNOWLEDGE, Feather.SEARCH, List.of(
                new McpTool("search", "Search the web with a query", Feather.SEARCH),
                new McpTool("fetch_url", "Fetch and extract content from a URL", Feather.LINK),
                new McpTool("news_search", "Search for recent news articles", Feather.GLOBE)
        )));

        list.add(new McpServer("knowledge-base", "Knowledge Base", "Access internal documentation and FAQs",
                ServerCategory.KNOWLEDGE, Feather.BOOK_OPEN, List.of(
                new McpTool("query_docs", "Query the documentation index", Feather.FILE_TEXT),
                new McpTool("search_faq", "Search frequently asked questions", Feather.HELP_CIRCLE),
                new McpTool("get_article", "Retrieve a specific article by ID", Feather.BOOKMARK),
                new McpTool("list_categories", "List all documentation categories", Feather.LIST)
        )));

        list.add(new McpServer("file-manager", "File Manager", "Read and manage local files and directories",
                ServerCategory.KNOWLEDGE, Feather.FOLDER, List.of(
                new McpTool("read_file", "Read the contents of a file", Feather.FILE),
                new McpTool("write_file", "Write content to a file", Feather.EDIT),
                new McpTool("list_dir", "List directory contents", Feather.FOLDER)
        )));

        // --- Code & Dev ---
        list.add(new McpServer("code-interpreter", "Code Interpreter", "Execute code in a sandboxed environment",
                ServerCategory.CODE, Feather.CODE, List.of(
                new McpTool("run_python", "Execute Python code", Feather.PLAY),
                new McpTool("run_javascript", "Execute JavaScript code", Feather.PLAY_CIRCLE),
                new McpTool("install_package", "Install a package in the sandbox", Feather.PACKAGE),
                new McpTool("get_output", "Get execution output and logs", Feather.TERMINAL),
                new McpTool("list_files", "List files in the sandbox", Feather.FOLDER)
        )));

        list.add(new McpServer("terminal", "Terminal", "Run shell commands and scripts",
                ServerCategory.CODE, Feather.TERMINAL, List.of(
                new McpTool("exec_command", "Execute a shell command", Feather.CHEVRON_RIGHT),
                new McpTool("read_output", "Read command output", Feather.FILE_TEXT),
                new McpTool("kill_process", "Terminate a running process", Feather.X_CIRCLE)
        )));

        list.add(new McpServer("git", "Git", "Git repository operations and version control",
                ServerCategory.CODE, Feather.GIT_BRANCH, List.of(
                new McpTool("git_status", "Show working tree status", Feather.INFO),
                new McpTool("git_diff", "Show changes between commits", Feather.FILE_MINUS),
                new McpTool("git_log", "Show commit logs", Feather.LIST),
                new McpTool("git_commit", "Record changes to the repository", Feather.CHECK),
                new McpTool("git_branch", "List or create branches", Feather.GIT_BRANCH),
                new McpTool("git_push", "Push commits to remote", Feather.UPLOAD)
        )));

        // --- Integrations ---
        list.add(new McpServer("api-connector", "API Connector", "Make HTTP requests to external APIs",
                ServerCategory.INTEGRATION, Feather.ZAP, List.of(
                new McpTool("http_get", "Send a GET request", Feather.ARROW_DOWN),
                new McpTool("http_post", "Send a POST request", Feather.ARROW_UP),
                new McpTool("http_put", "Send a PUT request", Feather.EDIT),
                new McpTool("http_delete", "Send a DELETE request", Feather.TRASH)
        )));

        list.add(new McpServer("database", "Database", "Query and manage relational databases",
                ServerCategory.INTEGRATION, Feather.DATABASE, List.of(
                new McpTool("run_query", "Execute a SQL query", Feather.PLAY),
                new McpTool("list_tables", "List all database tables", Feather.LIST),
                new McpTool("describe_table", "Get table schema", Feather.INFO),
                new McpTool("insert_row", "Insert a new row", Feather.PLUS),
                new McpTool("export_csv", "Export query results to CSV", Feather.DOWNLOAD)
        )));

        list.add(new McpServer("slack", "Slack", "Send messages and manage Slack channels",
                ServerCategory.INTEGRATION, Feather.MESSAGE_SQUARE, List.of(
                new McpTool("send_message", "Send a message to a channel", Feather.SEND),
                new McpTool("list_channels", "List available channels", Feather.HASH)
        )));

        // --- Analysis & Output ---
        list.add(new McpServer("chart-generator", "Chart Generator", "Create charts and data visualizations",
                ServerCategory.ANALYSIS, Feather.BAR_CHART_2, List.of(
                new McpTool("bar_chart", "Create a bar chart", Feather.BAR_CHART),
                new McpTool("line_chart", "Create a line chart", Feather.TRENDING_UP),
                new McpTool("pie_chart", "Create a pie chart", Feather.PIE_CHART)
        )));

        list.add(new McpServer("pdf-export", "PDF Export", "Generate PDF documents from content",
                ServerCategory.ANALYSIS, Feather.FILE_TEXT, List.of(
                new McpTool("create_pdf", "Generate a PDF from text/HTML", Feather.FILE_PLUS),
                new McpTool("merge_pdfs", "Merge multiple PDFs into one", Feather.LAYERS)
        )));

        list.add(new McpServer("data-transform", "Data Transform", "Transform, clean, and analyze datasets",
                ServerCategory.ANALYSIS, Feather.SHUFFLE, List.of(
                new McpTool("parse_csv", "Parse CSV data into records", Feather.FILE_TEXT),
                new McpTool("parse_json", "Parse and validate JSON data", Feather.CODE),
                new McpTool("filter_rows", "Filter rows by condition", Feather.FILTER),
                new McpTool("sort_data", "Sort dataset by column", Feather.ARROW_UP),
                new McpTool("aggregate", "Compute aggregates (sum, avg, count)", Feather.HASH),
                new McpTool("join_datasets", "Join two datasets on a key", Feather.LINK),
                new McpTool("pivot_table", "Create a pivot table", Feather.GRID),
                new McpTool("deduplicate", "Remove duplicate records", Feather.COPY),
                new McpTool("normalize", "Normalize column values", Feather.SLIDERS),
                new McpTool("export_result", "Export transformed data", Feather.DOWNLOAD),
                new McpTool("validate_schema", "Validate data against a schema", Feather.CHECK_CIRCLE),
                new McpTool("compute_stats", "Compute summary statistics", Feather.ACTIVITY)
        )));

        return list;
    }
}
