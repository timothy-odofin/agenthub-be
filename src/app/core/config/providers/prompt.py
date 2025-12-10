"""
Prompt configuration management using Settings system.
Centralizes prompt templates and provides dynamic prompt selection.
"""

from typing import Dict, Any, Optional, List
from enum import Enum

from ..framework.registry import BaseConfigSource, register_config
from ..framework.settings import settings


class PromptType(Enum):
    """Supported prompt types."""
    CHAT_DEFAULT = "chat.default"
    CHAT_TECHNICAL = "chat.technical"
    CHAT_BUSINESS = "chat.business"
    REACT_AGENT = "agent.react_agent"
    RESEARCH_AGENT = "agent.research_agent"
    DOCUMENT_ANALYSIS = "ingestion.document_analysis"
    CONTENT_SUMMARIZATION = "ingestion.content_summarization"
    ENTITY_EXTRACTION = "ingestion.entity_extraction"
    CODE_REVIEW = "code_review"
    DATA_INSIGHTS = "data_insights"
    MEETING_FACILITATOR = "meeting_facilitator"


class PromptConfigError(Exception):
    """Raised when prompt configuration is invalid or missing."""
    pass


@register_config(['prompt'])
class PromptConfig(BaseConfigSource):
    """Prompt configuration for all prompt types and templates using Settings system."""
    
    @property
    def default_config(self) -> Dict[str, Any]:
        """
        Get default prompt configuration.
        """
        if not hasattr(settings, 'prompt') or not hasattr(settings.prompt, 'default'):
            return {
                'provider': 'system',
                'language': 'en',
                'max_tokens': 4096,
                'temperature': 0.7
            }
        
        default = settings.prompt.default
        return {
            'provider': getattr(default, 'provider', 'system'),
            'language': getattr(default, 'language', 'en'),
            'max_tokens': getattr(default, 'max_tokens', 4096),
            'temperature': getattr(default, 'temperature', 0.7)
        }
    
    def get_system_prompt(self, prompt_type: str, **kwargs) -> str:
        """
        Get a system prompt by type with variable substitution.
        
        Args:
            prompt_type: Dot notation path to prompt (e.g., "chat.default", "agent.react_agent")
            **kwargs: Variables for template substitution
            
        Returns:
            Formatted prompt string
        """
        if not hasattr(settings, 'prompt') or not hasattr(settings.prompt, 'system'):
            raise PromptConfigError("System prompts not configured")
        
        try:
            # Navigate the nested prompt structure
            current = settings.prompt.system
            for part in prompt_type.split('.'):
                current = getattr(current, part)
            
            prompt_template = current
            if isinstance(prompt_template, str):
                # Perform variable substitution if kwargs provided
                if kwargs:
                    return prompt_template.format(**kwargs)
                return prompt_template
            else:
                raise PromptConfigError(f"Prompt type '{prompt_type}' is not a string template")
                
        except AttributeError:
            raise PromptConfigError(f"Prompt type '{prompt_type}' not found")
    
    def get_custom_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Get a custom prompt by name with variable substitution.
        
        Args:
            prompt_name: Name of the custom prompt
            **kwargs: Variables for template substitution
            
        Returns:
            Formatted prompt string
        """
        if not hasattr(settings, 'prompt') or not hasattr(settings.prompt, 'custom'):
            raise PromptConfigError("Custom prompts not configured")
        
        try:
            prompt_template = getattr(settings.prompt.custom, prompt_name)
            if isinstance(prompt_template, str):
                if kwargs:
                    return prompt_template.format(**kwargs)
                return prompt_template
            else:
                raise PromptConfigError(f"Custom prompt '{prompt_name}' is not a string template")
                
        except AttributeError:
            raise PromptConfigError(f"Custom prompt '{prompt_name}' not found")
    
    def get_template_variables(self) -> Dict[str, str]:
        """
        Get available template variables with their default values.
        
        Returns:
            Dictionary of variable names and default values
        """
        if not hasattr(settings, 'prompt') or not hasattr(settings.prompt, 'templates'):
            return {}
        
        variables = getattr(settings.prompt.templates, 'variables', {})
        if hasattr(variables, 'to_dict'):
            return variables.to_dict()
        return {}
    
    def get_template_prompt(self, template_name: str, **kwargs) -> str:
        """
        Get a prompt template with variable substitution.
        
        Args:
            template_name: Name of the template
            **kwargs: Variables for substitution (overrides defaults)
            
        Returns:
            Formatted prompt string
        """
        if not hasattr(settings, 'prompt') or not hasattr(settings.prompt, 'templates'):
            raise PromptConfigError("Template prompts not configured")
        
        try:
            template = getattr(settings.prompt.templates, template_name)
            if isinstance(template, str):
                # Get default variables and override with provided kwargs
                default_vars = self.get_template_variables()
                variables = {**default_vars, **kwargs}
                return template.format(**variables)
            else:
                raise PromptConfigError(f"Template '{template_name}' is not a string")
                
        except AttributeError:
            raise PromptConfigError(f"Template '{template_name}' not found")
    
    def get_environment_prompt(self, environment: str, prompt_type: str, **kwargs) -> str:
        """
        Get environment-specific prompt override.
        
        Args:
            environment: Environment name (development, staging, production)
            prompt_type: Type of prompt to get
            **kwargs: Variables for substitution
            
        Returns:
            Formatted prompt string or falls back to default
        """
        if (hasattr(settings, 'prompt') and 
            hasattr(settings.prompt, 'environments') and
            hasattr(settings.prompt.environments, environment)):
            
            env_config = getattr(settings.prompt.environments, environment)
            try:
                # Navigate to the prompt type within environment config
                current = env_config
                for part in prompt_type.split('.'):
                    current = getattr(current, part)
                
                prompt_template = current
                if isinstance(prompt_template, str):
                    if kwargs:
                        return prompt_template.format(**kwargs)
                    return prompt_template
            except AttributeError:
                pass  # Fall back to default prompt
        
        # Fall back to system prompt if environment-specific not found
        return self.get_system_prompt(prompt_type, **kwargs)
    
    def get_versioned_prompt(self, version: str, prompt_key: str, **kwargs) -> str:
        """
        Get a prompt from a specific version configuration.
        
        Args:
            version: Version identifier (e.g., "v1_0", "experimental")
            prompt_key: Key within the version's prompt mapping
            **kwargs: Variables for substitution
            
        Returns:
            Formatted prompt string
        """
        if (hasattr(settings, 'prompt') and 
            hasattr(settings.prompt, 'versions') and
            hasattr(settings.prompt.versions, version)):
            
            version_config = getattr(settings.prompt.versions, version)
            if hasattr(version_config, 'prompts') and hasattr(version_config.prompts, prompt_key):
                prompt_reference = getattr(version_config.prompts, prompt_key)
                
                # Resolve the prompt reference (e.g., "system.chat.default")
                if prompt_reference.startswith('system.'):
                    return self.get_system_prompt(prompt_reference[7:], **kwargs)
                elif prompt_reference.startswith('custom.'):
                    return self.get_custom_prompt(prompt_reference[7:], **kwargs)
                elif prompt_reference.startswith('templates.'):
                    return self.get_template_prompt(prompt_reference[10:], **kwargs)
        
        raise PromptConfigError(f"Versioned prompt '{prompt_key}' not found in version '{version}'")
    
    def get_active_version_prompt(self, prompt_key: str, user_id: Optional[str] = None, **kwargs) -> str:
        """
        Get prompt from the currently active version, with user-specific overrides.
        
        Args:
            prompt_key: Key within the version's prompt mapping
            user_id: Optional user ID for experimental feature access
            **kwargs: Variables for substitution
            
        Returns:
            Formatted prompt string
        """
        if hasattr(settings, 'prompt') and hasattr(settings.prompt, 'versions'):
            versions = settings.prompt.versions
            
            # Check for experimental access first
            if (user_id and hasattr(versions, 'experimental') and 
                hasattr(versions.experimental, 'enabled_for_users')):
                enabled_users = getattr(versions.experimental, 'enabled_for_users', [])
                if hasattr(enabled_users, '__iter__') and user_id in enabled_users:
                    try:
                        return self.get_versioned_prompt('experimental', prompt_key, **kwargs)
                    except PromptConfigError:
                        pass  # Fall back to active version
            
            # Find active version
            for version_name in dir(versions):
                if not version_name.startswith('_'):
                    version_config = getattr(versions, version_name)
                    if (hasattr(version_config, 'active') and 
                        getattr(version_config, 'active', False)):
                        try:
                            return self.get_versioned_prompt(version_name, prompt_key, **kwargs)
                        except PromptConfigError:
                            continue
        
        # Fall back to default system prompt
        return self.get_system_prompt('chat.default', **kwargs)
    
    def list_available_prompts(self) -> Dict[str, List[str]]:
        """
        List all available prompts organized by category.
        
        Returns:
            Dictionary with categories and their available prompts
        """
        result = {
            'system': [],
            'custom': [],
            'templates': [],
            'versions': []
        }
        
        if hasattr(settings, 'prompt'):
            # System prompts
            if hasattr(settings.prompt, 'system'):
                system = settings.prompt.system
                for category in dir(system):
                    if not category.startswith('_'):
                        category_obj = getattr(system, category)
                        for prompt_name in dir(category_obj):
                            if not prompt_name.startswith('_'):
                                result['system'].append(f"{category}.{prompt_name}")
            
            # Custom prompts
            if hasattr(settings.prompt, 'custom'):
                custom = settings.prompt.custom
                for prompt_name in dir(custom):
                    if not prompt_name.startswith('_'):
                        result['custom'].append(prompt_name)
            
            # Templates
            if hasattr(settings.prompt, 'templates'):
                templates = settings.prompt.templates
                for template_name in dir(templates):
                    if not template_name.startswith('_') and template_name != 'variables':
                        result['templates'].append(template_name)
            
            # Versions
            if hasattr(settings.prompt, 'versions'):
                versions = settings.prompt.versions
                for version_name in dir(versions):
                    if not version_name.startswith('_'):
                        result['versions'].append(version_name)
        
        return result
    
    def get_connection_config(self, connection_type: str = None) -> Dict[str, Any]:
        """
        Get prompt configuration for connection management.
        
        Args:
            connection_type: Type of connection (not used for prompts)
            
        Returns:
            Prompt configuration dictionary
        """
        return {
            'type': 'prompt',
            'default_config': self.default_config,
            'available_prompts': self.list_available_prompts()
        }


# Global instance
prompt_config = PromptConfig()
