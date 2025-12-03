"""
Jira integration tools for issue management and project tracking.
"""

import json
from typing import List, Dict, Any
from langchain.tools import Tool

from app.services.agent.tools.base.registry import ToolRegistry


@ToolRegistry.register("jira", "atlassian")
class JiraTools:
    """Jira issue management and project tracking tools."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with optional configuration."""
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
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
        
    def get_tools(self) -> List[Tool]:
        """Return list of JIRA tools."""
        if not self.enabled:
            return []
            
        return [
            Tool(
                name="create_jira_issue",
                description="Create a new Jira issue. Provide project key, summary, description, and issue type.",
                func=self._create_issue
            ),
            Tool(
                name="get_jira_issue",
                description="Get detailed information about a specific Jira issue by its key (e.g., 'PROJ-123').",
                func=self._get_issue
            ),
            Tool(
                name="search_jira_issues",
                description="Search Jira issues using JQL (Jira Query Language). Example: 'project = MYPROJ AND status = Open'",
                func=self._search_issues
            )
        ]
    
    def _create_issue(self, project_key: str, summary: str, description: str = "", issue_type: str = "Task") -> str:
        """Create a new Jira issue."""
        try:
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type}
            }
            
            new_issue = self.jira_service.create_issue(fields=issue_dict)
            
            result = {
                "status": "success",
                "issue_key": new_issue.key,
                "issue_id": new_issue.id,
                "summary": summary,
                "url": f"{self.jira_service.server_url}/browse/{new_issue.key}"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return f"Error creating Jira issue: {str(e)}"

    def _get_issue(self, issue_key: str) -> str:
        """Get details of a specific Jira issue."""
        try:
            issue = self.jira_service.issue(issue_key)
            
            result = {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "status": issue.fields.status.name,
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
                "reporter": issue.fields.reporter.displayName if issue.fields.reporter else "Unknown",
                "priority": issue.fields.priority.name if issue.fields.priority else "Unknown",
                "issue_type": issue.fields.issuetype.name,
                "created": str(issue.fields.created),
                "updated": str(issue.fields.updated),
                "url": f"{self.jira_service.server_url}/browse/{issue.key}"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return f"Error getting Jira issue: {str(e)}"

    def _search_issues(self, jql: str, max_results: int = 50) -> str:
        """Search for Jira issues using JQL."""
        try:
            issues = self.jira_service.search_issues(jql, maxResults=max_results)
            
            results = []
            for issue in issues:
                results.append({
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name,
                    "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
                    "priority": issue.fields.priority.name if issue.fields.priority else "Unknown",
                    "url": f"{self.jira_service.server_url}/browse/{issue.key}"
                })
            
            result = {
                "jql": jql,
                "total_found": len(results),
                "issues": results
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return f"Error searching Jira issues: {str(e)}"
