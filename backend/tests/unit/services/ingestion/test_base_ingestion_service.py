"""
Unit tests for BaseIngestionService abstract base class.

Tests the foundational ingestion service architecture including:
- Abstract class behavior and enforcement
- Configuration auto-location and validation
- Data source type handling
- Text splitter initialization
- Abstract method enforcement
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from abc import ABC

from app.services.ingestion.base import BaseIngestionService
from app.core.constants import DataSourceType
from app.core.schemas.ingestion_config import DataSourceConfig


class ConcreteIngestionServiceForTesting(BaseIngestionService):
    """Concrete implementation for testing abstract base class."""
    
    SOURCE_TYPE = DataSourceType.FILE
    
    def validate_config(self) -> None:
        """Test implementation of abstract method."""
        if not self.config.sources:
            raise ValueError("No sources configured")
    
    async def ingest(self) -> bool:
        """Test implementation of abstract method."""
        return True
    
    async def ingest_single(self, source: str) -> bool:
        """Test implementation of abstract method."""
        return True


class InvalidIngestionServiceForTesting(BaseIngestionService):
    """Invalid implementation missing SOURCE_TYPE for testing."""
    
    # Intentionally not defining SOURCE_TYPE
    def validate_config(self) -> None:
        pass
    
    async def ingest(self) -> bool:
        return True
    
    async def ingest_single(self, source: str) -> bool:
        return True


class TestBaseIngestionServiceArchitecture:
    """Test suite for BaseIngestionService abstract class architecture."""

    def test_is_abstract_base_class(self):
        """Test that BaseIngestionService is properly defined as abstract class."""
        assert issubclass(BaseIngestionService, ABC)
        
        # Verify abstract methods are defined
        abstract_methods = BaseIngestionService.__abstractmethods__
        expected_abstract_methods = {'validate_config', 'ingest', 'ingest_single'}
        assert abstract_methods == expected_abstract_methods

    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseIngestionService cannot be directly instantiated."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseIngestionService()

    def test_source_type_enforcement(self):
        """Test that SOURCE_TYPE must be defined in concrete implementations."""
        with pytest.raises(ValueError, match="must define SOURCE_TYPE class attribute"):
            InvalidIngestionServiceForTesting()

    @patch('app.core.config.application.AppConfig')
    def test_initialization_success(self, mock_app_config_class):
        """Test successful initialization with proper configuration."""
        # Setup mock configuration
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        # Mock ingestion config with file data source
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['test_source']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        
        mock_app_config.ingestion_config = mock_ingestion_config
        
        # Create service instance
        service = ConcreteIngestionServiceForTesting()
        
        # Verify initialization
        assert service.config == mock_data_source_config
        assert service.app_config == mock_app_config
        assert service.SOURCE_TYPE == DataSourceType.FILE
        assert hasattr(service, 'text_splitter')

    @patch('app.core.config.application.AppConfig')
    def test_initialization_no_ingestion_config(self, mock_app_config_class):
        """Test initialization failure when no ingestion config is loaded."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        mock_app_config.ingestion_config = None
        
        with pytest.raises(ValueError, match="No ingestion configuration loaded in AppConfig"):
            ConcreteIngestionServiceForTesting()

    @patch('app.core.config.application.AppConfig')
    def test_initialization_missing_data_source_config(self, mock_app_config_class):
        """Test initialization failure when data source config is missing."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_ingestion_config.data_sources = {'confluence': Mock()}  # Missing 'file' config
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with pytest.raises(ValueError, match="No configuration found for data source type: file"):
            ConcreteIngestionServiceForTesting()

    @patch('app.core.config.application.AppConfig')
    def test_config_validation_called(self, mock_app_config_class):
        """Test that validate_config is called during initialization."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        # Mock ingestion config with invalid data (empty sources)
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = []  # Empty sources should trigger validation error
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with pytest.raises(ValueError, match="No sources configured"):
            ConcreteIngestionServiceForTesting()


class TestBaseIngestionServiceProperties:
    """Test suite for BaseIngestionService properties and methods."""

    @patch('app.core.config.application.AppConfig')
    def test_source_type_property(self, mock_app_config_class):
        """Test source_type property returns correct DataSourceType."""
        # Setup mock
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['test_source']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        service = ConcreteIngestionServiceForTesting()
        
        assert service.source_type == DataSourceType.FILE
        assert service.source_type == service.SOURCE_TYPE

    @patch('app.core.config.application.AppConfig')
    def test_text_splitter_initialization(self, mock_app_config_class):
        """Test that text splitter is properly initialized with default settings."""
        # Setup mock
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['test_source']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        service = ConcreteIngestionServiceForTesting()
        
        # Verify text splitter configuration
        assert hasattr(service, 'text_splitter')
        assert service.text_splitter._chunk_size == 1000
        assert service.text_splitter._chunk_overlap == 200
        assert service.text_splitter._length_function == len
        assert service.text_splitter._is_separator_regex is False


class TestBaseIngestionServiceAbstractMethodsEnforcement:
    """Test suite for abstract method enforcement."""

    def test_abstract_methods_must_be_implemented(self):
        """Test that all abstract methods must be implemented in concrete classes."""
        # Test missing validate_config
        class MissingValidateConfig(BaseIngestionService):
            SOURCE_TYPE = DataSourceType.FILE
            async def ingest(self) -> bool:
                return True
            async def ingest_single(self, source: str) -> bool:
                return True
        
        with pytest.raises(TypeError):
            MissingValidateConfig()

        # Test missing ingest
        class MissingIngest(BaseIngestionService):
            SOURCE_TYPE = DataSourceType.FILE
            def validate_config(self) -> None:
                pass
            async def ingest_single(self, source: str) -> bool:
                return True
        
        with pytest.raises(TypeError):
            MissingIngest()

        # Test missing ingest_single
        class MissingIngestSingle(BaseIngestionService):
            SOURCE_TYPE = DataSourceType.FILE
            def validate_config(self) -> None:
                pass
            async def ingest(self) -> bool:
                return True
        
        with pytest.raises(TypeError):
            MissingIngestSingle()

    @patch('app.core.config.application.AppConfig')
    def test_concrete_implementation_works(self, mock_app_config_class):
        """Test that concrete implementation with all methods works correctly."""
        # Setup mock
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['test_source']
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        # This should work without errors
        service = ConcreteIngestionServiceForTesting()
        assert isinstance(service, BaseIngestionService)
        assert service.SOURCE_TYPE == DataSourceType.FILE


class TestBaseIngestionServiceDataSourceMapping:
    """Test suite for data source type to configuration key mapping."""

    @patch('app.core.config.application.AppConfig')
    def test_data_source_type_to_key_mapping(self, mock_app_config_class):
        """Test that DataSourceType enum values are correctly mapped to config keys."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_data_source_config = Mock(spec=DataSourceConfig)
        mock_data_source_config.sources = ['test_source']
        
        # Test FILE type maps to 'file' key
        mock_ingestion_config.data_sources = {'file': mock_data_source_config}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        service = ConcreteIngestionServiceForTesting()
        assert service.config == mock_data_source_config

    @patch('app.core.config.application.AppConfig')
    def test_error_message_includes_available_types(self, mock_app_config_class):
        """Test that error message includes available data source types."""
        mock_app_config = Mock()
        mock_app_config_class.return_value = mock_app_config
        
        mock_ingestion_config = Mock()
        mock_ingestion_config.data_sources = {'confluence': Mock(), 's3': Mock()}
        mock_app_config.ingestion_config = mock_ingestion_config
        
        with pytest.raises(ValueError) as exc_info:
            ConcreteIngestionServiceForTesting()
        
        error_msg = str(exc_info.value)
        assert "No configuration found for data source type: file" in error_msg
        assert "Available types: ['confluence', 's3']" in error_msg
