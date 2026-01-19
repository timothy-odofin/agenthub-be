"""
Web content chunking utility for fetching and processing web pages.

This module provides utilities for fetching web content, cleaning HTML,
and chunking text into manageable pieces for LLM consumption. It supports
caching to minimize redundant network requests and follows the same chunking
patterns as the document ingestion system.

Usage:
    >>> from app.core.utils.web_content_chunker import WebContentChunker
    >>> from app.services.cache.cache_factory import CacheFactory
    >>> 
    >>> # With caching
    >>> cache = CacheFactory.create_cache(namespace="web_content", default_ttl=3600)
    >>> chunker = WebContentChunker(cache_provider=cache)
    >>> documents = await chunker.fetch_and_chunk("https://docs.python.org/3/")
    >>> 
    >>> # Without caching
    >>> chunker = WebContentChunker()
    >>> documents = await chunker.fetch_and_chunk("https://example.com")
"""

import asyncio
import hashlib
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

from langchain.schema import Document
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup

from app.services.cache.base_cache_provider import BaseCacheProvider
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class WebContentChunker:
    """
    Utility for fetching and chunking web content into LangChain Documents.
    
    This class handles:
    - Asynchronous web content fetching
    - HTML cleaning and text extraction
    - Content chunking with configurable parameters
    - Optional caching to reduce network overhead
    
    Attributes:
        chunk_size: Maximum size of each text chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        cache_provider: Optional cache provider for storing fetched content
        cache_ttl: Time-to-live for cached content in seconds
        text_splitter: Text splitter instance for chunking
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        cache_provider: Optional[BaseCacheProvider] = None,
        cache_ttl: int = 3600
    ):
        """
        Initialize the web content chunker.
        
        Args:
            chunk_size: Maximum characters per chunk (default: 1000)
            chunk_overlap: Overlap between chunks to maintain context (default: 200)
            cache_provider: Optional cache provider for content caching
            cache_ttl: Cache time-to-live in seconds (default: 3600 = 1 hour)
            
        Example:
            >>> from app.services.cache.cache_factory import CacheFactory
            >>> cache = CacheFactory.create_cache(namespace="web_content")
            >>> chunker = WebContentChunker(
            ...     chunk_size=1000,
            ...     chunk_overlap=200,
            ...     cache_provider=cache,
            ...     cache_ttl=3600
            ... )
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.cache_provider = cache_provider
        self.cache_ttl = cache_ttl
        
        # Initialize text splitter with same configuration as ingestion system
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
        logger.debug(
            f"WebContentChunker initialized: chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}, caching={'enabled' if cache_provider else 'disabled'}"
        )
    
    async def fetch_and_chunk(
        self,
        url: str,
        use_cache: bool = True,
        max_content_length: Optional[int] = None
    ) -> List[Document]:
        """
        Fetch web content from URL and chunk it into Documents.
        
        This method:
        1. Checks cache if enabled and use_cache is True
        2. Fetches content from URL if not cached
        3. Cleans HTML and extracts text
        4. Chunks text into manageable pieces
        5. Creates LangChain Documents with metadata
        6. Caches result if cache is enabled
        
        Args:
            url: Full URL to fetch content from
            use_cache: Whether to use cached content if available (default: True)
            max_content_length: Optional maximum content length in characters.
                               Content exceeding this will be truncated.
        
        Returns:
            List of Document objects with chunked content and metadata
            
        Raises:
            ValueError: If URL is invalid or empty
            Exception: If fetching or processing fails
            
        Example:
            >>> documents = await chunker.fetch_and_chunk(
            ...     "https://docs.python.org/3/library/asyncio.html"
            ... )
            >>> print(f"Fetched {len(documents)} chunks")
            >>> print(documents[0].page_content[:100])
            >>> print(documents[0].metadata)
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
        
        url = url.strip()
        
        # Validate URL format
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL format: {url}")
        
        logger.info(f"Fetching and chunking content from: {url}")
        
        # Check cache first
        if use_cache and self.cache_provider:
            cached_docs = await self._get_from_cache(url)
            if cached_docs:
                logger.info(f"Retrieved {len(cached_docs)} chunks from cache for: {url}")
                return cached_docs
        
        # Fetch content from URL
        raw_content = await self._fetch_content(url)
        
        # Clean HTML and extract text
        cleaned_text, page_title = self._clean_html(raw_content)
        
        # Validate content length
        if max_content_length and len(cleaned_text) > max_content_length:
            logger.warning(
                f"Content length ({len(cleaned_text)}) exceeds maximum ({max_content_length}). "
                "Truncating content."
            )
            cleaned_text = cleaned_text[:max_content_length]
        
        # Create base document with metadata
        base_metadata = {
            "source": url,
            "url": url,
            "title": page_title,
            "fetch_time": datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat(),
            "content_length": len(cleaned_text)
        }
        
        document = Document(
            page_content=cleaned_text,
            metadata=base_metadata
        )
        
        # Chunk the document
        chunks = self.text_splitter.split_documents([document])
        
        # Add chunk-specific metadata
        for idx, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk.page_content)
            })
        
        logger.info(f"Successfully chunked content from {url} into {len(chunks)} pieces")
        
        # Cache the result
        if self.cache_provider:
            await self._save_to_cache(url, chunks)
        
        return chunks
    
    async def _fetch_content(self, url: str) -> str:
        """
        Fetch raw HTML content from URL using async loader.
        
        Args:
            url: URL to fetch
            
        Returns:
            Raw HTML content as string
            
        Raises:
            Exception: If fetching fails with "Failed to fetch URL content" prefix
        """
        try:
            loader = AsyncHtmlLoader([url])
            documents = await loader.aload()
            
            if not documents or len(documents) == 0:
                raise Exception(f"No content retrieved from {url}")
            
            content = documents[0].page_content
            logger.debug(f"Fetched {len(content)} characters from {url}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to fetch content from {url}: {e}")
            # Always raise with consistent error message format
            error_msg = str(e) if "Failed to fetch URL content" in str(e) else f"Failed to fetch URL content: {str(e)}"
            raise Exception(error_msg)
    
    def _clean_html(self, html_content: str) -> tuple[str, str]:
        """
        Clean HTML content and extract plain text.
        
        Removes:
        - Script and style tags
        - Navigation elements
        - Advertisements
        - Excessive whitespace
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Tuple of (cleaned_text, page_title)
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract page title
            page_title = ""
            title_tag = soup.find('title')
            if title_tag:
                page_title = title_tag.get_text().strip()
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
                element.decompose()
            
            # Extract text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            cleaned_text = '\n'.join(lines)
            
            logger.debug(
                f"Cleaned HTML: {len(html_content)} chars -> {len(cleaned_text)} chars, "
                f"title: '{page_title}'"
            )
            
            return cleaned_text, page_title
            
        except Exception as e:
            logger.warning(f"HTML cleaning failed, using raw content: {e}")
            return html_content, "Unknown"
    
    async def _get_from_cache(self, url: str) -> Optional[List[Document]]:
        """
        Retrieve chunked documents from cache.
        
        Args:
            url: URL to retrieve from cache
            
        Returns:
            List of Documents if found in cache, None otherwise
        """
        try:
            cache_key = self._generate_cache_key(url)
            cached_data = await self.cache_provider.get(cache_key, deserialize=True)
            
            if cached_data:
                # Reconstruct Document objects from cached data
                documents = [
                    Document(
                        page_content=doc_data['page_content'],
                        metadata=doc_data['metadata']
                    )
                    for doc_data in cached_data
                ]
                return documents
            
            return None
            
        except Exception as e:
            logger.warning(f"Cache retrieval failed for {url}: {e}")
            return None
    
    async def _save_to_cache(self, url: str, documents: List[Document]) -> bool:
        """
        Save chunked documents to cache.
        
        Args:
            url: URL to use as cache key
            documents: List of Documents to cache
            
        Returns:
            True if caching succeeded, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(url)
            
            # Serialize documents to JSON-compatible format
            serializable_docs = [
                {
                    'page_content': doc.page_content,
                    'metadata': doc.metadata
                }
                for doc in documents
            ]
            
            success = await self.cache_provider.set(
                cache_key,
                serializable_docs,
                ttl=self.cache_ttl
            )
            
            if success:
                logger.debug(f"Cached {len(documents)} chunks for {url} (TTL: {self.cache_ttl}s)")
            
            return success
            
        except Exception as e:
            logger.warning(f"Cache save failed for {url}: {e}")
            return False
    
    def _generate_cache_key(self, url: str) -> str:
        """
        Generate a cache key from URL.
        
        Uses SHA256 hash of URL to create a safe, fixed-length key.
        
        Args:
            url: URL to generate key for
            
        Returns:
            Cache key string
        """
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        return f"web_url_{url_hash}"
    
    def clear_cache_for_url(self, url: str) -> bool:
        """
        Clear cached content for a specific URL.
        
        Args:
            url: URL to clear from cache
            
        Returns:
            True if cache was cleared, False otherwise
        """
        if not self.cache_provider:
            logger.warning("No cache provider configured")
            return False
        
        try:
            cache_key = self._generate_cache_key(url)
            # Note: This is sync, but we're wrapping it for consistency
            return asyncio.run(self.cache_provider.delete(cache_key))
        except Exception as e:
            logger.error(f"Failed to clear cache for {url}: {e}")
            return False
