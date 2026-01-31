"""
Pydantic models for structured LLM outputs.

This module defines structured output formats for LLM responses
to ensure consistent, type-safe data handling across the application.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field

# Import from constants which re-exports the enums
from app.core.constants import DataSourceType


class LLMOutputBase(BaseModel):
    """Base class for all structured LLM outputs."""
    success: bool = True
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        extra = "allow"
        validate_assignment = True


# ============================================================================
# CHAT & CONVERSATION OUTPUTS
# ============================================================================

class AgentThinking(LLMOutputBase):
    """For agent reasoning and tool selection."""
    thought_process: str = Field(..., description="Agent's reasoning process")
    selected_action: Literal["respond", "use_tool", "ask_clarification", "escalate"] = Field(
        ..., description="Action the agent decided to take"
    )
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Confidence in the decision")
    requires_approval: bool = Field(default=False, description="Whether action needs approval")
    tool_selection: Optional[str] = Field(None, description="Selected tool name if any")
    tool_parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for tool")
    risk_assessment: Literal["low", "medium", "high"] = Field(default="low")
    fallback_plan: Optional[str] = Field(None, description="Alternative approach if primary fails")

    class Config:
        json_schema_extra = {
            "example": {
                "thought_process": "User is asking about database connection. I need to check system status first.",
                "selected_action": "use_tool",
                "confidence_level": 0.85,
                "requires_approval": False,
                "tool_selection": "database_health_check",
                "tool_parameters": {"connection_type": "postgres"},
                "risk_assessment": "low",
                "success": True
            }
        }


class ChatAgentResponse(LLMOutputBase):
    """Enhanced response for chat agents."""
    response_text: str = Field(..., description="The agent's response to the user")
    response_type: Literal["direct_answer", "tool_result", "clarification", "error"] = Field(
        ..., description="Type of response provided"
    )
    session_context_used: bool = Field(default=False, description="Whether session history was used")
    tools_invoked: List[str] = Field(default_factory=list, description="List of tools used")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    needs_human_intervention: bool = Field(default=False, description="Whether human help is needed")
    context_relevance: float = Field(default=0.0, ge=0.0, le=1.0, description="How relevant is the context")
    user_intent: Optional[str] = Field(None, description="Detected user intent")
    sentiment: Literal["positive", "negative", "neutral"] = Field(default="neutral")

    class Config:
        json_schema_extra = {
            "example": {
                "response_text": "Your database connection is healthy. All tables are accessible.",
                "response_type": "tool_result",
                "session_context_used": True,
                "tools_invoked": ["database_health_check"],
                "follow_up_suggestions": ["Would you like to check specific table status?"],
                "needs_human_intervention": False,
                "context_relevance": 0.9,
                "user_intent": "system_health_check",
                "sentiment": "neutral",
                "success": True
            }
        }


# ============================================================================
# DATA INGESTION OUTPUTS
# ============================================================================

class IngestionAnalysis(LLMOutputBase):
    """For analyzing documents during ingestion."""
    content_type: Literal["text", "structured", "image", "mixed"] = Field(
        ..., description="Type of content detected"
    )
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Content quality assessment")
    key_topics: List[str] = Field(default_factory=list, description="Main topics identified")
    document_summary: str = Field(..., description="Brief summary of the document")
    suggested_tags: List[str] = Field(default_factory=list, description="Suggested metadata tags")
    chunk_strategy: Literal["semantic", "fixed", "paragraph", "sentence"] = Field(
        default="semantic", description="Recommended chunking strategy"
    )
    language_detected: str = Field(default="en", description="Detected language code")
    complexity_level: Literal["low", "medium", "high"] = Field(default="medium")
    estimated_tokens: Optional[int] = Field(None, description="Estimated token count")

    class Config:
        json_schema_extra = {
            "example": {
                "content_type": "structured",
                "quality_score": 0.85,
                "key_topics": ["API documentation", "authentication", "rate limiting"],
                "document_summary": "Technical documentation covering API authentication methods and rate limiting policies.",
                "suggested_tags": ["technical", "api", "documentation", "auth"],
                "chunk_strategy": "semantic",
                "language_detected": "en",
                "complexity_level": "medium",
                "estimated_tokens": 1250,
                "success": True
            }
        }


class DataSourceProcessing(LLMOutputBase):
    """For processing different data sources."""
    source_type: DataSourceType = Field(..., description="Type of data source")
    processed_items: int = Field(default=0, description="Number of items processed")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Processing success rate")
    extraction_method: str = Field(..., description="Method used for data extraction")
    detected_format: str = Field(..., description="Detected file/data format")
    preprocessing_steps: List[str] = Field(default_factory=list, description="Steps taken during preprocessing")
    error_summary: Optional[str] = Field(None, description="Summary of any errors encountered")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")

    class Config:
        json_schema_extra = {
            "example": {
                "source_type": "confluence",
                "processed_items": 45,
                "success_rate": 0.91,
                "extraction_method": "confluence_api_v2",
                "detected_format": "html_with_attachments",
                "preprocessing_steps": ["html_cleaning", "link_resolution", "attachment_extraction"],
                "error_summary": "4 pages had permission issues",
                "recommendations": ["Check page permissions", "Update API credentials"],
                "success": True
            }
        }


# ============================================================================
# SYSTEM MONITORING OUTPUTS
# ============================================================================

class SystemDiagnostics(LLMOutputBase):
    """For system health analysis."""
    component_status: Dict[str, str] = Field(default_factory=dict, description="Status of system components")
    performance_metrics: Dict[str, float] = Field(default_factory=dict, description="Performance measurements")
    recommendations: List[str] = Field(default_factory=list, description="System improvement recommendations")
    alert_level: Literal["green", "yellow", "red"] = Field(default="green", description="System alert level")
    resource_usage: Dict[str, float] = Field(default_factory=dict, description="Resource usage statistics")
    bottlenecks: List[str] = Field(default_factory=list, description="Identified bottlenecks")
    uptime_status: Optional[str] = Field(None, description="System uptime information")

    class Config:
        json_schema_extra = {
            "example": {
                "component_status": {
                    "database": "healthy",
                    "redis": "healthy", 
                    "celery": "healthy",
                    "api": "healthy"
                },
                "performance_metrics": {
                    "response_time_ms": 145.5,
                    "cpu_usage": 0.25,
                    "memory_usage": 0.68
                },
                "recommendations": ["Consider adding database index", "Monitor memory usage"],
                "alert_level": "green",
                "resource_usage": {"cpu": 0.25, "memory": 0.68, "disk": 0.45},
                "bottlenecks": [],
                "uptime_status": "99.9% (7 days)",
                "success": True
            }
        }


# ============================================================================
# SESSION MANAGEMENT OUTPUTS
# ============================================================================

class SessionAnalysis(LLMOutputBase):
    """For analyzing chat sessions."""
    session_summary: str = Field(..., description="Summary of the conversation")
    conversation_topics: List[str] = Field(default_factory=list, description="Topics discussed")
    user_satisfaction: Literal["high", "medium", "low", "unknown"] = Field(
        default="unknown", description="Estimated user satisfaction"
    )
    resolution_status: Literal["resolved", "ongoing", "escalated"] = Field(
        default="ongoing", description="Status of user's issue"
    )
    key_insights: List[str] = Field(default_factory=list, description="Important insights from conversation")
    interaction_quality: float = Field(default=0.0, ge=0.0, le=1.0, description="Quality of interactions")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested follow-up actions")
    escalation_needed: bool = Field(default=False, description="Whether escalation is recommended")

    class Config:
        json_schema_extra = {
            "example": {
                "session_summary": "User asked about API rate limits and received comprehensive information with examples.",
                "conversation_topics": ["API rate limiting", "authentication", "error handling"],
                "user_satisfaction": "high",
                "resolution_status": "resolved",
                "key_insights": ["User is implementing new API client", "Needs rate limit best practices"],
                "interaction_quality": 0.92,
                "suggested_actions": ["Provide API client examples", "Send rate limit monitoring guide"],
                "escalation_needed": False,
                "success": True
            }
        }


# ============================================================================
# ENHANCED LLM RESPONSE WRAPPER
# ============================================================================

class StructuredLLMResponse(BaseModel):
    """Enhanced LLM response with structured output."""
    content: str = Field(..., description="Raw LLM response content")
    structured_output: Optional[LLMOutputBase] = Field(None, description="Parsed structured output")
    usage: Dict[str, Any] = Field(default_factory=dict, description="Token usage information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    model_name: str = Field(..., description="Name of the model used")
    provider: str = Field(..., description="LLM provider used")
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time_ms: Optional[float] = Field(None, description="Response generation time")

    class Config:
        extra = "allow"
        json_schema_extra = {
            "example": {
                "content": "Based on my analysis, your system is running smoothly...",
                "structured_output": None,
                "usage": {"input_tokens": 150, "output_tokens": 75, "total_tokens": 225},
                "metadata": {"temperature": 0.7, "max_tokens": 1000},
                "model_name": "llama-3.3-70b-versatile",
                "provider": "groq",
                "processing_time_ms": 1250.5
            }
        }

    def get_structured_data(self, output_class) -> Optional[LLMOutputBase]:
        """Extract structured data of specific type."""
        if isinstance(self.structured_output, output_class):
            return self.structured_output
        return None

    def has_structured_output(self) -> bool:
        """Check if response contains structured output."""
        return self.structured_output is not None
