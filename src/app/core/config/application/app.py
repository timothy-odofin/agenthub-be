"""
Core application configuration.
"""

from typing import Optional

from app.core.utils.single_ton import SingletonMeta
from app.core.schemas.ingestion_config import IngestionConfig
from app.core.utils import dynamic_config_to_dict
from ..framework.settings import settings


class AppConfig(metaclass=SingletonMeta):
    """Core application configuration using Settings system."""
    
    def __init__(self):
        # Load configurations from Settings system
        self._load_app_config()
        self._load_ingestion_config()
    
    def _load_app_config(self):
        """Load core application configuration from Settings system."""
        # App settings
        self.app_env = settings.app.environment
        self.debug = settings.app.debug
        self.app_name = settings.app.name
        self.app_version = settings.app.version
        
        # Security settings
        self.jwt_secret_key = settings.app.security.jwt_secret_key
        self.jwt_algorithm = settings.app.security.jwt_algorithm
        self.access_token_expire_minutes = settings.app.security.access_token_expire_minutes
        
        # API Configuration
        self.api_host = settings.app.api.host
        self.api_port = settings.app.api.port
        
        # Logging
        self.log_level = settings.app.logging.level
    
    def _load_ingestion_config(self) -> None:
        """Load the ingestion configuration from Settings system."""
        try:
            # Get data sources from Settings system
            if hasattr(settings, 'data_sources') and settings.data_sources:
                # Convert DynamicConfig to dictionary using the reusable utility
                data_sources_dict = dynamic_config_to_dict(settings.data_sources)
                
                self.ingestion_config = IngestionConfig.model_validate(data_sources_dict)
                print(f"Ingestion config loaded successfully from Settings, total config: {len(self.ingestion_config.data_sources)} data sources")
            else:
                self.ingestion_config = None
                print("No data sources found in Settings")
        except Exception as e:
            print(f"Error loading ingestion config from Settings: {e}")
            self.ingestion_config = None


# Create singleton instance
app_config = AppConfig()
