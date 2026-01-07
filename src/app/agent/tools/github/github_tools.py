"""
GitHub Tools Provider - Main entry point for GitHub integration.
"""

from typing import List, Dict, Any
from langchain.tools import StructuredTool

from app.agent.tools.base.registry import ToolRegistry
from app.core.utils.logger import get_logger
from .connection_manager import GitHubConnectionManager
from .tool_factory import GitHubToolFactory

logger = get_logger(__name__)


@ToolRegistry.register("github", "github")
class GitHubToolsProvider:
    """
    GitHub Tools Provider with multi-repository support and dynamic tool generation.
    
    This provider:
    1. Discovers accessible repositories via GitHub App
    2. Filters by configuration (allowed_repositories)
    3. Creates repository-scoped tools using LangChain GitHubToolkit
    4. Ensures tools only exist for accessible repositories
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize GitHub tools provider."""
        self.config = config or {}
        self._connection_manager = None
        self._tool_factory = None
        self._tools_cache = None
        
    @property
    def connection_manager(self) -> GitHubConnectionManager:
        """Lazy initialization of connection manager."""
        if self._connection_manager is None:
            self._connection_manager = GitHubConnectionManager()
        return self._connection_manager
        
    @property
    def tool_factory(self) -> GitHubToolFactory:
        """Lazy initialization of tool factory."""
        if self._tool_factory is None:
            self._tool_factory = GitHubToolFactory(self.connection_manager)
        return self._tool_factory
    
    def get_tools(self) -> List[StructuredTool]:
        """
        Get all GitHub tools for accessible repositories.
        
        This is the main entry point called by the ToolRegistry.
        
        Returns:
            List of repository-scoped GitHub tools
        """
        # Use cache if available
        if self._tools_cache is not None:
            return self._tools_cache
            
        try:
            # Step 1: Establish GitHub connection
            if not self.connection_manager.connect():
                logger.error("Failed to connect to GitHub, no tools will be available")
                return []
            
            # Step 2: Discover accessible and allowed repositories  
            allowed_repositories = self.connection_manager.get_allowed_repositories()
            
            if not allowed_repositories:
                logger.warning("No accessible repositories found, no GitHub tools will be available")
                return []
            
            # Step 3: Generate tools for each repository
            all_tools = self.tool_factory.get_all_repository_tools()
            
            # Step 4: Add cross-repository tools (if any)
            cross_repo_tools = self.tool_factory.create_cross_repository_tools()
            all_tools.extend(cross_repo_tools)
            
            # Step 5: Cache and return
            self._tools_cache = all_tools
            
            # Log summary
            repo_names = [repo.full_name for repo in allowed_repositories]
            logger.info(f"GitHub tools initialized: {len(all_tools)} tools across repositories: {repo_names}")
            
            return all_tools
            
        except Exception as e:
            logger.error(f"Failed to initialize GitHub tools: {e}")
            return []
    
    def invalidate_cache(self):
        """Invalidate the tools cache to force regeneration."""
        self._tools_cache = None
        if self._connection_manager:
            self._connection_manager._accessible_repositories = None
        logger.info("GitHub tools cache invalidated")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get GitHub connection information for debugging."""
        try:
            return self.connection_manager.get_connection_info()
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_repository_info(self) -> List[Dict[str, Any]]:
        """Get information about accessible repositories."""
        try:
            repositories = self.connection_manager.get_allowed_repositories()
            return [
                {
                    "full_name": repo.full_name,
                    "name": repo.name,
                    "owner": repo.owner,
                    "private": repo.private,
                    "safe_name": repo.safe_name
                }
                for repo in repositories
            ]
        except Exception as e:
            logger.error(f"Failed to get repository info: {e}")
            return []
    
    def validate_repository_access(self, repo_name: str) -> bool:
        """
        Validate access to a specific repository.
        
        Args:
            repo_name: Repository name in format 'owner/repo'
            
        Returns:
            True if repository is accessible and allowed
        """
        try:
            return self.connection_manager.validate_repository_access(repo_name)
        except Exception as e:
            logger.error(f"Failed to validate access to {repo_name}: {e}")
            return False
