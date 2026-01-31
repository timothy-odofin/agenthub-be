"""
Prompt configuration management using Settings system.
Simplified version following YAGNI principle - only includes what's currently used.
"""

from typing import Dict, Any, Optional
from enum import Enum

from ..framework.registry import BaseConfigSource, register_config
from ..framework.settings import settings


class PromptType(Enum):
    """Supported prompt types - Following YAGNI Principle."""
    REACT_AGENT = "agent.react_agent"  # Currently used by LangChain and LangGraph agents


class PromptConfigError(Exception):
    """Raised when prompt configuration is invalid or missing."""
    pass


@register_config(['prompt'])
class PromptConfig(BaseConfigSource):
    """Simplified prompt configuration using Settings system."""
    
    def get_connection_config(self, connection_name: str) -> dict:
        """
        Required by BaseConfigSource but not used for prompt configuration.
        Prompts don't have connections.
        """
        return {}
    
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
        Get system prompt for the specified type with variable substitution.
        
        Args:
            prompt_type: Type of prompt (e.g., "agent.react_agent")
            **kwargs: Variables for substitution in the prompt
            
        Returns:
            Formatted prompt string
        """
        if not hasattr(settings, 'prompt') or not hasattr(settings.prompt, 'system'):
            raise PromptConfigError("System prompts not configured")
        
        try:
            # Navigate through the nested structure (e.g., "agent.react_agent")
            current = settings.prompt.system
            for part in prompt_type.split('.'):
                current = getattr(current, part)
            
            if isinstance(current, str):
                return current.format(**kwargs) if kwargs else current
            else:
                raise PromptConfigError(f"System prompt '{prompt_type}' is not a string")
                
        except AttributeError:
            raise PromptConfigError(f"System prompt '{prompt_type}' not found")


# Global instance for easy access
prompt_config = PromptConfig()
