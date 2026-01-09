"""
Example usage of the new Settings system with profile-based configuration.

This demonstrates how to use the Settings system in your LLM library.
"""
from app.core.config import Settings

def demonstrate_settings_usage():
    """Demonstrate various ways to use the new Settings system."""
    
    print("=== Settings System Usage Examples ===\n")
    
    # Get the singleton instance
    settings = Settings.instance()
    
    print("1. Profile-based access:")
    print(f"   Available profiles: {settings.get_profile_names()}")
    print(f"   Available sections: {settings.list_sections()}")
    
    print("\n2. Direct profile dot notation access:")
    if hasattr(settings, 'llm'):
        print(f"   LLM Provider: {settings.llm.provider}")
        print(f"   LLM Model: {settings.llm.model}")
        print(f"   LLM Temperature: {settings.llm.temperature}")
    
    if hasattr(settings, 'vector'):
        print(f"   Vector DB Provider: {settings.vector.provider}")
        print(f"   Vector DB Embedding: {settings.vector.embedding}")
        print(f"   Vector DB Collection: {settings.vector.qdrant.collection_name}")
    
    if hasattr(settings, 'db'):
        print(f"   Database Provider: {settings.db.provider}")
        print(f"   DB Connection Timeout: {settings.db.connection_timeout}")
    
    if hasattr(settings, 'app'):
        print(f"   App Name: {settings.app.name}")
        print(f"   App Version: {settings.app.version}")
        print(f"   Max Agent Iterations: {settings.app.agent.max_iterations}")
    
    print("\n3. Using get_value method for flexible access:")
    llm_provider = settings.get_value('llm.provider', 'fallback_provider')
    vector_provider = settings.get_value('vector.provider', 'fallback_vector')
    timeout = settings.get_value('db.connection_timeout', 30)
    print(f"   LLM Provider with fallback: {llm_provider}")
    print(f"   Vector Provider with fallback: {vector_provider}")
    print(f"   DB timeout with fallback: {timeout}")
    
    print("\n4. Profile file path information:")
    for profile in settings.get_profile_names()[:3]:  # Show first 3 profiles
        path = settings.get_profile_file_path(profile)
        print(f"   Profile '{profile}': {path}")

def demonstrate_factory_integration():
    """Show how to integrate Settings with factory classes."""
    
    print("\n=== Factory Integration with Settings ===\n")
    
    settings = Settings.instance()
    
    # Example: LLM Factory with profile-based defaults
    def create_llm_with_settings(user_config=None, profile_override=None):
        """Example LLM factory using Settings system."""
        user_config = user_config or {}
        
        # Use profile-based settings as fallback
        if hasattr(settings, 'llm'):
            provider = user_config.get('provider', settings.llm.provider)
            model = user_config.get('model', settings.llm.model)
            temperature = user_config.get('temperature', settings.llm.temperature)
            max_tokens = user_config.get('max_tokens', settings.llm.max_tokens)
        else:
            # Fallback if no llm profile
            provider = user_config.get('provider', 'openai')
            model = user_config.get('model', 'gpt-4')
            temperature = user_config.get('temperature', 0.1)
            max_tokens = user_config.get('max_tokens', 4096)
        
        print(f"Creating LLM with:")
        print(f"  Provider: {provider}")
        print(f"  Model: {model}")
        print(f"  Temperature: {temperature}")
        print(f"  Max Tokens: {max_tokens}")
        
        return {
            'provider': provider,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
    
    # Example: Vector DB Factory with profile-based defaults
    def create_vector_db_with_settings(user_config=None):
        """Example Vector DB factory using Settings system."""
        user_config = user_config or {}
        
        # Use profile-based settings as fallback
        if hasattr(settings, 'vector'):
            provider = user_config.get('provider', settings.vector.provider)
            embedding = user_config.get('embedding', settings.vector.embedding)
            max_results = user_config.get('max_results', settings.vector.max_results)
            
            # Provider-specific settings
            if provider == 'qdrant' and hasattr(settings.vector, 'qdrant'):
                collection_name = user_config.get('collection_name', settings.vector.qdrant.collection_name)
            else:
                collection_name = user_config.get('collection_name', 'default_collection')
        else:
            # Fallback if no vector profile
            provider = user_config.get('provider', 'qdrant')
            embedding = user_config.get('embedding', 'openai')
            max_results = user_config.get('max_results', 10)
            collection_name = user_config.get('collection_name', 'default_collection')
        
        print(f"Creating Vector DB with:")
        print(f"  Provider: {provider}")
        print(f"  Embedding: {embedding}")
        print(f"  Max Results: {max_results}")
        print(f"  Collection: {collection_name}")
        
        return {
            'provider': provider,
            'embedding': embedding,
            'max_results': max_results,
            'collection_name': collection_name
        }
    
    # Example: Agent Factory with profile-based defaults
    def create_agent_with_settings(user_config=None):
        """Example Agent factory using Settings system."""
        user_config = user_config or {}
        
        # Use profile-based settings as fallback
        if hasattr(settings, 'app') and hasattr(settings.app, 'agent'):
            max_iterations = user_config.get('max_iterations', settings.app.agent.max_iterations)
            timeout = user_config.get('timeout', settings.app.agent.timeout)
            tool_timeout = user_config.get('tool_timeout', settings.app.agent.tool_timeout)
        else:
            # Fallback if no app.agent profile
            max_iterations = user_config.get('max_iterations', 10)
            timeout = user_config.get('timeout', 300)
            tool_timeout = user_config.get('tool_timeout', 60)
        
        print(f"Creating Agent with:")
        print(f"  Max Iterations: {max_iterations}")
        print(f"  Timeout: {timeout}s")
        print(f"  Tool Timeout: {tool_timeout}s")
        
        return {
            'max_iterations': max_iterations,
            'timeout': timeout,
            'tool_timeout': tool_timeout
        }
    
    # Test with no user config (all from settings)
    print("1. Using profile-based settings (no overrides):")
    llm = create_llm_with_settings()
    vector_db = create_vector_db_with_settings()
    agent = create_agent_with_settings()
    
    print("\n2. Overriding some settings:")
    llm_custom = create_llm_with_settings({
        'model': 'gpt-3.5-turbo',
        'temperature': 0.9
    })
    
    vector_db_custom = create_vector_db_with_settings({
        'provider': 'chroma',
        'max_results': 20
    })
    
    agent_custom = create_agent_with_settings({
        'max_iterations': 15,
        'timeout': 600
    })

def demonstrate_profile_management():
    """Demonstrate profile management features."""
    
    print("\n=== Profile Management Features ===\n")
    
    settings = Settings.instance()
    
    print("1. Profile discovery:")
    profiles = settings.get_profile_names()
    print(f"   Found {len(profiles)} profiles: {profiles}")
    
    print("\n2. Profile file locations:")
    for profile in profiles:
        file_path = settings.get_profile_file_path(profile)
        if file_path:
            print(f"   {profile}: {file_path}")
    
    print("\n3. Section checking:")
    for profile in profiles[:5]:  # Check first 5
        has_section = settings.has_section(profile)
        print(f"   Has section '{profile}': {has_section}")
    
    print("\n4. Settings representation:")
    print(f"   {settings}")

if __name__ == "__main__":
    demonstrate_settings_usage()
    demonstrate_factory_integration()
    demonstrate_profile_management()
