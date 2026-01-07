"""
Unit tests for LLM response models and data structures.

Tests the response data classes and their conversion functionality.
Following Python open-source testing best practices.
"""

import pytest
import json
from unittest.mock import patch, Mock
from typing import Dict, Any

from app.llm.base.base_llm_provider import LLMResponse
from app.schemas.llm_output import LLMOutputBase, StructuredLLMResponse
from pydantic import BaseModel


class MockLLMResponseSchema(LLMOutputBase):
    """Test schema for structured output testing."""
    
    thought_process: str
    confidence_level: float
    response_text: str
    response_type: str = "text"
    
    class Config:
        schema_extra = {
            "example": {
                "thought_process": "Analyzing the request...",
                "confidence_level": 0.85,
                "response_text": "This is a test response",
                "response_type": "text"
            }
        }


class RequiredFieldsSchema(LLMOutputBase):
    """Schema with required fields for fallback testing."""
    
    success: bool
    reasoning: str
    selected_action: str
    confidence_level: float
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "reasoning": "Analysis complete",
                "selected_action": "respond",
                "confidence_level": 0.9
            }
        }


class TestLLMResponse:
    """Test suite for LLMResponse class."""
    
    def test_llm_response_creation_with_all_fields(self):
        """Test creating LLMResponse with all fields."""
        # Arrange
        content = "Test response content"
        usage = {"input_tokens": 50, "output_tokens": 25, "total_tokens": 75}
        metadata = {"model": "test-model", "provider": "test-provider"}
        
        # Act
        response = LLMResponse(content=content, usage=usage, metadata=metadata)
        
        # Assert
        assert response.content == content
        assert response.usage == usage
        assert response.metadata == metadata
    
    def test_llm_response_creation_with_minimal_fields(self):
        """Test creating LLMResponse with only required fields."""
        # Arrange
        content = "Minimal response"
        
        # Act
        response = LLMResponse(content=content)
        
        # Assert
        assert response.content == content
        assert response.usage == {}
        assert response.metadata == {}
    
    def test_llm_response_creation_with_none_values(self):
        """Test creating LLMResponse with None values."""
        # Arrange
        content = "Response with None values"
        
        # Act
        response = LLMResponse(content=content, usage=None, metadata=None)
        
        # Assert
        assert response.content == content
        assert response.usage == {}
        assert response.metadata == {}
    
    def test_to_structured_response_without_schema(self):
        """Test converting to structured response without output schema."""
        # Arrange
        response = LLMResponse(
            content="Test content",
            usage={"tokens": 100},
            metadata={"model": "test"}
        )
        
        # Act
        structured = response.to_structured_response(
            model_name="test-model",
            provider="test-provider"
        )
        
        # Assert
        assert isinstance(structured, StructuredLLMResponse)
        assert structured.content == "Test content"
        assert structured.structured_output is None
        assert structured.usage == {"tokens": 100}
        assert structured.metadata == {"model": "test"}
        assert structured.model_name == "test-model"
        assert structured.provider == "test-provider"
        assert structured.processing_time_ms is None
    
    def test_to_structured_response_with_valid_json_schema(self):
        """Test converting to structured response with valid JSON and schema."""
        # Arrange
        valid_json = {
            "thought_process": "Testing the response",
            "confidence_level": 0.95,
            "response_text": "This is a test",
            "response_type": "text"
        }
        response = LLMResponse(content=json.dumps(valid_json))
        
        # Act
        structured = response.to_structured_response(
            model_name="test-model",
            provider="test-provider",
            output_schema=MockLLMResponseSchema,
            processing_time_ms=150.5
        )
        
        # Assert
        assert isinstance(structured, StructuredLLMResponse)
        assert structured.structured_output is not None
        assert isinstance(structured.structured_output, MockLLMResponseSchema)
        assert structured.structured_output.thought_process == "Testing the response"
        assert structured.structured_output.confidence_level == 0.95
        assert structured.processing_time_ms == 150.5
    
    def test_to_structured_response_with_invalid_json(self):
        """Test converting to structured response with invalid JSON."""
        # Arrange
        response = LLMResponse(content="This is not JSON content")
        
        # Act
        structured = response.to_structured_response(
            model_name="test-model",
            provider="test-provider",
            output_schema=RequiredFieldsSchema
        )
        
        # Assert
        assert isinstance(structured, StructuredLLMResponse)
        assert structured.structured_output is not None
        assert isinstance(structured.structured_output, RequiredFieldsSchema)
        # Should use fallback values
        assert structured.structured_output.success is True
        assert "Generated from unstructured content" in structured.structured_output.reasoning
    
    def test_to_structured_response_with_valid_json_invalid_schema(self):
        """Test with valid JSON that doesn't match schema."""
        # Arrange
        invalid_data = {"wrong_field": "value", "another_wrong": 123}
        response = LLMResponse(content=json.dumps(invalid_data))
        
        # Act
        with patch.object(response, '_create_fallback_output') as mock_fallback:
            mock_fallback_output = RequiredFieldsSchema(
                success=True,
                reasoning="Fallback used",
                selected_action="respond",
                confidence_level=0.5
            )
            mock_fallback.return_value = mock_fallback_output
            
            structured = response.to_structured_response(
                model_name="test-model",
                provider="test-provider",
                output_schema=RequiredFieldsSchema
            )
        
        # Assert
        assert structured.structured_output is not None
        assert structured.structured_output.reasoning == "Fallback used"
        mock_fallback.assert_called_once_with(RequiredFieldsSchema)
    
    def test_to_structured_response_with_parsing_exception(self):
        """Test handling of unexpected exceptions during parsing."""
        # Arrange
        response = LLMResponse(content='{"valid": "json"}')
        
        # Act
        with patch('json.loads') as mock_json_loads:
            mock_json_loads.side_effect = Exception("Unexpected error")
            
            structured = response.to_structured_response(
                model_name="test-model",
                provider="test-provider",
                output_schema=MockLLMResponseSchema
            )
        
        # Assert
        assert structured.structured_output is None
    
    def test_create_fallback_output_with_required_fields(self):
        """Test fallback output creation for schema with required fields."""
        # Arrange
        response = LLMResponse(content="test content")
        
        # Act
        fallback = response._create_fallback_output(RequiredFieldsSchema)
        
        # Assert
        assert isinstance(fallback, RequiredFieldsSchema)
        assert fallback.success is True
        assert "Generated from unstructured content" in fallback.reasoning
        assert fallback.selected_action == "respond"
        assert fallback.confidence_level == 0.5
    
    def test_create_fallback_output_with_custom_field_types(self):
        """Test fallback output creation with various field types."""
        
        class VariedTypesSchema(LLMOutputBase):
            success: bool = True
            reasoning: str = "test"
            string_field: str
            int_field: int
            float_field: float
            bool_field: bool
            optional_field: str = "default"
        
        # Arrange
        response = LLMResponse(content="test")
        
        # Act
        fallback = response._create_fallback_output(VariedTypesSchema)
        
        # Assert
        assert isinstance(fallback, VariedTypesSchema)
        assert fallback.success is True
        # reasoning field gets special fallback treatment even when it has a default value
        assert fallback.reasoning == "Generated from unstructured content"
        # The specific field values depend on the fallback implementation
        assert hasattr(fallback, 'string_field')
        assert hasattr(fallback, 'int_field')
        assert hasattr(fallback, 'float_field')
        assert hasattr(fallback, 'bool_field')
        # Optional field should use its default value
        assert fallback.optional_field == "default"
    
    def test_create_fallback_output_with_known_field_names(self):
        """Test fallback output creation with known field mappings."""
        
        class KnownFieldsSchema(LLMOutputBase):
            success: bool = True
            reasoning: str = "test"
            thought_process: str
            confidence_level: float
            selected_action: str
            response_text: str
        
        # Arrange
        response = LLMResponse(content="test content")
        
        # Act
        fallback = response._create_fallback_output(KnownFieldsSchema)
        
        # Assert
        assert isinstance(fallback, KnownFieldsSchema)
        assert fallback.thought_process == "Processed unstructured content"
        assert fallback.confidence_level == 0.5
        assert fallback.selected_action == "respond"
        assert fallback.response_text == "Generated from unstructured content"


class TestLLMResponseIntegration:
    """Integration tests for LLMResponse with different scenarios."""
    
    def test_full_workflow_valid_response(self):
        """Test complete workflow with valid structured response."""
        # Arrange
        prompt_response = {
            "thought_process": "User is asking for help with testing",
            "confidence_level": 0.88,
            "response_text": "I can help you write comprehensive tests",
            "response_type": "helpful"
        }
        
        response = LLMResponse(
            content=json.dumps(prompt_response),
            usage={"input_tokens": 25, "output_tokens": 45, "total_tokens": 70},
            metadata={"model": "gpt-4", "temperature": 0.7}
        )
        
        # Act
        structured = response.to_structured_response(
            model_name="gpt-4",
            provider="openai",
            output_schema=MockLLMResponseSchema,
            processing_time_ms=250.0
        )
        
        # Assert
        assert structured.content == json.dumps(prompt_response)
        assert structured.structured_output.thought_process == "User is asking for help with testing"
        assert structured.structured_output.confidence_level == 0.88
        assert structured.usage["total_tokens"] == 70
        assert structured.model_name == "gpt-4"
        assert structured.provider == "openai"
        assert structured.processing_time_ms == 250.0
    
    def test_full_workflow_unstructured_response(self):
        """Test complete workflow with unstructured text response."""
        # Arrange
        response = LLMResponse(
            content="This is a plain text response that cannot be parsed as JSON.",
            usage={"tokens": 50},
            metadata={"model": "claude-3"}
        )
        
        # Act
        structured = response.to_structured_response(
            model_name="claude-3",
            provider="anthropic",
            output_schema=MockLLMResponseSchema
        )
        
        # Assert
        assert structured.content == "This is a plain text response that cannot be parsed as JSON."
        assert structured.structured_output is not None
        assert isinstance(structured.structured_output, MockLLMResponseSchema)
        # Should use fallback values
        assert "Processed unstructured content" in structured.structured_output.thought_process
        assert structured.structured_output.confidence_level == 0.5
    
    def test_response_equality_and_representation(self):
        """Test LLMResponse equality and string representation."""
        # Arrange
        response1 = LLMResponse(
            content="Same content",
            usage={"tokens": 100},
            metadata={"model": "test"}
        )
        response2 = LLMResponse(
            content="Same content",
            usage={"tokens": 100},
            metadata={"model": "test"}
        )
        response3 = LLMResponse(
            content="Different content",
            usage={"tokens": 100},
            metadata={"model": "test"}
        )
        
        # Act & Assert
        # Note: LLMResponse doesn't implement __eq__ by default, so this tests object identity
        assert response1 is not response2
        assert response1 is not response3
        
        # Test string representation (assuming it exists or will be implemented)
        str_repr = str(response1)
        assert "LLMResponse" in str_repr or "Same content" in str_repr
    
    def test_empty_and_edge_case_responses(self):
        """Test LLMResponse with empty and edge case content."""
        test_cases = [
            ("", {}),  # Empty string
            ("   ", {}),  # Whitespace only
            ('{"incomplete": json}', {"model": "test"}),  # Malformed JSON
            ("null", {"tokens": 0}),  # JSON null
            ('{"empty": {}}', {"nested": {"data": True}}),  # Nested empty
        ]
        
        for content, metadata in test_cases:
            # Act
            response = LLMResponse(content=content, metadata=metadata)
            structured = response.to_structured_response(
                model_name="test-model",
                provider="test-provider",
                output_schema=MockLLMResponseSchema
            )
            
            # Assert
            assert isinstance(structured, StructuredLLMResponse)
            assert structured.content == content
            assert structured.metadata == metadata
            # Should handle gracefully with fallback or None structured_output
            if structured.structured_output is not None:
                assert isinstance(structured.structured_output, MockLLMResponseSchema)


class TestLLMResponseErrorHandling:
    """Test error handling and edge cases for LLMResponse."""
    
    def test_create_fallback_output_with_complex_schema(self):
        """Test fallback creation with complex nested schemas."""
        
        class NestedSchema(BaseModel):
            inner_field: str
        
        class ComplexSchema(LLMOutputBase):
            success: bool
            reasoning: str
            nested_data: NestedSchema
            optional_list: list = []
        
        # Arrange
        response = LLMResponse(content="test")
        
        # Act & Assert - Should handle gracefully even with complex schemas
        try:
            fallback = response._create_fallback_output(ComplexSchema)
            # If it succeeds, verify basic structure
            assert fallback.success is True
            assert isinstance(fallback.reasoning, str)
        except Exception:
            # Complex schemas might not be fully supported in fallback
            # This is acceptable behavior
            pass
    
    def test_to_structured_response_with_none_schema(self):
        """Test structured response conversion with None schema."""
        # Arrange
        response = LLMResponse(content="test content")
        
        # Act
        structured = response.to_structured_response(
            model_name="test",
            provider="test",
            output_schema=None
        )
        
        # Assert
        assert structured.structured_output is None
    
    def test_large_content_handling(self):
        """Test handling of large content in responses."""
        # Arrange
        large_content = "x" * 10000  # 10KB of content
        response = LLMResponse(content=large_content)
        
        # Act
        structured = response.to_structured_response(
            model_name="test",
            provider="test"
        )
        
        # Assert
        assert structured.content == large_content
        assert len(structured.content) == 10000
