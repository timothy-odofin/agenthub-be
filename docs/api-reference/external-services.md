# External Services API

> 🔌 **Integration with Jira, Confluence, and other external services**

## Overview

AgentHub integrates with external services to provide seamless access to organizational data through AI agents. Currently supports Atlassian products (Jira, Confluence).

**Base Path**: `/api/v1/external/`  
**Authentication**: Required (JWT Bearer token)  
**Status**: Planned (configuration ready)

---

## Supported Services

### Atlassian Services

| Service | Status | Purpose |
|---------|--------|---------|
| **Jira** | ✅ Configured | Issue tracking, project management |
| **Confluence** | ✅ Configured | Documentation, knowledge base |

### Coming Soon

| Service | Status | Purpose |
|---------|--------|---------|
| **GitHub** | 🔄 Planned | Code repositories, issues, PRs |
| **Slack** | 🔄 Planned | Team communication |
| **Google Drive** | 🔄 Planned | Document storage |
| **Microsoft Teams** | 🔄 Planned | Team collaboration |

---

## Configuration

### Jira Configuration

**File**: `resources/application-external.yaml`

```yaml
external:
  jira:
    base_url: "https://your-domain.atlassian.net"
    email: "your-email@example.com"
    api_token: "${JIRA_API_TOKEN}"
    project_keys:
      - "PROJ"
      - "DEV"
      - "OPS"
    enabled: true
```

**Environment Variables**:
```bash
export JIRA_API_TOKEN="your_jira_api_token"
```

**Get Jira API Token**:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the token
4. Set as environment variable

---

### Confluence Configuration

**File**: `resources/application-external.yaml`

```yaml
external:
  confluence:
    base_url: "https://your-domain.atlassian.net/wiki"
    email: "your-email@example.com"
    api_token: "${CONFLUENCE_API_TOKEN}"
    spaces:
      - "ENG"
      - "DOCS"
      - "PROD"
    enabled: true
```

**Environment Variables**:
```bash
export CONFLUENCE_API_TOKEN="your_confluence_api_token"
```

**Get Confluence API Token**:
Same as Jira (Atlassian uses the same token for both services)

---

## Planned Endpoints

### Jira API

#### GET /jira/issues

List Jira issues filtered by project, status, assignee, etc.

**Planned Request**:
```bash
curl "http://localhost:8000/api/v1/external/jira/issues?project=PROJ&status=Open" \
  -H "Authorization: Bearer eyJhbGci..."
```

**Planned Response**:
```json
{
  "issues": [
    {
      "key": "PROJ-123",
      "summary": "Implement user authentication",
      "status": "In Progress",
      "assignee": "john.doe@example.com",
      "priority": "High",
      "created": "2026-01-05T10:00:00Z",
      "updated": "2026-01-10T14:30:00Z",
      "description": "Implement JWT-based authentication...",
      "url": "https://your-domain.atlassian.net/browse/PROJ-123"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50
}
```

---

#### GET /jira/issues/{issue_key}

Get detailed information about a specific Jira issue.

**Planned Request**:
```bash
curl http://localhost:8000/api/v1/external/jira/issues/PROJ-123 \
  -H "Authorization: Bearer eyJhbGci..."
```

**Planned Response**:
```json
{
  "key": "PROJ-123",
  "summary": "Implement user authentication",
  "description": "Implement JWT-based authentication with access and refresh tokens...",
  "status": "In Progress",
  "assignee": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "avatar": "https://..."
  },
  "priority": "High",
  "labels": ["authentication", "security"],
  "components": ["Backend", "API"],
  "created": "2026-01-05T10:00:00Z",
  "updated": "2026-01-10T14:30:00Z",
  "comments": [
    {
      "author": "jane.smith@example.com",
      "body": "Added login endpoint",
      "created": "2026-01-08T12:00:00Z"
    }
  ],
  "attachments": [
    {
      "filename": "auth_diagram.png",
      "url": "https://..."
    }
  ],
  "url": "https://your-domain.atlassian.net/browse/PROJ-123"
}
```

---

#### POST /jira/issues

Create a new Jira issue.

**Planned Request**:
```bash
curl -X POST http://localhost:8000/api/v1/external/jira/issues \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{
    "project": "PROJ",
    "summary": "Fix login bug",
    "description": "Users unable to login with valid credentials",
    "issue_type": "Bug",
    "priority": "High",
    "assignee": "john.doe@example.com"
  }'
```

**Planned Response**:
```json
{
  "key": "PROJ-124",
  "url": "https://your-domain.atlassian.net/browse/PROJ-124",
  "message": "Issue created successfully"
}
```

---

### Confluence API

#### GET /confluence/pages

Search Confluence pages by title, space, or content.

**Planned Request**:
```bash
curl "http://localhost:8000/api/v1/external/confluence/pages?space=ENG&query=authentication" \
  -H "Authorization: Bearer eyJhbGci..."
```

**Planned Response**:
```json
{
  "pages": [
    {
      "id": "12345678",
      "title": "Authentication Architecture",
      "space": "ENG",
      "url": "https://your-domain.atlassian.net/wiki/spaces/ENG/pages/12345678",
      "excerpt": "This page describes our authentication system...",
      "created": "2025-12-01T10:00:00Z",
      "updated": "2026-01-10T14:00:00Z",
      "author": "john.doe@example.com"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50
}
```

---

#### GET /confluence/pages/{page_id}

Get full content of a Confluence page.

**Planned Request**:
```bash
curl http://localhost:8000/api/v1/external/confluence/pages/12345678 \
  -H "Authorization: Bearer eyJhbGci..."
```

**Planned Response**:
```json
{
  "id": "12345678",
  "title": "Authentication Architecture",
  "space": "ENG",
  "content": "# Authentication Architecture\n\n## Overview\n...",
  "content_html": "<h1>Authentication Architecture</h1>...",
  "url": "https://your-domain.atlassian.net/wiki/spaces/ENG/pages/12345678",
  "created": "2025-12-01T10:00:00Z",
  "updated": "2026-01-10T14:00:00Z",
  "author": {
    "name": "John Doe",
    "email": "john.doe@example.com"
  },
  "labels": ["architecture", "security"],
  "attachments": [
    {
      "filename": "auth_flow.png",
      "url": "https://..."
    }
  ]
}
```

---

## AI Agent Integration

### Asking About Jira Issues

```
User: "What are my open Jira tickets?"

AI Agent:
1. Calls GET /jira/issues?assignee=user@example.com&status=Open
2. Processes results
3. Responds: "You have 3 open tickets:
   - PROJ-123: Implement user authentication (High priority)
   - PROJ-125: Fix API response time (Medium priority)
   - DEV-42: Update documentation (Low priority)"
```

---

### Searching Confluence

```
User: "Find documentation about authentication"

AI Agent:
1. Calls GET /confluence/pages?query=authentication
2. Retrieves relevant pages
3. Responds: "I found 5 pages about authentication:
   1. Authentication Architecture (ENG space)
   2. JWT Token Guide (DOCS space)
   3. OAuth2 Integration (DOCS space)
   
   The main architecture page explains..."
```

---

## Service Connection Testing

### Python Example

```python
from app.services.atlassian_service import AtlassianService

# Test Jira connection
async def test_jira():
    service = AtlassianService()
    
    try:
        # Get test issue
        issue = await service.get_jira_issue("PROJ-1")
        print(f"✓ Jira connected: {issue['summary']}")
        return True
    except Exception as e:
        print(f"✗ Jira connection failed: {e}")
        return False

# Test Confluence connection
async def test_confluence():
    service = AtlassianService()
    
    try:
        # Search pages
        pages = await service.search_confluence_pages("test")
        print(f"✓ Confluence connected: Found {len(pages)} pages")
        return True
    except Exception as e:
        print(f"✗ Confluence connection failed: {e}")
        return False
```

---

## Authentication & Authorization

### API Token Security

**Best Practices**:

```bash
# ✅ GOOD - Use environment variables
export JIRA_API_TOKEN="your_token"

# ❌ BAD - Hardcode in config
api_token: "ATATxxxxxxxx"

# ✅ GOOD - Use secrets manager
export JIRA_API_TOKEN=$(aws secretsmanager get-secret-value --secret-id jira-token --query SecretString --output text)

# ✅ GOOD - Use .env file (local development)
# .env
JIRA_API_TOKEN=your_token
CONFLUENCE_API_TOKEN=your_token
```

### Token Permissions

Jira/Confluence API tokens inherit user permissions:

**Required Permissions**:
- ✅ Read issues (Jira)
- ✅ Create issues (Jira)
- ✅ Read pages (Confluence)
- ✅ Search content (Confluence)

---

## Error Handling

### Common Errors

```json
// Invalid Credentials (401)
{
  "error": "Authentication failed",
  "message": "Invalid Jira API token",
  "service": "jira"
}

// Forbidden (403)
{
  "error": "Authorization failed",
  "message": "User does not have access to project PROJ",
  "service": "jira"
}

// Not Found (404)
{
  "error": "Resource not found",
  "message": "Issue PROJ-999 does not exist",
  "service": "jira"
}

// Rate Limited (429)
{
  "error": "Rate limit exceeded",
  "message": "Too many requests to Jira API",
  "retry_after": 60,
  "service": "jira"
}

// Service Unavailable (503)
{
  "error": "Service unavailable",
  "message": "Jira API is currently down",
  "service": "jira"
}
```

---

## Rate Limiting

### Atlassian API Limits

**Jira Cloud**:
- 5 requests per second per user
- 60 requests per minute per user

**Confluence Cloud**:
- 5 requests per second per user
- 60 requests per minute per user

**AgentHub Handling**:
- ✅ Automatic retry with exponential backoff
- ✅ Request queuing
- ✅ Rate limit warnings

---

## Use Cases

### 1. Developer Assistant

```
User: "Create a bug ticket for login issue"

AI Agent:
- Extracts: issue type=Bug, summary="Login issue"
- Asks for missing details: description, priority
- Creates Jira ticket
- Responds: "Created PROJ-126: Login issue (High priority)"
```

---

### 2. Documentation Search

```
User: "How do we handle user authentication?"

AI Agent:
- Searches Confluence for "authentication"
- Retrieves relevant pages
- Summarizes key points
- Provides links to full documentation
```

---

### 3. Project Status

```
User: "What's the status of PROJ-123?"

AI Agent:
- Retrieves issue details
- Checks recent comments
- Reviews linked issues
- Responds: "PROJ-123 is In Progress. Last updated by Jane Smith 2 hours ago. 
  She added: 'Login endpoint complete, working on token refresh.'"
```

---

### 4. Knowledge Base Query

```
User: "Find all documentation about our API"

AI Agent:
- Searches Confluence spaces
- Filters by labels (API, documentation)
- Ranks by relevance
- Returns top 10 pages with summaries
```

---

## Configuration Management

### Service Status Check

```python
from app.core.config import get_settings

settings = get_settings()

# Check if services are enabled
jira_enabled = settings.external.jira.enabled
confluence_enabled = settings.external.confluence.enabled

# Get service URLs
jira_url = settings.external.jira.base_url
confluence_url = settings.external.confluence.base_url
```

---

### Dynamic Configuration

```yaml
# Enable/disable services without code changes
external:
  jira:
    enabled: true  # Toggle on/off
    timeout_seconds: 30
    retry_attempts: 3
  
  confluence:
    enabled: true
    timeout_seconds: 30
    retry_attempts: 3
```

---

## Testing

### Unit Tests

```python
import pytest
from app.services.atlassian_service import AtlassianService

@pytest.mark.asyncio
async def test_get_jira_issue():
    service = AtlassianService()
    issue = await service.get_jira_issue("PROJ-1")
    
    assert issue["key"] == "PROJ-1"
    assert "summary" in issue
    assert "status" in issue

@pytest.mark.asyncio
async def test_search_confluence():
    service = AtlassianService()
    pages = await service.search_confluence_pages("test")
    
    assert isinstance(pages, list)
    assert len(pages) > 0
```

### Integration Tests

```python
# tests/integration/test_jira_service_integration.py
@pytest.mark.integration
async def test_jira_connection():
    """Test actual Jira API connection."""
    service = AtlassianService()
    
    # This calls real Jira API
    issues = await service.list_jira_issues(project="PROJ", limit=1)
    assert len(issues) > 0
```

---

## Monitoring

### Service Health

```python
async def check_external_services():
    """Check health of external services."""
    health = {
        "jira": await test_jira_connection(),
        "confluence": await test_confluence_connection()
    }
    
    return health

async def test_jira_connection():
    try:
        service = AtlassianService()
        await service.get_jira_issue("PROJ-1")
        return {"status": "up", "response_time_ms": 120}
    except:
        return {"status": "down"}
```

---

## Future Enhancements

### GitHub Integration

```yaml
external:
  github:
    token: "${GITHUB_TOKEN}"
    organization: "your-org"
    repositories:
      - "repo1"
      - "repo2"
```

**Planned Features**:
- Search repositories
- List issues and PRs
- Create issues
- Review code

---

### Slack Integration

```yaml
external:
  slack:
    bot_token: "${SLACK_BOT_TOKEN}"
    channels:
      - "engineering"
      - "support"
```

**Planned Features**:
- Search messages
- Post messages
- Get channel info
- User lookups

---

## Related Documentation

- **[Configuration Guide](../guides/connections/README.md)** - External service configuration
- **[Ingestion API](./ingestion.md)** - Data ingestion from services
- **[Workers Guide](../guides/workers/README.md)** - Background processing

---

**Last Updated**: January 10, 2026  
**Status**: Configuration Ready (Endpoints Planned)

---
