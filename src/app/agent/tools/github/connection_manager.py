"""
GitHub Connection Manager for GitHub App integration with repository discovery.
"""

import os
import fnmatch
from typing import List, Dict, Any, Optional, Set

from github import Github, GithubException, GithubIntegration
from github.Repository import Repository
from github.Installation import Installation

from app.core.utils.logger import get_logger
from app.core.utils.file_utils import read_private_key_file, FileReadError
from app.core.config.framework.settings import settings

logger = get_logger(__name__)


class GitHubRepository:
    """Wrapper for GitHub repository information."""
    
    def __init__(self, repo: Repository):
        self.repo = repo
        self.full_name = repo.full_name
        self.name = repo.name
        self.owner = repo.owner.login
        self.private = repo.private
        self.permissions = repo.permissions
        
    @property
    def safe_name(self) -> str:
        """Repository name safe for tool naming."""
        return self.full_name.replace("/", "_").replace("-", "_")


class GitHubConnectionManager:
    """
    GitHub Connection Manager with App integration and repository discovery.
    Handles GitHub App authentication and repository access validation.
    """
    
    def __init__(self):
        self._github_app: Optional[Github] = None
        self._github_integration: Optional[GithubIntegration] = None
        self._installation: Optional[Installation] = None
        self._accessible_repositories: Optional[List[GitHubRepository]] = None
        
    @property
    def github_config(self) -> Dict[str, Any]:
        """Get GitHub configuration from settings."""
        if not hasattr(settings, 'external') or not hasattr(settings.external, 'github'):
            raise ValueError("GitHub configuration not found in external settings")
        
        # Convert DynamicConfig to dictionary
        github_config = settings.external.github
        return {
            'api_key': github_config.api_key,
            'base_url': github_config.base_url,
            'timeout': github_config.timeout,
            'app': {
                'app_id': github_config.app.app_id,
                'private_key_path': github_config.app.private_key_path,
                'installation_id': github_config.app.installation_id,
                'client_secret': github_config.app.client_secret,
            } if hasattr(github_config, 'app') else {},
            'allowed_repositories': github_config.allowed_repositories if hasattr(github_config, 'allowed_repositories') else []
        }
        
    def _get_github_app_auth(self) -> Github:
        """Create GitHub App authenticated client."""
        config = self.github_config
        
        # Check if we have GitHub App credentials
        app_config = config.get('app', {})
        app_id = app_config.get('app_id')
        private_key_path = app_config.get('private_key_path')  # This should be file path
        
        if not app_id or not private_key_path:
            # Fall back to personal access token
            api_key = config.get('api_key')
            if api_key:
                logger.info("Using GitHub personal access token authentication")
                return Github(api_key)
            else:
                raise ValueError("No GitHub authentication method configured (App or PAT)")
        
        logger.info(f"Using GitHub App authentication (App ID: {app_id})")
        
        # Read private key from file using utility
        try:
            private_key = read_private_key_file(private_key_path)
        except FileReadError as e:
            raise ValueError(f"Failed to read GitHub App private key: {e}")
        
        # GitHub App authentication using GithubIntegration
        self._github_integration = GithubIntegration(
            integration_id=app_id,
            private_key=private_key
        )
        
        # Get installation and then access token
        installation = self._get_installation()
        access_token = self._github_integration.get_access_token(installation.id).token
        return Github(access_token)
    
    def _get_installation(self) -> Installation:
        """Get GitHub App installation."""
        if not self._installation:
            config = self.github_config
            app_config = config.get('app', {})
            installation_id = app_config.get('installation_id')
            
            if installation_id and installation_id != 'None':
                # Use provided installation ID
                self._installation = self._github_integration.get_app_installation(int(installation_id))
                logger.info(f"Using configured installation ID: {installation_id}")
            else:
                # Try to find installation automatically using GithubIntegration
                installations = self._github_integration.get_installations()
                installation_list = list(installations)
                
                if not installation_list:
                    raise ValueError("No GitHub App installations found")
                
                # Use first installation (could be enhanced to select specific one)
                self._installation = installation_list[0]
                logger.info(f"Using first available installation: {self._installation.account.login} (ID: {self._installation.id})")
                
        return self._installation
    
    def connect(self) -> bool:
        """Establish GitHub connection and validate access."""
        try:
            self._github_app = self._get_github_app_auth()
            
            # Test connection
            if self.github_config.get('app'):
                # For GitHub App, test by getting installation
                installation = self._get_installation()
                logger.info(f"GitHub App connected successfully to installation: {installation.account.login}")
            else:
                # For PAT, test by getting user info
                user = self._github_app.get_user()
                logger.info(f"GitHub PAT connected successfully for user: {user.login}")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to GitHub: {e}")
            return False
    
    def discover_accessible_repositories(self) -> List[GitHubRepository]:
        """
        Discover all repositories the GitHub App/user has access to.
        Returns only repositories we actually have access to.
        """
        if self._accessible_repositories is not None:
            return self._accessible_repositories
            
        if not self._github_app:
            if not self.connect():
                return []
        
        accessible_repos = []
        
        try:
            if self.github_config.get('app'):
                # GitHub App: Get repositories from installation
                installation = self._get_installation()
                repos = installation.get_repos()
                
                for repo in repos:
                    try:
                        # Test actual access by trying to get repo info
                        repo.get_contents("README.md")  # This will fail if no access
                        accessible_repos.append(GitHubRepository(repo))
                    except GithubException:
                        # Don't have access to this repo, skip it
                        continue
                        
            else:
                # Personal Access Token: Get user repositories
                user = self._github_app.get_user()
                repos = user.get_repos()
                
                for repo in repos:
                    accessible_repos.append(GitHubRepository(repo))
                    
            logger.info(f"Discovered {len(accessible_repos)} accessible repositories")
            self._accessible_repositories = accessible_repos
            
        except Exception as e:
            logger.error(f"Failed to discover repositories: {e}")
            return []
            
        return accessible_repos
    
    def get_allowed_repositories(self) -> List[GitHubRepository]:
        """
        Get repositories filtered by configuration.
        Returns intersection of (accessible repositories + configured allowed repositories).
        """
        accessible_repos = self.discover_accessible_repositories()
        
        config = self.github_config
        allowed_repo_configs = config.get('allowed_repositories', [])
        
        if not allowed_repo_configs:
            logger.warning("No allowed repositories configured, allowing all accessible repositories")
            return accessible_repos
        
        filtered_repos = []
        
        for repo in accessible_repos:
            for repo_config in allowed_repo_configs:
                # Handle both string patterns (legacy) and dict configs with 'name' key
                pattern = repo_config if isinstance(repo_config, str) else repo_config.get('name', '')
                if self._matches_pattern(repo.full_name, pattern):
                    filtered_repos.append(repo)
                    break
        
        logger.info(f"Filtered to {len(filtered_repos)} allowed repositories from {len(accessible_repos)} accessible")
        return filtered_repos
    
    def _matches_pattern(self, repo_name: str, pattern: str) -> bool:
        """Check if repository name matches the allowed pattern."""
        # Support wildcards like "owner/*"
        return fnmatch.fnmatch(repo_name, pattern)
    
    def validate_repository_access(self, repo_name: str) -> bool:
        """Check if we have access to a specific repository."""
        allowed_repos = self.get_allowed_repositories()
        return any(repo.full_name == repo_name for repo in allowed_repos)
    
    def get_repository_by_name(self, repo_name: str) -> Optional[GitHubRepository]:
        """Get repository object by name if accessible."""
        allowed_repos = self.get_allowed_repositories()
        for repo in allowed_repos:
            if repo.full_name == repo_name:
                return repo
        return None
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for debugging."""
        if not self._github_app:
            return {"status": "not_connected"}
            
        try:
            accessible_repos = self.discover_accessible_repositories()
            allowed_repos = self.get_allowed_repositories()
            
            return {
                "status": "connected",
                "authentication": "github_app" if self.github_config.get('app') else "personal_token",
                "accessible_repositories": len(accessible_repos),
                "allowed_repositories": len(allowed_repos),
                "repository_names": [repo.full_name for repo in allowed_repos]
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
