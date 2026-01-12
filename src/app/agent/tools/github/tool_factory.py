"""
GitHub Tool Factory for dynamic repository-scoped tool creation.
"""

import re
from typing import List, Dict, Any, Optional
from langchain.tools import StructuredTool
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from langchain_community.utilities.github import GitHubAPIWrapper

from app.core.utils.logger import get_logger
from app.core.config.framework.settings import settings
from app.core.utils.file_utils import read_private_key_file
from .connection_manager import GitHubConnectionManager, GitHubRepository

logger = get_logger(__name__)


def sanitize_tool_name(name: str, max_length: int = 64) -> str:
    """
    Sanitize tool name to match OpenAI's requirements:
    - Pattern: ^[a-zA-Z0-9_-]+$
    - Maximum length: 64 characters
    
    Converts spaces and special characters to underscores, removes invalid characters,
    and truncates to max_length if needed.
    
    Args:
        name: Original tool name
        max_length: Maximum allowed length (default: 64 for OpenAI)
        
    Returns:
        Sanitized tool name matching the required pattern and length
    """
    # Replace spaces and common separators with underscores
    sanitized = name.replace(' ', '_').replace('.', '_').replace('/', '_')
    
    # Remove any characters that aren't alphanumeric, underscore, or hyphen
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', sanitized)
    
    # Remove consecutive underscores/hyphens
    sanitized = re.sub(r'[_-]+', '_', sanitized)
    
    # Remove leading/trailing underscores or hyphens
    sanitized = sanitized.strip('_-')
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "unknown_tool"
    
    # Truncate if exceeds max_length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_-')
    
    return sanitized


class GitHubToolFactory:
    """
    Factory for creating repository-scoped GitHub tools.
    Integrates LangChain GitHubToolkit with configuration-based filtering.
    """
    
    def __init__(self, connection_manager: GitHubConnectionManager):
        self.connection_manager = connection_manager
        
    @property
    def github_tools_config(self) -> Dict[str, Any]:
        """Get GitHub tools configuration."""
        if not hasattr(settings, 'tools') or not hasattr(settings.tools, 'tools') or not hasattr(settings.tools.tools, 'github'):
            return {'enabled': False}
        return settings.tools.tools.github
        
    def create_repository_tools(self, repository: GitHubRepository) -> List[StructuredTool]:
        """
        Create tools for a specific repository with professional filtering.
        
        Args:
            repository: Repository to create tools for
            
        Returns:
            List of repository-scoped tools
        """
        tools_config = self.github_tools_config
        
        if not tools_config.get('enabled', False):
            return []
            
        # Get GitHub configuration from global settings
        github_config = self.connection_manager.github_config
        app_config = github_config.get('app', {})
        
        # Create GitHubAPIWrapper directly with parameters
        private_key_content = read_private_key_file(app_config.get('private_key_path'))
        
        github_wrapper = GitHubAPIWrapper(
            github_repository=repository.full_name,
            github_app_id=str(app_config.get('app_id')),
            github_app_private_key=private_key_content
        )
        
        # Create toolkit using the wrapper
        toolkit = GitHubToolkit.from_github_api_wrapper(github_wrapper)
        
        # Get all available tools from the toolkit
        all_toolkit_tools = toolkit.get_tools()
        
        # Use simplified configuration-based filtering
        filtered_tools = self._filter_tools_simplified(all_toolkit_tools, repository)
        
        logger.info(f"Created {len(filtered_tools)} tools for repository: {repository.full_name}")
        return filtered_tools
    
    def _filter_tools_simplified(self, tools: List[StructuredTool], repository: GitHubRepository) -> List[StructuredTool]:
        """
        Simplified tool filtering based on direct tool name configuration.
        
        Args:
            tools: Original LangChain tools
            repository: Repository context
            
        Returns:
            Filtered and enhanced tools with repository-specific naming
        """
        enhanced_tools = []
        tools_config = self.github_tools_config.get('available_tools', {})
        
        for tool in tools:
            tool_name = getattr(tool, 'name', 'Unknown')
            
            # Check if tool is enabled in simplified config
            # Handle both boolean values and dict with 'enabled' key
            tool_setting = tools_config.get(tool_name, False)
            if isinstance(tool_setting, dict):
                is_enabled = tool_setting.get('enabled', False)
            else:
                is_enabled = bool(tool_setting)
            
            if is_enabled:
                enhanced_tool = self._create_enhanced_tool(tool, repository)
                if enhanced_tool:
                    enhanced_tools.append(enhanced_tool)
        
        return enhanced_tools
    
    def _create_enhanced_tool(self, original_tool: StructuredTool, repository: GitHubRepository) -> Optional[StructuredTool]:
        """
        Create enhanced tool with repository context and simplified naming.
        
        Args:
            original_tool: Original LangChain tool
            repository: Repository context
            
        Returns:
            Enhanced tool with repository-specific context or None if creation fails
        """
        try:
            tool_name = getattr(original_tool, 'name', 'Unknown')
            original_description = getattr(original_tool, 'description', tool_name)
            
            # Create repository-scoped tool name with length constraint
            enhanced_name = self._create_scoped_tool_name(tool_name, repository.full_name)
            
            # Enhance description with repository context
            enhanced_description = f"{original_description} (Repository: {repository.full_name})"
            
            # Get repository metadata if available
            repo_metadata = self._get_repository_metadata(repository)
            if repo_metadata:
                enhanced_description = f"{original_description} - {repo_metadata}"
            
            # Determine callable function to use
            func_to_use = self._get_tool_function(original_tool)
            if not func_to_use:
                logger.warning(f"No callable function found for tool: {tool_name}")
                return None
            
            # Create enhanced tool
            enhanced_tool = StructuredTool(
                name=enhanced_name,
                description=enhanced_description,
                func=func_to_use,
                args_schema=getattr(original_tool, 'args_schema', None),
                return_direct=getattr(original_tool, 'return_direct', False),
                verbose=getattr(original_tool, 'verbose', False),
                tags=[f"repository:{repository.full_name}", "github"],
                metadata={
                    "repository": repository.full_name,
                    "repository_owner": repository.owner,
                    "repository_name": repository.name,
                    "original_tool_name": tool_name,
                    "tool_source": "github_toolkit"
                }
            )
            
            return enhanced_tool
            
        except Exception as e:
            logger.error(f"Failed to create enhanced tool from {original_tool}: {e}")
            return None
    
    def _create_scoped_tool_name(self, tool_name: str, repo_full_name: str, max_length: int = 64) -> str:
        """
        Create a repository-scoped tool name that fits within OpenAI's length constraints.
        
        Strategy:
        1. Sanitize both tool name and repository name
        2. If combined name fits, use it
        3. If too long, intelligently truncate repository name
        4. Ensure final name is <= max_length
        
        Args:
            tool_name: Original tool name
            repo_full_name: Full repository name (owner/repo)
            max_length: Maximum allowed length (default: 64 for OpenAI)
            
        Returns:
            Scoped tool name that fits within length constraints
        """
        # Sanitize both parts
        sanitized_tool_name = sanitize_tool_name(tool_name, max_length=max_length)
        sanitized_repo_name = sanitize_tool_name(repo_full_name, max_length=max_length)
        
        # Try simple combination first
        combined_name = f"{sanitized_tool_name}_{sanitized_repo_name}"
        
        if len(combined_name) <= max_length:
            return combined_name
        
        # Need to truncate - prioritize tool name, shorten repo name
        # Reserve space for tool name + underscore + shortened repo
        underscore_length = 1
        available_for_repo = max_length - len(sanitized_tool_name) - underscore_length
        
        if available_for_repo < 5:  # If repo gets too short, truncate tool name too
            # Split space more evenly
            tool_length = (max_length - underscore_length) // 2
            repo_length = max_length - tool_length - underscore_length
            
            truncated_tool = sanitized_tool_name[:tool_length].rstrip('_-')
            truncated_repo = sanitized_repo_name[:repo_length].rstrip('_-')
            
            return f"{truncated_tool}_{truncated_repo}"
        else:
            # Just truncate repo name
            truncated_repo = sanitized_repo_name[:available_for_repo].rstrip('_-')
            return f"{sanitized_tool_name}_{truncated_repo}"
    
    def _get_repository_metadata(self, repository: GitHubRepository) -> Optional[str]:
        """
        Get repository-specific metadata for enhanced descriptions.
        
        Args:
            repository: Repository context
            
        Returns:
            Repository description or None if not available
        """
        try:
            # Check if repository has metadata in external config
            github_config = self.connection_manager.github_config
            allowed_repos = github_config.get('allowed_repositories', [])
            
            # Look for repository-specific description in allowed_repositories
            for repo_config in allowed_repos:
                if isinstance(repo_config, dict):
                    if repo_config.get('name') == repository.full_name:
                        description = repo_config.get('description', '')
                        if description:
                            return description
            
            # Fallback to generic repository context
            return f"Operations for {repository.full_name}"
            
        except Exception as e:
            logger.debug(f"Could not get repository metadata for {repository.full_name}: {e}")
            return None
    
    def _get_tool_function(self, tool: StructuredTool) -> Optional[callable]:
        """
        Extract callable function from LangChain tool with multiple fallback options.
        
        Args:
            tool: LangChain tool instance
            
        Returns:
            Callable function or None if no suitable function found
        """
        # Try to get the func attribute first (most direct)
        if hasattr(tool, 'func') and callable(tool.func):
            return tool.func
        
        # If no func, try to use the tool's invoke method which handles everything
        if hasattr(tool, 'invoke') and callable(tool.invoke):
            # Wrap invoke to match StructuredTool's expected signature
            def invoke_wrapper(**kwargs):
                return tool.invoke(kwargs)
            return invoke_wrapper
        
        # Fallback to run method
        if hasattr(tool, 'run') and callable(tool.run):
            # Wrap run method to match StructuredTool's expected signature
            def run_wrapper(**kwargs):
                return tool.run(kwargs)
            return run_wrapper
        
        # Last resort: _run method
        if hasattr(tool, '_run') and callable(tool._run):
            def _run_wrapper(**kwargs):
                return tool._run(kwargs)
            return _run_wrapper
        
        return None
    
    def get_all_repository_tools(self) -> List[StructuredTool]:
        """
        Get tools for all allowed repositories.
        
        Returns:
            List of all repository-scoped tools
        """
        all_tools = []
        
        try:
            allowed_repositories = self.connection_manager.get_allowed_repositories()
            
            for repository in allowed_repositories:
                repo_tools = self.create_repository_tools(repository)
                all_tools.extend(repo_tools)
                
            logger.info(f"Created total of {len(all_tools)} GitHub tools across {len(allowed_repositories)} repositories")
            
        except Exception as e:
            logger.error(f"Failed to get all repository tools: {e}")
            
        return all_tools
    
    def create_cross_repository_tools(self) -> List[StructuredTool]:
        """
        Create tools that operate across repositories (if any).
        
        Currently returns empty list, but can be extended for:
        - Organization-level tools
        - Multi-repository search tools
        - Cross-repo workflow tools
        
        Returns:
            List of cross-repository tools
        """
        # For future expansion - currently no cross-repo tools needed
        return []
