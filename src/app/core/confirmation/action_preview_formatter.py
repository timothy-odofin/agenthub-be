"""
Action Preview Formatter - Generate human-readable previews of pending actions.

Provides both generic and integration-specific formatting strategies.
Follows the Strategy pattern for extensibility.

Design Principles:
- Extensible: Easy to add custom formatters for specific tools
- Readable: Human-friendly output for user confirmation
- Simple: Falls back to generic formatting when no custom formatter exists
"""

from typing import Dict, Any, Callable, Optional
from datetime import datetime

from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class ActionPreviewFormatter:
    """
    Formats pending actions into human-readable previews.
    
    Supports custom formatters for specific tools while providing
    sensible generic formatting as a fallback.
    
    Usage:
        formatter = ActionPreviewFormatter()
        
        # Register custom formatter
        formatter.register_formatter("jira", "create_jira_issue", custom_format_fn)
        
        # Format action
        preview = formatter.format(action)
    """
    
    def __init__(self):
        """Initialize the formatter with empty custom formatters registry."""
        self._custom_formatters: Dict[str, Dict[str, Callable]] = {}
        logger.info("ActionPreviewFormatter initialized")
    
    def register_formatter(
        self,
        integration: str,
        tool_name: str,
        formatter_func: Callable[[Dict[str, Any]], str]
    ) -> None:
        """
        Register a custom formatter for a specific tool.
        
        Args:
            integration: Integration name (jira, email, github, etc.)
            tool_name: Specific tool name (create_jira_issue, send_email, etc.)
            formatter_func: Function that takes parameters dict and returns formatted string
        """
        if integration not in self._custom_formatters:
            self._custom_formatters[integration] = {}
        
        self._custom_formatters[integration][tool_name] = formatter_func
        logger.info(f"Registered custom formatter: {integration}.{tool_name}")
    
    def format(self, action: Any) -> str:
        """
        Format a pending action into a human-readable preview.
        
        Args:
            action: PendingAction instance
            
        Returns:
            Formatted preview string
        """
        # Try custom formatter first
        custom_preview = self._try_custom_formatter(action)
        if custom_preview:
            return custom_preview
        
        # Fall back to generic formatter
        return self._generic_format(action)
    
    def _try_custom_formatter(self, action: Any) -> Optional[str]:
        """
        Attempt to use a custom formatter for the action.
        
        Args:
            action: PendingAction instance
            
        Returns:
            Formatted string if custom formatter exists, None otherwise
        """
        integration_formatters = self._custom_formatters.get(action.integration)
        if not integration_formatters:
            return None
        
        formatter_func = integration_formatters.get(action.tool_name)
        if not formatter_func:
            return None
        
        try:
            return formatter_func(action.parameters)
        except Exception as e:
            logger.error(
                f"Custom formatter failed for {action.integration}.{action.tool_name}: {e}",
                exc_info=True
            )
            return None
    
    def _generic_format(self, action: Any) -> str:
        """
        Generate a generic preview for any action.
        
        Args:
            action: PendingAction instance
            
        Returns:
            Generic formatted preview
        """
        # Humanize tool name
        tool_display = self._humanize_tool_name(action.tool_name)
        
        # Format timestamps
        created_str = self._format_timestamp(action.created_at)
        expires_str = self._format_timestamp(action.expires_at)
        
        # Build preview
        lines = [
            f"🔔 **Action Confirmation Required**",
            f"",
            f"**Action:** {tool_display}",
            f"**Type:** {action.action_type.title()}",
            f"**Integration:** {action.integration.title()}",
            f"**Risk Level:** {self._format_risk_level(action.risk_level)}",
            f"",
            f"**Parameters:**",
        ]
        
        # Format parameters
        for key, value in action.parameters.items():
            display_key = self._humanize_key(key)
            display_value = self._format_value(value)
            lines.append(f"  • **{display_key}:** {display_value}")
        
        lines.extend([
            f"",
            f"**Action ID:** `{action.action_id}`",
            f"**Created:** {created_str}",
            f"**Expires:** {expires_str}",
            f"",
            f"⚠️ Please review carefully before confirming.",
        ])
        
        return "\n".join(lines)
    
    def _humanize_tool_name(self, tool_name: str) -> str:
        """
        Convert tool_name to human-readable format.
        
        Examples:
            create_jira_issue -> Create Jira Issue
            send_email -> Send Email
            add_jira_comment -> Add Jira Comment
        """
        return " ".join(word.capitalize() for word in tool_name.split("_"))
    
    def _humanize_key(self, key: str) -> str:
        """
        Convert parameter key to human-readable format.
        
        Examples:
            project_key -> Project Key
            issue_type -> Issue Type
            summary -> Summary
        """
        return " ".join(word.capitalize() for word in key.split("_"))
    
    def _format_value(self, value: Any, max_length: int = 200) -> str:
        """
        Format a parameter value for display.
        
        Args:
            value: The value to format
            max_length: Maximum length before truncation
            
        Returns:
            Formatted value string
        """
        if isinstance(value, dict):
            # Format dict as key-value pairs
            items = [f"{k}: {v}" for k, v in value.items()]
            formatted = ", ".join(items)
        elif isinstance(value, list):
            # Format list
            formatted = ", ".join(str(item) for item in value)
        else:
            formatted = str(value)
        
        # Truncate if too long
        if len(formatted) > max_length:
            formatted = formatted[:max_length - 3] + "..."
        
        return formatted
    
    def _format_risk_level(self, risk_level: str) -> str:
        """
        Format risk level with emoji indicator.
        
        Args:
            risk_level: Risk level (low, medium, high)
            
        Returns:
            Formatted risk level with emoji
        """
        risk_map = {
            "low": "🟢 Low",
            "medium": "🟡 Medium",
            "high": "🔴 High",
        }
        return risk_map.get(risk_level.lower(), f"⚪️ {risk_level.title()}")
    
    def _format_timestamp(self, dt: datetime) -> str:
        """
        Format timestamp in human-readable format.
        
        Args:
            dt: Datetime to format
            
        Returns:
            Formatted timestamp string
        """
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


# ============================================================================
# Built-in Custom Formatters
# ============================================================================

def format_jira_issue_creation(params: Dict[str, Any]) -> str:
    """Custom formatter for Jira issue creation."""
    summary = params.get("summary", "N/A")
    project = params.get("project", params.get("project_key", "N/A"))
    issue_type = params.get("issue_type", "Task")
    description = params.get("description", "")
    assignee = params.get("assignee", "Unassigned")
    priority = params.get("priority", "Not set")
    
    # Truncate description if too long
    if len(description) > 150:
        description = description[:150] + "..."
    
    lines = [
        "🎫 **Create Jira Issue**",
        "",
        f"**Summary:** {summary}",
        f"**Project:** {project}",
        f"**Type:** {issue_type}",
        f"**Assignee:** {assignee}",
        f"**Priority:** {priority}",
    ]
    
    if description:
        lines.extend([
            "",
            "**Description:**",
            f"{description}",
        ])
    
    lines.extend([
        "",
        "⚠️ This will create a new issue in your Jira project.",
    ])
    
    return "\n".join(lines)


def format_jira_comment(params: Dict[str, Any]) -> str:
    """Custom formatter for Jira comment addition."""
    issue_key = params.get("issue_key", "N/A")
    comment = params.get("comment", params.get("body", ""))
    
    # Truncate comment if too long
    if len(comment) > 200:
        comment = comment[:200] + "..."
    
    lines = [
        "💬 **Add Jira Comment**",
        "",
        f"**Issue:** {issue_key}",
        "",
        "**Comment:**",
        f"{comment}",
        "",
        "⚠️ This will add a comment to the specified issue.",
    ]
    
    return "\n".join(lines)


def format_email(params: Dict[str, Any]) -> str:
    """Custom formatter for email sending."""
    to = params.get("to", params.get("recipients", "N/A"))
    subject = params.get("subject", "No subject")
    body = params.get("body", params.get("message", ""))
    cc = params.get("cc")
    attachments = params.get("attachments", [])
    
    # Truncate body if too long
    if len(body) > 150:
        body = body[:150] + "..."
    
    lines = [
        "📧 **Send Email**",
        "",
        f"**To:** {to}",
    ]
    
    if cc:
        lines.append(f"**CC:** {cc}")
    
    lines.extend([
        f"**Subject:** {subject}",
        "",
        "**Message:**",
        f"{body}",
    ])
    
    if attachments:
        attachment_list = ", ".join(attachments) if isinstance(attachments, list) else attachments
        lines.extend([
            "",
            f"**Attachments:** {attachment_list}",
        ])
    
    lines.extend([
        "",
        "⚠️ This email will be sent immediately upon confirmation.",
    ])
    
    return "\n".join(lines)


def format_github_issue_creation(params: Dict[str, Any]) -> str:
    """Custom formatter for GitHub issue creation."""
    title = params.get("title", "N/A")
    repo = params.get("repo", params.get("repository", "N/A"))
    body = params.get("body", params.get("description", ""))
    labels = params.get("labels", [])
    assignees = params.get("assignees", [])
    
    # Truncate body if too long
    if len(body) > 150:
        body = body[:150] + "..."
    
    lines = [
        "🐙 **Create GitHub Issue**",
        "",
        f"**Title:** {title}",
        f"**Repository:** {repo}",
    ]
    
    if labels:
        label_str = ", ".join(labels) if isinstance(labels, list) else labels
        lines.append(f"**Labels:** {label_str}")
    
    if assignees:
        assignee_str = ", ".join(assignees) if isinstance(assignees, list) else assignees
        lines.append(f"**Assignees:** {assignee_str}")
    
    if body:
        lines.extend([
            "",
            "**Description:**",
            f"{body}",
        ])
    
    lines.extend([
        "",
        "⚠️ This will create a new issue in the GitHub repository.",
    ])
    
    return "\n".join(lines)


def get_default_formatter() -> ActionPreviewFormatter:
    """
    Get a formatter with all built-in custom formatters registered.
    
    Returns:
        ActionPreviewFormatter with built-in formatters
    """
    formatter = ActionPreviewFormatter()
    
    # Register Jira formatters
    formatter.register_formatter("jira", "create_jira_issue", format_jira_issue_creation)
    formatter.register_formatter("jira", "add_jira_comment", format_jira_comment)
    
    # Register Email formatter
    formatter.register_formatter("email", "send_email", format_email)
    
    # Register GitHub formatters
    formatter.register_formatter("github", "create_github_issue", format_github_issue_creation)
    
    logger.info("Loaded default formatter with 4 built-in custom formatters")
    
    return formatter
