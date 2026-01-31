# Jira "On Behalf Of" Comments

This guide explains how to add Jira comments that indicate they were made on behalf of a specific user (extracted from JWT token).

## Overview

When your service bot adds comments to Jira, they all appear from the bot account. To show which user actually initiated the action, you can use the "On behalf of" feature that automatically extracts user information from the JWT token and adds it to the comment.

## How It Works

### The Problem
```
Bot Account adds comment → Appears as "jira-bot@company.com commented"
```
Everyone sees the bot, not who actually requested the action.

### The Solution
```
Bot Account adds comment with context → Appears as:

"jira-bot@company.com commented:
 On behalf of: John Doe (john.doe@company.com)
 
 @Jane please review this issue"
```

## Implementation

### 1. Simple Text Comments

```python
# In your API endpoint
from fastapi import Depends
from app.core.security import get_current_user
from app.db.models.user import UserInDB
from app.agent.tools.atlassian.jira import JiraTools

@router.post("/jira/comment")
async def add_jira_comment(
    issue_key: str,
    comment: str,
    current_user: UserInDB = Depends(get_current_user)
):
    # Option 1: Use the user object directly
    on_behalf_of = f"{current_user.firstname} {current_user.lastname} ({current_user.email})"
    
    result = jira_tools.add_jira_comment(
        issue_key=issue_key,
        comment_body=comment,
        on_behalf_of=on_behalf_of
    )
    
    return result
```

### 2. Extract from JWT Token

```python
from app.core.security.token_manager import token_manager
from app.agent.tools.atlassian.jira import JiraTools

@router.post("/jira/comment")
async def add_jira_comment(
    issue_key: str,
    comment: str,
    token: str = Depends(oauth2_scheme)
):
    # Verify and decode token
    payload = token_manager.verify_token(token)
    
    if payload:
        # Extract user info from token
        on_behalf_of = JiraTools.extract_user_from_token(payload)
        
        result = jira_tools.add_jira_comment(
            issue_key=issue_key,
            comment_body=comment,
            on_behalf_of=on_behalf_of
        )
        
        return result
```

### 3. With User Mentions (ADF Format)

```python
import json
from app.agent.tools.atlassian.jira import JiraTools

@router.post("/jira/comment-with-mention")
async def add_comment_with_mention(
    issue_key: str,
    mention_account_id: str,
    mention_display_name: str,
    message: str,
    current_user: UserInDB = Depends(get_current_user)
):
    # Extract user info
    on_behalf_of = f"{current_user.firstname} {current_user.lastname} ({current_user.email})"
    
    # Create ADF with mention and "on behalf of"
    adf = JiraTools.create_mention_adf(
        account_id=mention_account_id,
        display_name=mention_display_name,
        additional_text=f" {message}",
        on_behalf_of=on_behalf_of
    )
    
    # Add comment
    result = jira_tools.add_jira_comment(
        issue_key=issue_key,
        comment_body=json.dumps(adf)
    )
    
    return result
```

### 4. Multiple Mentions with Context

```python
import json
from app.agent.tools.atlassian.jira import JiraTools

@router.post("/jira/comment-multiple-mentions")
async def add_comment_multiple_mentions(
    issue_key: str,
    current_user: UserInDB = Depends(get_current_user)
):
    # Build user context
    on_behalf_of = f"{current_user.firstname} {current_user.lastname} ({current_user.email})"
    
    # Create comment with multiple parts
    text_parts = [
        {"type": "text", "content": "Hi "},
        {"type": "mention", "account_id": "user1-account-id", "display_name": "John Doe"},
        {"type": "text", "content": " and "},
        {"type": "mention", "account_id": "user2-account-id", "display_name": "Jane Smith"},
        {"type": "text", "content": ", please review this issue!"}
    ]
    
    adf = JiraTools.create_comment_with_mentions(
        text_parts,
        on_behalf_of=on_behalf_of
    )
    
    result = jira_tools.add_jira_comment(
        issue_key=issue_key,
        comment_body=json.dumps(adf)
    )
    
    return result
```

## Result in Jira

### Simple Text Comment
```
jira-bot@company.com added a comment - 2 minutes ago

On behalf of: John Doe (john.doe@company.com)

This issue needs to be reviewed urgently.
```

### With Mentions (ADF)
```
jira-bot@company.com added a comment - 2 minutes ago

On behalf of: John Doe (john.doe@company.com)

@Jane Smith please review this issue
```

### Multiple Mentions
```
jira-bot@company.com added a comment - 2 minutes ago

On behalf of: John Doe (john.doe@company.com)

Hi @Jane Smith and @Bob Johnson, please review this issue!
```

## Token Payload Structure

Your JWT tokens contain:
```json
{
  "user_id": "123",
  "email": "john.doe@company.com",
  "username": "johndoe",
  "firstname": "John",
  "lastname": "Doe",
  "sub": "123",
  "type": "access",
  "exp": 1234567890
}
```

The `extract_user_from_token()` helper formats this as:
- If firstname & lastname & email: `"John Doe (john.doe@company.com)"`
- If firstname & lastname & username: `"John Doe (@johndoe)"`
- If firstname & lastname only: `"John Doe"`
- If email only: `"john.doe@company.com"`
- If username only: `"johndoe"`
- Fallback: `"Unknown User"`

## Complete Example: Chat Endpoint

Here's how you might use this in your chat endpoint:

```python
from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.db.models.user import UserInDB
from app.agent.tools.atlassian.jira import JiraTools

router = APIRouter()

@router.post("/chat")
async def chat(
    message: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Chat endpoint that can use Jira tools with user context.
    """
    # Build user context for any Jira operations
    user_context = f"{current_user.firstname} {current_user.lastname} ({current_user.email})"
    
    # Your LLM/Agent processing...
    # When the agent decides to add a Jira comment:
    
    result = jira_tools.add_jira_comment(
        issue_key="PROJ-123",
        comment_body="Agent response here",
        on_behalf_of=user_context
    )
    
    return {
        "message": "Comment added to Jira",
        "user": user_context,
        "result": result
    }
```

## Middleware Option

You can also create middleware to automatically inject user context:

```python
# middleware/user_context.py
from fastapi import Request
from app.core.security.token_manager import token_manager
from app.agent.tools.atlassian.jira import JiraTools

async def add_user_context_middleware(request: Request, call_next):
    """Automatically extract user context from JWT and add to request state."""
    
    # Get Authorization header
    auth_header = request.headers.get("Authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = token_manager.verify_token(token)
        
        if payload:
            # Add user context to request state
            request.state.user_context = JiraTools.extract_user_from_token(payload)
    
    response = await call_next(request)
    return response

# Then in your endpoint:
@router.post("/jira/comment")
async def add_comment(request: Request, issue_key: str, comment: str):
    on_behalf_of = getattr(request.state, "user_context", None)
    
    result = jira_tools.add_jira_comment(
        issue_key=issue_key,
        comment_body=comment,
        on_behalf_of=on_behalf_of
    )
    
    return result
```

## Best Practices

1. **Always pass user context** when available
   - Makes audit trails clearer
   - Users know who initiated actions

2. **Format consistently**
   - Use the `extract_user_from_token()` helper
   - Ensures consistent formatting across your app

3. **Handle missing context gracefully**
   - If `on_behalf_of` is `None`, comment is added without context
   - Bot identity is still clear in Jira

4. **Consider privacy**
   - Only include information users expect to be public
   - Email addresses are visible in Jira comments

5. **Log user actions**
   - Log who initiated bot actions
   - Helps with debugging and auditing

## Advantages Over Multiple Bot Accounts

| Feature | Multiple Bots | On Behalf Of (This Solution) |
|---------|--------------|------------------------------|
| **Setup Complexity** | High - Need multiple accounts & tokens | Low - One bot account |
| **User Identity** | Limited - Only pre-defined bot personas | Full - Any authenticated user |
| **Maintenance** | High - Manage multiple accounts/tokens | Low - Single account |
| **Audit Trail** | Medium - Know which bot, not which user | Excellent - Know exact user |
| **Scalability** | Poor - Can't scale to all users | Excellent - Works for any user |
| **Cost** | Higher - Multiple Jira licenses | Lower - Single bot license |

## Security Considerations

1. **Token Verification** - Always verify JWT before extracting user info
2. **Sanitize Input** - The user context is added to Jira comments, ensure it's safe
3. **Permission Checks** - Verify user has permission before acting on their behalf
4. **Audit Logging** - Log all actions with both bot and user context

## Troubleshooting

### Comment doesn't show "On behalf of"
- Check that `on_behalf_of` parameter is being passed
- Verify the parameter is not `None` or empty string

### User info is wrong
- Verify JWT token contains expected fields
- Check token expiration
- Ensure token was issued by your auth service

### Formatting looks wrong
- For plain text: Markdown formatting is used (_italic_ and **bold**)
- For ADF: Proper ADF nodes are created with formatting marks

## References

- [JWT Token Manager](../../core/security/token_manager.md)
- [Jira Mentions Guide](./jira-mentions.md)
- [Authentication System](../../core/security/authentication.md)
