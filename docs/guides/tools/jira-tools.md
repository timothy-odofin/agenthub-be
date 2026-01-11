# Jira Tools Integration

Connect your AI agents to Atlassian Jira for issue tracking and project management.

## Overview

This integration enables AI agents to interact with your Jira workspace to:
- List and explore Jira projects
- Create new issues and tasks
- Retrieve issue details and status
- Search issues using JQL (Jira Query Language)

## Features

- **Project Discovery** - List all accessible Jira projects
- **Issue Creation** - Create tasks, bugs, stories, and other issue types
- **Issue Retrieval** - Get detailed information about specific issues
- **Flexible Search** - Search using JQL for advanced queries
- **Easy Configuration** - YAML-based settings

## Setup

### Getting Your Atlassian API Token

You'll need an API token to authenticate with Jira:

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "AI Agent Integration")
4. Copy the token immediately (it's only shown once)

### Configuration

Add these environment variables to your `.env` file:

```bash
ATLASSIAN_API_KEY=your_api_token_here
ATLASSIAN_EMAIL=your.email@company.com
ATLASSIAN_BASE_URL=https://yourcompany.atlassian.net
```

Enable the tools in `resources/application-tools.yaml`:

```yaml
tools:
  jira:
    enabled: true
```

## Available Tools

### List Projects

Get all Jira projects you have access to.

**Parameters:** None

**Example:**

```python
get_jira_projects()
```

**Response:**

```json
{
  "status": "success",
  "total_projects": 3,
  "projects": [
    {
      "key": "PROJ",
      "name": "Main Project",
      "id": "10001",
      "description": "Our main development project",
      "project_type": "software",
      "lead": "John Doe"
    }
  ]
}
```

**Common Uses:**
- Discover available projects
- Verify access to projects
- Get project keys for issue creation

---

### Create Issue

Create a new Jira issue in a project.

**Parameters:**
- `project_key` - The Jira project key (e.g., "PROJ")
- `summary` - Brief description of the issue
- `description` - Detailed description (optional)
- `issue_type` - Type of issue: Task, Bug, Story, etc. (optional, default: "Task")

**Examples:**

```python
# Create a simple task
create_jira_issue(
    project_key="PROJ",
    summary="Update user authentication"
)

# Create a bug with full details
create_jira_issue(
    project_key="PROJ",
    summary="Login button not working",
    description="Users cannot click the login button on mobile devices",
    issue_type="Bug"
)

# Create a user story
create_jira_issue(
    project_key="PROJ",
    summary="As a user, I want to reset my password",
    description="User should be able to reset password via email link",
    issue_type="Story"
)
```

**Response:**

```json
{
  "status": "success",
  "issue": {
    "key": "PROJ-123",
    "id": "10456",
    "self": "https://yourcompany.atlassian.net/rest/api/2/issue/10456"
  },
  "summary": "Update user authentication",
  "project": "PROJ"
}
```

**Common Uses:**
- Create tasks from user requests
- Log bugs automatically
- Generate user stories
- Track action items from meetings

---

### Get Issue

Retrieve detailed information about a specific Jira issue.

**Parameters:**
- `issue_key` - The Jira issue key (e.g., "PROJ-123")

**Example:**

```python
get_jira_issue(issue_key="PROJ-123")
```

**Response:**

```json
{
  "status": "success",
  "issue": {
    "key": "PROJ-123",
    "summary": "Update user authentication",
    "status": "In Progress",
    "priority": "High",
    "assignee": "Jane Smith",
    "reporter": "John Doe",
    "created": "2026-01-08T10:30:00Z",
    "updated": "2026-01-09T14:20:00Z",
    "description": "Implement OAuth2 authentication...",
    "issue_type": "Task",
    "labels": ["security", "authentication"],
    "components": ["Backend", "API"]
  }
}
```

**Common Uses:**
- Check issue status
- Get issue details for reporting
- Verify issue assignments
- Track progress

---

### Search Issues

Search for Jira issues using JQL (Jira Query Language).

**Parameters:**
- `jql` - JQL query string
- `max_results` - Maximum number of results (optional, default: 50)

**Example Queries:**

```python
# Find all open issues in a project
search_jira_issues(
    jql="project = PROJ AND status = Open"
)

# Find high priority bugs
search_jira_issues(
    jql="project = PROJ AND issuetype = Bug AND priority = High"
)

# Find issues assigned to you
search_jira_issues(
    jql="assignee = currentUser() AND status != Done"
)

# Find recently updated issues
search_jira_issues(
    jql="project = PROJ AND updated >= -7d"
)

# Complex query with multiple criteria
search_jira_issues(
    jql="project = PROJ AND status IN (Open, 'In Progress') AND priority >= High",
    max_results=100
)
```

**Response:**

```json
{
  "status": "success",
  "jql": "project = PROJ AND status = Open",
  "max_results": 50,
  "search_results": {
    "total": 15,
    "issues": [
      {
        "key": "PROJ-123",
        "summary": "Update user authentication",
        "status": "Open",
        "priority": "High",
        "created": "2026-01-08T10:30:00Z",
        "issuetype": "Task"
      }
    ]
  }
}
```

**JQL Tips:**
- Use `=` for exact matches, `~` for text search
- Combine conditions with `AND`, `OR`
- Use `IN` for multiple values: `status IN (Open, 'In Progress')`
- Date queries: `created >= -7d` (last 7 days)
- Functions: `currentUser()`, `now()`, `startOfDay()`

**Common Uses:**
- Find open issues in a project
- Search for bugs or specific issue types
- Find issues by status or priority
- Track recently created or updated issues
- Generate reports on issue metrics

---

## Usage Examples

### Finding Open Issues

**User:** "What issues are open in the PROJ project?"

**Agent Actions:**
1. Uses `search_jira_issues` with JQL: `"project = PROJ AND status = Open"`
2. Formats the results for the user

**Agent Response:**
```
Found 5 open issues in project PROJ:

1. PROJ-123: Update user authentication (High priority)
   - Status: In Progress
   - Assigned to: Jane Smith

2. PROJ-124: Add error logging (Medium priority)
   - Status: Open
   - Unassigned

3. PROJ-125: Improve API documentation (Low priority)
   - Status: Open
   - Assigned to: John Doe

[... more issues ...]
```

---

### Creating an Issue

**User:** "Create a task to update the deployment documentation"

**Agent Actions:**
1. Identifies the appropriate project (e.g., "PROJ")
2. Uses `create_jira_issue` with summary and project key
3. Confirms creation to user

**Agent Response:**
```
I've created a new task in Jira:

Issue: PROJ-126
Summary: Update deployment documentation
Type: Task
Project: PROJ
Status: Open

View issue: https://yourcompany.atlassian.net/browse/PROJ-126
```

---

### Checking Issue Status

**User:** "What's the status of PROJ-123?"

**Agent Actions:**
1. Uses `get_jira_issue` with key "PROJ-123"
2. Extracts relevant status information

**Agent Response:**
```
Here's the status of PROJ-123:

Title: Update user authentication
Status: In Progress
Priority: High
Assignee: Jane Smith
Reporter: John Doe

Created: Jan 8, 2026
Last Updated: Jan 9, 2026 (today)

Description: Implement OAuth2 authentication for improved security...

Labels: security, authentication
```

---

## Best Practices

### Project Keys
- Always verify the project key before creating issues
- Use `get_jira_projects` to discover available projects
- Project keys are case-sensitive (usually uppercase)

### Issue Creation
- Provide clear, concise summaries
- Include enough detail in descriptions
- Choose appropriate issue types (Task, Bug, Story, etc.)
- Consider adding labels or components for better organization

### JQL Queries
- Start with simple queries, then add complexity
- Test queries in Jira's search interface first
- Use parentheses for complex logic: `(A OR B) AND C`
- Be specific to avoid returning too many results
- Use the `max_results` parameter to limit large result sets

### Performance
- Limit search results to what you need (use `max_results`)
- Use specific JQL queries rather than broad searches
- Cache project information if querying frequently

## Troubleshooting

### Service Not Available Error

If you see "Jira service not available":

1. Check your environment variables:
   ```bash
   ATLASSIAN_API_KEY=your_token
   ATLASSIAN_EMAIL=your_email
   ATLASSIAN_BASE_URL=https://yourcompany.atlassian.net
   ```

2. Test your credentials:
   ```bash
   curl -u "your_email:your_token" \
     "https://yourcompany.atlassian.net/rest/api/2/myself"
   ```

3. Verify your API token hasn't expired

### Cannot Create Issue

Common issues:

1. **Invalid project key** - Use `get_jira_projects` to find valid keys
2. **Missing permissions** - Check you have create permissions in the project
3. **Invalid issue type** - Verify the issue type exists in the project

### No Search Results

If JQL queries return no results:

1. Test the JQL query in Jira's search interface
2. Check for typos in field names or values
3. Verify you have permission to view those issues
4. Simplify the query to debug (remove conditions one by one)

### Tools Not Showing Up

Make sure Jira tools are enabled in `resources/application-tools.yaml`:

```yaml
tools:
  jira:
    enabled: true
```

## Combining with Other Tools

Your AI agent can use Jira alongside other integrations:

- **Jira + GitHub** - Create issues from code review comments or pull requests
- **Jira + Confluence** - Link documentation to issues
- **Jira + Datadog** - Create issues from monitoring alerts
- **Jira + Vector Store** - Search knowledge base, then create related issues

## Additional Resources

**Atlassian Documentation:**
- [Jira REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v2/intro/)
- [JQL (Jira Query Language)](https://www.atlassian.com/software/jira/guides/expand-jira/jql)
- [API Authentication](https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/)
- [Issue Types](https://support.atlassian.com/jira-cloud-administration/docs/what-are-issue-types/)

**Related Documentation:**
- [Confluence Tools](./confluence-tools.md)
- [All Available Tools](./README.md)
- [Configuration Guide](../configuration/resources-directory.md)

---

This integration brings Jira's powerful issue tracking directly to your AI agents, enabling them to help manage projects, track tasks, and keep your team organized.
