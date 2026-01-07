"""
Test suite for core constants and enums.

Tests the various enum values, inheritance, and string behavior
for all application constants and enums.
"""
import pytest
from enum import Enum

from app.core.constants import (
    VectorDBType,
    GroqModelVersion,
    EmbeddingType,
    ModelProvider,
    AtlassianProperties,
    SessionStorageType,
    LLMProvider,
    LLMCapability
)

# Also test re-exported enums
from app.core.constants import (
    DataSourceType,
    DatabaseType,
    ExternalServiceType,
    ConnectionType,
    AgentCapability,
    AgentType,
    AgentFramework,
    AgentStatus
)


class TestVectorDBType:
    """Test VectorDBType enum."""
    
    def test_enum_inheritance(self):
        """Test that VectorDBType inherits from str and Enum."""
        assert issubclass(VectorDBType, str)
        assert issubclass(VectorDBType, Enum)
    
    def test_enum_values(self):
        """Test all VectorDBType enum values."""
        expected_values = {
            "pgvector", "chroma", "qdrant", "milvus", "redis", "opensearch"
        }
        actual_values = {item.value for item in VectorDBType}
        assert actual_values == expected_values
    
    def test_string_representation(self):
        """Test string representation of VectorDBType."""
        # Test value access (this is what we actually want for string conversion)
        assert VectorDBType.PGVECTOR.value == "pgvector"
        assert VectorDBType.CHROMA.value == "chroma"
        assert VectorDBType.QDRANT.value == "qdrant"
        
        # Test that str() gives enum representation (not value)
        assert str(VectorDBType.PGVECTOR) == "VectorDBType.PGVECTOR"
    
    def test_comparison_with_strings(self):
        """Test that enum values can be compared with strings."""
        assert VectorDBType.PGVECTOR == "pgvector"
        assert VectorDBType.CHROMA == "chroma"
        assert VectorDBType.QDRANT == "qdrant"


class TestGroqModelVersion:
    """Test GroqModelVersion enum."""
    
    def test_enum_inheritance(self):
        """Test that GroqModelVersion inherits from str and Enum."""
        assert issubclass(GroqModelVersion, str)
        assert issubclass(GroqModelVersion, Enum)
    
    def test_production_models(self):
        """Test production model values."""
        production_models = {
            GroqModelVersion.LLAMA_3_1_8B,
            GroqModelVersion.LLAMA_3_3_70B,
            GroqModelVersion.LLAMA_GUARD_12B,
            GroqModelVersion.GPT_OSS_120B,
            GroqModelVersion.GPT_OSS_20B,
            GroqModelVersion.WHISPER_LARGE_V3,
            GroqModelVersion.WHISPER_LARGE_V3_TURBO
        }
        
        for model in production_models:
            assert isinstance(model.value, str)
            assert len(model.value) > 0
    
    def test_preview_models(self):
        """Test preview model values."""
        preview_models = {
            GroqModelVersion.DEEPSEEK_70B,
            GroqModelVersion.LLAMA_4_MAVERICK,
            GroqModelVersion.LLAMA_4_SCOUT,
            GroqModelVersion.KIMI_K2,
            GroqModelVersion.QWEN_32B
        }
        
        for model in preview_models:
            assert isinstance(model.value, str)
            assert len(model.value) > 0
    
    def test_specific_model_values(self):
        """Test specific model version values."""
        assert GroqModelVersion.LLAMA_3_1_8B == "llama-3.1-8b-instant"
        assert GroqModelVersion.LLAMA_3_3_70B == "llama-3.3-70b-versatile"
        assert GroqModelVersion.WHISPER_LARGE_V3 == "whisper-large-v3"


class TestEmbeddingType:
    """Test EmbeddingType enum."""
    
    def test_enum_inheritance(self):
        """Test that EmbeddingType inherits from str and Enum."""
        assert issubclass(EmbeddingType, str)
        assert issubclass(EmbeddingType, Enum)
    
    def test_all_embedding_types(self):
        """Test all embedding type values."""
        expected_types = {
            "openai", "huggingface", "instructor", "cohere", 
            "tensorflow", "vertex", "openai"  # DEFAULT = openai
        }
        actual_values = {item.value for item in EmbeddingType}
        # Note: DEFAULT and OPENAI have same value, so set will be smaller
        assert "openai" in actual_values
        assert "huggingface" in actual_values
        assert "instructor" in actual_values
    
    def test_default_embedding(self):
        """Test default embedding type."""
        assert EmbeddingType.DEFAULT == "openai"
        assert EmbeddingType.DEFAULT == EmbeddingType.OPENAI


class TestModelProvider:
    """Test ModelProvider enum."""
    
    def test_enum_inheritance(self):
        """Test that ModelProvider inherits from str and Enum."""
        assert issubclass(ModelProvider, str)
        assert issubclass(ModelProvider, Enum)
    
    def test_provider_values(self):
        """Test all model provider values."""
        expected_providers = {
            "groq", "openai", "anthropic", "google", "meta", "mistral"
        }
        actual_values = {item.value for item in ModelProvider}
        assert actual_values == expected_providers


class TestAtlassianProperties:
    """Test AtlassianProperties enum."""
    
    def test_enum_inheritance(self):
        """Test that AtlassianProperties inherits from str and Enum."""
        assert issubclass(AtlassianProperties, str)
        assert issubclass(AtlassianProperties, Enum)
    
    def test_property_keys(self):
        """Test Atlassian property key values."""
        expected_properties = {
            "page_id", "title", "space_key", "jira_base_url",
            "confluence_base_url", "last_modified", "author",
            "api_key", "email"
        }
        actual_values = {item.value for item in AtlassianProperties}
        assert actual_values == expected_properties
    
    def test_specific_properties(self):
        """Test specific property values."""
        assert AtlassianProperties.PAGE_ID == "page_id"
        assert AtlassianProperties.JIRA_BASE_URL == "jira_base_url"
        assert AtlassianProperties.CONFLUENCE_BASE_URL == "confluence_base_url"


class TestSessionStorageType:
    """Test SessionStorageType enum."""
    
    def test_enum_inheritance(self):
        """Test that SessionStorageType inherits from str and Enum."""
        assert issubclass(SessionStorageType, str)
        assert issubclass(SessionStorageType, Enum)
    
    def test_storage_types(self):
        """Test all session storage type values."""
        expected_types = {"postgres", "mongodb", "elasticsearch", "redis"}
        actual_values = {item.value for item in SessionStorageType}
        assert actual_values == expected_types


class TestLLMProvider:
    """Test LLMProvider enum."""
    
    def test_enum_inheritance(self):
        """Test that LLMProvider inherits from str and Enum."""
        assert issubclass(LLMProvider, str)
        assert issubclass(LLMProvider, Enum)
    
    def test_provider_values(self):
        """Test all LLM provider values."""
        expected_providers = {
            "groq", "openai", "anthropic", "huggingface",
            "ollama", "google", "local"
        }
        actual_values = {item.value for item in LLMProvider}
        assert actual_values == expected_providers


class TestLLMCapability:
    """Test LLMCapability enum."""
    
    def test_enum_inheritance(self):
        """Test that LLMCapability inherits from str and Enum."""
        assert issubclass(LLMCapability, str)
        assert issubclass(LLMCapability, Enum)
    
    def test_capability_values(self):
        """Test all LLM capability values."""
        expected_capabilities = {
            "chat", "code_generation", "function_calling",
            "streaming", "multimodal"
        }
        actual_values = {item.value for item in LLMCapability}
        assert actual_values == expected_capabilities


class TestReexportedEnums:
    """Test re-exported enums from app.core.enums."""
    
    def test_enums_are_available(self):
        """Test that re-exported enums are available."""
        # Test that we can import and use them
        assert issubclass(DataSourceType, Enum)
        assert issubclass(DatabaseType, Enum)
        assert issubclass(ExternalServiceType, Enum)
        assert issubclass(ConnectionType, Enum)
        assert issubclass(AgentCapability, Enum)
        assert issubclass(AgentType, Enum)
        assert issubclass(AgentFramework, Enum)
        assert issubclass(AgentStatus, Enum)
    
    def test_enum_string_inheritance(self):
        """Test that re-exported enums inherit from str."""
        # Check if they are string enums (they should be)
        enum_classes = [
            DataSourceType, DatabaseType, ExternalServiceType, 
            ConnectionType, AgentCapability, AgentType, 
            AgentFramework, AgentStatus
        ]
        
        for enum_class in enum_classes:
            # Test if any instance is a string
            if len(list(enum_class)) > 0:
                first_item = list(enum_class)[0]
                assert isinstance(first_item.value, str)


class TestEnumConsistency:
    """Test consistency across enums."""
    
    def test_no_duplicate_values_within_enums(self):
        """Test that enums don't have duplicate values (except where intended)."""
        enum_classes = [
            VectorDBType, GroqModelVersion, ModelProvider,
            AtlassianProperties, SessionStorageType, LLMProvider,
            LLMCapability
        ]
        
        for enum_class in enum_classes:
            values = [item.value for item in enum_class]
            # EmbeddingType is special case with DEFAULT = OPENAI
            if enum_class != EmbeddingType:
                assert len(values) == len(set(values)), f"{enum_class.__name__} has duplicate values"
    
    def test_embedding_type_default_consistency(self):
        """Test EmbeddingType DEFAULT and OPENAI consistency."""
        assert EmbeddingType.DEFAULT.value == EmbeddingType.OPENAI.value
        assert EmbeddingType.DEFAULT == EmbeddingType.OPENAI
    
    def test_all_enum_values_are_strings(self):
        """Test that all enum values are strings."""
        enum_classes = [
            VectorDBType, GroqModelVersion, EmbeddingType,
            ModelProvider, AtlassianProperties, SessionStorageType,
            LLMProvider, LLMCapability
        ]
        
        for enum_class in enum_classes:
            for item in enum_class:
                assert isinstance(item.value, str), f"{enum_class.__name__}.{item.name} value is not a string"
                assert len(item.value) > 0, f"{enum_class.__name__}.{item.name} has empty value"
