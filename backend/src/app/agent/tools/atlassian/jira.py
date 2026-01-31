"""
Jira integration tools for issue management and project tracking.
"""

import json
from typing import List, Dict, Any, Optional
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from app.agent.tools.base.registry import ToolRegistry
from app.core.utils.exception.http_exception_handler import handle_atlassian_errors
from app.core.utils.user_context import extract_user_from_token


# Pydantic models for structured input
class CreateIssueInput(BaseModel):
    """Input schema for creating a Jira issue."""
    project_key: str = Field(description="The Jira project key (e.g., 'MYPROJ')")
    summary: str = Field(description="Brief summary of the issue")
    description: Optional[str] = Field(default="", description="Detailed description of the issue")
    issue_type: Optional[str] = Field(default="Task", description="Type of issue (Task, Bug, Story, etc.)")


class GetIssueInput(BaseModel):
    """Input schema for getting a Jira issue."""
    issue_key: str = Field(description="The Jira issue key (e.g., 'PROJ-123')")


class SearchIssuesInput(BaseModel):
    """Input schema for searching Jira issues."""
    jql: str = Field(description="JQL query string (e.g., 'project = MYPROJ AND status = Open')")
    max_results: Optional[int] = Field(default=50, description="Maximum number of results to return")


class GetProjectsInput(BaseModel):
    """Input schema for getting Jira projects (no input required)."""
    pass


class AddCommentInput(BaseModel):
    """Input schema for adding a comment to a Jira issue."""
    issue_key: str = Field(description="The Jira issue key to add comment to (e.g., 'PROJ-123')")
    comment_body: str = Field(description="The comment text to add to the issue")
    on_behalf_of: Optional[str] = Field(default=None, description="Username or email of the user on whose behalf this comment is being added")


class SearchUsersInput(BaseModel):
    """Input schema for searching Jira users."""
    query: str = Field(description="Search query (username, email, or display name)")
    max_results: Optional[int] = Field(default=50, description="Maximum number of results to return")


class GetAllUsersInput(BaseModel):
    """Input schema for getting all Jira users."""
    start_at: Optional[int] = Field(default=0, description="Starting index for pagination")
    max_results: Optional[int] = Field(default=50, description="Maximum number of results to return")


class GetProjectUsersInput(BaseModel):
    """Input schema for getting users with access to a project."""
    project_key: str = Field(description="The Jira project key (e.g., 'MYPROJ')")
    start_at: Optional[int] = Field(default=0, description="Starting index for pagination")
    max_results: Optional[int] = Field(default=50, description="Maximum number of results to return")


@ToolRegistry.register("jira", "atlassian")
class JiraTools:
    """Jira issue management and project tracking tools."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with optional configuration."""
        self.config = config or {}
        self._jira_service = None
        
    @property
    def jira_service(self):
        """Lazy load jira service to avoid circular imports."""
        if self._jira_service is None:
            try:
                from app.services.external.jira_service import jira
                self._jira_service = jira
            except ImportError as e:
                print(f"Warning: Could not import jira service: {e}")
                self._jira_service = None
        return self._jira_service
        
    def get_tools(self) -> List[StructuredTool]:
        """Return list of JIRA tools."""
        return [
            StructuredTool(
                name="get_jira_projects",
                description="Get a list of all accessible Jira projects with their keys, names, and details.",
                func=self._get_projects,
                args_schema=GetProjectsInput
            ),
            StructuredTool(
                name="create_jira_issue",
                description="Create a new Jira issue with project key, summary, description, and issue type.",
                func=self._create_issue,
                args_schema=CreateIssueInput
            ),
            StructuredTool(
                name="get_jira_issue",
                description="Get detailed information about a specific Jira issue by its key.",
                func=self._get_issue,
                args_schema=GetIssueInput
            ),
            StructuredTool(
                name="search_jira_issues",
                description="Search Jira issues using JQL (Jira Query Language).",
                func=self._search_issues,
                args_schema=SearchIssuesInput
            ),
            StructuredTool(
                name="add_jira_comment",
                description="Add a comment to an existing Jira issue by its key.",
                func=self._add_comment,
                args_schema=AddCommentInput
            ),
            StructuredTool(
                name="search_jira_users",
                description="Search for Jira users by username, email, or display name to get their account IDs for mentions.",
                func=self._search_users,
                args_schema=SearchUsersInput
            ),
            StructuredTool(
                name="get_all_jira_users",
                description="Get a list of all Jira users with pagination. Use this to browse all available users in the system.",
                func=self._get_all_users,
                args_schema=GetAllUsersInput
            ),
            StructuredTool(
                name="get_jira_project_users",
                description="Get users who have access to a specific Jira project. Useful for finding who can be assigned or mentioned in project issues.",
                func=self._get_project_users,
                args_schema=GetProjectUsersInput
            )
        ]
    
    @handle_atlassian_errors()
    def _get_projects(self) -> str:
        """Get all accessible Jira projects."""
        if not self.jira_service:
            return json.dumps({"status": "error", "error": "Jira service not available"})
            
        projects = self.jira_service.get_projects()
        
        if not projects:
            return "No accessible Jira projects found."
        
        result = {
            "status": "success",
            "total_projects": len(projects),
            "projects": []
        }
        
        for project in projects:
            project_info = {
                "key": project.get('key', ''),
                "name": project.get('name', ''),
                "id": project.get('id', ''),
                "description": project.get('description', ''),
                "project_type": project.get('projectTypeKey', ''),
                "lead": project.get('lead', {}).get('displayName', 'Unknown') if project.get('lead') else 'Unknown'
            }
            result["projects"].append(project_info)
        
        return json.dumps(result, indent=2)

    @handle_atlassian_errors()
    def _create_issue(self, project_key: str, summary: str, description: str = "", issue_type: str = "Task") -> str:
        """Create a new Jira issue."""
        if not self.jira_service:
            return json.dumps({"status": "error", "error": "Jira service not available"})
        
        if not project_key or not summary:
            return json.dumps({"status": "error", "error": "project_key and summary are required"})
            
        # Use the correct service method signature
        new_issue = self.jira_service.create_issue(
            project=project_key,
            summary=summary, 
            description=description,
            issue_type=issue_type
        )
        
        result = {
            "status": "success",
            "issue": new_issue,
            "summary": summary,
            "project": project_key
        }
        
        return json.dumps(result, indent=2)

    @handle_atlassian_errors()
    def _get_issue(self, issue_key: str) -> str:
        """Get a specific Jira issue by its key."""
        if not self.jira_service:
            return json.dumps({"status": "error", "error": "Jira service not available"})
            
        if not issue_key or not issue_key.strip():
            return json.dumps({"status": "error", "error": "Issue key is required"})
            
        issue = self.jira_service.get_issue(issue_key.strip())
        
        result = {
            "status": "success", 
            "issue": issue
        }
        
        return json.dumps(result, indent=2)

    @handle_atlassian_errors()
    def _search_issues(self, jql: str, max_results: int = 50) -> str:
        """Search for Jira issues using JQL."""
        if not self.jira_service:
            return json.dumps({"status": "error", "error": "Jira service not available"})
        
        if not jql or not jql.strip():
            return json.dumps({"status": "error", "error": "JQL query is required"})
            
        # Use the correct service method signature with key field included
        issues = self.jira_service.search_issues(
            jql=jql.strip(), 
            limit=max_results,
            fields=['key', 'summary', 'status', 'created', 'priority', 'issuetype']
        )
        
        result = {
            "status": "success",
            "jql": jql.strip(),
            "max_results": max_results,
            "search_results": issues
        }
        
        return json.dumps(result, indent=2)

    @handle_atlassian_errors()
    def _add_comment(self, issue_key: str, comment_body: str, on_behalf_of: Optional[str] = None) -> str:
        """Add a comment to a Jira issue.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123')
            comment_body: Either plain text or JSON string of ADF format
            on_behalf_of: Optional user context (only used for plain text comments)
        """
        if not self.jira_service:
            return json.dumps({"status": "error", "error": "Jira service not available"})
        
        if not issue_key or not issue_key.strip():
            return json.dumps({"status": "error", "error": "Issue key is required"})
        
        if not comment_body or not comment_body.strip():
            return json.dumps({"status": "error", "error": "Comment body is required"})
        
        # Check if comment_body is ADF format (JSON string starting with {"version": 1)
        comment_body_stripped = comment_body.strip()
        is_adf = False
        final_comment = comment_body_stripped  # Default to use the string as-is
        
        try:
            parsed = json.loads(comment_body_stripped)
            if isinstance(parsed, dict) and parsed.get('version') == 1 and parsed.get('type') == 'doc':
                is_adf = True
                # Pass as dict - connection manager will handle it with direct API call
                final_comment = parsed
        except (json.JSONDecodeError, ValueError):
            pass
        
        # For plain text comments, add "On behalf of" if provided
        if not is_adf and on_behalf_of:
            # Use markdown-style formatting that Jira understands
            final_comment = f"_On behalf of:_ *{on_behalf_of}*\n\n{comment_body_stripped}"
        
        comment = self.jira_service.add_comment(
            issue_key=issue_key.strip(),
            comment_body=final_comment
        )
        
        result = {
            "status": "success",
            "issue_key": issue_key.strip(),
            "comment": comment,
            "on_behalf_of": on_behalf_of if not is_adf else None,
            "format": "adf" if is_adf else "text",
            "message": f"Comment successfully added to issue {issue_key.strip()}" + 
                      (f" on behalf of {on_behalf_of}" if on_behalf_of and not is_adf else "")
        }
        
        return json.dumps(result, indent=2)

    @handle_atlassian_errors()
    def _search_users(self, query: str, max_results: int = 50) -> str:
        """Search for Jira users."""
        if not self.jira_service:
            return json.dumps({"status": "error", "error": "Jira service not available"})
        
        if not query or not query.strip():
            return json.dumps({"status": "error", "error": "Search query is required"})
        
        users = self.jira_service.search_users(
            query=query.strip(),
            max_results=max_results
        )
        
        result = {
            "status": "success",
            "query": query.strip(),
            "total_results": len(users),
            "users": [],
            "usage_hint": "To mention a user in a comment, use their accountId in ADF format or use the create_mention_adf helper."
        }
        
        for user in users:
            user_info = {
                "account_id": user.get('accountId', ''),
                "display_name": user.get('displayName', ''),
                "email": user.get('emailAddress', 'N/A'),
                "active": user.get('active', True)
            }
            result["users"].append(user_info)
        
        return json.dumps(result, indent=2)
    
    @handle_atlassian_errors()
    def _get_all_users(self, start_at: int = 0, max_results: int = 50) -> str:
        """Get all Jira users."""
        if not self.jira_service:
            return json.dumps({"status": "error", "error": "Jira service not available"})
        
        users = self.jira_service.get_all_users(
            start_at=start_at,
            max_results=max_results
        )
        
        result = {
            "status": "success",
            "start_at": start_at,
            "max_results": max_results,
            "total_results": len(users),
            "users": [],
            "pagination_hint": f"To get more users, use start_at={start_at + max_results}",
            "usage_hint": "To mention a user in a comment, use their accountId in ADF format."
        }
        
        for user in users:
            user_info = {
                "account_id": user.get('accountId', ''),
                "display_name": user.get('displayName', ''),
                "email": user.get('emailAddress', 'N/A'),
                "active": user.get('active', True)
            }
            result["users"].append(user_info)
        
        return json.dumps(result, indent=2)
    
    @handle_atlassian_errors()
    def _get_project_users(self, project_key: str, start_at: int = 0, max_results: int = 50) -> str:
        """Get users with access to a Jira project."""
        if not self.jira_service:
            return json.dumps({"status": "error", "error": "Jira service not available"})
        
        if not project_key or not project_key.strip():
            return json.dumps({"status": "error", "error": "Project key is required"})
        
        users = self.jira_service.get_project_users(
            project_key=project_key.strip(),
            start_at=start_at,
            max_results=max_results
        )
        
        result = {
            "status": "success",
            "project_key": project_key.strip(),
            "start_at": start_at,
            "max_results": max_results,
            "total_results": len(users),
            "users": [],
            "pagination_hint": f"To get more users, use start_at={start_at + max_results}",
            "usage_hint": "These users have access to the project and can be mentioned in issue comments."
        }
        
        for user in users:
            user_info = {
                "account_id": user.get('accountId', ''),
                "display_name": user.get('displayName', ''),
                "email": user.get('emailAddress', 'N/A'),
                "active": user.get('active', True)
            }
            result["users"].append(user_info)
        
        return json.dumps(result, indent=2)
    
    @staticmethod
    def create_mention_adf(account_id: str, display_name: str, additional_text: str = "", on_behalf_of: Optional[str] = None) -> Dict:
        """
        Helper method to create an ADF (Atlassian Document Format) structure for mentioning a user.
        
        Note: When using on_behalf_of, it's better to use plain text format for better rendering in Jira.
        This method returns ADF for mentions, but if you need on_behalf_of, consider using plain text instead.
        
        Args:
            account_id: The Atlassian account ID of the user to mention
            display_name: The display name of the user (will be shown as @DisplayName)
            additional_text: Optional text to append after the mention
            on_behalf_of: DEPRECATED - Use plain text format with on_behalf_of parameter instead
            
        Returns:
            ADF JSON structure that can be used as comment_body
            
        Example:
            >>> adf = JiraTools.create_mention_adf(
            ...     "5b10ac8d82e05b22cc7d4ef5",
            ...     "John Doe",
            ...     " please review this issue"
            ... )
        """
        content = []
        
        # Add the mention
        content.append({
            "type": "mention",
            "attrs": {
                "id": account_id,
                "text": f"@{display_name}"
            }
        })
        
        # Add additional text if provided
        if additional_text:
            content.append({
                "type": "text",
                "text": additional_text
            })
        
        return {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": content
                }
            ]
        }
    
    @staticmethod
    def create_comment_with_mentions(text_parts: List[Dict[str, str]], on_behalf_of: Optional[str] = None) -> Dict:
        """
        Helper method to create an ADF comment with multiple text parts and mentions.
        
        Note: When using on_behalf_of, it's better to use plain text format for better rendering in Jira.
        
        Args:
            text_parts: List of dictionaries with keys:
                - 'type': Either 'text' or 'mention'
                - For 'text': 'content' (the text string)
                - For 'mention': 'account_id' and 'display_name'
            on_behalf_of: DEPRECATED - Use plain text format with on_behalf_of parameter instead
                
        Returns:
            ADF JSON structure that can be used as comment_body
            
        Example:
            >>> text_parts = [
            ...     {"type": "text", "content": "Hello "},
            ...     {"type": "mention", "account_id": "123", "display_name": "John"},
            ...     {"type": "text", "content": " and "},
            ...     {"type": "mention", "account_id": "456", "display_name": "Jane"},
            ...     {"type": "text", "content": ", please review this!"}
            ... ]
            >>> adf = JiraTools.create_comment_with_mentions(text_parts)
        """
        content = []
        
        # Add the text parts
        for part in text_parts:
            if part.get('type') == 'text':
                content.append({
                    "type": "text",
                    "text": part.get('content', '')
                })
            elif part.get('type') == 'mention':
                content.append({
                    "type": "mention",
                    "attrs": {
                        "id": part.get('account_id', ''),
                        "text": f"@{part.get('display_name', '')}"
                    }
                })
        
        return {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": content
                }
            ]
        }
    
    @staticmethod
    def extract_user_from_token(token_payload: Dict[str, Any]) -> str:
        """
        Extract user identification from JWT token payload.
        
        DEPRECATED: Use app.core.utils.user_context.extract_user_from_token instead.
        This method is kept for backward compatibility.
        
        Args:
            token_payload: Decoded JWT token payload containing user information
            
        Returns:
            User identification string (name + email or just email/username)
            
        Example:
            >>> from app.core.security.token_manager import token_manager
            >>> token = "eyJ..."
            >>> payload = token_manager.verify_token(token)
            >>> user_info = JiraTools.extract_user_from_token(payload)
            >>> # Returns: "John Doe (john.doe@company.com)"
        """
        # Delegate to the centralized utility
        from app.core.utils.user_context import extract_user_from_token as extract_user
        return extract_user(token_payload)
