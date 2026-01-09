"""
Example demonstrating structured LLM outputs with Groq provider.

This example shows how to use the new structured output schemas
with your existing LLM providers for enhanced agent capabilities.
"""

import asyncio
import json
from typing import Dict, Any

from app.schemas.llm_output import (
    AgentThinking,
    ChatAgentResponse,
    IngestionAnalysis,
    SystemDiagnostics,
    StructuredLLMResponse
)
from app.llm.factory.llm_factory import LLMFactory
from app.core.constants import LLMProvider
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class StructuredLLMDemo:
    """Demonstrates structured LLM output usage."""
    
    def __init__(self):
        self.llm_provider = None
    
    async def initialize(self):
        """Initialize LLM provider."""
        try:
            self.llm_provider = LLMFactory.create_llm(LLMProvider.GROQ)
            await self.llm_provider.initialize()
            logger.info("LLM provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            raise
    
    async def demonstrate_agent_thinking(self) -> StructuredLLMResponse:
        """Demonstrate agent thinking process."""
        prompt = """
        A user just asked: "Is my database connection working? I'm getting timeouts."
        
        As an AI agent, analyze this request and decide what action to take.
        Consider:
        - What tools you might need
        - The confidence level in your decision
        - Whether approval is needed
        - Risk assessment
        
        Provide your thinking process and decision.
        """
        
        print("🤖 Demonstrating Agent Thinking Process...")
        
        try:
            structured_response = await self.llm_provider.generate_structured(
                prompt=prompt,
                output_schema=AgentThinking,
                temperature=0.7,
                max_tokens=800
            )
            
            thinking = structured_response.structured_output
            if thinking:
                print(f"✅ Agent Decision: {thinking.selected_action}")
                print(f"🎯 Confidence: {thinking.confidence_level:.2f}")
                print(f"🛠️  Tool Selected: {thinking.tool_selection}")
                print(f"⚠️  Risk Level: {thinking.risk_assessment}")
                print(f"💭 Reasoning: {thinking.thought_process[:100]}...")
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Agent thinking demo failed: {e}")
            raise
    
    async def demonstrate_chat_response(self) -> StructuredLLMResponse:
        """Demonstrate structured chat response."""
        prompt = """
        Based on the database health check results:
        - Database: HEALTHY (response time: 45ms)
        - Connection pool: 85% utilized
        - Recent errors: None in last 24h
        - Index performance: Good
        
        Provide a helpful response to the user who was experiencing timeouts.
        Include follow-up suggestions and assess if human intervention is needed.
        """
        
        print("\n💬 Demonstrating Structured Chat Response...")
        
        try:
            structured_response = await self.llm_provider.generate_structured(
                prompt=prompt,
                output_schema=ChatAgentResponse,
                temperature=0.5,
                max_tokens=1000
            )
            
            chat_response = structured_response.structured_output
            if chat_response:
                print(f"📝 Response Type: {chat_response.response_type}")
                print(f"🎯 User Intent: {chat_response.user_intent}")
                print(f"🛠️  Tools Used: {', '.join(chat_response.tools_invoked)}")
                print(f"💡 Follow-ups: {len(chat_response.follow_up_suggestions)} suggestions")
                print(f"📄 Response: {chat_response.response_text[:150]}...")
                
                if chat_response.follow_up_suggestions:
                    print("   Suggestions:")
                    for i, suggestion in enumerate(chat_response.follow_up_suggestions[:3], 1):
                        print(f"   {i}. {suggestion}")
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Chat response demo failed: {e}")
            raise
    
    async def demonstrate_document_analysis(self) -> StructuredLLMResponse:
        """Demonstrate document ingestion analysis."""
        prompt = """
        Analyze this document content for ingestion into our knowledge base:
        
        # API Rate Limiting Guide
        
        ## Overview
        Our API implements rate limiting to ensure fair usage and system stability.
        
        ## Rate Limits
        - Standard tier: 100 requests/minute
        - Premium tier: 1000 requests/minute
        - Enterprise: Custom limits
        
        ## Headers
        - X-RateLimit-Limit: Maximum requests per window
        - X-RateLimit-Remaining: Requests remaining
        - X-RateLimit-Reset: Unix timestamp when limit resets
        
        ## Best Practices
        1. Implement exponential backoff
        2. Cache responses when possible
        3. Use batch operations for multiple items
        4. Monitor rate limit headers
        
        ## Error Handling
        When rate limited, API returns 429 status with retry-after header.
        
        Provide analysis for optimal chunking and metadata extraction.
        """
        
        print("\n📄 Demonstrating Document Analysis...")
        
        try:
            structured_response = await self.llm_provider.generate_structured(
                prompt=prompt,
                output_schema=IngestionAnalysis,
                temperature=0.3,
                max_tokens=1200
            )
            
            analysis = structured_response.structured_output
            if analysis:
                print(f"📋 Content Type: {analysis.content_type}")
                print(f"⭐ Quality Score: {analysis.quality_score:.2f}")
                print(f"🏷️  Key Topics: {', '.join(analysis.key_topics[:5])}")
                print(f"📊 Complexity: {analysis.complexity_level}")
                print(f"🧠 Strategy: {analysis.chunk_strategy}")
                print(f"🔢 Est. Tokens: {analysis.estimated_tokens}")
                print(f"📝 Summary: {analysis.document_summary}")
                
                if analysis.suggested_tags:
                    print(f"🏷️  Suggested Tags: {', '.join(analysis.suggested_tags[:5])}")
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Document analysis demo failed: {e}")
            raise
    
    async def demonstrate_system_diagnostics(self) -> StructuredLLMResponse:
        """Demonstrate system diagnostics analysis."""
        prompt = """
        Analyze this system health data and provide diagnostics:
        
        System Metrics:
        - CPU Usage: 45%
        - Memory Usage: 72%
        - Disk Usage: 34%
        - Network I/O: High (850 Mbps)
        
        Component Status:
        - PostgreSQL: Healthy (avg query time: 25ms)
        - Redis: Warning (memory usage 85%)
        - Celery: Healthy (5 active workers)
        - API Gateway: Healthy (avg response: 120ms)
        
        Recent Issues:
        - Redis memory spikes during peak hours
        - Occasional connection pool exhaustion
        - 2 failed background jobs last hour
        
        Error Logs:
        - 15 timeout errors in last hour
        - 3 Redis connection errors
        - 1 database deadlock resolved
        
        Provide comprehensive diagnostics and recommendations.
        """
        
        print("\n🏥 Demonstrating System Diagnostics...")
        
        try:
            structured_response = await self.llm_provider.generate_structured(
                prompt=prompt,
                output_schema=SystemDiagnostics,
                temperature=0.4,
                max_tokens=1500
            )
            
            diagnostics = structured_response.structured_output
            if diagnostics:
                print(f"🚦 Alert Level: {diagnostics.alert_level}")
                
                # Show component status
                print("\n🔧 Component Status:")
                for component, status in diagnostics.component_status.items():
                    status_emoji = "✅" if status == "healthy" else "⚠️" if status == "warning" else "❌"
                    print(f"   {status_emoji} {component}: {status}")
                
                # Show performance metrics
                if diagnostics.performance_metrics:
                    print("\n📊 Performance Metrics:")
                    for metric, value in list(diagnostics.performance_metrics.items())[:4]:
                        print(f"   📈 {metric}: {value}")
                
                # Show recommendations
                if diagnostics.recommendations:
                    print("\n💡 Recommendations:")
                    for i, rec in enumerate(diagnostics.recommendations[:3], 1):
                        print(f"   {i}. {rec}")
                
                # Show bottlenecks
                if diagnostics.bottlenecks:
                    print(f"\n🚫 Bottlenecks: {', '.join(diagnostics.bottlenecks)}")
            
            return structured_response
            
        except Exception as e:
            logger.error(f"System diagnostics demo failed: {e}")
            raise
    
    async def run_full_demo(self):
        """Run the complete demonstration."""
        print("🚀 Starting Structured LLM Output Demonstration\n")
        print("=" * 60)
        
        try:
            await self.initialize()
            
            # Run all demonstrations
            thinking_result = await self.demonstrate_agent_thinking()
            chat_result = await self.demonstrate_chat_response()
            doc_result = await self.demonstrate_document_analysis()
            diag_result = await self.demonstrate_system_diagnostics()
            
            # Show summary
            print("\n" + "=" * 60)
            print("📊 DEMONSTRATION SUMMARY")
            print("=" * 60)
            
            results = [
                ("Agent Thinking", thinking_result),
                ("Chat Response", chat_result),
                ("Document Analysis", doc_result),
                ("System Diagnostics", diag_result)
            ]
            
            for name, result in results:
                if result.structured_output:
                    print(f"✅ {name}: Successfully parsed structured output")
                    print(f"   📏 Response length: {len(result.content)} chars")
                    print(f"   ⏱️  Processing time: {result.processing_time_ms:.1f}ms")
                    print(f"   🧠 Model: {result.model_name} ({result.provider})")
                else:
                    print(f"❌ {name}: Failed to parse structured output")
                print()
            
            # Show token usage summary
            total_tokens = sum(
                result.usage.get('total_tokens', 0) 
                for _, result in results 
                if result.usage
            )
            print(f"🔢 Total tokens used: {total_tokens}")
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            print(f"❌ Demo failed: {e}")
        
        print("🏁 Demonstration complete!")


# Example usage functions for integration into your existing services

async def enhance_chat_service_example():
    """Example of enhancing chat service with structured outputs."""
    
    # This would be integrated into your existing ChatService
    llm_provider = LLMFactory.create_llm(LLMProvider.GROQ)
    await llm_provider.initialize()
    
    user_message = "Can you check if my API key is working correctly?"
    
    # Step 1: Agent thinking process
    thinking_prompt = f"""
    User message: "{user_message}"
    
    Analyze this request and determine the best action plan.
    """
    
    thinking_response = await llm_provider.generate_structured(
        prompt=thinking_prompt,
        output_schema=AgentThinking
    )
    
    thinking = thinking_response.structured_output
    
    # Step 2: Execute based on thinking
    if thinking.selected_action == "use_tool":
        # Simulate tool execution
        tool_result = "API key validation successful - key is active and valid"
        
        # Step 3: Generate final response
        response_prompt = f"""
        Tool execution result: {tool_result}
        Original user question: {user_message}
        
        Provide a helpful response to the user.
        """
        
        chat_response = await llm_provider.generate_structured(
            prompt=response_prompt,
            output_schema=ChatAgentResponse
        )
        
        return {
            "thinking": thinking,
            "response": chat_response.structured_output,
            "processing_time_ms": (
                thinking_response.processing_time_ms + 
                chat_response.processing_time_ms
            )
        }


async def enhance_ingestion_service_example():
    """Example of enhancing data ingestion with structured analysis."""
    
    llm_provider = LLMFactory.create_llm(LLMProvider.GROQ)
    await llm_provider.initialize()
    
    # Simulate document content
    document_content = """
    # User Authentication Guide
    
    This guide covers user authentication methods...
    [Document content would be here]
    """
    
    analysis_prompt = f"""
    Analyze this document for ingestion into our knowledge base:
    
    {document_content}
    
    Provide detailed analysis for optimal processing and chunking.
    """
    
    analysis_response = await llm_provider.generate_structured(
        prompt=analysis_prompt,
        output_schema=IngestionAnalysis
    )
    
    analysis = analysis_response.structured_output
    
    # Use the analysis for ingestion decisions
    chunk_size = 500 if analysis.complexity_level == "low" else 800
    chunk_strategy = analysis.chunk_strategy
    
    return {
        "analysis": analysis,
        "chunk_size": chunk_size,
        "chunk_strategy": chunk_strategy,
        "suggested_tags": analysis.suggested_tags,
        "quality_score": analysis.quality_score
    }


if __name__ == "__main__":
    # Run the demonstration
    demo = StructuredLLMDemo()
    asyncio.run(demo.run_full_demo())
