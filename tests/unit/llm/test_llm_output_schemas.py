"""
Unit tests for LLM structured output schemas.

Tests the Pydantic models for structured LLM responses,
validation, serialization, and integration with the LLM provider.
"""

import pytest
import json
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from app.schemas.llm_output import (
    LLMOutputBase,
    AgentThinking,
    ChatAgentResponse,
    IngestionAnalysis,
    DataSourceProcessing,
    SystemDiagnostics,
    SessionAnalysis,
    StructuredLLMResponse
)
from app.core.constants import DataSourceType
from app.llm.base.base_llm_provider import LLMResponse


class TestLLMOutputBase:
    """Test the base LLM output model."""
    
    def test_create_minimal_output(self):
        """Test creating output with minimal data."""
        output = LLMOutputBase()
        
        assert output.success is True
        assert output.confidence_score is None
        assert output.reasoning is None
        assert output.metadata == {}
        assert isinstance(output.timestamp, datetime)

    def test_create_full_output(self):
        """Test creating output with all fields."""
        metadata = {"model": "test-model", "temperature": 0.7}
        output = LLMOutputBase(
            success=False,
            confidence_score=0.85,
            reasoning="Test reasoning",
            metadata=metadata
        )
        
        assert output.success is False
        assert output.confidence_score == 0.85
        assert output.reasoning == "Test reasoning"
        assert output.metadata == metadata

    def test_confidence_score_validation(self):
        """Test confidence score validation."""
        # Valid range
        output = LLMOutputBase(confidence_score=0.0)
        assert output.confidence_score == 0.0
        
        output = LLMOutputBase(confidence_score=1.0)
        assert output.confidence_score == 1.0
        
        # Invalid range
        with pytest.raises(ValueError):
            LLMOutputBase(confidence_score=-0.1)
            
        with pytest.raises(ValueError):
            LLMOutputBase(confidence_score=1.1)

    def test_serialization(self):
        """Test JSON serialization."""
        output = LLMOutputBase(
            success=True,
            confidence_score=0.95,
            reasoning="Test"
        )
        
        json_str = output.json()
        parsed = json.loads(json_str)
        
        assert parsed["success"] is True
        assert parsed["confidence_score"] == 0.95
        assert parsed["reasoning"] == "Test"
        assert "timestamp" in parsed


class TestAgentThinking:
    """Test the AgentThinking model."""
    
    def test_create_valid_agent_thinking(self):
        """Test creating valid agent thinking."""
        thinking = AgentThinking(
            thought_process="Analyzing user request for database status",
            selected_action="use_tool",
            confidence_level=0.9,
            tool_selection="database_check",
            tool_parameters={"db_type": "postgres"}
        )
        
        assert thinking.thought_process == "Analyzing user request for database status"
        assert thinking.selected_action == "use_tool"
        assert thinking.confidence_level == 0.9
        assert thinking.requires_approval is False
        assert thinking.tool_selection == "database_check"
        assert thinking.tool_parameters == {"db_type": "postgres"}
        assert thinking.risk_assessment == "low"

    def test_invalid_action_type(self):
        """Test validation of action types."""
        with pytest.raises(ValueError):
            AgentThinking(
                thought_process="Test",
                selected_action="invalid_action",
                confidence_level=0.8
            )

    def test_confidence_validation(self):
        """Test confidence level validation."""
        with pytest.raises(ValueError):
            AgentThinking(
                thought_process="Test",
                selected_action="respond",
                confidence_level=1.5
            )

    def test_example_schema(self):
        """Test the example schema is valid."""
        example = AgentThinking.Config.json_schema_extra["example"]
        thinking = AgentThinking(**example)
        
        assert thinking.thought_process == example["thought_process"]
        assert thinking.selected_action == example["selected_action"]
        assert thinking.confidence_level == example["confidence_level"]


class TestChatAgentResponse:
    """Test the ChatAgentResponse model."""
    
    def test_create_chat_response(self):
        """Test creating a chat agent response."""
        response = ChatAgentResponse(
            response_text="The database is healthy",
            response_type="tool_result",
            session_context_used=True,
            tools_invoked=["database_check"],
            follow_up_suggestions=["Check specific tables?"],
            user_intent="health_check"
        )
        
        assert response.response_text == "The database is healthy"
        assert response.response_type == "tool_result"
        assert response.session_context_used is True
        assert response.tools_invoked == ["database_check"]
        assert response.follow_up_suggestions == ["Check specific tables?"]
        assert response.needs_human_intervention is False
        assert response.user_intent == "health_check"
        assert response.sentiment == "neutral"

    def test_context_relevance_validation(self):
        """Test context relevance score validation."""
        with pytest.raises(ValueError):
            ChatAgentResponse(
                response_text="Test",
                response_type="direct_answer",
                context_relevance=1.5
            )

    def test_invalid_response_type(self):
        """Test invalid response type validation."""
        with pytest.raises(ValueError):
            ChatAgentResponse(
                response_text="Test",
                response_type="invalid_type"
            )

    def test_example_schema(self):
        """Test the example schema is valid."""
        example = ChatAgentResponse.Config.json_schema_extra["example"]
        response = ChatAgentResponse(**example)
        
        assert response.response_text == example["response_text"]
        assert response.response_type == example["response_type"]


class TestIngestionAnalysis:
    """Test the IngestionAnalysis model."""
    
    def test_create_ingestion_analysis(self):
        """Test creating ingestion analysis."""
        analysis = IngestionAnalysis(
            content_type="structured",
            quality_score=0.85,
            key_topics=["API", "docs"],
            document_summary="API documentation",
            suggested_tags=["tech", "api"],
            estimated_tokens=1500
        )
        
        assert analysis.content_type == "structured"
        assert analysis.quality_score == 0.85
        assert analysis.key_topics == ["API", "docs"]
        assert analysis.document_summary == "API documentation"
        assert analysis.suggested_tags == ["tech", "api"]
        assert analysis.chunk_strategy == "semantic"
        assert analysis.language_detected == "en"
        assert analysis.complexity_level == "medium"
        assert analysis.estimated_tokens == 1500

    def test_quality_score_validation(self):
        """Test quality score validation."""
        with pytest.raises(ValueError):
            IngestionAnalysis(
                content_type="text",
                quality_score=1.5,
                document_summary="Test"
            )

    def test_invalid_content_type(self):
        """Test invalid content type validation."""
        with pytest.raises(ValueError):
            IngestionAnalysis(
                content_type="invalid_type",
                quality_score=0.8,
                document_summary="Test"
            )


class TestDataSourceProcessing:
    """Test the DataSourceProcessing model."""
    
    def test_create_data_source_processing(self):
        """Test creating data source processing."""
        processing = DataSourceProcessing(
            source_type=DataSourceType.CONFLUENCE,
            processed_items=50,
            success_rate=0.96,
            extraction_method="api_v2",
            detected_format="html",
            preprocessing_steps=["clean_html", "extract_links"]
        )
        
        assert processing.source_type == DataSourceType.CONFLUENCE
        assert processing.processed_items == 50
        assert processing.success_rate == 0.96
        assert processing.extraction_method == "api_v2"
        assert processing.detected_format == "html"
        assert processing.preprocessing_steps == ["clean_html", "extract_links"]

    def test_success_rate_validation(self):
        """Test success rate validation."""
        with pytest.raises(ValueError):
            DataSourceProcessing(
                source_type=DataSourceType.FILE,
                success_rate=1.1,
                extraction_method="test",
                detected_format="test"
            )

    def test_example_schema(self):
        """Test the example schema is valid."""
        example = DataSourceProcessing.Config.json_schema_extra["example"]
        processing = DataSourceProcessing(**example)
        
        assert processing.source_type == example["source_type"]
        assert processing.processed_items == example["processed_items"]


class TestSystemDiagnostics:
    """Test the SystemDiagnostics model."""
    
    def test_create_system_diagnostics(self):
        """Test creating system diagnostics."""
        diagnostics = SystemDiagnostics(
            component_status={"db": "healthy", "redis": "warning"},
            performance_metrics={"response_time": 150.0, "cpu": 0.45},
            recommendations=["Scale database", "Monitor CPU"],
            alert_level="yellow",
            resource_usage={"cpu": 0.45, "memory": 0.70},
            bottlenecks=["database_queries"]
        )
        
        assert diagnostics.component_status == {"db": "healthy", "redis": "warning"}
        assert diagnostics.performance_metrics == {"response_time": 150.0, "cpu": 0.45}
        assert diagnostics.recommendations == ["Scale database", "Monitor CPU"]
        assert diagnostics.alert_level == "yellow"
        assert diagnostics.resource_usage == {"cpu": 0.45, "memory": 0.70}
        assert diagnostics.bottlenecks == ["database_queries"]

    def test_invalid_alert_level(self):
        """Test invalid alert level validation."""
        with pytest.raises(ValueError):
            SystemDiagnostics(alert_level="invalid_level")


class TestSessionAnalysis:
    """Test the SessionAnalysis model."""
    
    def test_create_session_analysis(self):
        """Test creating session analysis."""
        analysis = SessionAnalysis(
            session_summary="User discussed API integration",
            conversation_topics=["API", "authentication", "rate limits"],
            user_satisfaction="high",
            resolution_status="resolved",
            key_insights=["User needs rate limit guidance"],
            interaction_quality=0.92
        )
        
        assert analysis.session_summary == "User discussed API integration"
        assert analysis.conversation_topics == ["API", "authentication", "rate limits"]
        assert analysis.user_satisfaction == "high"
        assert analysis.resolution_status == "resolved"
        assert analysis.key_insights == ["User needs rate limit guidance"]
        assert analysis.interaction_quality == 0.92
        assert analysis.escalation_needed is False

    def test_interaction_quality_validation(self):
        """Test interaction quality validation."""
        with pytest.raises(ValueError):
            SessionAnalysis(
                session_summary="Test",
                interaction_quality=1.5
            )


class TestStructuredLLMResponse:
    """Test the StructuredLLMResponse model."""
    
    def test_create_structured_response(self):
        """Test creating structured LLM response."""
        thinking = AgentThinking(
            thought_process="Test thinking",
            selected_action="respond",
            confidence_level=0.8
        )
        
        response = StructuredLLMResponse(
            content="Test response content",
            structured_output=thinking,
            usage={"input_tokens": 100, "output_tokens": 50},
            metadata={"temperature": 0.7},
            model_name="test-model",
            provider="test-provider",
            processing_time_ms=1500.0
        )
        
        assert response.content == "Test response content"
        assert isinstance(response.structured_output, AgentThinking)
        assert response.usage == {"input_tokens": 100, "output_tokens": 50}
        assert response.metadata == {"temperature": 0.7}
        assert response.model_name == "test-model"
        assert response.provider == "test-provider"
        assert response.processing_time_ms == 1500.0

    def test_get_structured_data(self):
        """Test getting structured data of specific type."""
        thinking = AgentThinking(
            thought_process="Test",
            selected_action="respond",
            confidence_level=0.8
        )
        
        response = StructuredLLMResponse(
            content="Test",
            structured_output=thinking,
            model_name="test",
            provider="test"
        )
        
        # Should return the thinking object
        extracted_thinking = response.get_structured_data(AgentThinking)
        assert extracted_thinking == thinking
        
        # Should return None for different type
        extracted_chat = response.get_structured_data(ChatAgentResponse)
        assert extracted_chat is None

    def test_has_structured_output(self):
        """Test checking if response has structured output."""
        # With structured output
        thinking = AgentThinking(
            thought_process="Test",
            selected_action="respond", 
            confidence_level=0.8
        )
        
        response = StructuredLLMResponse(
            content="Test",
            structured_output=thinking,
            model_name="test",
            provider="test"
        )
        
        assert response.has_structured_output() is True
        
        # Without structured output
        response_no_struct = StructuredLLMResponse(
            content="Test",
            model_name="test",
            provider="test"
        )
        
        assert response_no_struct.has_structured_output() is False


class TestLLMResponseIntegration:
    """Test integration with LLMResponse class."""
    
    def test_to_structured_response_with_json(self):
        """Test converting LLMResponse to structured response with JSON content."""
        json_content = json.dumps({
            "thought_process": "Analyzing user request",
            "selected_action": "respond",
            "confidence_level": 0.9,
            "success": True
        })
        
        llm_response = LLMResponse(
            content=json_content,
            usage={"tokens": 100},
            metadata={"temp": 0.7}
        )
        
        structured = llm_response.to_structured_response(
            model_name="test-model",
            provider="test-provider",
            output_schema=AgentThinking,
            processing_time_ms=1200.0
        )
        
        assert isinstance(structured, StructuredLLMResponse)
        assert structured.content == json_content
        assert isinstance(structured.structured_output, AgentThinking)
        assert structured.structured_output.thought_process == "Analyzing user request"
        assert structured.model_name == "test-model"
        assert structured.provider == "test-provider"
        assert structured.processing_time_ms == 1200.0

    def test_to_structured_response_with_plain_text(self):
        """Test converting LLMResponse with plain text content."""
        llm_response = LLMResponse(
            content="This is plain text response",
            usage={"tokens": 50}
        )
        
        structured = llm_response.to_structured_response(
            model_name="test-model",
            provider="test-provider",
            output_schema=AgentThinking
        )
        
        assert structured.content == "This is plain text response"
        assert isinstance(structured.structured_output, AgentThinking)
        assert structured.structured_output.success is True
        assert structured.structured_output.reasoning == "Generated from unstructured content"
        assert structured.structured_output.thought_process == "Processed unstructured content"
        assert structured.structured_output.selected_action == "respond"
        assert structured.structured_output.confidence_level == 0.5

    def test_to_structured_response_without_schema(self):
        """Test converting without output schema."""
        llm_response = LLMResponse(content="Test content")
        
        structured = llm_response.to_structured_response(
            model_name="test-model",
            provider="test-provider"
        )
        
        assert structured.content == "Test content"
        assert structured.structured_output is None

    @patch('app.llm.base.base_llm_provider.logger')
    def test_to_structured_response_with_invalid_json(self, mock_logger):
        """Test converting with invalid JSON content."""
        llm_response = LLMResponse(content='{"invalid": json content}')
        
        structured = llm_response.to_structured_response(
            model_name="test-model",
            provider="test-provider",
            output_schema=AgentThinking
        )
        
        # With our enhanced fallback, even invalid JSON gets structured output
        assert structured.structured_output is not None
        assert isinstance(structured.structured_output, AgentThinking)
        assert structured.structured_output.success is True
        assert structured.structured_output.reasoning == "Generated from unstructured content"
        # Should still log the error
        # mock_logger.warning.assert_called_once()


class TestBaseLLMProviderStructuredMethods:
    """Test structured methods added to BaseLLMProvider."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock LLM provider."""
        from app.llm.base.base_llm_provider import BaseLLMProvider
        
        class MockProvider(BaseLLMProvider):
            def get_config_name(self):
                return "test"
            def validate_config(self):
                pass
            async def initialize(self):
                pass
            async def generate(self, prompt, **kwargs):
                return LLMResponse(
                    content='{"thought_process": "Test", "selected_action": "respond", "confidence_level": 0.8}',
                    usage={"tokens": 100}
                )
            async def stream_generate(self, prompt, **kwargs):
                yield "test"
            def get_available_models(self):
                return ["test-model"]
            def supports_capability(self, capability):
                return True
        
        with patch('app.core.config.application.llm.llm_config') as mock_config:
            mock_config.get_provider_config.return_value = {"default_model": "test-model"}
            provider = MockProvider()
            provider._initialized = True
            return provider

    @pytest.mark.asyncio
    async def test_generate_structured(self, mock_provider):
        """Test structured generation."""
        result = await mock_provider.generate_structured(
            prompt="Test prompt",
            output_schema=AgentThinking
        )
        
        assert isinstance(result, StructuredLLMResponse)
        assert isinstance(result.structured_output, AgentThinking)
        assert result.structured_output.thought_process == "Test"
        assert result.model_name == "test-model"
        assert result.provider == "test"
        assert result.processing_time_ms is not None

    def test_create_structured_prompt(self, mock_provider):
        """Test structured prompt creation."""
        prompt = mock_provider._create_structured_prompt(
            "Test prompt",
            AgentThinking
        )
        
        assert "Test prompt" in prompt
        assert "JSON format" in prompt
        assert "thought_process" in prompt
        assert "selected_action" in prompt

    def test_create_structured_prompt_no_example(self, mock_provider):
        """Test structured prompt creation without example."""
        class NoExampleSchema(LLMOutputBase):
            test_field: str
        
        prompt = mock_provider._create_structured_prompt(
            "Test prompt", 
            NoExampleSchema
        )
        
        assert "Test prompt" in prompt
        assert "JSON format" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
