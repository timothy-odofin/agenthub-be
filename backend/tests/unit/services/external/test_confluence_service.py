"""
Unit tests for ConfluenceService.

Tests the Confluence external service functionality including:
- Singleton pattern implementation
- Atlassian API integration
- Space listing with pagination
- Page retrieval and content extraction
- HTML content cleaning and parsing
- Error handling scenarios
- Client initialization
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import requests
from bs4 import BeautifulSoup

from app.services.external.confluence_service import ConfluenceService


class TestConfluenceServiceArchitecture:
    """Test the architectural aspects of ConfluenceService."""

    def test_singleton_pattern_implementation(self):
        """Test that ConfluenceService implements singleton pattern correctly."""
        # Clear any existing instances
        ConfluenceService._instances = {}
        
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service1 = ConfluenceService()
            service2 = ConfluenceService()
            
            assert service1 is service2
            assert id(service1) == id(service2)

    @patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client')
    def test_initialization_calls_init_client(self, mock_init_client):
        """Test that initialization calls the client setup method."""
        # Clear singleton instances
        ConfluenceService._instances = {}
        ConfluenceService()
        mock_init_client.assert_called_once()

    def test_has_required_attributes_after_init(self):
        """Test that service has required attributes after initialization."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            assert hasattr(service, '_confluence')


class TestConfluenceServiceClientInitialization:
    """Test the Confluence client initialization."""
    
    def test_client_initialization_attributes(self):
        """Test that client initialization sets up required attributes."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            service._confluence = Mock()  # Simulate initialized client
            
            # Verify service has confluence client attribute
            assert hasattr(service, '_confluence')
            assert service._confluence is not None


class TestConfluenceServiceSpaceListing:
    """Test space listing functionality."""

    def test_list_confluence_spaces_wildcard_single_page(self):
        """Test listing all spaces with wildcard when results fit in single page."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            # Mock confluence client
            mock_confluence = Mock()
            service._confluence = mock_confluence
            
            # Setup mock response - single page of results
            mock_response = {
                'results': [
                    {'key': 'SPACE1', 'name': 'Space One'},
                    {'key': 'SPACE2', 'name': 'Space Two'}
                ],
                'size': 2
            }
            mock_confluence.get_all_spaces.return_value = mock_response
            
            # Execute
            result = service.list_confluence_spaces(['*'])
            
            # Verify
            assert result == ['SPACE1', 'SPACE2']
            mock_confluence.get_all_spaces.assert_called_once_with(
                start=0, limit=100, expand='description.plain,homepage'
            )

    def test_list_confluence_spaces_wildcard_multiple_pages(self):
        """Test listing all spaces with wildcard across multiple pages."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            mock_confluence = Mock()
            service._confluence = mock_confluence
            
            # Setup mock responses for pagination
            first_page = {
                'results': [{'key': 'SPACE1'}, {'key': 'SPACE2'}],
                'size': 100  # Full page
            }
            second_page = {
                'results': [{'key': 'SPACE3'}],
                'size': 1  # Last page with fewer results
            }
            
            mock_confluence.get_all_spaces.side_effect = [first_page, second_page]
            
            # Execute
            result = service.list_confluence_spaces(['*'])
            
            # Verify
            assert result == ['SPACE1', 'SPACE2', 'SPACE3']
            assert mock_confluence.get_all_spaces.call_count == 2
            
            # Check pagination calls
            calls = mock_confluence.get_all_spaces.call_args_list
            assert calls[0][1]['start'] == 0
            assert calls[1][1]['start'] == 100

    def test_list_confluence_spaces_specific_keys_success(self):
        """Test listing specific space keys successfully."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            mock_confluence = Mock()
            service._confluence = mock_confluence
            
            # Setup mock responses for specific spaces
            space1_data = {'key': 'SPACE1', 'name': 'Space One'}
            space2_data = {'key': 'SPACE2', 'name': 'Space Two'}
            
            mock_confluence.get_space.side_effect = [space1_data, space2_data]
            
            # Execute
            result = service.list_confluence_spaces(['SPACE1', 'SPACE2'])
            
            # Verify
            assert result == ['SPACE1', 'SPACE2']
            assert mock_confluence.get_space.call_count == 2
            mock_confluence.get_space.assert_any_call('SPACE1', expand='description.plain,homepage')
            mock_confluence.get_space.assert_any_call('SPACE2', expand='description.plain,homepage')

    def test_list_confluence_spaces_specific_keys_with_missing(self):
        """Test listing specific space keys with some missing."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            mock_confluence = Mock()
            service._confluence = mock_confluence
            
            # Setup mock responses - one exists, one doesn't
            space1_data = {'key': 'SPACE1', 'name': 'Space One'}
            
            mock_confluence.get_space.side_effect = [space1_data, None]
            
            # Execute with logging patch
            with patch('app.services.external.confluence_service.logger') as mock_logger:
                result = service.list_confluence_spaces(['SPACE1', 'MISSING'])
            
            # Verify
            assert result == ['SPACE1']
            mock_logger.warning.assert_called_once_with(
                "Could not find space MISSING in Confluence First Item"
            )


class TestConfluenceServicePageOperations:
    """Test page retrieval and content extraction."""

    def test_retrieve_confluence_page_success(self):
        """Test successful page retrieval."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            mock_confluence = Mock()
            service._confluence = mock_confluence
            
            # Setup mock page data
            mock_page = {
                'id': 'page123',
                'title': 'Test Page',
                'body': {
                    'storage': {
                        'value': '<p>Test content</p>'
                    }
                },
                'space': {'key': 'SPACE1'},
                'version': {'when': '2023-01-01', 'number': 1}
            }
            
            mock_confluence.get_page_by_id.return_value = mock_page
            
            # Execute
            content, metadata = service.retrieve_confluence_page('page123')
            
            # Verify
            mock_confluence.get_page_by_id.assert_called_once_with(
                'page123', expand='body.storage,version,ancestors,space'
            )
            
            assert 'Test Page' in content
            assert 'Test content' in content
            assert metadata['page_id'] == 'page123'
            assert metadata['title'] == 'Test Page'

    def test_list_confluence_pages_in_space_single_page(self):
        """Test listing pages in space with single page of results."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            mock_confluence = Mock()
            service._confluence = mock_confluence
            
            # Setup mock response
            mock_response = {
                'results': [
                    {'id': 'page1', 'title': 'Page One'},
                    {'id': 'page2', 'title': 'Page Two'}
                ],
                'size': 2
            }
            mock_confluence.get_all_pages_from_space_raw.return_value = mock_response
            
            # Execute
            result = service.list_confluence_pages_in_space('SPACE1')
            
            # Verify
            assert len(result) == 2
            assert result[0]['id'] == 'page1'
            assert result[1]['id'] == 'page2'

    def test_list_confluence_pages_in_space_multiple_pages(self):
        """Test listing pages in space across multiple API pages."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            mock_confluence = Mock()
            service._confluence = mock_confluence
            
            # Setup mock responses for pagination
            first_page = {
                'results': [{'id': 'page1'}, {'id': 'page2'}],
                'size': 100  # Full page
            }
            second_page = {
                'results': [{'id': 'page3'}],
                'size': 1  # Last page
            }
            
            mock_confluence.get_all_pages_from_space_raw.side_effect = [first_page, second_page]
            
            # Execute
            result = service.list_confluence_pages_in_space('SPACE1')
            
            # Verify
            assert len(result) == 3
            assert result[2]['id'] == 'page3'
            assert mock_confluence.get_all_pages_from_space_raw.call_count == 2


class TestConfluenceServiceContentExtraction:
    """Test HTML content extraction and cleaning."""

    def test_extract_content_from_page_with_html(self):
        """Test extracting content from page with HTML markup."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            page_data = {
                'id': 'page123',
                'title': 'Test Page',
                'body': {
                    'storage': {
                        'value': '<p>This is <strong>bold</strong> text with <em>italic</em> content.</p><script>alert("evil")</script>'
                    }
                },
                'space': {'key': 'SPACE1', 'name': 'Space Name'},
                'version': {'when': '2023-01-01', 'number': 1},
                '_links': {'webui': '/spaces/SPACE1/pages/123'}
            }
            
            # Execute
            content, metadata = service.extract_content_from_a_page(page_data)
            
            # Verify content cleaning
            assert 'Test Page' in content
            assert 'bold text with italic' in content
            assert '<script>' not in content  # Scripts should be removed
            assert '<p>' not in content  # HTML tags should be removed
            
            # Verify metadata
            assert metadata['page_id'] == 'page123'
            assert metadata['title'] == 'Test Page'
            assert metadata['source'] == 'confluence'
            assert metadata['space'] == 'SPACE1'
            assert metadata['type'] == 'confluence_page'

    def test_extract_content_from_page_with_ancestors(self):
        """Test content extraction with breadcrumb from ancestors."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            page_data = {
                'id': 'page123',
                'title': 'Child Page',
                'body': {'storage': {'value': '<p>Content</p>'}},
                'space': {'key': 'SPACE1'},
                'ancestors': [
                    {'title': 'Parent Page'},
                    {'title': 'Grandparent Page'}
                ]
            }
            
            # Execute
            content, metadata = service.extract_content_from_a_page(page_data)
            
            # Verify breadcrumb
            assert 'breadcrumb' in metadata
            assert metadata['breadcrumb'] == 'Parent Page > Grandparent Page > Child Page'

    def test_extract_content_from_page_no_content(self):
        """Test content extraction when page has no body content."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            page_data = {
                'id': 'page123',
                'title': 'Empty Page',
                'body': {},  # No storage content
                'space': {'key': 'SPACE1'}
            }
            
            # Execute
            content, metadata = service.extract_content_from_a_page(page_data)
            
            # Verify fallback to title and empty metadata
            assert content == 'Empty Page'
            assert metadata == {}  # Method returns empty dict when no content

    def test_extract_content_removes_scripts_and_styles(self):
        """Test that script and style elements are properly removed."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            page_data = {
                'id': 'page123',
                'title': 'Test Page',
                'body': {
                    'storage': {
                        'value': '''
                        <div>
                            <p>Good content</p>
                            <script>alert('bad script')</script>
                            <style>.hidden { display: none; }</style>
                            <p>More good content</p>
                        </div>
                        '''
                    }
                },
                'space': {'key': 'SPACE1'}
            }
            
            # Execute
            content, metadata = service.extract_content_from_a_page(page_data)
            
            # Verify script and style removal
            assert 'Good content' in content
            assert 'More good content' in content
            assert 'alert' not in content
            assert 'display: none' not in content
            assert '<script>' not in content
            assert '<style>' not in content


class TestConfluenceServiceErrorHandling:
    """Test error handling scenarios."""

    def test_list_confluence_spaces_with_decorator_error_handling(self):
        """Test that Atlassian error decorator returns default value on error."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            mock_confluence = Mock()
            service._confluence = mock_confluence
            
            # Setup mock to raise exception
            mock_confluence.get_all_spaces.side_effect = Exception("API Error")
            
            # Execute - should not raise, should return default empty list
            result = service.list_confluence_spaces(['*'])
            
            # Verify default return value
            assert result == []

    def test_retrieve_confluence_page_with_decorator_error_handling(self):
        """Test that page retrieval error decorator returns default value on error."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            mock_confluence = Mock()
            service._confluence = mock_confluence
            
            # Setup mock to raise exception
            mock_confluence.get_page_by_id.side_effect = Exception("Page not found")
            
            # Execute - should not raise, should return default values
            result = service.retrieve_confluence_page('invalid_id')
            
            # The decorator has default_return=[] (empty list)
            assert result == []


class TestConfluenceServiceUtilityMethods:
    """Test private utility methods."""

    def test_extract_keys_from_data(self):
        """Test key extraction utility method."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            test_data = [
                {'key': 'SPACE1', 'name': 'Space One'},
                {'key': 'SPACE2', 'name': 'Space Two'},
                {'key': 'SPACE3', 'name': 'Space Three'}
            ]
            
            # Execute private method
            result = service._ConfluenceService__extract_keys_from_data(test_data, 'key')
            
            # Verify
            assert result == ['SPACE1', 'SPACE2', 'SPACE3']

    def test_get_page_meta_complete_data(self):
        """Test page metadata extraction with complete data."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            page_data = {
                'id': 'page123',
                'title': 'Test Page',
                'space': {
                    'key': 'SPACE1',
                    'name': 'Test Space'
                },
                'version': {
                    'when': '2023-01-01T10:00:00Z',
                    'number': 5
                },
                '_links': {
                    'webui': '/spaces/SPACE1/pages/123456'
                },
                'ancestors': [
                    {'title': 'Parent'},
                    {'title': 'Grandparent'}
                ]
            }
            
            # Execute private method
            result = service._ConfluenceService__get_page_meta(page_data)
            
            # Verify complete metadata
            expected_metadata = {
                'source': 'confluence',
                'page_id': 'page123',
                'title': 'Test Page',
                'url': '/spaces/SPACE1/pages/123456',
                'space': 'SPACE1',
                'space_name': 'Test Space',
                'last_modified': '2023-01-01T10:00:00Z',
                'version': 5,
                'type': 'confluence_page',
                'breadcrumb': 'Parent > Grandparent > Test Page'
            }
            
            assert result == expected_metadata

    def test_get_page_meta_minimal_data(self):
        """Test page metadata extraction with minimal data."""
        with patch('app.services.external.confluence_service.ConfluenceService._ConfluenceService__init_client'):
            service = ConfluenceService()
            
            page_data = {
                'id': 'page123',
                'title': 'Test Page'
                # Missing optional fields
            }
            
            # Execute private method
            result = service._ConfluenceService__get_page_meta(page_data)
            
            # Verify minimal metadata with defaults
            assert result['source'] == 'confluence'
            assert result['page_id'] == 'page123'
            assert result['title'] == 'Test Page'
            assert result['url'] == ''  # Default for missing _links
            assert result['space'] == ''  # Default for missing space
            assert result['version'] == 1  # Default for missing version
            assert 'breadcrumb' not in result  # No ancestors provided
