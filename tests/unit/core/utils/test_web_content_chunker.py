"""
Unit tests for WebContentChunker utility.

Tests the web content fetching, chunking, and caching functionality.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from langchain.schema import Document

from app.core.utils.web_content_chunker import WebContentChunker
from app.services.cache.base_cache_provider import BaseCacheProvider


class TestWebContentChunkerInitialization:
    """Test WebContentChunker initialization."""
    
    def test_initialization_default_parameters(self):
        """Test initialization with default parameters."""
        chunker = WebContentChunker()
        
        assert chunker.chunk_size == 1000
        assert chunker.chunk_overlap == 200
        assert chunker.cache_provider is None
        assert chunker.cache_ttl == 3600
        assert chunker.text_splitter is not None
    
    def test_initialization_custom_parameters(self):
        """Test initialization with custom parameters."""
        mock_cache = Mock(spec=BaseCacheProvider)
        
        chunker = WebContentChunker(
            chunk_size=500,
            chunk_overlap=100,
            cache_provider=mock_cache,
            cache_ttl=1800
        )
        
        assert chunker.chunk_size == 500
        assert chunker.chunk_overlap == 100
        assert chunker.cache_provider == mock_cache
        assert chunker.cache_ttl == 1800
    
    def test_text_splitter_configuration(self):
        """Test that text splitter is configured correctly."""
        chunker = WebContentChunker(chunk_size=500, chunk_overlap=50)
        
        assert chunker.text_splitter._chunk_size == 500
        assert chunker.text_splitter._chunk_overlap == 50


class TestWebContentChunkerFetching:
    """Test web content fetching functionality."""
    
    @pytest.mark.asyncio
    async def test_fetch_and_chunk_simple_content(self):
        """Test fetching and chunking simple content."""
        chunker = WebContentChunker()
        
        # Mock the fetch method
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Test Content</h1>
                <p>This is a test paragraph with some content.</p>
            </body>
        </html>
        """
        
        with patch.object(chunker, '_fetch_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = html_content
            
            documents = await chunker.fetch_and_chunk("https://example.com")
            
            assert len(documents) > 0
            assert all(isinstance(doc, Document) for doc in documents)
            assert all('url' in doc.metadata for doc in documents)
            assert all('title' in doc.metadata for doc in documents)
            assert all('chunk_index' in doc.metadata for doc in documents)
            mock_fetch.assert_called_once_with("https://example.com")
    
    @pytest.mark.asyncio
    async def test_fetch_and_chunk_large_content(self):
        """Test chunking of large content."""
        chunker = WebContentChunker(chunk_size=100, chunk_overlap=20)
        
        # Create large content that will require multiple chunks
        large_content = "<html><body><p>" + ("Test content. " * 200) + "</p></body></html>"
        
        with patch.object(chunker, '_fetch_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = large_content
            
            documents = await chunker.fetch_and_chunk("https://example.com")
            
            # Should be split into multiple chunks
            assert len(documents) > 1
            
            # Verify chunk metadata
            for idx, doc in enumerate(documents):
                assert doc.metadata['chunk_index'] == idx
                assert doc.metadata['total_chunks'] == len(documents)
    
    @pytest.mark.asyncio
    async def test_fetch_and_chunk_invalid_url(self):
        """Test error handling for invalid URL."""
        chunker = WebContentChunker()
        
        with pytest.raises(ValueError, match="Invalid URL format"):
            await chunker.fetch_and_chunk("not-a-url")
    
    @pytest.mark.asyncio
    async def test_fetch_and_chunk_empty_url(self):
        """Test error handling for empty URL."""
        chunker = WebContentChunker()
        
        with pytest.raises(ValueError, match="URL cannot be empty"):
            await chunker.fetch_and_chunk("")
    
    @pytest.mark.asyncio
    async def test_fetch_and_chunk_with_max_content_length(self):
        """Test content truncation with max_content_length."""
        chunker = WebContentChunker()
        
        large_content = "<html><body><p>" + ("A" * 10000) + "</p></body></html>"
        
        with patch.object(chunker, '_fetch_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = large_content
            
            documents = await chunker.fetch_and_chunk(
                "https://example.com",
                max_content_length=500
            )
            
            # Content should be truncated
            total_content = ''.join(doc.page_content for doc in documents)
            assert len(total_content) <= 500


class TestWebContentChunkerCaching:
    """Test caching functionality."""
    
    @pytest.mark.asyncio
    async def test_fetch_with_cache_miss(self):
        """Test fetching when cache misses."""
        mock_cache = Mock(spec=BaseCacheProvider)
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)
        
        chunker = WebContentChunker(cache_provider=mock_cache)
        
        html_content = "<html><body><p>Test content</p></body></html>"
        
        with patch.object(chunker, '_fetch_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = html_content
            
            documents = await chunker.fetch_and_chunk("https://example.com")
            
            # Cache get should be called
            mock_cache.get.assert_called_once()
            
            # Content should be fetched
            mock_fetch.assert_called_once()
            
            # Cache set should be called
            mock_cache.set.assert_called_once()
            
            assert len(documents) > 0
    
    @pytest.mark.asyncio
    async def test_fetch_with_cache_hit(self):
        """Test fetching when cache hits."""
        mock_cache = Mock(spec=BaseCacheProvider)
        
        # Simulate cached documents
        cached_data = [
            {
                'page_content': 'Cached content',
                'metadata': {
                    'url': 'https://example.com',
                    'title': 'Test',
                    'chunk_index': 0
                }
            }
        ]
        mock_cache.get = AsyncMock(return_value=cached_data)
        
        chunker = WebContentChunker(cache_provider=mock_cache)
        
        with patch.object(chunker, '_fetch_content', new_callable=AsyncMock) as mock_fetch:
            documents = await chunker.fetch_and_chunk("https://example.com")
            
            # Cache get should be called
            mock_cache.get.assert_called_once()
            
            # Content should NOT be fetched (cache hit)
            mock_fetch.assert_not_called()
            
            # Should return cached documents
            assert len(documents) == 1
            assert documents[0].page_content == 'Cached content'
    
    @pytest.mark.asyncio
    async def test_fetch_without_cache(self):
        """Test fetching without cache provider."""
        chunker = WebContentChunker()  # No cache provider
        
        html_content = "<html><body><p>Test content</p></body></html>"
        
        with patch.object(chunker, '_fetch_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = html_content
            
            documents = await chunker.fetch_and_chunk("https://example.com")
            
            # Content should be fetched
            mock_fetch.assert_called_once()
            
            assert len(documents) > 0
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation."""
        chunker = WebContentChunker()
        
        key1 = chunker._generate_cache_key("https://example.com")
        key2 = chunker._generate_cache_key("https://example.com")
        key3 = chunker._generate_cache_key("https://different.com")
        
        # Same URL should generate same key
        assert key1 == key2
        
        # Different URLs should generate different keys
        assert key1 != key3
        
        # Key should have expected format
        assert key1.startswith("web_url_")
        assert len(key1) == 24  # web_url_ + 16 char hash


class TestHTMLCleaning:
    """Test HTML cleaning functionality."""
    
    def test_clean_html_simple(self):
        """Test cleaning simple HTML."""
        chunker = WebContentChunker()
        
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Header</h1>
                <p>Paragraph content</p>
            </body>
        </html>
        """
        
        cleaned_text, title = chunker._clean_html(html)
        
        assert "Test Page" == title
        assert "Header" in cleaned_text
        assert "Paragraph content" in cleaned_text
    
    def test_clean_html_remove_scripts(self):
        """Test removal of script tags."""
        chunker = WebContentChunker()
        
        html = """
        <html>
            <body>
                <p>Visible content</p>
                <script>alert('hidden');</script>
                <style>.hidden { display: none; }</style>
            </body>
        </html>
        """
        
        cleaned_text, _ = chunker._clean_html(html)
        
        assert "Visible content" in cleaned_text
        assert "alert" not in cleaned_text
        assert ".hidden" not in cleaned_text
    
    def test_clean_html_remove_navigation(self):
        """Test removal of navigation elements."""
        chunker = WebContentChunker()
        
        html = """
        <html>
            <body>
                <nav>Navigation menu</nav>
                <header>Site header</header>
                <main>Main content</main>
                <footer>Footer content</footer>
            </body>
        </html>
        """
        
        cleaned_text, _ = chunker._clean_html(html)
        
        assert "Main content" in cleaned_text
        assert "Navigation menu" not in cleaned_text
        assert "Site header" not in cleaned_text
        assert "Footer content" not in cleaned_text
    
    def test_clean_html_whitespace_normalization(self):
        """Test whitespace normalization."""
        chunker = WebContentChunker()
        
        html = """
        <html>
            <body>
                <p>Line 1</p>
                
                
                <p>Line 2</p>
            </body>
        </html>
        """
        
        cleaned_text, _ = chunker._clean_html(html)
        
        # Should not have excessive blank lines
        assert "\n\n\n" not in cleaned_text


class TestDocumentMetadata:
    """Test document metadata generation."""
    
    @pytest.mark.asyncio
    async def test_metadata_includes_required_fields(self):
        """Test that metadata includes all required fields."""
        chunker = WebContentChunker()
        
        html_content = "<html><body><p>Test</p></body></html>"
        
        with patch.object(chunker, '_fetch_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = html_content
            
            documents = await chunker.fetch_and_chunk("https://example.com/test")
            
            for doc in documents:
                assert 'source' in doc.metadata
                assert 'url' in doc.metadata
                assert 'title' in doc.metadata
                assert 'fetch_time' in doc.metadata
                assert 'content_length' in doc.metadata
                assert 'chunk_index' in doc.metadata
                assert 'total_chunks' in doc.metadata
                assert 'chunk_size' in doc.metadata
    
    @pytest.mark.asyncio
    async def test_metadata_url_accuracy(self):
        """Test that URL in metadata matches input."""
        chunker = WebContentChunker()
        
        test_url = "https://example.com/page"
        html_content = "<html><body><p>Test</p></body></html>"
        
        with patch.object(chunker, '_fetch_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = html_content
            
            documents = await chunker.fetch_and_chunk(test_url)
            
            for doc in documents:
                assert doc.metadata['url'] == test_url
                assert doc.metadata['source'] == test_url


class TestErrorHandling:
    """Test error handling."""
    
    @pytest.mark.asyncio
    async def test_fetch_failure_handling(self):
        """Test handling of fetch failures."""
        chunker = WebContentChunker()
        
        with patch.object(chunker, '_fetch_content', new_callable=AsyncMock) as mock_fetch:
            # Mock raises exception with our expected format
            mock_fetch.side_effect = Exception("Failed to fetch URL content: Network error")
            
            with pytest.raises(Exception, match="Failed to fetch URL content"):
                await chunker.fetch_and_chunk("https://example.com")
    
    @pytest.mark.asyncio
    async def test_cache_failure_graceful_degradation(self):
        """Test that cache failures don't break functionality."""
        mock_cache = Mock(spec=BaseCacheProvider)
        mock_cache.get = AsyncMock(side_effect=Exception("Cache error"))
        
        chunker = WebContentChunker(cache_provider=mock_cache)
        
        html_content = "<html><body><p>Test</p></body></html>"
        
        with patch.object(chunker, '_fetch_content', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = html_content
            
            # Should still work despite cache failure
            documents = await chunker.fetch_and_chunk("https://example.com")
            
            assert len(documents) > 0
