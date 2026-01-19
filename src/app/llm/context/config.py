"""
Configuration management for context window settings using Settings system.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.core.config.framework.settings import settings


@dataclass 
class ContextWindowConfig:
    """Configuration for context window management."""
    
    default_strategy: str = "recent"
    default_model: str = "gpt-4"
    
    # Strategy configurations
    sliding_config: Dict[str, Any] = None
    summarization_config: Dict[str, Any] = None
    
    # Model overrides
    model_overrides: Dict[str, Dict[str, int]] = None
    
    # Performance settings
    enable_token_caching: bool = True
    log_utilization: bool = True
    warn_threshold: float = 0.9
    max_processing_time: float = 2.0
    
    # Safety settings
    min_preserved_messages: int = 2
    max_single_message_tokens: int = 2000
    emergency_message_limit: int = 5


def get_context_window_config() -> ContextWindowConfig:
    """Get context window configuration from Settings system."""
    try:
        # Access context configuration from Settings system
        # This will automatically load from resources/application-context.yaml
        if hasattr(settings, 'context_window'):
            context_config = settings.context_window
            
            # Extract configurations with defaults
            default_strategy = getattr(context_config, 'default_strategy', 'recent')
            default_model = getattr(context_config, 'default_model', 'gpt-4')
            
            # Strategy configurations
            strategies = getattr(context_config, 'strategies', None)
            sliding_config = {}
            summarization_config = {}
            
            if strategies:
                if hasattr(strategies, 'sliding'):
                    sliding_config = {
                        'min_recent_messages': getattr(strategies.sliding, 'min_recent_messages', 5)
                    }
                    
                if hasattr(strategies, 'summarization'):
                    summarization_config = {
                        'summarization_threshold': getattr(strategies.summarization, 'summarization_threshold', 20),
                        'keep_recent_messages': getattr(strategies.summarization, 'keep_recent_messages', 10)
                    }
            
            # Model overrides
            model_overrides = {}
            if hasattr(context_config, 'model_overrides'):
                model_overrides_config = context_config.model_overrides
                for model_name in dir(model_overrides_config):
                    if not model_name.startswith('_'):
                        model_config = getattr(model_overrides_config, model_name)
                        if model_config:
                            model_overrides[model_name] = {
                                'max_tokens': getattr(model_config, 'max_tokens', 4096),
                                'reserved_tokens': getattr(model_config, 'reserved_tokens', 500),
                                'system_prompt_tokens': getattr(model_config, 'system_prompt_tokens', 100)
                            }
            
            # Performance settings
            performance_config = getattr(context_config, 'performance', None)
            enable_token_caching = True
            log_utilization = True
            warn_threshold = 0.9
            max_processing_time = 2.0
            
            if performance_config:
                enable_token_caching = getattr(performance_config, 'enable_token_caching', True)
                log_utilization = getattr(performance_config, 'log_utilization', True)
                warn_threshold = getattr(performance_config, 'warn_threshold', 0.9)
                max_processing_time = getattr(performance_config, 'max_processing_time', 2.0)
            
            # Safety settings
            safety_config = getattr(context_config, 'safety', None)
            min_preserved_messages = 2
            max_single_message_tokens = 2000
            emergency_message_limit = 5
            
            if safety_config:
                min_preserved_messages = getattr(safety_config, 'min_preserved_messages', 2)
                max_single_message_tokens = getattr(safety_config, 'max_single_message_tokens', 2000)
                emergency_message_limit = getattr(safety_config, 'emergency_message_limit', 5)
            
            return ContextWindowConfig(
                default_strategy=default_strategy,
                default_model=default_model,
                sliding_config=sliding_config,
                summarization_config=summarization_config,
                model_overrides=model_overrides,
                enable_token_caching=enable_token_caching,
                log_utilization=log_utilization,
                warn_threshold=warn_threshold,
                max_processing_time=max_processing_time,
                min_preserved_messages=min_preserved_messages,
                max_single_message_tokens=max_single_message_tokens,
                emergency_message_limit=emergency_message_limit
            )
        else:
            # No context configuration found, use defaults
            return ContextWindowConfig()
            
    except Exception as e:
        # Fallback to defaults on any error
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not load context window config from Settings: {e}, using defaults")
        return ContextWindowConfig()
