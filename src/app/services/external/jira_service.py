from app.connections.factory.connection_factory import ConnectionFactory
from app.connections.base import ConnectionType
from app.core.utils.logger import get_logger
from app.core.utils.single_ton import SingletonMeta

logger = get_logger(__name__)


class JiraClient(metaclass=SingletonMeta):
    """Jira client using the unified connection management system."""
    
    def __init__(self):
        self._connection_manager = None
        self._jira_client = None

    def _ensure_connected(self):
        """Ensure Jira connection is established."""
        if not self._connection_manager:
            self._connection_manager = ConnectionFactory.get_connection_manager(ConnectionType.JIRA)
        
        if not self._jira_client:
            self._jira_client = self._connection_manager.connect()
        
        return self._jira_client

    def search_issues(self, jql: str, limit: int = 50, fields=None):
        """Search for issues using JQL."""
        self._ensure_connected()
        return self._connection_manager.search_issues(jql, limit=limit, fields=fields)

    def create_issue(self, project: str, summary: str, description: str, issue_type="Task"):
        """Create a new issue."""
        self._ensure_connected()
        return self._connection_manager.create_issue(
            project_key=project,
            summary=summary,
            description=description,
            issue_type=issue_type
        )

    def get_issue(self, issue_key: str):
        """Get a specific issue by key."""
        self._ensure_connected()
        return self._connection_manager.get_issue(issue_key)
    
    def get_projects(self):
        """Get all accessible projects."""
        self._ensure_connected()
        return self._connection_manager.get_projects()
    
    def get_server_info(self):
        """Get Jira server information."""
        self._ensure_connected()
        return self._connection_manager.get_server_info()
    
    def add_comment(self, issue_key: str, comment_body: str):
        """Add a comment to an issue."""
        self._ensure_connected()
        return self._connection_manager.add_comment(issue_key, comment_body)
    
    def search_users(self, query: str, max_results: int = 50):
        """Search for users in Jira."""
        self._ensure_connected()
        return self._connection_manager.search_users(query, max_results)
    
    def get_user_by_account_id(self, account_id: str):
        """Get user details by account ID."""
        self._ensure_connected()
        return self._connection_manager.get_user_by_account_id(account_id)
    
    def get_all_users(self, start_at: int = 0, max_results: int = 50):
        """Get all users with pagination."""
        self._ensure_connected()
        return self._connection_manager.get_all_users(start_at, max_results)
    
    def get_project_users(self, project_key: str, start_at: int = 0, max_results: int = 50):
        """Get users who have access to a specific project."""
        self._ensure_connected()
        return self._connection_manager.get_project_users(project_key, start_at, max_results)
    
    def disconnect(self):
        """Close the Jira connection."""
        if self._connection_manager:
            self._connection_manager.disconnect()
            self._jira_client = None

jira = JiraClient()