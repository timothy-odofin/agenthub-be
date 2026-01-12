# Tools Integration Guides

Comprehensive guides for integrating external tools and services with AgentHub AI agents.

## Overview

AgentHub provides AI agents with access to various external tools and services through a unified tool integration system. Each tool is:
- **Configuration-driven**: Enable/disable tools via YAML
- **LLM-accessible**: Automatically registered for agent use
- **Well-documented**: Clear parameters and examples
- **Production-ready**: Error handling and service availability checks

## Safety & Confirmation

### **[Confirmation Workflow](./confirmation-workflow.md)** 🔒
Two-phase confirmation protocol for mutating actions.

**Key Features:**
- Prepare-confirm pattern for all mutating operations
- User review and approval before execution
- Action preview with detailed descriptions
- Automatic expiration (5 minutes)
- Risk level classification

**Available Tools:**
- `prepare_action` - Prepare action for user review
- `confirm_action` - Execute after user approval
- `cancel_action` - Cancel pending action
- `list_pending_actions` - View all pending confirmations

**Use Cases:**
- Creating Jira issues with user approval
- Adding comments/mentions after review
- Creating GitHub PRs with confirmation
- Any operation that modifies external systems

**⚠️ REQUIRED** for all mutating operations:
- Creating/updating/deleting resources
- Adding comments or mentions
- Triggering workflows or notifications

---

## Available Tool Integrations

### Atlassian Tools

#### **[Confluence Tools](./confluence-tools.md)** 📄
Real-time access to Confluence spaces, pages, and content.

**Key Features:**
- List and explore Confluence spaces
- Search pages with CQL queries
- Retrieve full page content and metadata
- Real-time data vs embedded/vector store approach

**Available Tools:**
- `list_confluence_spaces` - Discover accessible spaces
- `get_confluence_space` - Get space details
- `list_pages_in_space` - List all pages in a space
- `search_confluence_pages` - Search by text/CQL
- `get_confluence_page` - Retrieve full page content

**Use Cases:**
- Get latest documentation
- Search for technical guides
- Explore team workspaces
- Access real-time Confluence content

---

#### **[Jira Tools](./jira-tools.md)** 🎫
Issue tracking and project management with Jira.

**Key Features:**
- List projects and discover workspaces
- Create issues (tasks, bugs, stories)
- Retrieve issue details and status
- Search issues with JQL

**Available Tools:**
- `get_jira_projects` - List all accessible projects
- `create_jira_issue` - Create new issues
- `get_jira_issue` - Get issue details by key
- `search_jira_issues` - Search using JQL

**Use Cases:**
- Create tasks from user requests
- Track issue status
- Search for bugs or specific issues
- Generate project reports

---

### Monitoring & Observability

#### **[Datadog Tools](./datadog-tools.md)** 📊
System monitoring and performance metrics from Datadog.

**Key Features:**
- Query metrics and logs
- Monitor system performance
- Alert on thresholds
- Historical data analysis

**Use Cases:**
- System health checks
- Performance troubleshooting
- Log analysis
- Infrastructure monitoring

---

### Version Control

#### **GitHub Tools** 🐙
*(Documentation to be added)*

Access to GitHub repositories, issues, and pull requests.

**Available Tools:**
- Repository information
- Issue and PR management
- Code search and navigation
- Commit and branch operations

---

### Knowledge Management

#### **[Vector Store Tools](./vector-store-tools.md)** 🔍
Semantic search across your embedded knowledge base.

**Key Features:**
- Cross-source semantic search (Confluence + files + more)
- Similarity-based retrieval using vector embeddings
- Fast knowledge base queries
- Understand meaning and context, not just keywords

**Available Tool:**
- `retrieve_information` - Search indexed content semantically

**Use Cases:**
- Search across all document types simultaneously
- Find similar or related content
- Answer questions from knowledge base
- Discover documentation when you don't know exact keywords
- Cross-reference multiple sources

---

## Tool Selection Guide

### When to Use Real-Time Tools (Confluence, Jira, GitHub, Datadog)

✅ **Preferred** when:
- Need **latest/current/up-to-date** information
- Querying specific service (e.g., "search Confluence", "check Datadog metrics")
- Listing/discovering resources (spaces, projects, repos)
- Real-time accuracy is critical
- User asks about specific system

**Examples:**
- "What's in the DEV Confluence space?"
- "Show me recent Jira issues"
- "Check current system metrics"
- "List GitHub repositories"

### When to Use Vector Store

✅ **Use** when:
- User explicitly requests "search knowledge base" or "search all documents"
- Need **cross-source semantic search** (Confluence + files + URLs)
- Semantic similarity more important than real-time accuracy
- Real-time tools unavailable
- User asks to search "entire knowledge base"

**Examples:**
- "Search all knowledge base for API patterns"
- "Find similar documents about microservices"
- "What do we have about testing?" (broad, cross-source)

---

## Configuration

All tools are configured in `resources/application-tools.yaml`:

```yaml
tools:
  confluence:
    enabled: true
    available_tools:
      # Tool configuration...
  
  jira:
    enabled: true
    available_tools:
      # Tool configuration...
  
  github:
    enabled: true
    available_tools:
      # Tool configuration...
  
  datadog:
    enabled: true
    available_tools:
      # Tool configuration...
  
  vector:
    enabled: true
    available_tools:
      # Tool configuration...
```

### LLM Guidance

System prompts in `resources/application-prompt.yaml` guide the LLM on:
- When to use each tool category
- Decision criteria for tool selection
- Examples of good tool choices
- Fallback strategies

---

## Implementation Pattern

All tool integrations follow a consistent pattern:

### 1. Tool Registry
```python
@ToolRegistry.register("tool_name", "category")
class ToolProvider:
    def get_tools(self) -> List[StructuredTool]:
        return [tool1, tool2, tool3]
```

### 2. Lazy Service Loading
```python
@property
def service(self):
    if self._service is None:
        from app.services.external.service import Service
        self._service = Service()
    return self._service
```

### 3. Service Availability Check
```python
def tool_function(param: str) -> str:
    service = self.service
    if not service:
        return json.dumps({"status": "error", "error": "Service not available"})
    
    # Tool implementation...
```

### 4. Structured Tool Definition
```python
from langchain.pydantic_v1 import BaseModel, Field

class ToolInput(BaseModel):
    param: str = Field(..., description="Parameter description")

tool = StructuredTool.from_function(
    func=tool_function,
    name="tool_name",
    description="Tool description",
    args_schema=ToolInput
)
```

---

## Adding New Tools

To add a new tool integration:

1. **Implement Service** (if needed):
   - Create in `src/app/services/external/`
   - Follow singleton or factory pattern
   - Add credentials to `resources/application-external.yaml`

2. **Create Tool Provider**:
   - Create in `src/app/agent/tools/<category>/`
   - Use `@ToolRegistry.register()` decorator
   - Implement `get_tools()` method
   - Follow lazy loading pattern

3. **Configure Tools**:
   - Add to `resources/application-tools.yaml`
   - Define enabled state and categories

4. **Update Prompts**:
   - Add to `resources/application-prompt.yaml`
   - Provide LLM guidance on when to use
   - Add examples

5. **Write Tests**:
   - Create unit tests in `tests/unit/agent/tools/`
   - Mock external services
   - Test all scenarios (success, errors, unavailable)

6. **Document**:
   - Create guide in `docs/guides/tools/`
   - Follow existing pattern (see confluence-tools.md, datadog-tools.md)
   - Update this README

---

## Testing Tools

All tools have comprehensive unit tests in `tests/unit/agent/tools/`:

```bash
# Run all tool tests
pytest tests/unit/agent/tools/

# Run specific tool tests
pytest tests/unit/agent/tools/test_confluence_tools.py

# Run with coverage
pytest tests/unit/agent/tools/ --cov=src/app/agent/tools --cov-report=html
```

**Testing Best Practices:**
- ✅ Mock all external service calls
- ✅ Test success scenarios
- ✅ Test error scenarios
- ✅ Test service unavailable scenarios
- ✅ Test parameter validation
- ✅ Use PropertyMock for property mocking

---

## Related Documentation

- [Configuration System](../configuration/resources-directory.md) - How tool configuration works
- [LLM Integration](../llm-providers/README.md) - How LLMs use tools
- [Architecture Overview](../../architecture/overview.md) - System design
- [RAG Pipeline](../../core-concepts/rag-pipeline.md) - Vector store approach

---

## Tool Comparison

| Tool | Real-Time | Cost | Latency | Use Case |
|------|-----------|------|---------|----------|
| **Confluence** | ✅ Yes | API calls | ~500ms | Latest documentation |
| **Jira** | ✅ Yes | API calls | ~500ms | Current issue status |
| **GitHub** | ✅ Yes | API calls | ~500ms | Repository data |
| **Datadog** | ✅ Yes | API calls | ~500ms | System metrics |
| **Vector Store** | ❌ Embedded | Embedding | ~100ms | Cross-source search |

---

## Summary

AgentHub's tool system provides:
- ✅ **Real-time access** to external services
- ✅ **Configuration-driven** enabling/disabling
- ✅ **LLM-guided** intelligent tool selection
- ✅ **Comprehensive documentation** for each integration
- ✅ **Consistent patterns** across all tools
- ✅ **Production-ready** error handling

Each tool integration is documented with examples, use cases, configuration, and best practices. Start with the specific tool guide that matches your needs.
