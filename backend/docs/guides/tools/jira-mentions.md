# Jira User Mentions in Comments

This guide explains how to mention users in Jira comments using the AgentHub Jira tools.

## Overview

Jira Cloud uses the **Atlassian Document Format (ADF)** for rich text content, including comments. To mention a user in a comment, you need to use ADF JSON format with the user's **Account ID**.

## Quick Start

### 1. List or Search for Users

You have three options to find users:

#### Option A: Search for a specific user
```python
# Search for a user by name or email
result = jira_tools.search_jira_users(
    query="john.doe@example.com",
    max_results=10
)
```

#### Option B: Get all users in the system
```python
# Get all users (with pagination)
result = jira_tools.get_all_jira_users(
    start_at=0,
    max_results=50
)
```

#### Option C: Get users for a specific project
```python
# Get users who have access to a project
result = jira_tools.get_jira_project_users(
    project_key="MYPROJ",
    max_results=50
)
```

All options return users in the same format:
```json
{
  "status": "success",
  "total_results": 1,
  "users": [
    {
      "account_id": "5b10ac8d82e05b22cc7d4ef5",
      "display_name": "John Doe",
      "email": "john.doe@example.com",
      "active": true
    }
  ]
}
```

### 2. Add Comment with Mention (Simple)

For a simple mention with text:

```python
import json
from app.agent.tools.atlassian.jira import JiraTools

# Create ADF with mention
adf = JiraTools.create_mention_adf(
    account_id="5b10ac8d82e05b22cc7d4ef5",
    display_name="John Doe",
    additional_text=" please review this issue"
)

# Add comment
result = jira_tools.add_jira_comment(
    issue_key="PROJ-123",
    comment_body=json.dumps(adf)
)
```

### 3. Add Comment with Multiple Mentions

For complex comments with multiple mentions and text:

```python
import json
from app.agent.tools.atlassian.jira import JiraTools

# Create comment with multiple parts
text_parts = [
    {"type": "text", "content": "Hello "},
    {"type": "mention", "account_id": "5b10ac8d82e05b22cc7d4ef5", "display_name": "John Doe"},
    {"type": "text", "content": " and "},
    {"type": "mention", "account_id": "6c20bd9e93f16c33dd8e5fg6", "display_name": "Jane Smith"},
    {"type": "text", "content": ", please review this critical issue!"}
]

adf = JiraTools.create_comment_with_mentions(text_parts)

# Add comment
result = jira_tools.add_jira_comment(
    issue_key="PROJ-123",
    comment_body=json.dumps(adf)
)
```

### 4. Plain Text Comments (No Mentions)

You can still add plain text comments without mentions:

```python
# Add simple text comment
result = jira_tools.add_jira_comment(
    issue_key="PROJ-123",
    comment_body="This is a simple comment without mentions"
)
```

## ADF Format Explained

### Basic ADF Structure

```json
{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {
          "type": "text",
          "text": "Your text here"
        }
      ]
    }
  ]
}
```

### Mention Node

```json
{
  "type": "mention",
  "attrs": {
    "id": "account-id-here",
    "text": "@DisplayName"
  }
}
```

### Complete Example

```json
{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {
          "type": "text",
          "text": "Hey "
        },
        {
          "type": "mention",
          "attrs": {
            "id": "5b10ac8d82e05b22cc7d4ef5",
            "text": "@John Doe"
          }
        },
        {
          "type": "text",
          "text": " can you take a look at this?"
        }
      ]
    }
  ]
}
```

## Available Tools

### 1. `search_jira_users`
Search for users to get their Account IDs.

**Parameters:**
- `query` (str): Username, email, or display name
- `max_results` (int, optional): Maximum results (default: 50)

**Returns:** List of users with their account IDs

**Use Case:** When you know part of the user's name or email and want to find them specifically.

**Example:**
```python
result = jira_tools.search_jira_users(query="john.doe")
```

### 2. `get_all_jira_users`
Get a list of all users in the Jira instance.

**Parameters:**
- `start_at` (int, optional): Starting index for pagination (default: 0)
- `max_results` (int, optional): Maximum results (default: 50)

**Returns:** List of all users with their account IDs

**Use Case:** When you want to browse all available users or need pagination through the user list.

**Example:**
```python
# Get first 50 users
result = jira_tools.get_all_jira_users(max_results=50)

# Get next 50 users
result = jira_tools.get_all_jira_users(start_at=50, max_results=50)
```

### 3. `get_jira_project_users`
Get users who have access to a specific project.

**Parameters:**
- `project_key` (str): Project key (e.g., 'MYPROJ')
- `start_at` (int, optional): Starting index for pagination (default: 0)
- `max_results` (int, optional): Maximum results (default: 50)

**Returns:** List of users with access to the project

**Use Case:** When you want to find users who can be assigned or mentioned in issues for a specific project.

**Example:**
```python
result = jira_tools.get_jira_project_users(project_key="MYPROJ")
```

### 4. `add_jira_comment`
Add a comment to a Jira issue.

**Parameters:**
- `issue_key` (str): Issue key (e.g., 'PROJ-123')
- `comment_body` (str): Comment text (plain text or ADF JSON string)

**Returns:** Created comment details

## Helper Methods

### `create_mention_adf(account_id, display_name, additional_text="")`
Creates ADF for a single mention with optional text.

### `create_comment_with_mentions(text_parts)`
Creates ADF for complex comments with multiple mentions and text parts.

## Best Practices

1. **Choose the right tool for finding users:**
   - Use `search_jira_users` when you know part of the user's name/email
   - Use `get_jira_project_users` when working with project-specific issues
   - Use `get_all_jira_users` when you need to browse all users

2. **Always verify the user has access** to the issue before mentioning them

3. **Use display names** that match the user's actual Jira profile

4. **Test with plain text** before adding complex mentions

5. **Handle errors** - users might not exist or might not have access

6. **Serialize ADF to JSON** when passing to `add_jira_comment`

7. **Consider pagination** - If you need to find a user from a large organization, use pagination with `start_at`

## Complete Workflow Example

Here's a complete example showing how an LLM can help find and mention users:

```python
import json
from app.agent.tools.atlassian.jira import JiraTools

# Step 1: List users in a specific project to find who to tag
project_users = jira_tools.get_jira_project_users(
    project_key="PROJ",
    max_results=20
)

# Step 2: LLM identifies the right person based on context
# For example, finding the team lead or a specific developer
# The LLM can parse the response and select: account_id="5b10ac8d..."

# Step 3: Create comment with mention
text_parts = [
    {"type": "text", "content": "Hi "},
    {"type": "mention", "account_id": "5b10ac8d82e05b22cc7d4ef5", "display_name": "John Doe"},
    {"type": "text", "content": ", this issue needs your attention for review."}
]

adf = JiraTools.create_comment_with_mentions(text_parts)

# Step 4: Add the comment
result = jira_tools.add_jira_comment(
    issue_key="PROJ-123",
    comment_body=json.dumps(adf)
)
```

## LLM Usage Examples

### Example 1: Find and mention the project lead

**User:** "Add a comment to PROJ-123 mentioning the project lead"

**LLM Actions:**
1. Call `get_jira_project_users(project_key="PROJ")`
2. Identify the lead from the user list (or from project info)
3. Create mention ADF with the lead's account_id
4. Call `add_jira_comment()` with the ADF

### Example 2: Mention multiple team members

**User:** "Mention John and Jane in a comment on PROJ-456 asking for code review"

**LLM Actions:**
1. Call `search_jira_users(query="John")` to find John's account_id
2. Call `search_jira_users(query="Jane")` to find Jane's account_id
3. Create comment with multiple mentions using `create_comment_with_mentions()`
4. Call `add_jira_comment()` with the ADF

### Example 3: Browse and select from all users

**User:** "Show me all developers and let me pick who to mention"

**LLM Actions:**
1. Call `get_all_jira_users()` or `get_jira_project_users()`
2. Present the list to the user
3. User selects specific person(s)
4. Create and add comment with selected mentions

## Best Practices

1. **Always search for users first** to get the correct Account ID
2. **Use display names** that match the user's actual Jira profile
3. **Test with plain text** before adding complex mentions
4. **Handle errors** - users might not exist or might not have access
5. **Serialize ADF to JSON** when passing to `add_jira_comment`

## Common Issues

### Issue: Mention doesn't notify the user
**Solution:** Ensure the Account ID is correct and the user has access to the issue.

### Issue: Comment appears as plain text
**Solution:** Make sure you're passing ADF as a JSON string, not a Python dict.

### Issue: User search returns no results
**Solution:** Try different search terms (email, username, or partial display name).

## References

- [Atlassian Document Format Documentation](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)
- [Mention Node Specification](https://developer.atlassian.com/cloud/jira/platform/apis/document/nodes/mention/)
