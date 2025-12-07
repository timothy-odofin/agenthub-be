"""
External services configuration management using Settings system.
"""

from typing import Dict, Any
from app.core.constants import AtlassianProperties
from ..framework.registry import BaseConfigSource, register_connections
from ..framework.settings import settings


@register_connections(['confluence', 'jira', 's3', 'sharepoint', 'github', 'bitbucket'])
class ExternalServicesConfig(BaseConfigSource):
    """External services configuration using Settings system."""
    
    def get_connection_config(self, connection_name: str) -> dict:
        """Get configuration for a specific connection name."""
        # Map connection names to appropriate configuration methods
        if connection_name in ['confluence', 'jira']:
            # Transform AtlassianProperties keys to expected connection manager format
            atlassian_config = self.atlassian_config
            if not atlassian_config:
                return {}
            return {
                'base_url': atlassian_config.get(AtlassianProperties.CONFLUENCE_BASE_URL) if connection_name == 'confluence' 
                           else atlassian_config.get(AtlassianProperties.JIRA_BASE_URL),
                'username': atlassian_config.get(AtlassianProperties.EMAIL),
                'api_token': atlassian_config.get(AtlassianProperties.API_KEY)
            }
        elif connection_name == 's3':
            return self.s3_config
        elif connection_name == 'sharepoint':
            return self.sharepoint_config
        elif connection_name == 'github':
            return self.github_config
        elif connection_name == 'bitbucket':
            return self.bitbucket_config
        elif connection_name == 'langchain':
            return self.langchain_config
        
        return {}
    
    @property
    def atlassian_config(self) -> Dict[str, Any]:
        """Atlassian configuration for Confluence and Jira"""
        if not hasattr(settings, 'external') or not hasattr(settings.external, 'atlassian'):
            return {}
        return {
            AtlassianProperties.API_KEY: settings.external.atlassian.api_key,
            AtlassianProperties.EMAIL: settings.external.atlassian.email,
            AtlassianProperties.CONFLUENCE_BASE_URL: settings.external.atlassian.confluence_base_url,
            AtlassianProperties.JIRA_BASE_URL: settings.external.atlassian.jira_base_url
        }
    
    @property
    def github_config(self) -> Dict[str, Any]:
        """GitHub API configuration"""
        if not hasattr(settings, 'external') or not hasattr(settings.external, 'github'):
            return {}
        return {
            'api_key': settings.external.github.api_key,
            'base_url': settings.external.github.base_url,
            'timeout': settings.external.github.timeout,
        }
    
    @property
    def bitbucket_config(self) -> Dict[str, Any]:
        """Bitbucket API configuration"""
        if not hasattr(settings, 'external') or not hasattr(settings.external, 'bitbucket'):
            return {}
        return {
            'username': settings.external.bitbucket.username,
            'app_password': settings.external.bitbucket.app_password,
            'base_url': settings.external.bitbucket.base_url,
            'timeout': settings.external.bitbucket.timeout,
        }
    
    @property
    def s3_config(self) -> Dict[str, Any]:
        """AWS S3 configuration"""
        if not hasattr(settings, 'external') or not hasattr(settings.external, 's3'):
            return {}
        return {
            'access_key_id': settings.external.s3.access_key_id,
            'secret_access_key': settings.external.s3.secret_access_key,
            'region': settings.external.s3.region,
            'bucket_name': settings.external.s3.bucket_name,
            'endpoint_url': settings.external.s3.endpoint_url,
        }
    
    @property
    def sharepoint_config(self) -> Dict[str, Any]:
        """SharePoint configuration"""
        if not hasattr(settings, 'external') or not hasattr(settings.external, 'sharepoint'):
            return {}
        return {
            'tenant_id': settings.external.sharepoint.tenant_id,
            'client_id': settings.external.sharepoint.client_id,
            'client_secret': settings.external.sharepoint.client_secret,
            'site_url': settings.external.sharepoint.site_url,
            'timeout': settings.external.sharepoint.timeout,
        }
    
    @property
    def langchain_config(self) -> Dict[str, Any]:
        """LangChain configuration"""
        if not hasattr(settings, 'external') or not hasattr(settings.external, 'langchain'):
            return {}
        return {
            'api_key': settings.external.langchain.api_key,
            'project': settings.external.langchain.project,
            'tracing_v2': settings.external.langchain.tracing_v2,
            'endpoint': settings.external.langchain.endpoint,
        }


# Create singleton instance
external_services_config = ExternalServicesConfig()
