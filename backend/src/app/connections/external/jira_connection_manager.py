"""
Jira connection manager implementation.

Provides connection management for Jira (Atlassian) with proper
configuration validation and health checking.

Requirements:
    - atlassian-python-api: pip install atlassian-python-api
    - requests: pip install requests
"""

from typing import Any, Optional, Dict, List, Union
import requests
from atlassian import Jira

from app.connections.base import BaseConnectionManager, ConnectionRegistry, ConnectionType
from app.core.utils.logger import get_logger
from app.core.resilience import retry, circuit_breaker, RetryConfig, CircuitBreakerConfig, RetryStrategy
from app.core.config import settings

logger = get_logger(__name__)

# Resilience configurations for Jira API - loaded from settings
def _get_jira_retry_config() -> RetryConfig:
    """Get retry configuration from settings."""
    return RetryConfig(
        max_attempts=settings.app.resilience.retry.max_attempts,
        base_delay=settings.app.resilience.retry.base_delay,
        max_delay=settings.app.resilience.retry.max_delay,
        strategy=RetryStrategy[settings.app.resilience.retry.strategy],
        jitter=settings.app.resilience.retry.jitter
    )

def _get_jira_circuit_config() -> CircuitBreakerConfig:
    """Get circuit breaker configuration from settings."""
    return CircuitBreakerConfig(
        name="jira_api",
        failure_threshold=settings.app.resilience.circuit_breaker.failure_threshold,
        failure_window=settings.app.resilience.circuit_breaker.failure_window,
        recovery_timeout=settings.app.resilience.circuit_breaker.recovery_timeout,
        success_threshold=settings.app.resilience.circuit_breaker.success_threshold
    )

JIRA_RETRY_CONFIG = _get_jira_retry_config()
JIRA_CIRCUIT_CONFIG = _get_jira_circuit_config()


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
            
        Note:
            Uses requests directly with the new /rest/api/3/search/jql endpoint
            because the atlassian-python-api library still uses the deprecated
            /rest/api/3/search endpoint internally.
        """
        self.ensure_connected()
        
        try:
            # Build the API URL with the new endpoint  
            url = f"{self.config['base_url']}/rest/api/3/search/jql"
            
            # Prepare headers
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # Prepare the payload according to the new API spec
            payload = {
                "jql": jql,
                "maxResults": limit
            }
            
            # Add fields if specified
            if fields:
                if isinstance(fields, list):
                    payload["fields"] = fields
                else:
                    payload["fields"] = [fields]
            
            # Make the API call with basic auth
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                auth=(self.config['username'], self.config['api_token']),
                verify=self.config.get('verify_ssl', True),
                timeout=self.config.get('timeout', 30)
            )
            
            # Check for errors
            if response.status_code not in (200, 201):
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Failed to search issues with JQL '{jql}': {error_msg}")
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully searched issues with JQL: {jql}")
            
            # The new API returns slightly different structure - convert to match old format
            # New API: {'isLast': true, 'issues': [...]}
            # Old API: {'issues': [...], 'maxResults': 50, 'startAt': 0, 'total': 1}
            # Add compatibility fields if they're missing
            if 'issues' in result and 'maxResults' not in result:
                result['maxResults'] = limit
                result['startAt'] = 0
                result['total'] = len(result.get('issues', []))
            
            return result
            
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
            params = {}
            if fields:
                params['fields'] = fields
            if expand:
                params['expand'] = expand
            # Use REST API to ensure consistent dict shape
            issue = self._jira_client.get(f'/rest/api/3/issue/{issue_key}', params=params)
            return issue
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
    
    @retry(JIRA_RETRY_CONFIG)
    @circuit_breaker(JIRA_CIRCUIT_CONFIG)
    def add_comment(self, issue_key: str, comment_body: Union[str, dict]) -> Dict:
        """
        Add a comment to an issue.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            comment_body: The comment - either plain text string or ADF dict
            
        Returns:
            Created comment data
            
        Note:
            - For plain text: pass a string directly
            - For ADF with mentions: pass a dict with version, type, and content fields
        """
        self.ensure_connected()
        
        try:
            # Check if comment_body is ADF format (dict with proper structure)
            if isinstance(comment_body, dict) and comment_body.get('type') == 'doc':
                # ADF format - use requests directly to send proper JSON
                return self._add_adf_comment(issue_key, comment_body)
            else:
                # Plain text - use atlassian library (works fine for strings)
                result = self._jira_client.issue_add_comment(issue_key, comment_body)
                logger.info(f"Added comment to issue {issue_key}")
                return result
        except Exception as e:
            logger.error(f"Failed to add comment to issue {issue_key}: {e}")
            raise
    
    def _add_adf_comment(self, issue_key: str, adf_body: dict) -> Dict:
        """
        Add ADF format comment using direct API call.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            adf_body: ADF document structure as dict
            
        Returns:
            Created comment data
            
        Note:
            Uses requests directly because atlassian-python-api doesn't handle
            ADF JSON properly - it converts it to string instead of keeping as object.
        """
        # Build the API URL
        url = f"{self.config['base_url']}/rest/api/3/issue/{issue_key}/comment"
        
        # Prepare headers
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Prepare the payload - ADF must be sent as actual JSON object, not string
        payload = {
            "body": adf_body
        }
        
        # Make the API call with basic auth
        response = requests.post(
            url,
            json=payload,  # This sends as proper JSON, not stringified
            headers=headers,
            auth=(self.config['username'], self.config['api_token']),
            verify=self.config.get('verify_ssl', True),
            timeout=self.config.get('timeout', 30)
        )
        
        # Check for errors
        if response.status_code not in (200, 201):
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"Failed to add ADF comment to {issue_key}: {error_msg}")
            response.raise_for_status()
        
        result = response.json()
        logger.info(f"Added ADF comment to issue {issue_key}")
        return result
    
    @retry(JIRA_RETRY_CONFIG)
    @circuit_breaker(JIRA_CIRCUIT_CONFIG)
    def search_users(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        Search for users in Jira.
        
        Args:
            query: Search query (username, email, or display name)
            max_results: Maximum number of results to return
            
        Returns:
            List of user objects with accountId, displayName, emailAddress, etc.
        """
        self.ensure_connected()
        
        try:
            # Use the REST user search endpoint (consistent across API versions)
            params = {
                'query': query,
                'maxResults': max_results
            }
            users = self._jira_client.get('/rest/api/3/user/search', params=params)
            logger.info(f"Found {len(users) if users else 0} users matching '{query}'")
            return users or []
        except Exception as e:
            logger.error(f"Failed to search users with query '{query}': {e}")
            raise
    
    @retry(JIRA_RETRY_CONFIG)
    @circuit_breaker(JIRA_CIRCUIT_CONFIG)
    def get_user_by_account_id(self, account_id: str) -> Dict:
        """
        Get user details by account ID.
        
        Args:
            account_id: Atlassian account ID
            
        Returns:
            User object with accountId, displayName, emailAddress, etc.
        """
        self.ensure_connected()
        
        try:
            user = self._jira_client.user(account_id)
            logger.info(f"Retrieved user details for account ID: {account_id}")
            return user
        except Exception as e:
            logger.error(f"Failed to get user with account ID '{account_id}': {e}")
            raise
    
    @retry(JIRA_RETRY_CONFIG)
    @circuit_breaker(JIRA_CIRCUIT_CONFIG)
    def get_all_users(self, start_at: int = 0, max_results: int = 50) -> List[Dict]:
        """
        Get all users (with pagination support).
        
        Args:
            start_at: Starting index for pagination (default: 0)
            max_results: Maximum number of results to return (default: 50)
            
        Returns:
            List of user objects with accountId, displayName, emailAddress, etc.
            
        Note:
            This may return a large number of users. Consider using search_users 
            for more targeted results.
        """
        self.ensure_connected()
        
        try:
            params = {
                'startAt': start_at,
                'maxResults': max_results
            }
            # Use users search endpoint
            users = self._jira_client.get('/rest/api/3/users/search', params=params)
            logger.info(f"Retrieved {len(users) if users else 0} users (start: {start_at}, limit: {max_results})")
            return users or []
        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            raise
    
    @retry(JIRA_RETRY_CONFIG)
    @circuit_breaker(JIRA_CIRCUIT_CONFIG)
    def get_project_users(self, project_key: str, start_at: int = 0, max_results: int = 50) -> List[Dict]:
        """
        Get users who have access to a specific project.
        
        Args:
            project_key: Project key (e.g., 'PROJ')
            start_at: Starting index for pagination (default: 0)
            max_results: Maximum number of results to return (default: 50)
            
        Returns:
            List of user objects with accountId, displayName, emailAddress, etc.
        """
        self.ensure_connected()
        
        try:
            params = {
                'project': project_key,
                'startAt': start_at,
                'maxResults': max_results
            }
            # Use assignable user search for project membership/permissions
            users = self._jira_client.get('/rest/api/3/user/assignable/search', params=params)
            logger.info(f"Retrieved {len(users) if users else 0} users for project {project_key}")
            return users or []
        except Exception as e:
            logger.error(f"Failed to get users for project '{project_key}': {e}")
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
