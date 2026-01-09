"""
Example: Using Context Window Manager with Settings System
"""

from app.llm.context import ContextWindowManager
from app.sessions.models.message import ChatMessage


def example_usage():
    """Example of how to use the context window manager."""
    
    # Create some sample chat messages
    messages = [
        ChatMessage(role="user", content="Hello, how are you?"),
        ChatMessage(role="assistant", content="I'm doing well, thank you! How can I help you today?"),
        ChatMessage(role="user", content="Can you help me understand Python decorators?"),
        ChatMessage(role="assistant", content="Of course! Python decorators are a powerful feature that allows you to modify or extend the behavior of functions or classes without permanently modifying their code. Here's a basic example:\n\n```python\ndef my_decorator(func):\n    def wrapper():\n        print('Before function call')\n        func()\n        print('After function call')\n    return wrapper\n\n@my_decorator\ndef say_hello():\n    print('Hello!')\n```"),
        ChatMessage(role="user", content="That's helpful! Can you show me a more complex example with arguments?"),
        ChatMessage(role="assistant", content="Absolutely! Here's a more advanced decorator example that works with functions that take arguments:\n\n```python\nimport functools\n\ndef retry(max_attempts=3):\n    def decorator(func):\n        @functools.wraps(func)\n        def wrapper(*args, **kwargs):\n            for attempt in range(max_attempts):\n                try:\n                    return func(*args, **kwargs)\n                except Exception as e:\n                    if attempt == max_attempts - 1:\n                        raise e\n                    print(f'Attempt {attempt + 1} failed: {e}')\n            return None\n        return wrapper\n    return decorator\n\n@retry(max_attempts=3)\ndef unreliable_api_call(url):\n    # Simulate API call that might fail\n    import random\n    if random.random() < 0.7:\n        raise Exception('API temporarily unavailable')\n    return f'Success! Data from {url}'\n```"),
    ]
    
    # Get the context window manager (singleton)
    context_manager = ContextWindowManager()
    
    # Test different strategies
    strategies = ["recent", "sliding", "summarization"]
    models = ["gpt-4", "claude-3-sonnet", "llama-3.3-70b-versatile"]
    
    print("=== Context Window Manager Examples ===\n")
    
    for model in models:
        print(f"Model: {model}")
        print("-" * 40)
        
        for strategy in strategies:
            # Prepare context using different strategies
            processed_messages, metadata = context_manager.prepare_context(
                messages=messages,
                model=model,
                strategy=strategy
            )
            
            print(f"Strategy: {strategy}")
            print(f"  Original messages: {metadata['original_message_count']}")
            print(f"  Final messages: {metadata['final_message_count']}")
            print(f"  Original tokens: {metadata['original_tokens']}")
            print(f"  Final tokens: {metadata['final_tokens']}")
            print(f"  Token utilization: {metadata['token_utilization']:.1%}")
            print(f"  Processing time: {metadata['processing_time']:.3f}s")
            print(f"  Messages truncated: {metadata['messages_truncated']}")
            print()
        
        print()


def agent_integration_example():
    """Example of how to integrate with agent implementations."""
    
    # Simulated agent context
    class AgentContext:
        def __init__(self):
            self.user_id = "user123"
            self.session_id = "session456"
    
    # Simulated session repository
    class MockSessionRepository:
        def __init__(self):
            # Simulate a long conversation history
            self.messages = []
            for i in range(50):  # 50 message pairs = 100 total messages
                self.messages.append(
                    ChatMessage(role="user", content=f"User message {i}: This is a sample message from the user with some content.")
                )
                self.messages.append(
                    ChatMessage(role="assistant", content=f"Assistant response {i}: This is a detailed response from the assistant with helpful information and context.")
                )
        
        async def get_session_history(self, user_id: str, session_id: str):
            return self.messages
    
    async def optimized_agent_query(query: str, context: AgentContext, session_repo: MockSessionRepository):
        """Example of optimized agent query with context window management."""
        
        # Get conversation history
        history = await session_repo.get_session_history(context.user_id, context.session_id)
        
        # Use context window manager for intelligent truncation
        context_manager = ContextWindowManager()
        
        # Get model name (would come from your LLM provider configuration)
        model_name = "gpt-4"  # or get from llm.model_name
        
        # Prepare context with token-aware truncation
        processed_messages, metadata = context_manager.prepare_context(
            messages=history,
            model=model_name,
            strategy="sliding"  # Use sliding window for balanced context
        )
        
        print(f"Context preparation for query: '{query[:50]}...'")
        print(f"  Reduced {metadata['original_message_count']} → {metadata['final_message_count']} messages")
        print(f"  Token utilization: {metadata['token_utilization']:.1%}")
        print(f"  Tokens saved: {metadata['tokens_saved']}")
        print(f"  Processing time: {metadata['processing_time']:.3f}s")
        
        return processed_messages, metadata
    
    # Example usage
    import asyncio
    
    context = AgentContext()
    session_repo = MockSessionRepository()
    
    # Test the optimized approach
    async def test_optimization():
        messages, metadata = await optimized_agent_query(
            "What did we discuss about Python decorators?",
            context,
            session_repo
        )
        
        print(f"\nFinal context messages: {len(messages)}")
        print("Messages ready for LLM processing!")
    
    asyncio.run(test_optimization())


if __name__ == "__main__":
    print("Context Window Manager Examples")
    print("===============================\n")
    
    # Run basic examples
    example_usage()
    
    print("\n" + "="*60 + "\n")
    
    # Run agent integration example
    agent_integration_example()
