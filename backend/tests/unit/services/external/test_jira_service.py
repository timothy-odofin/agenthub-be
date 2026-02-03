"""
Unit tests for JiraService.

Tests the JiraService functionality including:
- Singleton pattern implementation
- Connection management and initialization
- JIRA issue operations (search, create, get)
- Project and server info retrieval
- Error handling and edge cases
- Connection lifecycle management
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.external.jira_service import JiraClient, jira
from app.infrastructure.connections.base import ConnectionType


class TestJiraServiceArchitecture:
    """Test the architectural patterns of JiraService."""
    
    def teardown_method(self):
        """Clean up singleton state after each test."""
        if hasattr(JiraClient, '_instances'):
            JiraClient._instances.clear()

    def test_singleton_pattern_implementation(self):
        """Test that JiraClient follows singleton pattern correctly."""
        # Create multiple instances
        client1 = JiraClient()
        client2 = JiraClient()
        
        # Should be the same instance
        assert client1 is client2
        assert id(client1) == id(client2)

    def test_initialization_sets_none_attributes(self):
        """Test that JiraClient initializes with None connection attributes."""
        client = JiraClient()
        
        assert client._connection_manager is None
        assert client._jira_client is None

    def test_module_level_jira_instance_available(self):
        """Test that the module provides a jira instance."""
        from app.services.external.jira_service import jira
        
        assert jira is not None
        assert isinstance(jira, JiraClient)


class TestJiraServiceConnectionManagement:
    """Test JIRA connection management functionality."""
    
    def teardown_method(self):
        """Clean up singleton state after each test."""
        if hasattr(JiraClient, '_instances'):
            JiraClient._instances.clear()

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_ensure_connected_initializes_connection_manager(self, mock_connection_factory):
        """Test that _ensure_connected properly initializes connection manager."""
        mock_manager = Mock()
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        client._ensure_connected()
        
        mock_connection_factory.get_connection_manager.assert_called_once_with(ConnectionType.JIRA)
        assert client._connection_manager is mock_manager

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_ensure_connected_establishes_client_connection(self, mock_connection_factory):
        """Test that _ensure_connected establishes JIRA client connection."""
        mock_manager = Mock()
        mock_jira_client = Mock()
        mock_manager.connect.return_value = mock_jira_client
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        result = client._ensure_connected()
        
        mock_manager.connect.assert_called_once()
        assert client._jira_client is mock_jira_client
        assert result is mock_jira_client

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_ensure_connected_reuses_existing_connection(self, mock_connection_factory):
        """Test that _ensure_connected reuses existing connections."""
        mock_manager = Mock()
        mock_jira_client = Mock()
        mock_manager.connect.return_value = mock_jira_client
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        
        # First call should initialize
        result1 = client._ensure_connected()
        # Second call should reuse
        result2 = client._ensure_connected()
        
        # Should only call connect once
        mock_manager.connect.assert_called_once()
        assert result1 is result2


class TestJiraServiceIssueOperations:
    """Test JIRA issue-related operations."""
    
    def teardown_method(self):
        """Clean up singleton state after each test."""
        if hasattr(JiraClient, '_instances'):
            JiraClient._instances.clear()

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_search_issues_with_default_parameters(self, mock_connection_factory):
        """Test searching for issues with default parameters."""
        mock_manager = Mock()
        mock_issues = [{'key': 'PROJ-1', 'summary': 'Test Issue'}]
        mock_manager.search_issues.return_value = mock_issues
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        result = client.search_issues('project = PROJ')
        
        mock_manager.search_issues.assert_called_once_with('project = PROJ', limit=50, fields=None)
        assert result == mock_issues

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_search_issues_with_custom_parameters(self, mock_connection_factory):
        """Test searching for issues with custom parameters."""
        mock_manager = Mock()
        mock_issues = [{'key': 'PROJ-1', 'fields': {'summary': 'Test'}}]
        mock_manager.search_issues.return_value = mock_issues
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        result = client.search_issues('assignee = currentUser()', limit=100, fields=['summary', 'status'])
        
        mock_manager.search_issues.assert_called_once_with(
            'assignee = currentUser()', 
            limit=100, 
            fields=['summary', 'status']
        )
        assert result == mock_issues

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_create_issue_with_default_type(self, mock_connection_factory):
        """Test creating an issue with default issue type."""
        mock_manager = Mock()
        mock_issue = {'key': 'PROJ-123', 'id': '10001'}
        mock_manager.create_issue.return_value = mock_issue
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        result = client.create_issue('PROJ', 'Test Summary', 'Test Description')
        
        mock_manager.create_issue.assert_called_once_with(
            project_key='PROJ',
            summary='Test Summary',
            description='Test Description',
            issue_type='Task'
        )
        assert result == mock_issue

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_create_issue_with_custom_type(self, mock_connection_factory):
        """Test creating an issue with custom issue type."""
        mock_manager = Mock()
        mock_issue = {'key': 'PROJ-124', 'id': '10002'}
        mock_manager.create_issue.return_value = mock_issue
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        result = client.create_issue('PROJ', 'Bug Summary', 'Bug Description', 'Bug')
        
        mock_manager.create_issue.assert_called_once_with(
            project_key='PROJ',
            summary='Bug Summary',
            description='Bug Description',
            issue_type='Bug'
        )
        assert result == mock_issue

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_get_issue_success(self, mock_connection_factory):
        """Test retrieving a specific issue by key."""
        mock_manager = Mock()
        mock_issue = {
            'key': 'PROJ-123',
            'fields': {
                'summary': 'Test Issue',
                'status': {'name': 'Open'},
                'issuetype': {'name': 'Task'}
            }
        }
        mock_manager.get_issue.return_value = mock_issue
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        result = client.get_issue('PROJ-123')
        
        mock_manager.get_issue.assert_called_once_with('PROJ-123')
        assert result == mock_issue


class TestJiraServiceProjectOperations:
    """Test JIRA project-related operations."""
    
    def teardown_method(self):
        """Clean up singleton state after each test."""
        if hasattr(JiraClient, '_instances'):
            JiraClient._instances.clear()

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_get_projects_success(self, mock_connection_factory):
        """Test retrieving accessible projects."""
        mock_manager = Mock()
        mock_projects = [
            {'key': 'PROJ1', 'name': 'Project One', 'id': '10001'},
            {'key': 'PROJ2', 'name': 'Project Two', 'id': '10002'}
        ]
        mock_manager.get_projects.return_value = mock_projects
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        result = client.get_projects()
        
        mock_manager.get_projects.assert_called_once()
        assert result == mock_projects

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_get_server_info_success(self, mock_connection_factory):
        """Test retrieving JIRA server information."""
        mock_manager = Mock()
        mock_server_info = {
            'version': '8.20.0',
            'versionNumbers': [8, 20, 0],
            'buildNumber': 820000,
            'serverTitle': 'Test JIRA'
        }
        mock_manager.get_server_info.return_value = mock_server_info
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        result = client.get_server_info()
        
        mock_manager.get_server_info.assert_called_once()
        assert result == mock_server_info


class TestJiraServiceConnectionLifecycle:
    """Test JIRA connection lifecycle management."""
    
    def teardown_method(self):
        """Clean up singleton state after each test."""
        if hasattr(JiraClient, '_instances'):
            JiraClient._instances.clear()

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_disconnect_with_active_connection(self, mock_connection_factory):
        """Test disconnecting with an active connection manager."""
        mock_manager = Mock()
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        client._ensure_connected()  # Establish connection
        client.disconnect()
        
        mock_manager.disconnect.assert_called_once()
        assert client._jira_client is None

    def test_disconnect_with_no_connection(self):
        """Test disconnecting when no connection is active."""
        client = JiraClient()
        
        # Should not raise any exceptions
        client.disconnect()
        
        assert client._connection_manager is None
        assert client._jira_client is None


class TestJiraServiceErrorHandling:
    """Test error handling in JiraService operations."""
    
    def teardown_method(self):
        """Clean up singleton state after each test."""
        if hasattr(JiraClient, '_instances'):
            JiraClient._instances.clear()

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_connection_failure_propagates_error(self, mock_connection_factory):
        """Test that connection failures are properly propagated."""
        mock_connection_factory.get_connection_manager.side_effect = Exception("Connection failed")
        
        client = JiraClient()
        
        with pytest.raises(Exception, match="Connection failed"):
            client._ensure_connected()

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_search_issues_error_propagation(self, mock_connection_factory):
        """Test that search_issues errors are properly propagated."""
        mock_manager = Mock()
        mock_manager.search_issues.side_effect = Exception("Search failed")
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        
        with pytest.raises(Exception, match="Search failed"):
            client.search_issues('invalid jql')

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_create_issue_error_propagation(self, mock_connection_factory):
        """Test that create_issue errors are properly propagated."""
        mock_manager = Mock()
        mock_manager.create_issue.side_effect = Exception("Creation failed")
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        
        with pytest.raises(Exception, match="Creation failed"):
            client.create_issue('INVALID', 'Test', 'Test')

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_get_issue_error_propagation(self, mock_connection_factory):
        """Test that get_issue errors are properly propagated."""
        mock_manager = Mock()
        mock_manager.get_issue.side_effect = Exception("Issue not found")
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        
        with pytest.raises(Exception, match="Issue not found"):
            client.get_issue('NONEXISTENT-123')


class TestJiraServiceIntegration:
    """Test integration aspects of JiraService."""
    
    def teardown_method(self):
        """Clean up singleton state after each test."""
        if hasattr(JiraClient, '_instances'):
            JiraClient._instances.clear()

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_multiple_operations_reuse_connection(self, mock_connection_factory):
        """Test that multiple operations reuse the same connection."""
        mock_manager = Mock()
        mock_manager.get_projects.return_value = []
        mock_manager.get_server_info.return_value = {}
        mock_manager.search_issues.return_value = []
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        client = JiraClient()
        
        # Perform multiple operations
        client.get_projects()
        client.get_server_info()
        client.search_issues('project = TEST')
        
        # Should only create connection manager once
        mock_connection_factory.get_connection_manager.assert_called_once_with(ConnectionType.JIRA)
        # Connection manager should be called multiple times for operations
        mock_manager.get_projects.assert_called_once()
        mock_manager.get_server_info.assert_called_once()
        mock_manager.search_issues.assert_called_once()

    @patch('app.services.external.jira_service.ConnectionFactory')
    def test_module_level_instance_maintains_state(self, mock_connection_factory):
        """Test that the module-level jira instance maintains state across calls."""
        mock_manager = Mock()
        mock_connection_factory.get_connection_manager.return_value = mock_manager
        
        # Use module-level instance
        from app.services.external.jira_service import jira
        
        # First operation establishes connection
        jira.get_server_info()
        
        # Second operation should reuse connection
        jira.get_projects()
        
        # Should only initialize connection manager once
        mock_connection_factory.get_connection_manager.assert_called_once()
