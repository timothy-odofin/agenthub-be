"""
Unit tests for Web tools implementation.

Tests the WebTools provider and tool registration.
"""

import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from langchain.schema import Document

from app.agent.tools.web.web_tools import WebTools


class TestWebToolsInitialization:
    """Test WebTools provider initialization."""
    
    def test_provider_initialization(self):
        """Test basic provider initialization."""
        provider = WebTools()
        
        assert provider is not None
        assert provider.config == {}
    
    def test_provider_with_config(self):
        """Test provider initialization with configuration."""
        config = {"test_key": "test_value"}
        provider = WebTools(config=config)
        
        assert provider.config == config
    
    def test_chunker_lazy_initialization(self):
        """Test web content chunker lazy initialization."""
        provider = WebTools()
        
        # Chunker should be None initially
        assert provider._chunker is None
        
        # Access chunker property - should trigger lazy load
        with patch('app.services.cache.cache_factory.CacheFactory.create_cache') as mock_cache_factory:
            mock_cache = Mock()
            mock_cache_factory.return_value = mock_cache
            
            chunker = provider.chunker
            
            # Chunker should now be initialized
            assert chunker is not None
            mock_cache_factory.assert_called_once()


class TestWebToolsConfiguration:
    """Test configuration loading and parsing."""
    
    @patch('app.agent.tools.web.web_tools.settings')
    def test_load_static_url_configurations(self, mock_settings):
        """Test loading static URL configurations."""
        # Mock configuration
        mock_doc_config = Mock()
        mock_tool = Mock()
        mock_tool.enabled = True
        mock_tool.url = "https://docs.python.org"
        mock_tool.description = "Python docs"
        mock_tool.max_content_length = 50000
        
        mock_doc_config.read_python_docs = mock_tool
        
        mock_available_tools = Mock()
        mock_available_tools.documentation = mock_doc_config
        mock_available_tools.generic = None
        
        mock_web_config = Mock()
        mock_web_config.available_tools = mock_available_tools
        
        mock_tools_config = Mock()
        mock_tools_config.web = mock_web_config
        
        mock_settings.tools.tools = mock_tools_config
        
        provider = WebTools()
        
        assert len(provider._static_url_configs) > 0
    
    def test_is_domain_allowed_exact_match(self):
        """Test exact domain matching."""
        provider = WebTools()
        
        allowed_domains = ["docs.python.org", "example.com"]
        
        assert provider._is_domain_allowed("docs.python.org", allowed_domains) is True
        assert provider._is_domain_allowed("example.com", allowed_domains) is True
        assert provider._is_domain_allowed("other.com", allowed_domains) is False
    
    def test_is_domain_allowed_wildcard(self):
        """Test wildcard domain matching."""
        provider = WebTools()
        
        allowed_domains = ["*.example.com", "*.internal"]
        
        assert provider._is_domain_allowed("api.example.com", allowed_domains) is True
        assert provider._is_domain_allowed("docs.example.com", allowed_domains) is True
        assert provider._is_domain_allowed("app.internal", allowed_domains) is True
        assert provider._is_domain_allowed("example.com", allowed_domains) is False
        assert provider._is_domain_allowed("other.com", allowed_domains) is False


class TestWebToolsCreation:
    """Test tool creation."""
    
    @patch('app.agent.tools.web.web_tools.settings')
    def test_get_tools_returns_list(self, mock_settings):
        """Test that get_tools returns a list."""
        # Mock minimal configuration
        mock_settings.tools.tools.web.available_tools.documentation = Mock()
        mock_settings.tools.tools.web.available_tools.generic.read_web_url.enabled = False
        
        provider = WebTools()
        provider._static_url_configs = []  # No static URLs
        provider._generic_config = {'enabled': False}
        
        tools = provider.get_tools()
        
        assert isinstance(tools, list)
    
    @patch('app.agent.tools.web.web_tools.settings')
    def test_create_static_url_tool(self, mock_settings):
        """Test creation of static URL tool."""
        provider = WebTools()
        
        config = {
            'name': 'read_python_docs',
            'url': 'https://docs.python.org/3/',
            'description': 'Search Python documentation',
            'max_content_length': 50000
        }
        
        tool = provider._create_static_url_tool(config)
        
        assert tool is not None
        assert tool.name == 'read_python_docs'
        assert 'Python documentation' in tool.description
    
    @patch('app.agent.tools.web.web_tools.settings')
    def test_create_generic_url_tool(self, mock_settings):
        """Test creation of generic URL tool."""
        provider = WebTools()
        provider._generic_config = {
            'enabled': True,
            'description': 'Read any whitelisted URL',
            'allowed_domains': ['example.com']
        }
        
        tool = provider._create_generic_url_tool()
        
        assert tool is not None
        assert tool.name == 'read_web_url'


class TestStaticUrlReading:
    """Test static URL reading functionality."""
    
    @pytest.mark.asyncio
    async def test_read_static_url_success(self):
        """Test successful static URL reading."""
        provider = WebTools()
        
        # Mock chunker
        mock_chunker = Mock()
        mock_documents = [
            Document(
                page_content="Python is a programming language.",
                metadata={'url': 'https://docs.python.org', 'title': 'Python Docs'}
            ),
            Document(
                page_content="It supports multiple programming paradigms.",
                metadata={'url': 'https://docs.python.org', 'title': 'Python Docs'}
            )
        ]
        mock_chunker.fetch_and_chunk = AsyncMock(return_value=mock_documents)
        provider._chunker = mock_chunker
        
        result = await provider._read_static_url(
            "https://docs.python.org",
            "programming",
            max_content_length=50000
        )
        
        # Parse JSON response
        response = json.loads(result)
        
        assert response['status'] == 'success'
        assert 'Python' in str(response)
        assert response['url'] == 'https://docs.python.org'
    
    @pytest.mark.asyncio
    async def test_read_static_url_with_query(self):
        """Test static URL reading with search query."""
        provider = WebTools()
        
        mock_chunker = Mock()
        mock_documents = [
            Document(
                page_content="Python supports async programming.",
                metadata={'url': 'https://docs.python.org', 'title': 'Python Docs'}
            ),
            Document(
                page_content="JavaScript is another language.",
                metadata={'url': 'https://docs.python.org', 'title': 'Python Docs'}
            )
        ]
        mock_chunker.fetch_and_chunk = AsyncMock(return_value=mock_documents)
        provider._chunker = mock_chunker
        
        result = await provider._read_static_url(
            "https://docs.python.org",
            "async",
            max_content_length=50000
        )
        
        response = json.loads(result)
        
        # Should find the chunk containing "async"
        assert response['status'] == 'success'
        assert response['matching_chunks'] >= 1
    
    @pytest.mark.asyncio
    async def test_read_static_url_no_content(self):
        """Test static URL reading when no content is returned."""
        provider = WebTools()
        
        mock_chunker = Mock()
        mock_chunker.fetch_and_chunk = AsyncMock(return_value=[])
        provider._chunker = mock_chunker
        
        result = await provider._read_static_url(
            "https://docs.python.org",
            "test",
            max_content_length=50000
        )
        
        response = json.loads(result)
        
        assert response['status'] == 'error'
        assert 'No content retrieved' in response['message']
    
    @pytest.mark.asyncio
    async def test_read_static_url_fetch_error(self):
        """Test error handling in static URL reading."""
        provider = WebTools()
        
        mock_chunker = Mock()
        mock_chunker.fetch_and_chunk = AsyncMock(side_effect=Exception("Network error"))
        provider._chunker = mock_chunker
        
        result = await provider._read_static_url(
            "https://docs.python.org",
            "test",
            max_content_length=50000
        )
        
        response = json.loads(result)
        
        assert response['status'] == 'error'
        assert 'Failed to fetch content' in response['message']


class TestDynamicUrlReading:
    """Test dynamic URL reading functionality."""
    
    @pytest.mark.asyncio
    async def test_read_dynamic_url_success(self):
        """Test successful dynamic URL reading."""
        provider = WebTools()
        provider._generic_config = {
            'enabled': True,
            'allowed_domains': ['example.com'],
            'max_content_length': 50000
        }
        
        mock_chunker = Mock()
        mock_documents = [
            Document(
                page_content="Example content here.",
                metadata={'url': 'https://example.com', 'title': 'Example'}
            )
        ]
        mock_chunker.fetch_and_chunk = AsyncMock(return_value=mock_documents)
        provider._chunker = mock_chunker
        
        result = await provider._read_dynamic_url(
            "https://example.com/page",
            "content"
        )
        
        response = json.loads(result)
        
        assert response['status'] == 'success'
        assert 'Example content' in str(response)
    
    @pytest.mark.asyncio
    async def test_read_dynamic_url_domain_not_whitelisted(self):
        """Test rejection of non-whitelisted domain."""
        provider = WebTools()
        provider._generic_config = {
            'enabled': True,
            'allowed_domains': ['example.com'],
            'max_content_length': 50000
        }
        
        result = await provider._read_dynamic_url(
            "https://malicious.com/page",
            "test"
        )
        
        response = json.loads(result)
        
        assert response['status'] == 'error'
        assert 'not whitelisted' in response['message']
        assert 'malicious.com' in response['message']
    
    @pytest.mark.asyncio
    async def test_read_dynamic_url_empty_url(self):
        """Test error handling for empty URL."""
        provider = WebTools()
        provider._generic_config = {'enabled': True, 'allowed_domains': []}
        
        result = await provider._read_dynamic_url("", "test")
        
        response = json.loads(result)
        
        assert response['status'] == 'error'
        assert 'URL is required' in response['message']
    
    @pytest.mark.asyncio
    async def test_read_dynamic_url_wildcard_domain(self):
        """Test wildcard domain matching."""
        provider = WebTools()
        provider._generic_config = {
            'enabled': True,
            'allowed_domains': ['*.example.com'],
            'max_content_length': 50000
        }
        
        mock_chunker = Mock()
        mock_documents = [
            Document(
                page_content="Subdomain content",
                metadata={'url': 'https://api.example.com', 'title': 'API'}
            )
        ]
        mock_chunker.fetch_and_chunk = AsyncMock(return_value=mock_documents)
        provider._chunker = mock_chunker
        
        result = await provider._read_dynamic_url(
            "https://api.example.com/docs",
            "content"
        )
        
        response = json.loads(result)
        
        assert response['status'] == 'success'


class TestContentSearching:
    """Test content searching functionality."""
    
    def test_search_chunks_with_matches(self):
        """Test searching chunks for matching content."""
        provider = WebTools()
        
        documents = [
            Document(page_content="Python is great", metadata={}),
            Document(page_content="JavaScript is popular", metadata={}),
            Document(page_content="Python supports async", metadata={}),
        ]
        
        results = provider._search_chunks(documents, "Python")
        
        assert len(results) == 2
        assert all("Python" in doc.page_content for doc in results)
    
    def test_search_chunks_no_matches(self):
        """Test searching with no matching content."""
        provider = WebTools()
        
        documents = [
            Document(page_content="Python is great", metadata={}),
            Document(page_content="JavaScript is popular", metadata={}),
        ]
        
        results = provider._search_chunks(documents, "Ruby")
        
        assert len(results) == 0
    
    def test_search_chunks_case_insensitive(self):
        """Test case-insensitive searching."""
        provider = WebTools()
        
        documents = [
            Document(page_content="Python is GREAT", metadata={}),
        ]
        
        results = provider._search_chunks(documents, "python")
        
        assert len(results) == 1
    
    def test_search_chunks_limit(self):
        """Test that search results are limited."""
        provider = WebTools()
        
        # Create more than 5 matching documents
        documents = [
            Document(page_content=f"Python tutorial {i}", metadata={})
            for i in range(10)
        ]
        
        results = provider._search_chunks(documents, "Python")
        
        # Should be limited to 5
        assert len(results) == 5


class TestResponseFormatting:
    """Test response formatting."""
    
    def test_format_response_with_results(self):
        """Test formatting response with results."""
        provider = WebTools()
        
        relevant_chunks = [
            Document(
                page_content="Python content here",
                metadata={'title': 'Python Docs', 'chunk_index': 0}
            )
        ]
        
        all_documents = relevant_chunks * 3
        
        result = provider._format_response(
            "https://docs.python.org",
            relevant_chunks,
            "Python",
            all_documents
        )
        
        response = json.loads(result)
        
        assert response['status'] == 'success'
        assert response['url'] == 'https://docs.python.org'
        assert response['title'] == 'Python Docs'
        assert response['query'] == 'Python'
        assert response['matching_chunks'] == 1
        assert len(response['sections']) == 1
    
    def test_format_response_no_results(self):
        """Test formatting response with no results."""
        provider = WebTools()
        
        all_documents = [
            Document(page_content="Some content", metadata={'title': 'Test'})
        ]
        
        result = provider._format_response(
            "https://example.com",
            [],  # No relevant chunks
            "query",
            all_documents
        )
        
        response = json.loads(result)
        
        assert response['status'] == 'success'
        assert 'No content found' in response['message']
        assert response['matching_chunks'] == 0
    
    def test_format_response_content_truncation(self):
        """Test that content is truncated in response."""
        provider = WebTools()
        
        # Create content longer than 800 characters
        long_content = "A" * 1000
        
        relevant_chunks = [
            Document(
                page_content=long_content,
                metadata={'title': 'Test', 'chunk_index': 0}
            )
        ]
        
        result = provider._format_response(
            "https://example.com",
            relevant_chunks,
            "test",
            relevant_chunks
        )
        
        response = json.loads(result)
        
        # Content should be truncated to 800 chars
        section_content = response['sections'][0]['content']
        assert len(section_content) == 800


class TestCacheTTL:
    """Test cache TTL configuration."""
    
    @patch('app.agent.tools.web.web_tools.settings')
    def test_get_cache_ttl_from_config(self, mock_settings):
        """Test getting cache TTL from configuration."""
        mock_web_config = Mock()
        mock_web_config.cache_ttl = 7200  # 2 hours
        
        mock_settings.tools.tools.web = mock_web_config
        
        provider = WebTools()
        ttl = provider._get_cache_ttl()
        
        assert ttl == 7200
    
    @patch('app.agent.tools.web.web_tools.settings')
    def test_get_cache_ttl_default(self, mock_settings):
        """Test default cache TTL when config not available."""
        mock_settings.tools.tools.web = None
        
        provider = WebTools()
        ttl = provider._get_cache_ttl()
        
        assert ttl == 3600  # Default 1 hour
