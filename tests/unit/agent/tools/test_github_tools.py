"""
Unit tests for GitHub tools implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain.tools import StructuredTool

from app.agent.tools.github.github_tools import GitHubToolsProvider
from app.agent.tools.github.tool_factory import GitHubToolFactory, sanitize_tool_name
from app.agent.tools.github.connection_manager import GitHubConnectionManager, GitHubRepository


class TestToolNameSanitization:
    """Tests for tool name sanitization to match OpenAI requirements."""
    
    def test_sanitize_simple_name(self):
        """Test sanitization of already valid names."""
        assert sanitize_tool_name("get_issues") == "get_issues"
        assert sanitize_tool_name("create-branch") == "create_branch"  # Hyphens converted to underscores
        assert sanitize_tool_name("Get_Pull_Requests") == "Get_Pull_Requests"
    
    def test_sanitize_spaces(self):
        """Test converting spaces to underscores."""
        assert sanitize_tool_name("get pull requests") == "get_pull_requests"
        assert sanitize_tool_name("create new issue") == "create_new_issue"
    
    def test_sanitize_special_characters(self):
        """Test removing special characters."""
        assert sanitize_tool_name("get.issues") == "get_issues"
        assert sanitize_tool_name("get/issues") == "get_issues"
        assert sanitize_tool_name("get@issues#123") == "getissues123"
        assert sanitize_tool_name("get(issues)") == "getissues"
    
    def test_sanitize_consecutive_separators(self):
        """Test removing consecutive underscores and hyphens."""
        assert sanitize_tool_name("get___issues") == "get_issues"
        assert sanitize_tool_name("get---issues") == "get_issues"
        assert sanitize_tool_name("get_-_issues") == "get_issues"
    
    def test_sanitize_leading_trailing(self):
        """Test removing leading/trailing underscores and hyphens."""
        assert sanitize_tool_name("_get_issues_") == "get_issues"
        assert sanitize_tool_name("-get-issues-") == "get_issues"
        assert sanitize_tool_name("__get_issues__") == "get_issues"
    
    def test_sanitize_empty_or_invalid(self):
        """Test handling empty or completely invalid names."""
        assert sanitize_tool_name("") == "unknown_tool"
        assert sanitize_tool_name("@#$%") == "unknown_tool"
        assert sanitize_tool_name("___") == "unknown_tool"
    
    def test_sanitize_real_world_examples(self):
        """Test sanitization of real-world tool names that might come from LangChain."""
        assert sanitize_tool_name("Get Issues") == "Get_Issues"
        assert sanitize_tool_name("List Pull Requests") == "List_Pull_Requests"
        assert sanitize_tool_name("Create Branch (v2)") == "Create_Branch_v2"
        assert sanitize_tool_name("get.repository.info") == "get_repository_info"
    
    def test_sanitize_max_length(self):
        """Test that names are truncated to max_length."""
        long_name = "a" * 100
        result = sanitize_tool_name(long_name, max_length=64)
        assert len(result) == 64
        assert result == "a" * 64
    
    def test_sanitize_max_length_with_trailing_chars(self):
        """Test that trailing underscores/hyphens are removed after truncation."""
        long_name = "get_issues_" + "x" * 100
        result = sanitize_tool_name(long_name, max_length=64)
        assert len(result) <= 64
        assert not result.endswith('_')
        assert not result.endswith('-')
    
    def test_sanitize_preserves_case(self):
        """Test that case is preserved during sanitization."""
        assert sanitize_tool_name("GetIssues") == "GetIssues"
        assert sanitize_tool_name("LIST_PULL_REQUESTS") == "LIST_PULL_REQUESTS"


class TestGitHubRepository:
    """Tests for GitHubRepository wrapper."""
    
    def test_repository_initialization(self):
        """Test repository initialization with mock PyGithub repo."""
        mock_repo = Mock()
        mock_repo.full_name = "owner/repo"
        mock_repo.name = "repo"
        mock_repo.owner.login = "owner"
        mock_repo.private = False
        mock_repo.permissions = Mock()
        
        repo = GitHubRepository(mock_repo)
        
        assert repo.full_name == "owner/repo"
        assert repo.name == "repo"
        assert repo.owner == "owner"
        assert repo.private is False
    
    def test_safe_name_conversion(self):
        """Test repository safe name for tool naming."""
        mock_repo = Mock()
        mock_repo.full_name = "owner/my-repo"
        mock_repo.name = "my-repo"
        mock_repo.owner.login = "owner"
        mock_repo.private = False
        mock_repo.permissions = Mock()
        
        repo = GitHubRepository(mock_repo)
        
        assert repo.safe_name == "owner_my_repo"


class TestGitHubConnectionManager:
    """Tests for GitHubConnectionManager."""
    
    @patch('app.agent.tools.github.connection_manager.settings')
    def test_github_config_property(self, mock_settings):
        """Test GitHub configuration extraction."""
        mock_github = Mock()
        mock_github.api_key = "test_key"
        mock_github.base_url = "https://api.github.com"
        mock_github.timeout = 30
        
        mock_app = Mock()
        mock_app.app_id = "12345"
        mock_app.private_key_path = "/path/to/key.pem"
        mock_app.installation_id = "67890"
        mock_app.client_secret = "secret"
        mock_github.app = mock_app
        
        mock_allowed_repos = [
            {"name": "owner/repo1", "description": "Repo 1"},
            {"name": "owner/repo2", "description": "Repo 2"}
        ]
        mock_github.allowed_repositories = mock_allowed_repos
        
        mock_external = Mock()
        mock_external.github = mock_github
        mock_settings.external = mock_external
        
        manager = GitHubConnectionManager()
        config = manager.github_config
        
        assert config['api_key'] == "test_key"
        assert config['base_url'] == "https://api.github.com"
        assert config['app']['app_id'] == "12345"
        assert config['allowed_repositories'] == mock_allowed_repos
    
    def test_matches_pattern_exact(self):
        """Test exact pattern matching."""
        manager = GitHubConnectionManager()
        
        assert manager._matches_pattern("owner/repo", "owner/repo") is True
        assert manager._matches_pattern("owner/repo", "owner/other") is False
    
    def test_matches_pattern_wildcard(self):
        """Test wildcard pattern matching."""
        manager = GitHubConnectionManager()
        
        assert manager._matches_pattern("owner/repo1", "owner/*") is True
        assert manager._matches_pattern("owner/repo2", "owner/*") is True
        assert manager._matches_pattern("other/repo", "owner/*") is False


class TestGitHubToolFactory:
    """Tests for GitHubToolFactory."""
    
    def test_factory_initialization(self):
        """Test factory initialization with connection manager."""
        mock_manager = Mock(spec=GitHubConnectionManager)
        factory = GitHubToolFactory(mock_manager)
        
        assert factory.connection_manager == mock_manager
    
    @patch('app.agent.tools.github.tool_factory.settings')
    def test_github_tools_config_enabled(self, mock_settings):
        """Test reading GitHub tools configuration."""
        mock_github_tools = Mock()
        mock_github_tools.enabled = True
        mock_github_tools.available_tools = {
            "Get Issues": True,
            "Read File": True
        }
        
        mock_tools_obj = Mock()
        mock_tools_obj.tools = Mock()
        mock_tools_obj.tools.github = mock_github_tools
        
        mock_settings.tools = mock_tools_obj
        
        mock_manager = Mock(spec=GitHubConnectionManager)
        factory = GitHubToolFactory(mock_manager)
        
        config = factory.github_tools_config
        
        assert config.enabled is True
        assert "Get Issues" in config.available_tools
    
    def test_get_tool_function_from_func(self):
        """Test extracting callable from tool with func attribute."""
        mock_tool = Mock()
        test_func = Mock(return_value="result")
        mock_tool.func = test_func
        mock_tool.name = "test_tool"
        
        mock_manager = Mock(spec=GitHubConnectionManager)
        factory = GitHubToolFactory(mock_manager)
        
        func = factory._get_tool_function(mock_tool)
        
        assert func is not None
        assert callable(func)
        assert func is test_func  # Should return the func directly
    
    def test_get_tool_function_from_invoke(self):
        """Test extracting callable from tool with invoke method."""
        mock_tool = Mock()
        mock_tool.invoke = Mock(return_value="invoke_result")
        delattr(mock_tool, 'func')  # Ensure func doesn't exist
        mock_tool.name = "test_tool"
        
        mock_manager = Mock(spec=GitHubConnectionManager)
        factory = GitHubToolFactory(mock_manager)
        
        func = factory._get_tool_function(mock_tool)
        
        assert func is not None
        assert callable(func)
        
        # Test that the wrapper works correctly
        result = func(param1="value1", param2="value2")
        mock_tool.invoke.assert_called_once_with({"param1": "value1", "param2": "value2"})
        assert result == "invoke_result"
    
    def test_get_tool_function_from_run(self):
        """Test extracting callable from tool with run method."""
        mock_tool = Mock()
        mock_tool.run = Mock(return_value="run_result")
        mock_tool.name = "test_tool"
        delattr(mock_tool, 'func')  # Ensure func doesn't exist
        delattr(mock_tool, 'invoke')  # Ensure invoke doesn't exist
        
        mock_manager = Mock(spec=GitHubConnectionManager)
        factory = GitHubToolFactory(mock_manager)
        
        func = factory._get_tool_function(mock_tool)
        
        assert func is not None
        assert callable(func)
        
        # Test that the wrapper works correctly
        result = func(param1="value1")
        mock_tool.run.assert_called_once_with({"param1": "value1"})
        assert result == "run_result"
    
    def test_get_repository_metadata_from_config(self):
        """Test getting repository metadata from configuration."""
        mock_manager = Mock(spec=GitHubConnectionManager)
        mock_manager.github_config = {
            'allowed_repositories': [
                {"name": "owner/repo1", "description": "Test Repo 1"},
                {"name": "owner/repo2", "description": "Test Repo 2"}
            ]
        }
        
        factory = GitHubToolFactory(mock_manager)
        
        mock_repo = Mock()
        mock_repo.full_name = "owner/repo1"
        repository = Mock(spec=GitHubRepository)
        repository.full_name = "owner/repo1"
        
        metadata = factory._get_repository_metadata(repository)
        
        assert metadata == "Test Repo 1"
    
    def test_get_repository_metadata_fallback(self):
        """Test fallback when repository metadata is not in config."""
        mock_manager = Mock(spec=GitHubConnectionManager)
        mock_manager.github_config = {
            'allowed_repositories': [
                {"name": "owner/other-repo", "description": "Other Repo"}
            ]
        }
        
        factory = GitHubToolFactory(mock_manager)
        
        repository = Mock(spec=GitHubRepository)
        repository.full_name = "owner/repo1"
        
        metadata = factory._get_repository_metadata(repository)
        
        assert metadata == "Operations for owner/repo1"
    
    def test_create_scoped_tool_name_short(self):
        """Test scoped tool name creation when combined name is short enough."""
        mock_manager = Mock(spec=GitHubConnectionManager)
        factory = GitHubToolFactory(mock_manager)
        
        result = factory._create_scoped_tool_name("get_issues", "owner/repo")
        
        assert result == "get_issues_owner_repo"
        assert len(result) <= 64
    
    def test_create_scoped_tool_name_long(self):
        """Test scoped tool name creation when combined name exceeds max length."""
        mock_manager = Mock(spec=GitHubConnectionManager)
        factory = GitHubToolFactory(mock_manager)
        
        # Create a very long tool and repo name
        long_tool_name = "get_pull_requests_with_detailed_information"
        long_repo_name = "organization-name/very-long-repository-name-here"
        
        result = factory._create_scoped_tool_name(long_tool_name, long_repo_name)
        
        assert len(result) <= 64
        assert result.startswith("get_pull_requests_with_detailed_information")
        assert not result.endswith('_')
        assert not result.endswith('-')
    
    def test_create_scoped_tool_name_very_long(self):
        """Test scoped tool name with extremely long names requiring balanced truncation."""
        mock_manager = Mock(spec=GitHubConnectionManager)
        factory = GitHubToolFactory(mock_manager)
        
        # Both parts are very long
        very_long_tool = "a" * 50
        very_long_repo = "b" * 50
        
        result = factory._create_scoped_tool_name(very_long_tool, very_long_repo)
        
        assert len(result) <= 64
        assert 'a' in result
        assert 'b' in result
        assert '_' in result
        """Test fallback metadata when no config exists."""
        mock_manager = Mock(spec=GitHubConnectionManager)
        mock_manager.github_config = {'allowed_repositories': []}
        
        factory = GitHubToolFactory(mock_manager)
        
        repository = Mock(spec=GitHubRepository)
        repository.full_name = "owner/repo"
        
        metadata = factory._get_repository_metadata(repository)
        
        assert "owner/repo" in metadata


class TestGitHubToolsProvider:
    """Tests for GitHubToolsProvider."""
    
    def test_provider_initialization_without_config(self):
        """Test provider initialization without configuration."""
        provider = GitHubToolsProvider()
        
        assert provider.config == {}
        assert provider._connection_manager is None
        assert provider._tool_factory is None
        assert provider._tools_cache is None
    
    def test_provider_initialization_with_config(self):
        """Test provider initialization with configuration."""
        config = {"test_key": "test_value"}
        provider = GitHubToolsProvider(config=config)
        
        assert provider.config == config
    
    def test_lazy_connection_manager_initialization(self):
        """Test lazy initialization of connection manager."""
        provider = GitHubToolsProvider()
        
        # Access connection_manager property
        manager = provider.connection_manager
        
        assert manager is not None
        assert isinstance(manager, GitHubConnectionManager)
        # Verify it returns same instance on subsequent calls
        assert provider.connection_manager is manager
    
    def test_lazy_tool_factory_initialization(self):
        """Test lazy initialization of tool factory."""
        provider = GitHubToolsProvider()
        
        # Access tool_factory property
        factory = provider.tool_factory
        
        assert factory is not None
        assert isinstance(factory, GitHubToolFactory)
        # Verify it returns same instance on subsequent calls
        assert provider.tool_factory is factory
    
    def test_invalidate_cache(self):
        """Test cache invalidation."""
        provider = GitHubToolsProvider()
        
        # Set mock cache
        provider._tools_cache = [Mock()]
        provider._connection_manager = Mock()
        provider._connection_manager._accessible_repositories = [Mock()]
        
        # Invalidate
        provider.invalidate_cache()
        
        assert provider._tools_cache is None
        assert provider._connection_manager._accessible_repositories is None
    
    @patch('app.agent.tools.github.github_tools.GitHubConnectionManager')
    @patch('app.agent.tools.github.github_tools.GitHubToolFactory')
    def test_get_tools_with_connection_failure(self, mock_factory_class, mock_manager_class):
        """Test get_tools when connection fails."""
        mock_manager = Mock()
        mock_manager.connect.return_value = False
        mock_manager_class.return_value = mock_manager
        
        provider = GitHubToolsProvider()
        tools = provider.get_tools()
        
        assert tools == []
    
    @patch('app.agent.tools.github.github_tools.GitHubConnectionManager')
    @patch('app.agent.tools.github.github_tools.GitHubToolFactory')
    def test_get_tools_with_no_repositories(self, mock_factory_class, mock_manager_class):
        """Test get_tools when no repositories are accessible."""
        mock_manager = Mock()
        mock_manager.connect.return_value = True
        mock_manager.get_allowed_repositories.return_value = []
        mock_manager_class.return_value = mock_manager
        
        provider = GitHubToolsProvider()
        tools = provider.get_tools()
        
        assert tools == []
    
    @patch('app.agent.tools.github.github_tools.GitHubConnectionManager')
    @patch('app.agent.tools.github.github_tools.GitHubToolFactory')
    def test_get_tools_successful(self, mock_factory_class, mock_manager_class):
        """Test successful tools creation."""
        # Mock repository
        mock_repo = Mock(spec=GitHubRepository)
        mock_repo.full_name = "owner/repo"
        
        # Mock tools
        mock_tool1 = Mock(spec=StructuredTool)
        mock_tool1.name = "tool1"
        mock_tool2 = Mock(spec=StructuredTool)
        mock_tool2.name = "tool2"
        
        # Mock manager
        mock_manager = Mock()
        mock_manager.connect.return_value = True
        mock_manager.get_allowed_repositories.return_value = [mock_repo]
        mock_manager_class.return_value = mock_manager
        
        # Mock factory
        mock_factory = Mock()
        mock_factory.get_all_repository_tools.return_value = [mock_tool1, mock_tool2]
        mock_factory.create_cross_repository_tools.return_value = []
        mock_factory_class.return_value = mock_factory
        
        provider = GitHubToolsProvider()
        tools = provider.get_tools()
        
        assert len(tools) == 2
        assert tools[0].name == "tool1"
        assert tools[1].name == "tool2"
    
    def test_get_tools_uses_cache(self):
        """Test that get_tools uses cache on subsequent calls."""
        provider = GitHubToolsProvider()
        
        # Set mock cache
        mock_tool = Mock(spec=StructuredTool)
        provider._tools_cache = [mock_tool]
        
        tools = provider.get_tools()
        
        assert len(tools) == 1
        assert tools[0] is mock_tool


class TestGitHubToolsIntegration:
    """Integration-style tests for GitHub tools with comprehensive mocking."""
    
    @patch('app.agent.tools.github.connection_manager.GithubIntegration')
    @patch('app.agent.tools.github.connection_manager.read_private_key_file')
    @patch('app.agent.tools.github.connection_manager.settings')
    def test_full_tool_creation_flow(self, mock_settings, mock_read_key, mock_github_integration):
        """Test complete flow of tool creation from configuration to tools."""
        # Setup mock configuration
        mock_github = Mock()
        mock_github.api_key = None
        mock_github.base_url = "https://api.github.com"
        mock_github.timeout = 30
        
        mock_app = Mock()
        mock_app.app_id = "12345"
        mock_app.private_key_path = "/path/to/key.pem"
        mock_app.installation_id = "67890"
        mock_app.client_secret = "secret"
        mock_github.app = mock_app
        
        mock_github.allowed_repositories = [
            {"name": "owner/repo1", "description": "Test Repository 1"}
        ]
        
        mock_external = Mock()
        mock_external.github = mock_github
        mock_settings.external = mock_external
        
        # Mock tools configuration
        mock_github_tools = Mock()
        mock_github_tools.enabled = True
        mock_github_tools.available_tools = {
            "Get Issues": True,
            "Read File": True
        }
        mock_tools = Mock()
        mock_tools.github = mock_github_tools
        mock_settings.tools.tools = mock_tools
        
        # Mock private key reading
        mock_read_key.return_value = "fake_private_key"
        
        # Mock GitHub integration and installation
        mock_installation = Mock()
        mock_installation.id = 67890
        mock_installation.account.login = "owner"
        
        mock_integration_instance = Mock()
        mock_integration_instance.get_app_installation.return_value = mock_installation
        mock_integration_instance.get_access_token.return_value.token = "fake_token"
        mock_github_integration.return_value = mock_integration_instance
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.full_name = "owner/repo1"
        mock_repo.name = "repo1"
        mock_repo.owner.login = "owner"
        mock_repo.private = False
        mock_repo.permissions = Mock()
        mock_repo.get_contents.return_value = Mock()  # Simulates README access
        
        mock_installation.get_repos.return_value = [mock_repo]
        
        # Test provider
        provider = GitHubToolsProvider()
        
        # Verify connection manager is created
        assert provider.connection_manager is not None
        
        # Verify tool factory is created
        assert provider.tool_factory is not None
    
    @patch('app.agent.tools.github.connection_manager.settings')
    def test_repository_filtering(self, mock_settings):
        """Test repository filtering based on configuration."""
        # Setup mock configuration with allowed repositories
        mock_github = Mock()
        mock_github.api_key = "test_key"
        mock_github.base_url = "https://api.github.com"
        mock_github.timeout = 30
        mock_github.allowed_repositories = [
            {"name": "owner/repo1", "description": "Allowed Repo 1"},
            {"name": "owner/repo2", "description": "Allowed Repo 2"}
        ]
        
        mock_external = Mock()
        mock_external.github = mock_github
        mock_settings.external = mock_external
        
        provider = GitHubToolsProvider()
        
        # Create mock repositories
        mock_repo1 = Mock()
        mock_repo1.full_name = "owner/repo1"
        mock_repo1.name = "repo1"
        mock_repo1.owner.login = "owner"
        mock_repo1.private = False
        mock_repo1.permissions = Mock()
        
        mock_repo2 = Mock()
        mock_repo2.full_name = "owner/repo2"
        mock_repo2.name = "repo2"
        mock_repo2.owner.login = "owner"
        mock_repo2.private = False
        mock_repo2.permissions = Mock()
        
        mock_repo3 = Mock()
        mock_repo3.full_name = "owner/repo3"
        mock_repo3.name = "repo3"
        mock_repo3.owner.login = "owner"
        mock_repo3.private = False
        mock_repo3.permissions = Mock()
        
        # Mock accessible repos (includes one not in allowed list)
        provider.connection_manager._accessible_repositories = [
            GitHubRepository(mock_repo1),
            GitHubRepository(mock_repo2),
            GitHubRepository(mock_repo3)
        ]
        
        # Get allowed repositories
        allowed = provider.connection_manager.get_allowed_repositories()
        
        # Should only include repo1 and repo2
        assert len(allowed) == 2
        assert all(repo.full_name in ["owner/repo1", "owner/repo2"] for repo in allowed)
    
    @patch('app.agent.tools.github.connection_manager.settings')
    def test_wildcard_repository_pattern(self, mock_settings):
        """Test wildcard pattern matching for repositories."""
        # Setup mock configuration with wildcard
        mock_github = Mock()
        mock_github.api_key = "test_key"
        mock_github.base_url = "https://api.github.com"
        mock_github.timeout = 30
        mock_github.allowed_repositories = [
            {"name": "owner/*", "description": "All owner repos"}
        ]
        
        mock_external = Mock()
        mock_external.github = mock_github
        mock_settings.external = mock_external
        
        provider = GitHubToolsProvider()
        
        # Create mock repositories
        mock_repo1 = Mock()
        mock_repo1.full_name = "owner/repo1"
        mock_repo1.name = "repo1"
        mock_repo1.owner.login = "owner"
        mock_repo1.private = False
        mock_repo1.permissions = Mock()
        
        mock_repo2 = Mock()
        mock_repo2.full_name = "owner/repo2"
        mock_repo2.name = "repo2"
        mock_repo2.owner.login = "owner"
        mock_repo2.private = False
        mock_repo2.permissions = Mock()
        
        mock_repo3 = Mock()
        mock_repo3.full_name = "other/repo3"
        mock_repo3.name = "repo3"
        mock_repo3.owner.login = "other"
        mock_repo3.private = False
        mock_repo3.permissions = Mock()
        
        # Mock accessible repos
        provider.connection_manager._accessible_repositories = [
            GitHubRepository(mock_repo1),
            GitHubRepository(mock_repo2),
            GitHubRepository(mock_repo3)
        ]
        
        # Get allowed repositories
        allowed = provider.connection_manager.get_allowed_repositories()
        
        # Should only include owner repos
        assert len(allowed) == 2
        assert all(repo.owner == "owner" for repo in allowed)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
