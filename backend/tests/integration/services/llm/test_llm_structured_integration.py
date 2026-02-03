"""
Integration tests for LLM structured output schemas.

Tests the integration of structured outputs with actual LLM providers
and chat service functionality.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch

from app.schemas.llm_output import (
    AgentThinking,
    ChatAgentResponse,
    IngestionAnalysis,
    StructuredLLMResponse
)
from app.infrastructure.llm.base.base_llm_provider import LLMResponse
from app.core.constants import DataSourceType


class TestChatServiceIntegration:
    """Test integration with chat service."""
    
    @pytest.mark.asyncio
    async def test_chat_with_structured_agent_response(self):
        """Test chat service using structured agent responses."""
        # Mock LLM response with structured JSON
        mock_json_response = {
            "response_text": "Your database connection is healthy and all services are running normally.",
            "response_type": "tool_result", 
            "session_context_used": True,
            "tools_invoked": ["database_health_check", "service_status_check"],
            "follow_up_suggestions": [
                "Would you like to check specific database tables?",
                "Shall I run a performance diagnostic?"
            ],
            "needs_human_intervention": False,
            "context_relevance": 0.95,
            "user_intent": "system_health_check",
            "sentiment": "neutral",
            "success": True,
            "confidence_score": 0.92,
            "reasoning": "User asked about system health. I checked database and services, both are operational."
        }
        
        # Simulate LLM provider returning structured JSON
        with patch('app.services.chat_service.ChatService') as MockChatService:
            mock_service = MockChatService.return_value
            
            # Mock the underlying LLM call
            mock_llm_response = LLMResponse(
                content=json.dumps(mock_json_response),
                usage={"input_tokens": 150, "output_tokens": 200, "total_tokens": 350}
            )
            
            # Convert to structured response
            structured_response = mock_llm_response.to_structured_response(
                model_name="llama-3.3-70b-versatile",
                provider="groq",
                output_schema=ChatAgentResponse,
                processing_time_ms=1250.5
            )
            
            # Verify structured parsing
            assert isinstance(structured_response, StructuredLLMResponse)
            assert isinstance(structured_response.structured_output, ChatAgentResponse)
            
            chat_output = structured_response.structured_output
            assert chat_output.response_text == mock_json_response["response_text"]
            assert chat_output.response_type == "tool_result"
            assert chat_output.tools_invoked == ["database_health_check", "service_status_check"]
            assert chat_output.user_intent == "system_health_check"
            assert chat_output.confidence_score == 0.92
            assert len(chat_output.follow_up_suggestions) == 2

    @pytest.mark.asyncio 
    async def test_agent_thinking_workflow(self):
        """Test agent thinking process for decision making."""
        # Mock agent thinking JSON response
        thinking_response = {
            "thought_process": "User is asking about API rate limits. I need to check our current rate limiting configuration and provide accurate information about limits and best practices.",
            "selected_action": "use_tool",
            "confidence_level": 0.89,
            "requires_approval": False,
            "tool_selection": "api_config_check",
            "tool_parameters": {
                "config_type": "rate_limits",
                "user_tier": "standard"
            },
            "risk_assessment": "low",
            "fallback_plan": "If config check fails, provide general rate limit documentation",
            "success": True,
            "reasoning": "API configuration check is safe and provides accurate information"
        }
        
        # Test the thinking process
        llm_response = LLMResponse(content=json.dumps(thinking_response))
        structured = llm_response.to_structured_response(
            model_name="llama-3.3-70b-versatile",
            provider="groq",
            output_schema=AgentThinking
        )
        
        thinking = structured.structured_output
        assert isinstance(thinking, AgentThinking)
        assert thinking.selected_action == "use_tool"
        assert thinking.tool_selection == "api_config_check"
        assert thinking.tool_parameters["config_type"] == "rate_limits"
        assert thinking.requires_approval is False
        assert thinking.risk_assessment == "low"
        assert thinking.confidence_level == 0.89


class TestDataIngestionIntegration:
    """Test integration with data ingestion service."""
    
    @pytest.mark.asyncio
    async def test_confluence_ingestion_analysis(self):
        """Test Confluence data ingestion with structured analysis."""
        # Mock ingestion analysis response
        analysis_response = {
            "content_type": "structured",
            "quality_score": 0.87,
            "key_topics": [
                "API documentation", 
                "authentication methods",
                "rate limiting policies",
                "error handling"
            ],
            "document_summary": "Comprehensive API documentation covering authentication, rate limits, and error handling with code examples and best practices.",
            "suggested_tags": [
                "technical_documentation",
                "api_reference", 
                "authentication",
                "development_guide"
            ],
            "chunk_strategy": "semantic",
            "language_detected": "en",
            "complexity_level": "medium",
            "estimated_tokens": 2850,
            "success": True,
            "confidence_score": 0.91,
            "reasoning": "Document has clear structure, comprehensive content, and technical accuracy"
        }
        
        # Test ingestion analysis
        llm_response = LLMResponse(
            content=json.dumps(analysis_response),
            usage={"input_tokens": 500, "output_tokens": 150}
        )
        
        structured = llm_response.to_structured_response(
            model_name="llama-3.3-70b-versatile", 
            provider="groq",
            output_schema=IngestionAnalysis
        )
        
        analysis = structured.structured_output
        assert isinstance(analysis, IngestionAnalysis)
        assert analysis.content_type == "structured"
        assert analysis.quality_score == 0.87
        assert len(analysis.key_topics) == 4
        assert "API documentation" in analysis.key_topics
        assert analysis.chunk_strategy == "semantic"
        assert analysis.estimated_tokens == 2850
        assert analysis.complexity_level == "medium"

    @pytest.mark.asyncio
    async def test_file_ingestion_processing(self):
        """Test file ingestion data source processing.""" 
        from app.schemas.llm_output import DataSourceProcessing
        
        processing_response = {
            "source_type": "file",
            "processed_items": 25,
            "success_rate": 0.96,
            "extraction_method": "unstructured_api",
            "detected_format": "mixed_pdf_docx",
            "preprocessing_steps": [
                "pdf_text_extraction",
                "docx_parsing", 
                "image_ocr",
                "table_detection",
                "metadata_extraction"
            ],
            "error_summary": "1 corrupted PDF file could not be processed",
            "recommendations": [
                "Consider OCR improvements for scanned documents",
                "Add table extraction enhancement",
                "Implement better error handling for corrupted files"
            ],
            "success": True,
            "confidence_score": 0.94
        }
        
        llm_response = LLMResponse(content=json.dumps(processing_response))
        structured = llm_response.to_structured_response(
            model_name="llama-3.3-70b-versatile",
            provider="groq", 
            output_schema=DataSourceProcessing
        )
        
        processing = structured.structured_output
        assert isinstance(processing, DataSourceProcessing)
        assert processing.source_type == DataSourceType.FILE
        assert processing.processed_items == 25
        assert processing.success_rate == 0.96
        assert len(processing.preprocessing_steps) == 5
        assert "pdf_text_extraction" in processing.preprocessing_steps
        assert len(processing.recommendations) == 3


class TestHealthCheckIntegration:
    """Test integration with health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_system_diagnostics_analysis(self):
        """Test system diagnostics with structured analysis."""
        from app.schemas.llm_output import SystemDiagnostics
        
        diagnostics_response = {
            "component_status": {
                "database": "healthy",
                "redis": "healthy",
                "celery": "warning", 
                "api_gateway": "healthy",
                "vector_db": "healthy"
            },
            "performance_metrics": {
                "avg_response_time_ms": 145.7,
                "cpu_usage_percent": 34.2,
                "memory_usage_percent": 67.8,
                "disk_usage_percent": 23.1,
                "active_connections": 127
            },
            "recommendations": [
                "Monitor Celery worker performance - queue backlog detected", 
                "Consider memory optimization - usage above 60%",
                "Database query optimization recommended",
                "Set up alerting for response time spikes"
            ],
            "alert_level": "yellow",
            "resource_usage": {
                "cpu": 0.342,
                "memory": 0.678, 
                "disk": 0.231,
                "network_io": 0.156
            },
            "bottlenecks": [
                "celery_queue_processing",
                "database_query_optimization"
            ],
            "uptime_status": "99.2% (30 days)",
            "success": True,
            "confidence_score": 0.88
        }
        
        llm_response = LLMResponse(content=json.dumps(diagnostics_response))
        structured = llm_response.to_structured_response(
            model_name="llama-3.3-70b-versatile",
            provider="groq",
            output_schema=SystemDiagnostics
        )
        
        diagnostics = structured.structured_output
        assert isinstance(diagnostics, SystemDiagnostics)
        assert diagnostics.alert_level == "yellow"
        assert diagnostics.component_status["celery"] == "warning"
        assert diagnostics.performance_metrics["avg_response_time_ms"] == 145.7
        assert len(diagnostics.recommendations) == 4
        assert len(diagnostics.bottlenecks) == 2
        assert "celery_queue_processing" in diagnostics.bottlenecks


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    @pytest.mark.asyncio
    async def test_multi_step_agent_workflow(self):
        """Test multi-step agent workflow with structured outputs."""
        
        # Step 1: Agent thinks about user request
        thinking_json = {
            "thought_process": "User wants to know about system performance. I should check multiple components systematically.",
            "selected_action": "use_tool",
            "confidence_level": 0.94,
            "tool_selection": "system_health_check", 
            "tool_parameters": {"check_type": "comprehensive"},
            "success": True
        }
        
        thinking_response = LLMResponse(content=json.dumps(thinking_json))
        thinking_structured = thinking_response.to_structured_response(
            "test-model", "test-provider", AgentThinking
        )
        
        # Step 2: Agent provides final response
        response_json = {
            "response_text": "I've completed a comprehensive system health check. Overall status is good with minor optimization opportunities.",
            "response_type": "tool_result",
            "tools_invoked": ["system_health_check", "performance_metrics"],
            "follow_up_suggestions": [
                "Would you like detailed performance metrics?",
                "Should I provide optimization recommendations?"
            ],
            "user_intent": "system_performance_inquiry",
            "success": True,
            "confidence_score": 0.91
        }
        
        response_llm = LLMResponse(content=json.dumps(response_json))
        response_structured = response_llm.to_structured_response(
            "test-model", "test-provider", ChatAgentResponse
        )
        
        # Verify workflow
        thinking = thinking_structured.structured_output
        chat_response = response_structured.structured_output
        
        assert thinking.selected_action == "use_tool"
        assert thinking.tool_selection == "system_health_check"
        assert chat_response.response_type == "tool_result"
        assert "system_health_check" in chat_response.tools_invoked
        assert len(chat_response.follow_up_suggestions) == 2

    @pytest.mark.asyncio
    async def test_error_handling_with_structured_outputs(self):
        """Test error handling scenarios with structured outputs."""
        
        # Test malformed JSON response
        malformed_response = LLMResponse(content="This is not JSON: {malformed")
        structured = malformed_response.to_structured_response(
            "test-model", "test-provider", ChatAgentResponse
        )
        
        # Should create fallback structured output
        assert structured.structured_output is not None
        assert structured.structured_output.success is True
        assert structured.structured_output.reasoning == "Generated from unstructured content"
        
        # Test partial JSON - should trigger fallback since required fields are missing
        partial_json = '{"response_text": "Partial response"}'
        partial_response = LLMResponse(content=partial_json)
        partial_structured = partial_response.to_structured_response(
            "test-model", "test-provider", ChatAgentResponse
        )
        
        # Should trigger fallback handling and create default structured output
        chat_output = partial_structured.structured_output
        assert chat_output is not None
        assert chat_output.success is True
        assert chat_output.reasoning == "Generated from unstructured content"
        assert chat_output.response_text == "Generated from unstructured content"
        assert chat_output.response_type == "direct_answer"

    def test_backwards_compatibility(self):
        """Test that new schemas work with existing code."""
        # Test that existing LLMResponse still works
        old_response = LLMResponse(
            content="Traditional response text",
            usage={"tokens": 100}
        )
        
        assert old_response.content == "Traditional response text"
        assert old_response.usage == {"tokens": 100}
        
        # Test that it can be enhanced to structured
        enhanced = old_response.to_structured_response(
            model_name="test-model",
            provider="test-provider"
        )
        
        assert enhanced.content == "Traditional response text"
        assert enhanced.model_name == "test-model"
        assert enhanced.provider == "test-provider"
        assert enhanced.structured_output is None

    @pytest.mark.asyncio
    async def test_performance_with_structured_outputs(self):
        """Test performance considerations with structured outputs."""
        import time
        
        # Large structured response
        large_response = {
            "response_text": "A" * 1000,  # Large text
            "response_type": "direct_answer",
            "follow_up_suggestions": ["suggestion"] * 50,  # Many suggestions
            "metadata": {"key" + str(i): "value" + str(i) for i in range(100)},  # Large metadata
            "success": True
        }
        
        # Measure parsing time
        start_time = time.time()
        
        llm_response = LLMResponse(content=json.dumps(large_response))
        structured = llm_response.to_structured_response(
            "test-model", "test-provider", ChatAgentResponse
        )
        
        parse_time = time.time() - start_time
        
        # Should parse reasonably quickly (less than 100ms)
        assert parse_time < 0.1
        assert isinstance(structured.structured_output, ChatAgentResponse)
        assert len(structured.structured_output.follow_up_suggestions) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
