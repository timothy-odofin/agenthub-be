from abc import ABC, abstractmethod
from typing import Any, Callable, Dict

from app.core.config.framework.settings import settings
from app.core.config.utils.config_converter import dynamic_config_to_dict
from app.core.constants import EmbeddingType
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingConfigProvider(ABC):
    """
    Abstract base class for embedding configuration providers.
    
    This allows different strategies for retrieving embedding configurations,
    making the system more flexible and testable.
    """
    
    @abstractmethod
    def get_config(self, embedding_type: EmbeddingType) -> Dict[str, Any]:
        """
        Retrieve configuration for a specific embedding type.
        
        Args:
            embedding_type: The type of embedding to get configuration for
            
        Returns:
            Configuration dictionary for the embedding
            
        Raises:
            ValueError: If configuration for the embedding type is not found
        """
        pass


class SettingsConfigProvider(EmbeddingConfigProvider):
    """
    Configuration provider that retrieves embedding configs from the settings singleton.
    
    This is the default provider used in production, accessing configurations from
    the application-embeddings.yaml file via the settings system.
    """
    
    def get_config(self, embedding_type: EmbeddingType) -> Dict[str, Any]:
        """
        Retrieve embedding configuration from settings.
        
        Args:
            embedding_type: The type of embedding to get configuration for
            
        Returns:
            Configuration dictionary for the embedding
            
        Raises:
            ValueError: If the embedding configuration is not found in settings
        """
        try:
            # Get the embedding type name (e.g., 'openai', 'huggingface')
            config_key = embedding_type.value.lower()
            
            # Access settings.embeddings.<provider_name>
            if not hasattr(settings.embeddings, config_key):
                raise ValueError(
                    f"Configuration for '{config_key}' not found in settings.embeddings. "
                    f"Available providers: {[attr for attr in dir(settings.embeddings) if not attr.startswith('_')]}"
                )
            
            embedding_config = getattr(settings.embeddings, config_key)
            
            # Convert DynamicConfig to dictionary for consistent interface
            config_dict = dynamic_config_to_dict(embedding_config)
            
            logger.debug(f"Retrieved configuration for {embedding_type} from settings")
            return config_dict
            
        except AttributeError as e:
            raise ValueError(f"Failed to retrieve configuration for {embedding_type}: {e}")


class DictConfigProvider(EmbeddingConfigProvider):
    """
    Configuration provider that uses a pre-defined dictionary.
    
    Useful for testing or when you want to provide custom configurations
    without relying on the settings system.
    """
    
    def __init__(self, configs: Dict[EmbeddingType, Dict[str, Any]]):
        """
        Initialize with a dictionary of configurations.
        
        Args:
            configs: Dictionary mapping embedding types to their configurations
        """
        self._configs = configs
    
    def get_config(self, embedding_type: EmbeddingType) -> Dict[str, Any]:
        """
        Retrieve embedding configuration from the internal dictionary.
        
        Args:
            embedding_type: The type of embedding to get configuration for
            
        Returns:
            Configuration dictionary for the embedding
            
        Raises:
            ValueError: If the embedding type is not in the configs dictionary
        """
        if embedding_type not in self._configs:
            raise ValueError(
                f"Configuration for {embedding_type} not found in provided configs. "
                f"Available types: {list(self._configs.keys())}"
            )
        
        logger.debug(f"Retrieved configuration for {embedding_type} from dict provider")
        return self._configs[embedding_type]


class EmbeddingFactory:
    """
    Factory for creating embedding models with pluggable configuration strategy.
    
    Uses the Strategy Pattern to allow different configuration sources (settings, dict, custom).
    The factory is responsible only for creating embeddings, while configuration retrieval
    is delegated to the config provider.
    """

    _registry: Dict[EmbeddingType, Callable[[Dict[str, Any]], Any]] = {}
    _config_provider: EmbeddingConfigProvider = SettingsConfigProvider()  # Default provider

    @classmethod
    def register(cls, name: EmbeddingType):
        """
        Decorator for registering embedding creators.
        
        Args:
            name: The embedding type this creator handles
            
        Returns:
            Decorator function that registers the creator
        """
        def decorator(func: Callable[[Dict[str, Any]], Any]):
            cls._registry[name] = func
            logger.info(f"Registered embedding creator for type: {name}")
            return func
        return decorator

    @classmethod
    def set_config_provider(cls, provider: EmbeddingConfigProvider) -> None:
        """
        Set a custom configuration provider.
        
        This allows swapping the configuration strategy at runtime,
        useful for testing or different deployment scenarios.
        
        Args:
            provider: The config provider to use
        """
        cls._config_provider = provider
        logger.info(f"Set embedding config provider to: {provider.__class__.__name__}")

    @classmethod
    def get_embedding_model(cls, embedding_type: EmbeddingType):
        """
        Get or create an embedding model by type.
        
        The factory retrieves configuration from the configured provider
        and passes it to the appropriate creator function.
        
        Args:
            embedding_type: Type of embedding to create
            
        Returns:
            Configured embedding model instance
            
        Raises:
            ValueError: If the embedding type is not registered or config is not found
        """
        if embedding_type not in cls._registry:
            available_types = list(cls._registry.keys())
            raise ValueError(
                f"Unsupported embedding type: {embedding_type}. "
                f"Available types: {available_types}"
            )

        logger.info(f"Creating embedding model for type: {embedding_type}")
        try:
            # Delegate configuration retrieval to the config provider
            config = cls._config_provider.get_config(embedding_type)
            
            # Call the registered creator with the configuration
            embedding_model = cls._registry[embedding_type](config)
            
            logger.info(f"Successfully created {embedding_type} embedding model")
            return embedding_model
            
        except Exception as e:
            logger.error(f"Failed to initialize {embedding_type} embedding: {e}")
            raise
