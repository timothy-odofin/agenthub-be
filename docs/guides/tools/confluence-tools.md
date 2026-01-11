# Confluence Tools Integration

Connect your AI agents to Atlassian Confluence for real-time access to your team's documentation.

## Overview

This integration enables AI agents to interact with your Confluence workspace to:
- List and explore Confluence spaces
- Search for pages across your documentation
- Retrieve full page content with metadata
- Access the latest information directly from Confluence

## Two Ways to Access Confluence

This project supports two complementary methods for accessing Confluence content:

### Real-Time API Access (This Guide)
Directly query Confluence through its API for the most current information.

**Best for:**
- Getting the latest page content
- Searching for specific documentation
- Listing available spaces and pages
- When real-time accuracy is critical

**Trade-offs:**
- Requires an API call for each query
- Depends on Confluence being available

### Embedded Content (Vector Store)
Pre-processed Confluence content stored in a vector database for semantic search.

**Best for:**
- Searching across multiple sources (Confluence + files + other documents)
- Semantic similarity queries
- When you need fast responses without API calls

**Trade-offs:**
- Content may be slightly outdated
- Requires periodic re-indexing
- Embedding processing costs

Both approaches work together - the AI agent automatically chooses the best method based on your query.

## Features

- **Real-Time Access** - Always get current content from Confluence
- **Space Discovery** - List and explore all accessible spaces
- **Flexible Search** - Find pages by keyword or CQL query
- **Complete Metadata** - Get page history, authors, and modification dates
- **Easy Configuration** - YAML-based settings  

## Setup

### Getting Your Atlassian API Token

You'll need an API token to authenticate with Confluence:

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "AI Agent Integration")
4. Copy the token immediately (it's only shown once)

### Configuration

Add these environment variables to your `.env` file:

```bash
ATLASSIAN_API_KEY=your_api_token_here
ATLASSIAN_EMAIL=your.email@company.com
ATLASSIAN_BASE_URL_CONFLUENCE=https://yourcompany.atlassian.net
```

Enable the tools in `resources/application-tools.yaml`:

```yaml
tools:
  confluence:
    enabled: true
```

## Available Tools

### List Spaces

Get a list of all Confluence spaces you have access to.

**Parameters:**
- `space_keys` - Specific space keys to retrieve (optional, default: all spaces)

**Examples:**
```python
# List all accessible spaces
list_confluence_spaces(space_keys=["*"])

# List specific spaces
list_confluence_spaces(space_keys=["DEV", "PROD", "SD"])
```

**Response Format:**
```json
{
  "status": "success",
  "total_spaces": 3,
  "space_keys": ["DEV", "PROD", "SD"]
}
```

**Common Uses:**
- Discover what documentation spaces exist
- Verify access to specific spaces
- List all available workspaces

---

### Get Space Details

Retrieve detailed information about a specific Confluence space.

**Parameters:**
- `space_key` - The Confluence space key (e.g., "DEV")

**Example:**
```python
get_confluence_space(space_key="DEV")
```

**Response Format:**
```json
{
  "status": "success",
  "space": {
    "key": "DEV",
    "name": "Development",
    "id": "12345",
    "type": "global",
    "description": "Development space for the team",
    "homepage": {
      "id": "111",
      "title": "Dev Home"
    },
    "url": "/wiki/spaces/DEV"
  }
}
```

**Common Uses:**
- Get space name and description
- Find the space homepage
- Check space configuration

---

### List Pages in Space

Get all pages within a specific Confluence space.

**Parameters:**
- `space_key` - The Confluence space key
- `max_results` - Maximum number of pages to return (optional, default: 50)

**Examples:**
```python
# List first 50 pages in DEV space
list_pages_in_space(space_key="DEV")

# List more pages
list_pages_in_space(space_key="PROD", max_results=100)
```

**Response Format:**
```json
{
  "status": "success",
  "space_key": "DEV",
  "total_pages": 25,
  "returned_pages": 25,
  "pages": [
    {
      "id": "111",
      "title": "API Documentation",
      "type": "page",
      "status": "current",
      "url": "/wiki/spaces/DEV/pages/111",
      "version": 5,
      "last_modified": "2026-01-05T10:30:00Z"
    }
  ]
}
```

**Common Uses:**
- Browse all pages in a space
- Find recently updated documentation
- Generate a content inventory
- Understand documentation structure

---

### Search Pages

Search for Confluence pages by keyword or phrase.

**Parameters:**
- `query` - Search text
- `space_key` - Limit search to specific space (optional)
- `max_results` - Maximum results to return (optional, default: 10)

**Examples:**
```python
# Search across all spaces
search_confluence_pages(query="API authentication")

# Search within specific space
search_confluence_pages(query="deployment guide", space_key="DEV")

# Get more results
search_confluence_pages(query="microservices", max_results=20)
```

**Response Format:**
```json
{
  "status": "success",
  "query": "API authentication",
  "space_key": null,
  "total_results": 5,
  "returned_results": 5,
  "results": [
    {
      "id": "111",
      "title": "API Authentication Guide",
      "type": "page",
      "space": "DEV",
      "url": "/wiki/spaces/DEV/pages/111",
      "excerpt": "This guide covers OAuth2 and JWT authentication..."
    }
  ]
}
```

**Search Tips:**
- Use specific keywords for better results
- Combine terms: "API authentication OAuth"
- Filter by space for targeted results
- Natural language queries work well

**Common Uses:**
- Find documentation by topic
- Locate specific guides or tutorials
- Search for technical information
- Discover related content

---

### Get Page Content

Retrieve the complete content and metadata of a specific page.

**Parameters:**
- `page_id` - The Confluence page ID

**Example:**
```python
# Get page by ID (from search results or direct reference)
get_confluence_page(page_id="123456789")
```

**Response Format:**
```json
{
  "status": "success",
  "page_id": "123456789",
  "content": "# API Authentication Guide\n\nThis guide covers...",
  "metadata": {
    "page_id": "123456789",
    "title": "API Authentication Guide",
    "space": "DEV",
    "space_name": "Development",
    "url": "/wiki/spaces/DEV/pages/123456789",
    "last_modified": "2026-01-05T10:30:00Z",
    "version": 5,
    "breadcrumb": "Home > Development > API Authentication Guide"
  }
}
```

**Common Uses:**
- Read complete documentation pages
- Get the latest version of content
- Extract metadata for tracking
- Access full text for analysis

---

## Usage Examples

### Discovering Available Spaces

**User Query:** "What Confluence spaces do we have?"

**LLM Reasoning:**
```
Thought: User wants to see available Confluence spaces. I should use list_confluence_spaces.
Action: Use list_confluence_spaces tool
Observation: Returns ["DEV", "PROD", "SD", "agenthubdo"]
```

**Agent Response:**
```
Here are the available Confluence spaces:
- DEV (Development)
- PROD (Production)  
- SD (System Design)
- agenthubdo (AgentHub Documentation)
```

---

### Searching for Documentation

**User Query:** "Find documentation about API authentication"

**LLM Reasoning:**
```
Thought: User is looking for Confluence documentation. I should use search_confluence_pages 
for real-time results rather than vector store.
Action: Use search_confluence_pages with query "API authentication"
Observation: Returns 3 pages from DEV and SD spaces
```

**Agent Response:**
```
I found 3 Confluence pages about API authentication:

1. **API Authentication Guide** (DEV space)
   - Covers OAuth2 and JWT implementation
   - Last updated: Jan 5, 2026
   - [View page](/wiki/spaces/DEV/pages/111)

2. **Security Best Practices** (SD space)
   - Includes authentication patterns and security guidelines
   - [View page](/wiki/spaces/SD/pages/222)

3. **OAuth Integration Tutorial** (DEV space)
   - Step-by-step OAuth2 setup guide
   - [View page](/wiki/spaces/DEV/pages/333)
```

---

### Getting Latest Page Content

**User Query:** "Show me the deployment guide"

**LLM Reasoning:**
```
Thought: User wants specific page content. I'll first search for it, then retrieve full content.
Action 1: Use search_confluence_pages with query "deployment guide"
Observation: Found page ID 456789 in PROD space
Action 2: Use get_confluence_page with page_id="456789"
Observation: Returns full content and metadata
```

**Agent Response:**
```
Here's the Deployment Guide from Confluence (last updated: Jan 8, 2026):

# Deployment Guide

## Prerequisites
- Docker installed
- Access to production environment
- Valid SSL certificates

## Deployment Steps
1. Build Docker image: `docker build -t app:latest .`
2. Push to registry: `docker push registry.company.com/app:latest`
3. Deploy to production: `kubectl apply -f k8s/production/`
...

Source: [Deployment Guide](/wiki/spaces/PROD/pages/456789)
Version: 12 (most recent)
```

---

### Cross-Source Semantic Search

**User Query:** "Search all knowledge base for microservices architecture examples"

**LLM Reasoning:**
```
Thought: User explicitly wants to search "all knowledge base" which includes files, 
Confluence, and other sources. Vector store is better for this cross-source semantic search.
Action: Use vector store search tool
Observation: Returns documents from Confluence, PDFs, and markdown files
```

**Agent Response:**
```
I searched across all knowledge sources and found microservices architecture examples in:

**Confluence Pages** (3 results):
- Microservices Design Patterns (SD space)
- Service Mesh Implementation (DEV space)

**PDF Documents** (2 results):
- Architecture Decision Records (uploaded files)
- System Design Handbook

**Markdown Files** (5 results):
- README files from various services
- Technical specifications

[Detailed summaries with links...]
```

---

## When to Use Which Approach

### Use Real-Time Confluence Tools

**Best for:**
- Queries specifically about Confluence content
- Questions like "What's in Confluence?" or "Show me the latest docs"
- When you need current, up-to-date information
- Listing spaces or pages
- Real-time accuracy matters

**Example queries:**
- "What pages are in the DEV space?"
- "Search Confluence for authentication docs"
- "Show me the latest onboarding guide"
- "List all Confluence spaces"
- "Get the current deployment guide"

### Use Vector Store (Semantic Search)

**Best for:**
- Searching across multiple sources (Confluence + files + other docs)
- Finding similar or related content
- When user explicitly requests "search knowledge base"
- Semantic similarity more important than real-time data

**Example queries:**
- "Search all documentation for API patterns"
- "Find similar documents about microservices"
- "What do we have about testing?" (broad search)
- "Search the knowledge base for security practices"

---

## Best Practices

### Search Strategy
- Start with `search_confluence_pages` to find relevant pages
- Use `list_pages_in_space` when you know the space
- Chain operations: search first, then get full page content

### Performance Tips
- Use `max_results` to limit response size
- Filter by `space_key` when you know the space
- Cache frequently accessed page IDs

### User Experience
- Include Confluence URLs in responses
- Show last modified dates
- Be clear whether content is real-time or from cache

---

## Troubleshooting

### Service Not Available Error

If you see "Confluence service not available":

1. Check your environment variables are set correctly:
   ```bash
   ATLASSIAN_API_KEY=your_token
   ATLASSIAN_EMAIL=your_email
   ATLASSIAN_BASE_URL_CONFLUENCE=https://yourcompany.atlassian.net
   ```

2. Test your credentials manually:
   ```bash
   curl -u "your_email:your_token" \
     "https://yourcompany.atlassian.net/wiki/rest/api/space"
   ```

3. Verify your API token hasn't expired

### Can't Retrieve Page

If you can't access a specific page:

1. Verify the page ID is correct
2. Check you have permission to access that space
3. Make sure the page hasn't been deleted or archived
4. Try searching for the page first

### No Search Results

If searches return no results:

1. Try broader search terms
2. Remove space filters to search everywhere
3. Use synonyms (e.g., "auth" instead of "authentication")
4. Consider using vector store for semantic search

### Tools Not Showing Up

Make sure Confluence tools are enabled in `resources/application-tools.yaml`:

```yaml
tools:
  confluence:
    enabled: true
```

---

## Extending the Integration

You can add additional Confluence capabilities by:

1. Adding methods to the service layer (`src/app/services/external/confluence_service.py`)
2. Creating new tool functions (`src/app/agent/tools/atlassian/confluence.py`)
3. Enabling the new tools in configuration
4. Writing tests for the new functionality

### Running Tests

The integration includes comprehensive unit tests:

```bash
pytest tests/unit/agent/tools/test_confluence_tools.py -v
```

---

## Combining with Other Tools

Your AI agent can use Confluence alongside other integrations:

- **Confluence + GitHub** - Find docs, then check related code
- **Confluence + Jira** - Read documentation, then create or check tickets
- **Confluence + Datadog** - Analyze errors, then search docs for solutions
- **Confluence + Vector Store** - Combine real-time Confluence data with broader semantic search

## Additional Resources

**Atlassian Documentation:**
- [Confluence REST API](https://developer.atlassian.com/cloud/confluence/rest/v1/intro/)
- [API Authentication](https://developer.atlassian.com/cloud/confluence/basic-auth-for-rest-apis/)
- [CQL (Confluence Query Language)](https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/)

**Related Documentation:**
- [Datadog Tools](./datadog-tools.md)
- [All Available Tools](./README.md)
- [Configuration Guide](../configuration/resources-directory.md)

---

This integration brings your Confluence documentation directly to your AI agents, enabling them to answer questions, find information, and help your team navigate your knowledge base more effectively.
