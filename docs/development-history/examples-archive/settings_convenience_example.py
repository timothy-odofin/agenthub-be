"""
Example demonstrating the convenience of the module-level settings instance.

This shows how you can directly import and use 'settings' throughout your application.
"""

# Option 1: Import the module-level instance directly (RECOMMENDED)
from app.core.config import settings

# Option 2: Import the class and create instance (if you need more control)
from app.core.config import Settings

def demonstrate_convenience_access():
    """Show how convenient the module-level settings instance is."""
    
    print("=== Convenient Settings Access ===\n")
    
    # Direct access using the module-level instance
    print("1. Direct module-level access:")
    print(f"   LLM Provider: {settings.llm.provider}")
    print(f"   LLM Model: {settings.llm.model}")
    print(f"   Vector DB: {settings.vector.provider}")
    print(f"   Database: {settings.db.provider}")
    
    print("\n2. Configuration paths:")
    print(f"   App Name: {settings.app.name}")
    print(f"   App Version: {settings.app.version}")
    
    print("\n3. Nested configuration access:")
    if hasattr(settings.vector, 'qdrant'):
        print(f"   Qdrant Collection: {settings.vector.qdrant.collection_name}")
        
        # Check for optional host/port with fallbacks
        host = getattr(settings.vector.qdrant, 'host', 'localhost')
        port = getattr(settings.vector.qdrant, 'port', 6333)
        print(f"   Qdrant Host: {host}")
        print(f"   Qdrant Port: {port}")
        
        # Show what's actually available in qdrant config
        qdrant_attrs = [attr for attr in dir(settings.vector.qdrant) 
                       if not attr.startswith('_') and not callable(getattr(settings.vector.qdrant, attr))]
        print(f"   Available Qdrant settings: {qdrant_attrs}")
    
    print("\n4. Fallback values using get_value:")
    timeout = settings.get_value('db.connection_timeout', 30)
    max_retries = settings.get_value('db.max_retries', 3)
    print(f"   DB Timeout: {timeout}s")
    print(f"   Max Retries: {max_retries}")
    
    print("\n5. Profile information:")
    profiles = settings.get_profile_names()
    print(f"   Available profiles: {profiles}")
    print(f"   Total profiles: {len(profiles)}")

def example_service_using_settings():
    """Example of how a service would use the settings."""
    
    print("\n=== Example Service Usage ===\n")
    
    class DatabaseService:
        """Example service that uses settings for configuration."""
        
        def __init__(self):
            # Use settings directly - no need to pass config around
            self.provider = settings.db.provider
            self.timeout = settings.get_value('db.connection_timeout', 30)
            self.max_retries = settings.get_value('db.max_retries', 3)
            
        def connect(self):
            print(f"Connecting to {self.provider} database...")
            print(f"  Timeout: {self.timeout}s")
            print(f"  Max retries: {self.max_retries}")
            return True
    
    class LLMService:
        """Example LLM service using settings."""
        
        def __init__(self):
            # Access LLM configuration directly
            self.provider = settings.llm.provider
            self.model = settings.llm.model
            self.temperature = settings.llm.temperature
            self.max_tokens = settings.llm.max_tokens
            
        def generate(self, prompt: str):
            print(f"Generating with {self.provider} {self.model}")
            print(f"  Temperature: {self.temperature}")
            print(f"  Max tokens: {self.max_tokens}")
            print(f"  Prompt: {prompt[:50]}...")
            return f"Generated response using {self.model}"
    
    class VectorService:
        """Example vector service using settings."""
        
        def __init__(self):
            # Access vector configuration directly
            self.provider = settings.vector.provider
            self.embedding = settings.vector.embedding
            self.max_results = settings.vector.max_results
            
            if self.provider == 'qdrant' and hasattr(settings.vector, 'qdrant'):
                self.collection = settings.vector.qdrant.collection_name
                self.host = getattr(settings.vector.qdrant, 'host', 'localhost')
                self.port = getattr(settings.vector.qdrant, 'port', 6333)
            else:
                self.collection = 'default_collection'
                self.host = 'localhost'
                self.port = 6333
                
        def search(self, query: str):
            print(f"Searching in {self.provider} vector DB")
            print(f"  Collection: {self.collection}")
            print(f"  Host: {self.host}:{self.port}")
            print(f"  Embedding: {self.embedding}")
            print(f"  Max results: {self.max_results}")
            print(f"  Query: {query}")
            return [f"Result {i}" for i in range(self.max_results)]
    
    # Create and use services
    print("Creating services using settings...")
    
    db_service = DatabaseService()
    llm_service = LLMService() 
    vector_service = VectorService()
    
    print("\nUsing services:")
    db_service.connect()
    response = llm_service.generate("What is the meaning of life?")
    results = vector_service.search("artificial intelligence")
    
    print(f"\nLLM Response: {response}")
    print(f"Vector Results: {results[:2]}...")  # Show first 2 results

def demonstrate_configuration_checking():
    """Show how to check configuration availability."""
    
    print("\n=== Configuration Checking ===\n")
    
    def check_feature_enabled(feature_path: str, default: bool = False) -> bool:
        """Check if a feature is enabled in configuration."""
        return settings.get_value(feature_path, default)
    
    def get_provider_config(provider_type: str):
        """Get provider-specific configuration."""
        if hasattr(settings, provider_type):
            provider_config = getattr(settings, provider_type)
            return {
                'provider': getattr(provider_config, 'provider', 'unknown'),
                'available': True,
                'config': provider_config
            }
        return {
            'provider': 'unknown',
            'available': False,
            'config': None
        }
    
    # Check various configurations
    print("1. Feature availability checks:")
    llm_config = get_provider_config('llm')
    vector_config = get_provider_config('vector')
    db_config = get_provider_config('db')
    
    print(f"   LLM Available: {llm_config['available']} (Provider: {llm_config['provider']})")
    print(f"   Vector Available: {vector_config['available']} (Provider: {vector_config['provider']})")
    print(f"   Database Available: {db_config['available']} (Provider: {db_config['provider']})")
    
    print("\n2. Configuration sections:")
    sections = settings.list_sections()
    for section in sections:
        has_section = settings.has_section(section)
        print(f"   {section}: {'✓' if has_section else '✗'}")

if __name__ == "__main__":
    demonstrate_convenience_access()
    example_service_using_settings()
    demonstrate_configuration_checking()
