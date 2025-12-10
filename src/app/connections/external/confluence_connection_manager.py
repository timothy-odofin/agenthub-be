"""
Confluence connection manager implementation.

Provides connection management for Atlassian Confluence with proper
configuration validation and health checking.
"""

from typing import Any, Optional, List, Dict
from atlassian import Confluence
import requests

from app.connections.base import BaseConnectionManager, ConnectionRegistry, ConnectionType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


@ConnectionRegistry.register(ConnectionType.CONFLUENCE)
class ConfluenceConnectionManager(BaseConnectionManager):
    """Confluence connection manager implementation."""
    
    def __init__(self):
        super().__init__()
        self._confluence_client: Optional[Confluence] = None
    
    def get_connection_name(self) -> str:
        """Return the configuration name for Confluence."""
        return ConnectionType.CONFLUENCE.value
    
    def validate_config(self) -> None:
        """Validate Confluence configuration."""
        required_fields = ['base_url', 'username', 'api_token']
        
        for field in required_fields:
            if not self.config.get(field):
                raise ValueError(f"Confluence connection requires '{field}' in configuration")
        
        # Validate base_url format
        base_url = self.config.get('base_url')
        if not base_url.startswith(('http://', 'https://')):
            raise ValueError(f"Confluence base_url must start with http:// or https://, got: {base_url}")
        
        # Validate timeout
        timeout = self.config.get('timeout', 30)
        if not isinstance(timeout, int) or timeout <= 0:
            raise ValueError(f"Confluence timeout must be a positive integer, got: {timeout}")
        
        # Validate page_limit
        page_limit = self.config.get('page_limit', 100)
        if not isinstance(page_limit, int) or page_limit <= 0:
            raise ValueError(f"Confluence page_limit must be a positive integer, got: {page_limit}")
        
        # Validate space_keys if not wildcard
        space_keys = self.config.get('space_keys', ['*'])
        if isinstance(space_keys, str):
            space_keys = [space_keys]
        if not isinstance(space_keys, list):
            raise ValueError("Confluence space_keys must be a string or list of strings")
        
        logger.info("Confluence connection configuration validated successfully")
    
    def connect(self) -> Confluence:
        """Establish Confluence connection."""
        if self._confluence_client:
            # Test existing connection
            if self._test_connection():
                return self._confluence_client
            else:
                # Connection might be stale, recreate
                self.disconnect()
        
        try:
            # Create Confluence client
            self._confluence_client = Confluence(
                url=self.config['base_url'],
                username=self.config['username'],
                password=self.config['api_token'],  # API token acts as password
                timeout=self.config.get('timeout', 30),
                verify_ssl=self.config.get('verify_ssl', True)
            )
            
            # Test connection by getting server info
            server_info = self._confluence_client.get_server_info()
            if not server_info:
                raise ConnectionError("Failed to get Confluence server info")
            
            self._connection = self._confluence_client
            self._is_connected = True
            
            logger.info(f"Confluence connection established to {self.config['base_url']}")
            return self._confluence_client
            
        except Exception as e:
            self._connection = None
            self._is_connected = False
            logger.error(f"Failed to connect to Confluence: {e}")
            raise ConnectionError(f"Confluence connection failed: {e}")
    
    def disconnect(self) -> None:
        """Close Confluence connection."""
        # Confluence client doesn't have explicit close method
        # Just clear the reference
        if self._confluence_client:
            self._confluence_client = None
            logger.info("Confluence connection cleared")
        
        self._connection = None
        self._is_connected = False
    
    def is_healthy(self) -> bool:
        """Check if Confluence connection is healthy."""
        if not self._confluence_client:
            return False
        
        try:
            # Quick sync test
            return bool(self._confluence_client)
        except Exception:
            return False
    
    def _test_connection(self) -> bool:
        """Test Confluence connection synchronously."""
        if not self._confluence_client:
            return False
        
        try:
            # Test with a simple API call
            server_info = self._confluence_client.get_server_info()
            return bool(server_info)
        except Exception:
            return False
    
    # Confluence-specific convenience methods
    
    def get_spaces(self, space_keys: Optional[List[str]] = None) -> List[Dict]:
        """
        Get Confluence spaces.
        
        Args:
            space_keys: List of space keys to fetch, None for configured spaces
            
        Returns:
            List of space information
        """
        self.ensure_connected()
        
        if space_keys is None:
            space_keys = self.config.get('space_keys', ['*'])
        
        if '*' in space_keys:
            # Get all spaces
            return self._confluence_client.get_all_spaces(
                start=0,
                limit=self.config.get('page_limit', 100),
                expand='description.plain,homepage'
            ).get('results', [])
        else:
            # Get specific spaces
            spaces = []
            for space_key in space_keys:
                try:
                    space = self._confluence_client.get_space(
                        space_key, 
                        expand='description.plain,homepage'
                    )
                    if space:
                        spaces.append(space)
                except Exception as e:
                    logger.warning(f"Failed to get space {space_key}: {e}")
            return spaces
    
    def get_pages_in_space(self, space_key: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Get pages in a Confluence space.
        
        Args:
            space_key: The space key
            limit: Maximum number of pages to return
            
        Returns:
            List of page information
        """
        self.ensure_connected()
        
        if limit is None:
            limit = self.config.get('page_limit', 100)
        
        return self._confluence_client.get_all_pages_from_space(
            space=space_key,
            start=0,
            limit=limit,
            expand='body.storage,metadata.labels'
        )
    
    def get_page_content(self, page_id: str) -> Optional[Dict]:
        """
        Get detailed page content.
        
        Args:
            page_id: The page ID
            
        Returns:
            Page content information
        """
        self.ensure_connected()
        
        try:
            return self._confluence_client.get_page_by_id(
                page_id=page_id,
                expand='body.storage,metadata.labels,version'
            )
        except Exception as e:
            logger.error(f"Failed to get page content for {page_id}: {e}")
            return None
    
    def search_content(self, query: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Search Confluence content.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        self.ensure_connected()
        
        if limit is None:
            limit = self.config.get('page_limit', 100)
        
        try:
            return self._confluence_client.cql(
                cql=query,
                start=0,
                limit=limit,
                expand='content.body.storage'
            ).get('results', [])
        except Exception as e:
            logger.error(f"Failed to search content: {e}")
            return []
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get Confluence connection information."""
        base_info = super().get_connection_info()
        
        if self._confluence_client:
            try:
                server_info = self._confluence_client.get_server_info()
                base_info.update({
                    'server_version': server_info.get('version'),
                    'server_title': server_info.get('serverTitle'),
                    'base_url': self.config.get('base_url'),
                    'configured_spaces': self.config.get('space_keys')
                })
            except Exception as e:
                base_info['connection_error'] = str(e)
        
        return base_info