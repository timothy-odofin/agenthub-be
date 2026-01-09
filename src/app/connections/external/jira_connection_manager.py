"""
Jira connection manager implementation.

Provides connection management for Jira (Atlassian) with proper
configuration validation and health checking.

Requirements:
    - atlassian-python-api: pip install atlassian-python-api
    - requests: pip install requests
"""

from typing import Any, Optional, Dict, List
import requests
from atlassian import Jira

from app.connections.base import BaseConnectionManager, ConnectionRegistry, ConnectionType
from app.core.utils.logger import get_logger
from app.core.resilience import retry, circuit_breaker, RetryConfig, CircuitBreakerConfig, RetryStrategy

logger = get_logger(__name__)

# Resilience configurations for Jira API
JIRA_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=10.0,
    strategy=RetryStrategy.EXPONENTIAL,
    jitter=True
)

JIRA_CIRCUIT_CONFIG = CircuitBreakerConfig(
    name="jira_api",
    failure_threshold=5,
    failure_window=60.0,
    recovery_timeout=30.0,
    success_threshold=2
)


@ConnectionRegistry.register(ConnectionType.JIRA)
class JiraConnectionManager(BaseConnectionManager):
    """Jira (Atlassian) connection manager implementation."""
    
    def __init__(self):
        super().__init__()
        self._jira_client: Optional[Jira] = None
        self._session: Optional[requests.Session] = None
    
    def get_connection_name(self) -> str:
        """Return the configuration name for Jira."""
        return ConnectionType.JIRA.value
    
    def validate_config(self) -> None:
        """Validate Jira configuration."""
        required_fields = ['base_url', 'username', 'api_token']
        
        for field in required_fields:
            if not self.config.get(field):
                raise ValueError(f"Jira connection requires '{field}' in configuration")
        
        # Validate URL format
        base_url = self.config.get('base_url')
        if not base_url.startswith(('http://', 'https://')):
            raise ValueError(f"Jira base_url must start with http:// or https://, got: {base_url}")
        
        logger.info("Jira connection configuration validated successfully")
    
    def connect(self) -> Jira:
        """Establish Jira connection."""
        if self._jira_client:
            # Test existing connection
            if self._test_connection():
                return self._jira_client
            else:
                # Connection might be stale, recreate
                self.disconnect()
        
        try:
            # Create requests session for connection pooling
            self._session = requests.Session()
            
            # Create Jira client
            self._jira_client = Jira(
                url=self.config['base_url'],
                username=self.config['username'],
                password=self.config['api_token'],  # API token used as password
                session=self._session,
                verify_ssl=self.config.get('verify_ssl', True),
                timeout=self.config.get('timeout', 30)
            )
            
            # Test connection by getting server info
            server_info = self._jira_client.get_server_info()
            logger.info(f"Connected to Jira server: {server_info.get('serverTitle', 'Unknown')} "
                       f"version {server_info.get('version', 'Unknown')}")
            
            self._connection = self._jira_client
            self._is_connected = True
            
            logger.info(f"Jira connection established to {self.config['base_url']}")
            return self._jira_client
            
        except Exception as e:
            self._connection = None
            self._is_connected = False
            logger.error(f"Failed to connect to Jira: {e}")
            raise ConnectionError(f"Jira connection failed: {e}")
    
    def disconnect(self) -> None:
        """Close Jira connection."""
        try:
            if self._session:
                self._session.close()
                logger.info("Jira session closed")
        except Exception as e:
            logger.warning(f"Error closing Jira session: {e}")
        finally:
            self._jira_client = None
            self._session = None
            self._connection = None
            self._is_connected = False
    
    def is_healthy(self) -> bool:
        """Check if Jira connection is healthy."""
        if not self._jira_client:
            return False
        
        try:
            # Quick test - just check if we can reach the server
            self._jira_client.server_info()
            return True
        except Exception:
            return False
    
    def _test_connection(self) -> bool:
        """Test Jira connection asynchronously."""
        if not self._jira_client:
            return False
        
        try:
            # Test with a simple API call
            self._jira_client.get_server_info()
            return True
        except Exception:
            return False
    
    # Jira-specific convenience methods
    
    @retry(JIRA_RETRY_CONFIG)
    @circuit_breaker(JIRA_CIRCUIT_CONFIG)
    def get_server_info(self) -> Dict:
        """Get Jira server information."""
        self.ensure_connected()
        
        try:
            return self._jira_client.get_server_info()
        except Exception as e:
            logger.error(f"Failed to get server info: {e}")
            raise
    
    @retry(JIRA_RETRY_CONFIG)
    @circuit_breaker(JIRA_CIRCUIT_CONFIG)
    def search_issues(self, jql: str, limit: int = 50, fields: Optional[List[str]] = None) -> Dict:
        """
        Search for issues using JQL.
        
        Args:
            jql: JQL (Jira Query Language) string
            limit: Maximum number of results
            fields: List of fields to return
            
        Returns:
            Search results
        """
        self.ensure_connected()
        
        try:
            # Use API v3 endpoint instead of deprecated v2
            params = {
                'jql': jql,
                'maxResults': limit,
                'startAt': 0
            }
            
            if fields:
                params['fields'] = ','.join(fields) if isinstance(fields, list) else fields
                
            # Use the get method with API v3 endpoint
            return self._jira_client.get('/rest/api/3/search/jql', params=params)
        except Exception as e:
            logger.error(f"Failed to search issues with JQL '{jql}': {e}")
            raise
    
    @retry(JIRA_RETRY_CONFIG)
    @circuit_breaker(JIRA_CIRCUIT_CONFIG)
    def get_issue(self, issue_key: str, fields: Optional[str] = None, expand: Optional[str] = None) -> Dict:
        """
        Get a specific issue by key.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            fields: Comma-separated list of fields to return
            expand: Comma-separated list of fields to expand
            
        Returns:
            Issue data
        """
        self.ensure_connected()
        
        try:
            return self._jira_client.issue(issue_key, fields=fields, expand=expand)
        except Exception as e:
            logger.error(f"Failed to get issue {issue_key}: {e}")
            raise
    
    @retry(JIRA_RETRY_CONFIG)
    @circuit_breaker(JIRA_CIRCUIT_CONFIG)
    def create_issue(self, project_key: str, summary: str, description: str, 
                          issue_type: str = "Task", **additional_fields) -> Dict:
        """
        Create a new issue.
        
        Args:
            project_key: Project key
            summary: Issue summary
            description: Issue description  
            issue_type: Issue type (Task, Bug, Story, etc.)
            **additional_fields: Additional issue fields
            
        Returns:
            Created issue data
        """
        self.ensure_connected()
        
        try:
            issue_data = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": issue_type},
                    **additional_fields
                }
            }
            
            result = self._jira_client.issue_create(issue_data)
            logger.info(f"Created Jira issue: {result.get('key')}")
            return result
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            raise
    
    @retry(JIRA_RETRY_CONFIG)
    @circuit_breaker(JIRA_CIRCUIT_CONFIG)
    def get_projects(self) -> List[Dict]:
        """Get all accessible projects."""
        self.ensure_connected()
        
        try:
            return self._jira_client.projects()
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            raise
    
    @retry(JIRA_RETRY_CONFIG)
    @circuit_breaker(JIRA_CIRCUIT_CONFIG)
    def get_issue_types(self) -> List[Dict]:
        """Get all issue types."""
        self.ensure_connected()
        
        try:
            return self._jira_client.issue_types()
        except Exception as e:
            logger.error(f"Failed to get issue types: {e}")
            raise
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get Jira connection information."""
        base_info = super().get_connection_info()
        
        if self._jira_client:
            try:
                server_info = self._jira_client.server_info()
                base_info.update({
                    'base_url': self.config.get('base_url'),
                    'username': self.config.get('username'),
                    'server_title': server_info.get('serverTitle'),
                    'server_version': server_info.get('version'),
                    'build_number': server_info.get('buildNumber'),
                })
            except Exception as e:
                base_info['connection_error'] = str(e)
        
        return base_info
