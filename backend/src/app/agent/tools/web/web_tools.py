"""
Web tools for reading and searching web content.

This module provides LangChain tools for accessing external web resources,
enabling agents to read documentation, blogs, and other web content without
requiring vector store embedding.

Features:
- Static URL tools: Pre-configured tools for frequently accessed documentation
- Dynamic URL reader: Generic tool for accessing any whitelisted URL
- Domain whitelisting: Security through allowed domain configuration
- Content caching: Reduces redundant network requests
- Content chunking: Handles large pages efficiently
"""

import json
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from app.agent.tools.base.registry import ToolRegistry
from app.core.utils.web_content_chunker import WebContentChunker
from app.services.cache.cache_factory import CacheFactory
from app.core.utils.logger import get_logger
from app.core.config.framework.settings import settings

logger = get_logger(__name__)


# Pydantic input schemas for tool arguments
class SearchUrlInput(BaseModel):
    """Input schema for searching content within a static URL."""
    query: str = Field(
        description="Search query text to find within the web content. "
                   "Leave empty to retrieve general content from the page."
    )


class DynamicUrlInput(BaseModel):
    """Input schema for reading any whitelisted URL."""
    url: str = Field(
        description="Full URL to read content from (must be in allowed domains list)"
    )
    query: Optional[str] = Field(
        default="",
        description="Optional search query to find specific content within the page"
    )


@ToolRegistry.register("web", "web")
class WebTools:
    """
    Web content reading and search tools for agents.
    
    This tool provider enables agents to access external web resources directly
    without requiring document embedding. It supports both static (pre-configured)
    URLs for frequently accessed documentation and a generic URL reader for
    ad-hoc web access.
    
    Configuration is loaded from application-tools.yaml under the 'web' category.
    
    Security Features:
    - Domain whitelisting to prevent access to unauthorized sites
    - Content length limits to prevent excessive resource usage
    - Caching to minimize network overhead
    
    Example configuration:
        tools:
          web:
            enabled: true
            cache_ttl: 3600
            available_tools:
              documentation:
                read_python_docs:
                  enabled: true
                  url: "https://docs.python.org/3/"
                  description: "Search Python documentation"
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize web tools provider.
        
        Args:
            config: Optional configuration dictionary from tool registry
        """
        self.config = config or {}
        self._chunker = None
        self._static_url_configs = []
        self._generic_config = {}
        
        # Load tool configurations
        self._load_configurations()
        
        logger.info(
            f"WebTools initialized: {len(self._static_url_configs)} static URLs, "
            f"generic tool: {bool(self._generic_config)}"
        )
    
    @property
    def chunker(self) -> WebContentChunker:
        """
        Lazy-load web content chunker with cache.
        
        Returns:
            WebContentChunker instance with caching enabled
        """
        if self._chunker is None:
            try:
                # Get cache TTL from configuration
                cache_ttl = self._get_cache_ttl()
                
                # Get chunking configuration (with defaults)
                chunk_size, chunk_overlap = self._get_chunking_config()
                
                # Create cache provider for web content
                cache = CacheFactory.create_cache(
                    namespace="web_content",
                    default_ttl=cache_ttl
                )
                
                # Initialize chunker with cache
                self._chunker = WebContentChunker(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    cache_provider=cache,
                    cache_ttl=cache_ttl
                )
                
                logger.debug(
                    f"WebContentChunker initialized with cache "
                    f"(chunk_size: {chunk_size}, chunk_overlap: {chunk_overlap}, TTL: {cache_ttl}s)"
                )
                
            except Exception as e:
                logger.warning(f"Failed to initialize cache, using chunker without cache: {e}")
                self._chunker = WebContentChunker()
        
        return self._chunker
    
    def get_tools(self) -> List[StructuredTool]:
        """
        Return list of web reading tools for agent use.
        
        Creates tools for:
        1. Each configured static URL (pre-configured documentation sites)
        2. Generic URL reader (for dynamic URL access with whitelist)
        
        Returns:
            List of LangChain StructuredTool objects
        """
        tools = []
        
        # Create static URL tools
        for url_config in self._static_url_configs:
            tool = self._create_static_url_tool(url_config)
            if tool:
                tools.append(tool)
        
        # Create generic URL reader tool if configured
        if self._generic_config.get('enabled', False):
            generic_tool = self._create_generic_url_tool()
            if generic_tool:
                tools.append(generic_tool)
        
        logger.info(f"Created {len(tools)} web tools")
        return tools
    
    def _create_static_url_tool(self, config: Dict[str, Any]) -> Optional[StructuredTool]:
        """
        Create a tool for a specific static URL.
        
        Args:
            config: Configuration dictionary for the static URL tool
            
        Returns:
            StructuredTool instance or None if creation fails
        """
        try:
            tool_name = config['name']
            url = config['url']
            description = config['description']
            
            # Create the tool function with closure over url
            async def search_url(query: str) -> str:
                return await self._read_static_url(url, query, config.get('max_content_length'))
            
            tool = StructuredTool(
                name=tool_name,
                description=description,
                func=search_url,
                coroutine=search_url,
                args_schema=SearchUrlInput
            )
            
            logger.debug(f"Created static URL tool: {tool_name} -> {url}")
            return tool
            
        except Exception as e:
            logger.error(f"Failed to create static URL tool: {e}")
            return None
    
    def _create_generic_url_tool(self) -> Optional[StructuredTool]:
        """
        Create a generic URL reader tool with domain whitelisting.
        
        Returns:
            StructuredTool instance or None if creation fails
        """
        try:
            tool = StructuredTool(
                name="read_web_url",
                description=self._generic_config.get(
                    'description',
                    "Read and search content from any whitelisted web URL"
                ),
                func=self._read_dynamic_url,
                coroutine=self._read_dynamic_url,
                args_schema=DynamicUrlInput
            )
            
            logger.debug("Created generic URL reader tool")
            return tool
            
        except Exception as e:
            logger.error(f"Failed to create generic URL tool: {e}")
            return None
    
    async def _read_static_url(
        self,
        url: str,
        query: str,
        max_content_length: Optional[int] = None
    ) -> str:
        """
        Read and search content from a static (pre-configured) URL.
        
        Args:
            url: URL to fetch content from
            query: Search query text
            max_content_length: Optional maximum content length
            
        Returns:
            Formatted response with relevant content or error message
        """
        try:
            logger.info(f"Reading static URL: {url}, query: '{query}'")
            
            # Fetch and chunk content
            documents = await self.chunker.fetch_and_chunk(
                url,
                use_cache=True,
                max_content_length=max_content_length
            )
            
            if not documents:
                return json.dumps({
                    "status": "error",
                    "message": "No content retrieved from URL",
                    "url": url
                })
            
            # Search for relevant chunks if query provided
            if query and query.strip():
                relevant_chunks = self._search_chunks(documents, query)
            else:
                # Return first few chunks if no specific query
                relevant_chunks = documents[:3]
            
            # Format response
            return self._format_response(url, relevant_chunks, query, documents)
            
        except Exception as e:
            logger.error(f"Failed to read static URL {url}: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Failed to fetch content: {str(e)}",
                "url": url
            })
    
    async def _read_dynamic_url(self, url: str, query: str = "") -> str:
        """
        Read and search content from any whitelisted URL.
        
        Args:
            url: Full URL to fetch
            query: Optional search query
            
        Returns:
            Formatted response with content or error message
        """
        try:
            # Validate URL format
            if not url or not url.strip():
                return json.dumps({
                    "status": "error",
                    "message": "URL is required"
                })
            
            url = url.strip()
            
            # Extract domain and check whitelist
            domain = urlparse(url).netloc
            allowed_domains = self._generic_config.get('allowed_domains', [])
            
            if not self._is_domain_allowed(domain, allowed_domains):
                return json.dumps({
                    "status": "error",
                    "message": f"Domain '{domain}' is not whitelisted",
                    "allowed_domains": allowed_domains,
                    "hint": "Contact your administrator to whitelist this domain"
                })
            
            logger.info(f"Reading dynamic URL: {url}, query: '{query}'")
            
            # Get max content length from config
            max_length = self._generic_config.get('max_content_length')
            
            # Fetch and chunk content
            documents = await self.chunker.fetch_and_chunk(
                url,
                use_cache=True,
                max_content_length=max_length
            )
            
            if not documents:
                return json.dumps({
                    "status": "error",
                    "message": "No content retrieved from URL",
                    "url": url
                })
            
            # Search for relevant chunks
            if query and query.strip():
                relevant_chunks = self._search_chunks(documents, query)
            else:
                relevant_chunks = documents[:3]
            
            # Format response
            return self._format_response(url, relevant_chunks, query, documents)
            
        except Exception as e:
            logger.error(f"Failed to read dynamic URL {url}: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Failed to fetch content: {str(e)}",
                "url": url
            })
    
    def _search_chunks(self, documents: List, query: str) -> List:
        """
        Search document chunks for query text.
        
        Performs case-insensitive keyword search across chunks.
        
        Args:
            documents: List of Document objects
            query: Search query string
            
        Returns:
            List of matching Document objects
        """
        query_lower = query.lower()
        relevant = [
            doc for doc in documents
            if query_lower in doc.page_content.lower()
        ]
        
        # Limit to top 5 most relevant chunks
        return relevant[:5]
    
    def _format_response(
        self,
        url: str,
        relevant_chunks: List,
        query: str,
        all_documents: List
    ) -> str:
        """
        Format search results into agent-friendly response.
        
        Args:
            url: Source URL
            relevant_chunks: List of relevant Document chunks
            query: Original search query
            all_documents: All document chunks (for context)
            
        Returns:
            JSON-formatted response string
        """
        if not relevant_chunks:
            return json.dumps({
                "status": "success",
                "message": f"No content found matching '{query}' in the page",
                "url": url,
                "total_chunks": len(all_documents),
                "matching_chunks": 0
            })
        
        # Extract page title from first chunk metadata
        page_title = relevant_chunks[0].metadata.get('title', 'Unknown')
        
        # Build content sections
        content_sections = []
        for idx, chunk in enumerate(relevant_chunks, 1):
            section = {
                "section": idx,
                "content": chunk.page_content[:800],  # Limit to 800 chars per section
                "chunk_index": chunk.metadata.get('chunk_index', 0),
                "relevance": "high" if query and query.lower() in chunk.page_content.lower() else "medium"
            }
            content_sections.append(section)
        
        response = {
            "status": "success",
            "url": url,
            "title": page_title,
            "query": query if query else "general content",
            "total_chunks": len(all_documents),
            "matching_chunks": len(relevant_chunks),
            "sections": content_sections,
            "note": f"Showing top {len(relevant_chunks)} most relevant sections"
        }
        
        return json.dumps(response, indent=2)
    
    def _is_domain_allowed(self, domain: str, allowed_domains: List[str]) -> bool:
        """
        Check if domain is in whitelist.
        
        Supports:
        - Exact matching: "docs.python.org"
        - Wildcard matching: "*.company.com" matches "api.company.com" but not "company.com"
        
        Args:
            domain: Domain to check
            allowed_domains: List of allowed domain patterns
            
        Returns:
            True if domain is allowed, False otherwise
        """
        for allowed_domain in allowed_domains:
            if allowed_domain.startswith("*."):
                # Wildcard match: *.company.com matches api.company.com
                # but not company.com (must have subdomain)
                suffix = allowed_domain[2:]
                if domain.endswith(suffix) and domain != suffix:
                    return True
            elif domain == allowed_domain:
                # Exact match
                return True
        
        return False
    
    def _load_configurations(self) -> None:
        """
        Load tool configurations from settings.
        
        Parses the application-tools.yaml configuration to extract:
        - Static URL configurations
        - Generic tool configuration
        - Cache settings
        """
        try:
            if not hasattr(settings, 'tools') or not hasattr(settings.tools, 'tools'):
                logger.warning("No tools configuration found")
                return
            
            web_config = getattr(settings.tools.tools, 'web', None)
            if not web_config:
                logger.warning("No web tools configuration found")
                return
            
            # Load available tools configuration
            available_tools = getattr(web_config, 'available_tools', None)
            if not available_tools:
                logger.warning("No available_tools configuration found")
                return
            
            # Load static URL tools from 'documentation' section
            documentation = getattr(available_tools, 'documentation', None)
            if documentation:
                self._static_url_configs = self._parse_static_urls(documentation)
            
            # Load generic tool configuration
            generic = getattr(available_tools, 'generic', None)
            if generic:
                self._generic_config = self._parse_generic_config(generic)
            
        except Exception as e:
            logger.error(f"Failed to load web tools configuration: {e}")
    
    def _parse_static_urls(self, documentation_config) -> List[Dict[str, Any]]:
        """
        Parse static URL configurations from documentation section.
        
        Args:
            documentation_config: Documentation configuration object
            
        Returns:
            List of static URL configuration dictionaries
        """
        static_urls = []
        
        try:
            # Iterate through all attributes (tool names)
            for tool_name in dir(documentation_config):
                if tool_name.startswith('_'):
                    continue
                
                tool_config = getattr(documentation_config, tool_name)
                
                # Check if tool is enabled
                if not getattr(tool_config, 'enabled', False):
                    continue
                
                # Extract configuration
                url = getattr(tool_config, 'url', None)
                description = getattr(tool_config, 'description', '')
                max_content_length = getattr(tool_config, 'max_content_length', None)
                
                if url:
                    static_urls.append({
                        'name': tool_name,
                        'url': url,
                        'description': description,
                        'max_content_length': max_content_length
                    })
                    logger.debug(f"Loaded static URL config: {tool_name} -> {url}")
        
        except Exception as e:
            logger.error(f"Failed to parse static URLs: {e}")
        
        return static_urls
    
    def _parse_generic_config(self, generic_config) -> Dict[str, Any]:
        """
        Parse generic tool configuration.
        
        Args:
            generic_config: Generic tool configuration object
            
        Returns:
            Dictionary with generic tool configuration
        """
        try:
            read_web_url = getattr(generic_config, 'read_web_url', None)
            if not read_web_url:
                return {}
            
            enabled = getattr(read_web_url, 'enabled', False)
            if not enabled:
                return {}
            
            description = getattr(read_web_url, 'description', '')
            allowed_domains = list(getattr(read_web_url, 'allowed_domains', []))
            max_content_length = getattr(read_web_url, 'max_content_length', None)
            
            config = {
                'enabled': enabled,
                'description': description,
                'allowed_domains': allowed_domains,
                'max_content_length': max_content_length
            }
            
            logger.debug(
                f"Loaded generic config: {len(allowed_domains)} allowed domains, "
                f"max_length: {max_content_length}"
            )
            
            return config
        
        except Exception as e:
            logger.error(f"Failed to parse generic config: {e}")
            return {}
    
    def _get_cache_ttl(self) -> int:
        """
        Get cache TTL from configuration.
        
        Returns:
            Cache TTL in seconds (default: 3600 = 1 hour)
        """
        try:
            if hasattr(settings, 'tools') and hasattr(settings.tools, 'tools'):
                web_config = getattr(settings.tools.tools, 'web', None)
                if web_config:
                    return getattr(web_config, 'cache_ttl', 3600)
        
        except Exception:
            pass
        
        return 3600  # Default: 1 hour

    def _get_chunking_config(self) -> tuple[int, int]:
        """
        Get chunking configuration from settings.
        
        Returns:
            Tuple of (chunk_size, chunk_overlap) with defaults (1000, 200)
        """
        try:
            if hasattr(settings, 'tools') and hasattr(settings.tools, 'tools'):
                web_config = getattr(settings.tools.tools, 'web', None)
                if web_config and hasattr(web_config, 'chunking'):
                    chunking_config = web_config.chunking
                    chunk_size = getattr(chunking_config, 'chunk_size', 1000)
                    chunk_overlap = getattr(chunking_config, 'chunk_overlap', 200)
                    return (chunk_size, chunk_overlap)
        
        except Exception:
            pass
        
        return (1000, 200)  # Default values
