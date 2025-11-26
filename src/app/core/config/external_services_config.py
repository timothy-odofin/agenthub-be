"""
External services configuration management.
"""

import os
from app.core.constants import AtlassianProperties
from app.core.utils.single_ton import SingletonMeta


class ExternalServicesConfig(metaclass=SingletonMeta):
    """External services configuration (APIs, integrations, etc.)."""
    
    @property
    def atlassian_config(self) -> dict:
        """Atlassian configuration for Confluence and Jira"""
        return {
            AtlassianProperties.API_KEY: os.getenv('ATLASSIAN_API_KEY'),
            AtlassianProperties.EMAIL: os.getenv('ATLASSIAN_EMAIL'),
            AtlassianProperties.CONFLUENCE_BASE_URL: os.getenv('ATLASSIAN_BASE_URL_CONFLUENCE'),
            AtlassianProperties.JIRA_BASE_URL: os.getenv('ATLASSIAN_BASE_URL_JIRA')
        }
    
    @property
    def github_config(self) -> dict:
        """GitHub API configuration"""
        return {
            'api_key': os.getenv('GITHUB_API_KEY'),
            'base_url': os.getenv('GITHUB_BASE_URL', 'https://api.github.com'),
            'timeout': int(os.getenv('GITHUB_TIMEOUT', '30')),
        }
    
    @property
    def bitbucket_config(self) -> dict:
        """Bitbucket API configuration"""
        return {
            'username': os.getenv('BITBUCKET_USERNAME'),
            'app_password': os.getenv('BITBUCKET_APP_PASSWORD'),
            'base_url': os.getenv('BITBUCKET_BASE_URL', 'https://api.bitbucket.org/2.0'),
            'timeout': int(os.getenv('BITBUCKET_TIMEOUT', '30')),
        }
    
    @property
    def s3_config(self) -> dict:
        """AWS S3 configuration"""
        return {
            'access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
            'secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'region': os.getenv('AWS_REGION', 'us-east-1'),
            'bucket_name': os.getenv('S3_BUCKET_NAME'),
            'endpoint_url': os.getenv('S3_ENDPOINT_URL'),  # For S3-compatible services
        }
    
    @property
    def sharepoint_config(self) -> dict:
        """SharePoint configuration"""
        return {
            'tenant_id': os.getenv('SHAREPOINT_TENANT_ID'),
            'client_id': os.getenv('SHAREPOINT_CLIENT_ID'),
            'client_secret': os.getenv('SHAREPOINT_CLIENT_SECRET'),
            'site_url': os.getenv('SHAREPOINT_SITE_URL'),
            'timeout': int(os.getenv('SHAREPOINT_TIMEOUT', '60')),
        }
    
    @property
    def langchain_config(self) -> dict:
        """LangChain configuration"""
        return {
            'api_key': os.getenv('LANGCHAIN_API_KEY'),
            'project': os.getenv('LANGCHAIN_PROJECT', 'agenthub'),
            'tracing_v2': os.getenv('LANGCHAIN_TRACING_V2', 'true').lower() == 'true',
            'endpoint': os.getenv('LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com'),
        }
    
    def get_connection_config(self, connection_name: str) -> dict:
        """
        Get configuration for a specific external service connection.
        
        Args:
            connection_name: Name of the external service connection
            
        Returns:
            Dict with external service configuration
            
        Raises:
            KeyError: If connection name not found
        """
        config_map = {
            'confluence': {
                'base_url': self.atlassian_config.get(AtlassianProperties.CONFLUENCE_BASE_URL),
                'username': self.atlassian_config.get(AtlassianProperties.EMAIL),
                'api_token': self.atlassian_config.get(AtlassianProperties.API_KEY),
            },
            'jira': {
                'base_url': self.atlassian_config.get(AtlassianProperties.JIRA_BASE_URL),
                'username': self.atlassian_config.get(AtlassianProperties.EMAIL),
                'api_token': self.atlassian_config.get(AtlassianProperties.API_KEY),
            },
            's3': self.s3_config,
            'sharepoint': self.sharepoint_config,
            'github': self.github_config,
            'bitbucket': self.bitbucket_config,
        }
        
        if connection_name not in config_map:
            available = list(config_map.keys())
            raise KeyError(f"External service connection '{connection_name}' not found. Available: {available}")
        
        return config_map[connection_name]


# Create singleton instance
external_services_config = ExternalServicesConfig()
