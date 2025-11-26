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

    async def _ensure_connected(self):
        """Ensure Jira connection is established."""
        if not self._connection_manager:
            self._connection_manager = ConnectionFactory.get_connection_manager(ConnectionType.JIRA)
        
        if not self._jira_client:
            self._jira_client = await self._connection_manager.connect()
        
        return self._jira_client

    async def search_issues(self, jql: str, limit: int = 50, fields=None):
        """Search for issues using JQL."""
        await self._ensure_connected()
        return await self._connection_manager.search_issues(jql, limit=limit, fields=fields)

    async def create_issue(self, project: str, summary: str, description: str, issue_type="Task"):
        """Create a new issue."""
        await self._ensure_connected()
        return await self._connection_manager.create_issue(
            project_key=project,
            summary=summary,
            description=description,
            issue_type=issue_type
        )

    async def get_issue(self, issue_key: str):
        """Get a specific issue by key."""
        await self._ensure_connected()
        return await self._connection_manager.get_issue(issue_key)
    
    async def get_projects(self):
        """Get all accessible projects."""
        await self._ensure_connected()
        return await self._connection_manager.get_projects()
    
    async def get_server_info(self):
        """Get Jira server information."""
        await self._ensure_connected()
        return await self._connection_manager.get_server_info()
    
    async def disconnect(self):
        """Close the Jira connection."""
        if self._connection_manager:
            await self._connection_manager.disconnect()
            self._jira_client = None

jira = JiraClient()