"""
Unit tests for Confluence tools implementation.
Tests the Confluence tools provider and tool registration.
"""

import json
import unittest
from unittest.mock import Mock, patch, PropertyMock
from app.agent.tools.atlassian.confluence import ConfluenceTools


class TestConfluenceTools(unittest.TestCase):
    """Test Confluence tools provider."""
    
    def test_provider_initialization(self):
        """Test basic provider initialization."""
        provider = ConfluenceTools()
        assert provider is not None
        assert provider.config == {}
    
    def test_provider_with_config(self):
        """Test provider initialization with configuration."""
        config = {"test_key": "test_value"}
        provider = ConfluenceTools(config=config)
        assert provider.config == config
    
    @patch('app.services.external.confluence_service.ConfluenceService')
    def test_service_lazy_initialization(self, mock_service_class):
        """Test Confluence service lazy initialization."""
        # Setup mock
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        provider = ConfluenceTools()
        
        # Service should be None initially
        assert provider._confluence_service is None
        
        # Access service property - should trigger lazy load
        service = provider.confluence_service
        
        # Service should now be initialized
        assert service is not None
        assert service == mock_service
        mock_service_class.assert_called_once()
    
    def test_get_tools(self):
        """Test getting tools from provider."""
        provider = ConfluenceTools()
        tools = provider.get_tools()
        
        # Should return 5 tools
        assert len(tools) == 5
        
        # Verify tool names
        tool_names = [tool.name for tool in tools]
        assert "list_confluence_spaces" in tool_names
        assert "get_confluence_page" in tool_names
        assert "list_pages_in_space" in tool_names
        assert "search_confluence_pages" in tool_names
        assert "get_confluence_space" in tool_names


class TestListSpacesTool(unittest.TestCase):
    """Test list_confluence_spaces tool functionality."""
    
    def test_list_all_spaces(self):
        """Test listing all Confluence spaces."""
        provider = ConfluenceTools()
        
        # Mock the service
        mock_service = Mock()
        mock_service.list_confluence_spaces.return_value = ["SPACE1", "SPACE2", "SPACE3"]
        provider._confluence_service = mock_service
        
        result = provider._list_spaces(["*"])
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert result_data["total_spaces"] == 3
        assert "SPACE1" in result_data["space_keys"]
        assert "SPACE2" in result_data["space_keys"]
        mock_service.list_confluence_spaces.assert_called_once_with(["*"])
    
    def test_list_specific_spaces(self):
        """Test listing specific Confluence spaces."""
        provider = ConfluenceTools()
        
        # Mock the service
        mock_service = Mock()
        mock_service.list_confluence_spaces.return_value = ["DEV", "PROD"]
        provider._confluence_service = mock_service
        
        result = provider._list_spaces(["DEV", "PROD"])
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert result_data["total_spaces"] == 2
        mock_service.list_confluence_spaces.assert_called_once_with(["DEV", "PROD"])
    
    def test_list_spaces_no_results(self):
        """Test listing spaces when none found."""
        provider = ConfluenceTools()
        
        # Mock the service
        mock_service = Mock()
        mock_service.list_confluence_spaces.return_value = []
        provider._confluence_service = mock_service
        
        result = provider._list_spaces()
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert result_data["total_spaces"] == 0
        assert result_data["spaces"] == []
    
    def test_list_spaces_service_unavailable(self):
        """Test listing spaces when service unavailable."""
        provider = ConfluenceTools()
        
        # Mock the property to return None
        with patch.object(type(provider), 'confluence_service', new_callable=PropertyMock) as mock_prop:
            mock_prop.return_value = None
            
            result = provider._list_spaces()
            result_data = json.loads(result)
            
            assert result_data["status"] == "error"
            assert "not available" in result_data["message"]
    
    def test_list_spaces_exception_handling(self):
        """Test exception handling in list spaces."""
        provider = ConfluenceTools()
        
        # Mock service to raise exception
        mock_service = Mock()
        mock_service.list_confluence_spaces.side_effect = Exception("API Error")
        provider._confluence_service = mock_service
        
        result = provider._list_spaces()
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "API Error" in result_data["message"]


class TestGetPageTool(unittest.TestCase):
    """Test get_confluence_page tool functionality."""
    
    def test_get_page_success(self):
        """Test successfully retrieving a Confluence page."""
        provider = ConfluenceTools()
        
        # Mock the service
        mock_service = Mock()
        mock_content = "# Test Page\n\nThis is test content."
        mock_metadata = {
            "page_id": "123456",
            "title": "Test Page",
            "space": "DEV",
            "url": "https://example.atlassian.net/wiki/spaces/DEV/pages/123456"
        }
        mock_service.retrieve_confluence_page.return_value = (mock_content, mock_metadata)
        provider._confluence_service = mock_service
        
        result = provider._get_page("123456")
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert result_data["page_id"] == "123456"
        assert result_data["content"] == mock_content
        assert result_data["metadata"]["title"] == "Test Page"
        mock_service.retrieve_confluence_page.assert_called_once_with("123456")
    
    def test_get_page_empty_page_id(self):
        """Test getting page with empty page ID."""
        provider = ConfluenceTools()
        provider._confluence_service = Mock()
        
        result = provider._get_page("")
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "required" in result_data["message"].lower()
    
    def test_get_page_not_found(self):
        """Test getting page when content is empty."""
        provider = ConfluenceTools()
        
        # Mock service to return empty content
        mock_service = Mock()
        mock_service.retrieve_confluence_page.return_value = ("", {})
        provider._confluence_service = mock_service
        
        result = provider._get_page("999999")
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "Could not retrieve" in result_data["message"]
    
    def test_get_page_service_unavailable(self):
        """Test getting page when service unavailable."""
        provider = ConfluenceTools()
        
        # Mock the property to return None
        with patch.object(type(provider), 'confluence_service', new_callable=PropertyMock) as mock_prop:
            mock_prop.return_value = None
            
            result = provider._get_page("123456")
            result_data = json.loads(result)
            
            assert result_data["status"] == "error"
            assert "not available" in result_data["message"]
    
    def test_get_page_exception_handling(self):
        """Test exception handling in get page."""
        provider = ConfluenceTools()
        
        # Mock service to raise exception
        mock_service = Mock()
        mock_service.retrieve_confluence_page.side_effect = Exception("Connection timeout")
        provider._confluence_service = mock_service
        
        result = provider._get_page("123456")
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "Connection timeout" in result_data["message"]


class TestListPagesInSpaceTool(unittest.TestCase):
    """Test list_pages_in_space tool functionality."""
    
    def test_list_pages_success(self):
        """Test successfully listing pages in a space."""
        provider = ConfluenceTools()
        
        # Mock the service
        mock_service = Mock()
        mock_pages = [
            {
                "id": "111",
                "title": "Page 1",
                "type": "page",
                "status": "current",
                "_links": {"webui": "/wiki/spaces/DEV/pages/111"},
                "version": {"number": 5, "when": "2024-01-01T00:00:00Z"}
            },
            {
                "id": "222",
                "title": "Page 2",
                "type": "page",
                "status": "current",
                "_links": {"webui": "/wiki/spaces/DEV/pages/222"},
                "version": {"number": 3, "when": "2024-01-02T00:00:00Z"}
            }
        ]
        mock_service.list_confluence_pages_in_space.return_value = mock_pages
        provider._confluence_service = mock_service
        
        result = provider._list_pages_in_space("DEV")
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert result_data["space_key"] == "DEV"
        assert result_data["total_pages"] == 2
        assert result_data["returned_pages"] == 2
        assert len(result_data["pages"]) == 2
        assert result_data["pages"][0]["title"] == "Page 1"
        mock_service.list_confluence_pages_in_space.assert_called_once_with("DEV")
    
    def test_list_pages_with_limit(self):
        """Test listing pages with result limit."""
        provider = ConfluenceTools()
        
        # Mock the service with many pages
        mock_service = Mock()
        mock_pages = [
            {"id": str(i), "title": f"Page {i}", "type": "page", "status": "current",
             "_links": {}, "version": {"number": 1}}
            for i in range(100)
        ]
        mock_service.list_confluence_pages_in_space.return_value = mock_pages
        provider._confluence_service = mock_service
        
        result = provider._list_pages_in_space("LARGE", max_results=10)
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert result_data["total_pages"] == 100
        assert result_data["returned_pages"] == 10
        assert len(result_data["pages"]) == 10
    
    def test_list_pages_empty_space_key(self):
        """Test listing pages with empty space key."""
        provider = ConfluenceTools()
        provider._confluence_service = Mock()
        
        result = provider._list_pages_in_space("")
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "required" in result_data["message"].lower()
    
    def test_list_pages_no_results(self):
        """Test listing pages when space is empty."""
        provider = ConfluenceTools()
        
        # Mock service to return empty list
        mock_service = Mock()
        mock_service.list_confluence_pages_in_space.return_value = []
        provider._confluence_service = mock_service
        
        result = provider._list_pages_in_space("EMPTY")
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert result_data["total_pages"] == 0
        assert result_data["pages"] == []
    
    def test_list_pages_service_unavailable(self):
        """Test listing pages when service unavailable."""
        provider = ConfluenceTools()
        
        # Mock the property to return None
        with patch.object(type(provider), 'confluence_service', new_callable=PropertyMock) as mock_prop:
            mock_prop.return_value = None
            
            result = provider._list_pages_in_space("DEV")
            result_data = json.loads(result)
            
            assert result_data["status"] == "error"
            assert "not available" in result_data["message"]
    
    def test_list_pages_exception_handling(self):
        """Test exception handling in list pages."""
        provider = ConfluenceTools()
        
        # Mock service to raise exception
        mock_service = Mock()
        mock_service.list_confluence_pages_in_space.side_effect = Exception("Invalid space")
        provider._confluence_service = mock_service
        
        result = provider._list_pages_in_space("INVALID")
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "Invalid space" in result_data["message"]


class TestSearchPagesTool(unittest.TestCase):
    """Test search_confluence_pages tool functionality."""
    
    def test_search_pages_success(self):
        """Test successfully searching for pages."""
        provider = ConfluenceTools()
        
        # Mock the service
        mock_service = Mock()
        mock_confluence_client = Mock()
        mock_search_results = {
            "results": [
                {
                    "content": {
                        "id": "111",
                        "title": "Test Page 1",
                        "type": "page",
                        "space": {"key": "DEV"},
                        "_links": {"webui": "/wiki/spaces/DEV/pages/111"}
                    },
                    "excerpt": "This is a test page with the search term..."
                },
                {
                    "content": {
                        "id": "222",
                        "title": "Test Page 2",
                        "type": "page",
                        "space": {"key": "PROD"},
                        "_links": {"webui": "/wiki/spaces/PROD/pages/222"}
                    },
                    "excerpt": "Another page matching the search..."
                }
            ],
            "totalSize": 2
        }
        mock_confluence_client.cql.return_value = mock_search_results
        mock_service._confluence = mock_confluence_client
        provider._confluence_service = mock_service
        
        result = provider._search_pages("test query")
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert result_data["query"] == "test query"
        assert result_data["total_results"] == 2
        assert result_data["returned_results"] == 2
        assert len(result_data["results"]) == 2
        assert result_data["results"][0]["title"] == "Test Page 1"
    
    def test_search_pages_with_space_filter(self):
        """Test searching pages with space filter."""
        provider = ConfluenceTools()
        
        # Mock the service
        mock_service = Mock()
        mock_confluence_client = Mock()
        mock_search_results = {
            "results": [
                {
                    "content": {
                        "id": "111",
                        "title": "Dev Page",
                        "type": "page",
                        "space": {"key": "DEV"},
                        "_links": {"webui": "/wiki/spaces/DEV/pages/111"}
                    },
                    "excerpt": "Development page..."
                }
            ],
            "totalSize": 1
        }
        mock_confluence_client.cql.return_value = mock_search_results
        mock_service._confluence = mock_confluence_client
        provider._confluence_service = mock_service
        
        result = provider._search_pages("development", space_key="DEV", max_results=10)
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert result_data["space_key"] == "DEV"
        assert result_data["total_results"] == 1
        # Verify CQL query includes space filter
        call_args = mock_confluence_client.cql.call_args[0][0]
        assert 'AND space = "DEV"' in call_args
    
    def test_search_pages_empty_query(self):
        """Test searching with empty query."""
        provider = ConfluenceTools()
        provider._confluence_service = Mock()
        
        result = provider._search_pages("")
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "required" in result_data["message"].lower()
    
    def test_search_pages_no_results(self):
        """Test searching when no pages match."""
        provider = ConfluenceTools()
        
        # Mock service with empty results
        mock_service = Mock()
        mock_confluence_client = Mock()
        mock_confluence_client.cql.return_value = {"results": [], "totalSize": 0}
        mock_service._confluence = mock_confluence_client
        provider._confluence_service = mock_service
        
        result = provider._search_pages("nonexistent term")
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert result_data["total_results"] == 0
        assert result_data["results"] == []
    
    def test_search_pages_service_unavailable(self):
        """Test searching when service unavailable."""
        provider = ConfluenceTools()
        
        # Mock the property to return None
        with patch.object(type(provider), 'confluence_service', new_callable=PropertyMock) as mock_prop:
            mock_prop.return_value = None
            
            result = provider._search_pages("test")
            result_data = json.loads(result)
            
            assert result_data["status"] == "error"
            assert "not available" in result_data["message"]
    
    def test_search_pages_exception_handling(self):
        """Test exception handling in search pages."""
        provider = ConfluenceTools()
        
        # Mock service to raise exception
        mock_service = Mock()
        mock_confluence_client = Mock()
        mock_confluence_client.cql.side_effect = Exception("Search failed")
        mock_service._confluence = mock_confluence_client
        provider._confluence_service = mock_service
        
        result = provider._search_pages("test")
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "Search failed" in result_data["message"]


class TestGetSpaceTool(unittest.TestCase):
    """Test get_confluence_space tool functionality."""
    
    def test_get_space_success(self):
        """Test successfully getting a Confluence space."""
        provider = ConfluenceTools()
        
        # Mock the service
        mock_service = Mock()
        mock_confluence_client = Mock()
        mock_space_data = {
            "key": "DEV",
            "name": "Development",
            "id": "12345",
            "type": "global",
            "description": {
                "plain": {
                    "value": "Development space for the team"
                }
            },
            "homepage": {
                "id": "111",
                "title": "Dev Home"
            },
            "_links": {
                "webui": "/wiki/spaces/DEV"
            }
        }
        mock_confluence_client.get_space.return_value = mock_space_data
        mock_service._confluence = mock_confluence_client
        provider._confluence_service = mock_service
        
        result = provider._get_space("DEV")
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert result_data["space"]["key"] == "DEV"
        assert result_data["space"]["name"] == "Development"
        assert result_data["space"]["description"] == "Development space for the team"
        assert result_data["space"]["homepage"]["title"] == "Dev Home"
        mock_confluence_client.get_space.assert_called_once_with("DEV", expand='description.plain,homepage')
    
    def test_get_space_empty_key(self):
        """Test getting space with empty key."""
        provider = ConfluenceTools()
        provider._confluence_service = Mock()
        
        result = provider._get_space("")
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "required" in result_data["message"].lower()
    
    def test_get_space_not_found(self):
        """Test getting space when it doesn't exist."""
        provider = ConfluenceTools()
        
        # Mock service to return None
        mock_service = Mock()
        mock_confluence_client = Mock()
        mock_confluence_client.get_space.return_value = None
        mock_service._confluence = mock_confluence_client
        provider._confluence_service = mock_service
        
        result = provider._get_space("NOTFOUND")
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "Could not find space" in result_data["message"]
    
    def test_get_space_service_unavailable(self):
        """Test getting space when service unavailable."""
        provider = ConfluenceTools()
        
        # Mock the property to return None
        with patch.object(type(provider), 'confluence_service', new_callable=PropertyMock) as mock_prop:
            mock_prop.return_value = None
            
            result = provider._get_space("DEV")
            result_data = json.loads(result)
            
            assert result_data["status"] == "error"
            assert "not available" in result_data["message"]
    
    def test_get_space_exception_handling(self):
        """Test exception handling in get space."""
        provider = ConfluenceTools()
        
        # Mock service to raise exception
        mock_service = Mock()
        mock_confluence_client = Mock()
        mock_confluence_client.get_space.side_effect = Exception("Permission denied")
        mock_service._confluence = mock_confluence_client
        provider._confluence_service = mock_service
        
        result = provider._get_space("RESTRICTED")
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "Permission denied" in result_data["message"]


class TestConfluenceToolsIntegration(unittest.TestCase):
    """Integration tests for Confluence tools with registry."""
    
    def test_tools_properly_registered(self):
        """Test that Confluence tools class is properly registered."""
        from app.agent.tools.base.registry import ToolRegistry
        
        # Just verify our module imported and registered without errors
        # The actual registry integration is tested in test_tool_registry.py
        assert ConfluenceTools is not None
        assert hasattr(ConfluenceTools, 'get_tools')
        
        # Verify we can instantiate and get tools
        provider = ConfluenceTools()
        tools = provider.get_tools()
        assert len(tools) == 5


if __name__ == '__main__':
    unittest.main()
