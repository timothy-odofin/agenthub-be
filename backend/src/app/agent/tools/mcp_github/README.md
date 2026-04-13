# MCP GitHub Tools Integration

GitHub integration for agenthub using the **Model Context Protocol (MCP)** — the industry standard for connecting LLM agents to external tools and data sources.

## Architecture

```
┌──────────────────┐     stdio/SSE      ┌─────────────────────┐     REST API     ┌──────────────┐
│  MCPGitHubTools  │◀──────────────────▶│  GitHub MCP Server  │◀───────────────▶│  GitHub API  │
│  Provider        │  MCP protocol      │  (subprocess/remote)│  authenticated  │              │
│  (LangChain)     │                    │                     │                  │              │
└────────┬─────────┘                    └─────────────────────┘                  └──────────────┘
         │
         │ StructuredTool[]
         ▼
┌──────────────────┐
│  ToolRegistry    │
│  (same as Jira,  │
│   Confluence...) │
└──────────────────┘
```

**Key difference from the previous custom implementation:**
- ❌ **Before:** Custom `GitHubConnectionManager` + `GitHubToolFactory` + `GitHubAPIWrapper` + `PyGithub` — 800+ lines of custom code managing GitHub App auth, repository discovery, tool creation, name sanitization
- ✅ **After:** ~300 lines. The MCP server handles everything. We just connect, load tools, and register them.

## Setup

### 1. Install the GitHub MCP Server

```bash
# Via npm (recommended)
npm install -g @modelcontextprotocol/server-github

# Or via Docker
docker pull ghcr.io/github/github-mcp-server
```

### 2. Set Environment Variables

```bash
# Required: GitHub Personal Access Token
export GITHUB_TOKEN="ghp_your_token_here"

# Optional: Restrict to specific repositories
export GITHUB_MCP_TOOL_FILTER="search_repositories,get_file_contents,list_issues,create_issue"
```

### 3. Configuration

All configuration lives in `resources/application-tools.yaml`:

```yaml
github:
  enabled: true
  transport: stdio              # "stdio" (subprocess) or "sse" (remote HTTP)
  command: github-mcp-server    # MCP server binary
  args: ["--stdio"]             # Command arguments
  env:
    GITHUB_TOKEN: "${GITHUB_TOKEN}"
  tool_filter:                  # Optional: only expose these tools
    - search_repositories
    - get_file_contents
    - list_issues
    - create_issue
    - list_pull_requests
    - search_code
```

## Transport Options

### stdio (Development / Local)
The MCP server runs as a subprocess. Simple, no extra infrastructure.

```yaml
transport: stdio
command: github-mcp-server
args: ["--stdio"]
```

### SSE / HTTP (Production)
The MCP server runs as a remote service (e.g., Docker sidecar in `docker-compose.yml`).

```yaml
transport: sse
url: "http://github-mcp-server:8080/sse"
```

## Available Tools

The GitHub MCP server exposes these tools (subset — see full list at [github/github-mcp-server](https://github.com/github/github-mcp-server)):

| Tool | Description |
|------|-------------|
| `search_repositories` | Search for GitHub repositories |
| `get_file_contents` | Read file contents from a repository |
| `list_issues` | List issues in a repository |
| `create_issue` | Create a new issue |
| `list_pull_requests` | List pull requests |
| `create_pull_request` | Create a new pull request |
| `search_code` | Search code across repositories |
| `list_branches` | List branches in a repository |
| `create_branch` | Create a new branch |
| ... | And many more |

Use `tool_filter` in config to restrict which tools are exposed to the agent.

## Comparison: Custom vs MCP

| Aspect | Custom (Old) | MCP (New) |
|--------|-------------|-----------|
| Code size | ~800 lines | ~300 lines |
| Dependencies | `PyGithub`, `langchain-community[github]` | `langchain-mcp-adapters`, `mcp` |
| Auth handling | Custom `GitHubConnectionManager` | MCP server (GITHUB_TOKEN) |
| Tool creation | Custom `GitHubToolFactory` + sanitization | Automatic via MCP protocol |
| Maintenance | Must update when GitHub API changes | MCP server updated independently |
| Multi-repo | Custom discovery + filtering | MCP server handles it |
| Extensibility | Write Python code | Add MCP server config |
