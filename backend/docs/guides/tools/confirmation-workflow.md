# Confirmation Workflow for Mutating Actions

> **Two-phase confirmation protocol** ensuring user approval before executing actions that modify external systems

## Overview

The confirmation workflow is a critical safety feature that prevents the AI agent from making unauthorized changes to external systems. All mutating operations (creating issues, adding comments, updating files, etc.) **must** go through a two-phase confirmation process.

## Architecture

```
User Request
↓
Agent Decision
↓
┌─────────────────────────┐
│ Phase 1: PREPARE │
│ - prepare_action │
│ - Generate preview │
│ - Store pending action │
└───────┬─────────────────┘
↓
User Reviews Preview
↓
User Confirms/Cancels
↓
┌─────────────────────────┐
│ Phase 2: EXECUTE │
│ - confirm_action │
│ - Execute stored tool │
│ - Return result │
└─────────────────────────┘
```

## Why It Matters

### Without Confirmation Workflow 
```
User: "Tag @john on SCRUM-2 to provide user stories"
Agent: [Calls add_jira_comment directly]
Agent: "Done - I mentioned John on SCRUM-2"
User: "Wait, I wanted to review the message first!"
```

### With Confirmation Workflow 
```
User: "Tag @john on SCRUM-2 to provide user stories"
Agent: [Calls prepare_action]
Agent: "I've prepared to add this comment to SCRUM-2:

'@John Smith - could you please provide more user stories
for this sprint? We need detailed acceptance criteria.'

Would you like me to proceed?"
User: "Change 'could you please' to 'please'"
Agent: [User revises, then confirms]
Agent: [Calls confirm_action]
Agent: "Done - comment added to SCRUM-2"
```

## Core Components

### 1. prepare_action

**Purpose**: Prepare a mutating action for user review without executing it.

**Parameters**:
```python
{
"tool_name": str, # Name of the tool to execute (e.g., "add_jira_comment")
"tool_args": dict, # Arguments to pass to the tool
"risk_level": str, # "high", "medium", or "low"
"user_id": str, # User making the request
"session_id": str # Optional session context
}
```

**Returns**:
```python
{
"action_id": str, # Unique ID for this pending action
"preview": str, # Human-readable description
"expires_at": datetime, # Expiration timestamp (5 minutes)
"risk_level": str
}
```

**Example**:
```python
prepare_action(
tool_name="create_jira_issue",
tool_args={
"project": "PROJ",
"summary": "Fix login bug on mobile",
"description": "Users report crashes...",
"issue_type": "Bug"
},
risk_level="medium",
user_id="user_123"
)
```

### 2. confirm_action

**Purpose**: Execute a previously prepared action after user approval.

**Parameters**:
```python
{
"action_id": str, # ID from prepare_action response
"user_id": str # Must match original user
}
```

**Returns**:
```python
{
"status": "success",
"result": {...}, # Tool execution result
"executed_tool": str, # Tool that was executed
"execution_time": float # Time taken
}
```

**Example**:
```python
confirm_action(
action_id="action_abc123",
user_id="user_123"
)
```

### 3. cancel_action

**Purpose**: Cancel a pending action without executing it.

**Parameters**:
```python
{
"action_id": str,
"user_id": str
}
```

### 4. list_pending_actions

**Purpose**: Show all pending confirmations for a user/session.

**Parameters**:
```python
{
"user_id": str,
"session_id": str # Optional
}
```

## Risk Levels

### High Risk 
**Impact**: Significant, hard to reverse
- Creating GitHub pull requests (triggers CI/CD, notifies teams)
- Updating files in repositories (affects codebase)
- Deleting resources
- Creating Jira issues (creates work items, assigns to teams)

**Expiration**: 5 minutes

### Medium Risk 
**Impact**: Moderate, some reversibility
- Adding comments to issues (can be edited/deleted)
- Updating issue status
- Creating branches

**Expiration**: 5 minutes

### Low Risk 
**Impact**: Limited, easily reversible
- Reading data
- Searching
- Listing resources

**Expiration**: 5 minutes (though low risk actions may not always require confirmation)

## Agent Behavior Rules

### CRITICAL: What Agents MUST Do

1. **Use prepare_action for ALL mutating operations**
- Create, update, delete operations
- Adding comments or mentions
- Triggering workflows

2. **Show preview to user and wait for confirmation**
- Never say "Done" after prepare_action
- Clearly present what will happen
- Wait for explicit user approval

3. **Only execute after user confirms**
- Call confirm_action only after user says yes
- Respect cancellations

4. **Communicate action state clearly**
- "I've **prepared** to..." (after prepare_action)
- "Done - action **completed**" (after confirm_action)

### PROHIBITED: What Agents MUST NEVER Do

1. **Never call mutating tools directly**
```python
# WRONG - bypasses confirmation
add_jira_comment(issue_key="SCRUM-2", comment="...")

# CORRECT - uses confirmation workflow
prepare_action(
tool_name="add_jira_comment",
tool_args={"issue_key": "SCRUM-2", "comment": "..."},
risk_level="medium"
)
```

2. **Never say "Done" before user confirms**
```
# WRONG
Agent: "Done - I mentioned John on SCRUM-2" # Action not executed yet!

# CORRECT
Agent: "I've prepared to mention John. Would you like me to proceed?"
```

3. **Never skip showing the preview**
- Users must see what will happen
- Especially important for comments with mentions

4. **Never execute without user approval**
- Even if it seems obvious
- Even for "small" changes

## Usage Examples

### Example 1: Creating Jira Issue

**User Request**: "Create a bug ticket for the login issue"

**Agent Flow**:
```
1. Agent Thought: Creating Jira issue is mutating - need confirmation

2. Agent Action: prepare_action(
tool_name="create_jira_issue",
tool_args={
"project": "PROJ",
"summary": "Login page crashes on mobile Safari",
"description": "Users report crashes when accessing login...",
"issue_type": "Bug"
},
risk_level="high",
user_id="user_123"
)

3. Agent Response: "I've prepared to create a Jira issue:

Project: PROJ
Type: Bug
Summary: Login page crashes on mobile Safari

This will create a new issue and notify the project team.
Would you like me to proceed?"

4. User: "yes"

5. Agent Action: confirm_action(
action_id="action_abc123",
user_id="user_123"
)

6. Agent Response: "Done - created issue PROJ-456"
```

### Example 2: Adding Comment with Mention

**User Request**: "Tag asiyanbola on SCRUM-2 to provide user stories"

**Agent Flow**:
```
1. Agent searches for user: search_jira_users(query="asiyanbola")
→ Finds Ahmad Asiyanbola (accountId: 123abc)

2. Agent prepares comment:
prepare_action(
tool_name="add_jira_comment",
tool_args={
"issue_key": "SCRUM-2",
"comment_body": "{JSON ADF format with mention}"
},
risk_level="medium",
user_id="user_123"
)

3. Agent shows preview:
"I've prepared to add this comment to SCRUM-2:

'@Ahmad Asiyanbola - Could you please provide more user stories
for this sprint? We need detailed acceptance criteria and example
scenarios to properly scope the work.'

This will mention Ahmad and send him a notification.
Would you like me to proceed?"

4. User reviews and confirms

5. Agent executes: confirm_action(...)

6. Agent responds: "Done - mentioned Ahmad on SCRUM-2"
```

### Example 3: User Cancels Action

**User Request**: "Create a PR for the feature branch"

**Agent Flow**:
```
1. Agent: prepare_action(...)

2. Agent: "I've prepared to create a pull request:

From: feature/new-ui
To: main
Title: Add new user interface

This will trigger CI/CD pipelines and notify reviewers.
Would you like me to proceed?"

3. User: "Actually, no. I want to add more commits first."

4. Agent: cancel_action(action_id="...", user_id="...")

5. Agent: "OK, I've cancelled the PR creation. Let me know when
you're ready to create it."
```

## Configuration

### Cache Settings

Pending actions are stored in Redis with automatic expiration:

```yaml
# resources/application-tools.yaml
tools:
confirmation:
cache:
ttl: 300 # 5 minutes
namespace: "confirmation"
```

### Backend Implementation

The confirmation service uses:
- **Storage**: Redis via `confirmation_cache`
- **Serialization**: Automatic JSON handling
- **Expiration**: TTL-based (5 minutes)
- **Validation**: User ID matching, action existence checks

## Troubleshooting

### Agent Bypassing Confirmation

**Symptom**: Agent says "Done" immediately without asking for confirmation

**Cause**: Agent is calling mutating tools directly instead of using prepare_action

**Solution**: 
1. Check agent prompt includes strict prohibitions against direct tool calls
2. Verify `CRITICAL RULE` and `STRICTLY PROHIBITED` sections are in system prompt
3. Review agent logs to see which tool was called

### Action Expired

**Symptom**: User confirms but gets "action expired" error

**Cause**: More than 5 minutes passed between prepare and confirm

**Solution**:
1. User needs to re-request the action
2. Agent will call prepare_action again
3. User should confirm more quickly

### Preview Not Showing

**Symptom**: Agent asks for confirmation but doesn't show what will happen

**Cause**: Preview generation failed or agent skipped showing it

**Solution**:
1. Check confirmation service logs
2. Verify tool_name and tool_args are valid
3. Ensure agent prompt emphasizes showing preview

## Best Practices

### For Agent Developers

1. **Always use prepare_action for mutating operations**
- Even if it seems redundant
- Better safe than sorry

2. **Make previews detailed and clear**
- Show exactly what will happen
- Include who will be notified
- Mention any side effects

3. **Test confirmation workflow thoroughly**
- Happy path (confirm)
- Cancellation path
- Expiration handling

4. **Set appropriate risk levels**
- High: Irreversible or high-impact changes
- Medium: Moderate impact, some reversibility
- Low: Minimal impact

### For Users

1. **Review previews carefully**
- Check message content before confirming
- Verify @mentions are correct
- Ensure parameters are what you expect

2. **Confirm promptly**
- Actions expire after 5 minutes
- You'll need to re-request if expired

3. **Use cancel freely**
- No penalty for cancelling
- Better to cancel and revise than confirm wrong action

## Related Documentation

- [Jira Tools](./jira-tools.md) - Jira-specific operations
- [Jira Mentions](./jira-mentions.md) - How to mention users in Jira
- [Agent Configuration](../configuration/README.md) - System prompt configuration
