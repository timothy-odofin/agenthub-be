"""
Jira integration tools for issue management and project tracking.
"""

import json
from typing import List, Dict, Any, Optional
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from app.agent.tools.base.registry import ToolRegistry


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
        
    def get_tools(self) -> List[StructuredTool]:
        """Return list of JIRA tools."""
        if not self.enabled:
            return []
            
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
            )
        ]
    
    def _get_projects(self) -> str:
        """Get all accessible Jira projects."""
        try:
            if not self.jira_service:
                return "Error: Jira service not available"
                
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
            
        except Exception as e:
            return f"Error getting Jira projects: {str(e)}"

    def _create_issue(self, project_key: str, summary: str, description: str = "", issue_type: str = "Task") -> str:
        """Create a new Jira issue."""
        try:
            if not self.jira_service:
                return "Error: Jira service not available"
            
            if not project_key or not summary:
                return "Error: project_key and summary are required"
                
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
            
        except Exception as e:
            return f"Error creating Jira issue: {str(e)}"

    def _get_issue(self, issue_key: str) -> str:
        """Get a specific Jira issue by its key."""
        try:
            if not self.jira_service:
                return "Error: Jira service not available"
                
            if not issue_key or not issue_key.strip():
                return "Error: Issue key is required"
                
            issue = self.jira_service.get_issue(issue_key.strip())
            
            result = {
                "status": "success", 
                "issue": issue
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return f"Error getting Jira issue: {str(e)}"

    def _search_issues(self, jql: str, max_results: int = 50) -> str:
        """Search for Jira issues using JQL."""
        try:
            if not self.jira_service:
                return "Error: Jira service not available"
            
            if not jql or not jql.strip():
                return "Error: JQL query is required"
                
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
            
        except Exception as e:
            return f"Error searching Jira issues: {str(e)}"
