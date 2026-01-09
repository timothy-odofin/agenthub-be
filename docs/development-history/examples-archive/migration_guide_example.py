"""
Migration Guide: From Direct Config Loading to Settings System

This guide shows how to migrate your existing configuration code to use the new 
profile-based Settings system.
"""

# =============================================================================
# BEFORE: Old Pattern - Direct YAML Loading
# =============================================================================

# Old way - direct file loading
def old_get_database_config():
    import yaml
    import os
    from pathlib import Path
    
    # Manual path construction
    project_root = Path(__file__).parent.parent
    config_file = project_root / "resources" / "application-data-sources.yaml"
    
    # Manual YAML loading
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Manual navigation and fallbacks
    db_config = config.get('database', {})
    provider = db_config.get('provider', 'mongodb')  # Manual fallback
    host = db_config.get('host', 'localhost')
    port = db_config.get('port', 27017)
    
    return {
        'provider': provider,
        'host': host,
        'port': port
    }

# Old way - environment variable dependency
def old_get_llm_config():
    import os
    
    # Manual environment variable handling
    provider = os.getenv('LLM_PROVIDER', 'openai')
    model = os.getenv('LLM_MODEL', 'gpt-4')
    temperature = float(os.getenv('LLM_TEMPERATURE', '0.1'))
    
    return {
        'provider': provider,
        'model': model,
        'temperature': temperature
    }

# Old way - hardcoded factory defaults
def old_create_vector_db():
    # Hardcoded defaults scattered throughout code
    provider = 'qdrant'
    host = 'localhost'
    port = 6333
    collection = 'default_collection'
    
    return {
        'provider': provider,
        'host': host,
        'port': port,
        'collection': collection
    }


# =============================================================================
# AFTER: New Pattern - Settings System
# =============================================================================

from app.core.config import Settings

# New way - centralized settings access
def new_get_database_config():
    settings = Settings.instance()
    
    # Direct dot notation access with automatic fallbacks from YAML
    return {
        'provider': settings.db.provider,  # From application-db.yaml
        'host': settings.db.host,
        'port': settings.db.port,
        'connection_timeout': settings.db.connection_timeout
    }

# New way - settings-based with user overrides
def new_get_llm_config(user_overrides=None):
    settings = Settings.instance()
    user_overrides = user_overrides or {}
    
    # Settings as defaults, user overrides take precedence
    return {
        'provider': user_overrides.get('provider', settings.llm.provider),
        'model': user_overrides.get('model', settings.llm.model),
        'temperature': user_overrides.get('temperature', settings.llm.temperature),
        'max_tokens': user_overrides.get('max_tokens', settings.llm.max_tokens)
    }

# New way - profile-based configuration
def new_create_vector_db(user_config=None):
    settings = Settings.instance()
    user_config = user_config or {}
    
    # Profile-based defaults from application-vector.yaml
    provider = user_config.get('provider', settings.vector.provider)
    embedding = user_config.get('embedding', settings.vector.embedding)
    max_results = user_config.get('max_results', settings.vector.max_results)
    
    # Provider-specific settings
    if provider == 'qdrant':
        collection = user_config.get('collection', settings.vector.qdrant.collection_name)
        host = user_config.get('host', settings.vector.qdrant.host)
        port = user_config.get('port', settings.vector.qdrant.port)
    else:
        # Fallback for other providers
        collection = user_config.get('collection', 'default_collection')
        host = user_config.get('host', 'localhost')
        port = user_config.get('port', 6333)
    
    return {
        'provider': provider,
        'embedding': embedding,
        'max_results': max_results,
        'collection': collection,
        'host': host,
        'port': port
    }


# =============================================================================
# ADVANCED PATTERNS
# =============================================================================

# Pattern 1: Settings with flexible fallbacks
def get_config_with_fallbacks(path, fallback_value=None):
    """Get configuration value with flexible path and fallback."""
    settings = Settings.instance()
    return settings.get_value(path, fallback_value)

# Usage examples:
def advanced_config_examples():
    # Dot notation with fallbacks
    llm_provider = get_config_with_fallbacks('llm.provider', 'openai')
    vector_timeout = get_config_with_fallbacks('vector.qdrant.timeout', 30)
    agent_iterations = get_config_with_fallbacks('app.agent.max_iterations', 10)
    
    # Nested configuration access
    settings = Settings.instance()
    if hasattr(settings, 'llm') and hasattr(settings.llm, 'openai'):
        openai_model = settings.llm.openai.model
        openai_api_key = getattr(settings.llm.openai, 'api_key', None)

# Pattern 2: Factory with Settings integration
class SettingsAwareFactory:
    """Factory that uses Settings system for configuration."""
    
    def __init__(self):
        self.settings = Settings.instance()
    
    def create_component(self, component_type, user_config=None):
        """Create component using settings + user overrides."""
        user_config = user_config or {}
        
        # Get settings for component type
        if hasattr(self.settings, component_type):
            settings_config = getattr(self.settings, component_type)
            
            # Build final config: settings + user overrides
            final_config = {}
            
            # Add all settings attributes
            for attr in dir(settings_config):
                if not attr.startswith('_'):
                    final_config[attr] = getattr(settings_config, attr)
            
            # Apply user overrides
            final_config.update(user_config)
            
            return final_config
        else:
            # No settings available, use user config only
            return user_config

# Pattern 3: Configuration validation
def validate_settings():
    """Validate that required settings are present."""
    settings = Settings.instance()
    
    required_sections = ['llm', 'vector', 'db']
    missing_sections = []
    
    for section in required_sections:
        if not settings.has_section(section):
            missing_sections.append(section)
    
    if missing_sections:
        raise ValueError(f"Missing required configuration sections: {missing_sections}")
    
    # Validate specific required values
    if not hasattr(settings.llm, 'provider'):
        raise ValueError("LLM provider not configured")
    
    if not hasattr(settings.vector, 'provider'):
        raise ValueError("Vector DB provider not configured")
    
    return True


# =============================================================================
# MIGRATION CHECKLIST
# =============================================================================

def migration_checklist():
    """
    Migration Checklist from old config to Settings system:
    
    ✅ DONE: Replace direct YAML file loading with Settings.instance()
    ✅ DONE: Replace environment variable access with settings.{profile}.{property}
    ✅ DONE: Replace hardcoded defaults with profile-based YAML configuration
    ✅ DONE: Use dot notation (settings.llm.provider) instead of dict access
    ✅ DONE: Use settings.get_value() for flexible path access with fallbacks
    ✅ DONE: Add profile-based configuration files (application-*.yaml)
    ✅ DONE: Update factory classes to use Settings for defaults
    ✅ DONE: Add user override support in factory methods
    ✅ DONE: Add configuration validation methods
    ✅ DONE: Update imports to use Settings instead of old config classes
    
    📋 TODO for your specific codebase:
    □ Update all factory classes to use Settings system
    □ Replace any remaining direct config file access
    □ Update environment variable handling to use Settings fallbacks
    □ Add settings validation to application startup
    □ Update tests to use Settings system
    □ Document new configuration structure for your team
    □ Add configuration reload functionality for development
    □ Update deployment scripts to handle profile-based YAML files
    """
    pass


# =============================================================================
# EXAMPLE INTEGRATION
# =============================================================================

if __name__ == "__main__":
    print("=== Configuration Migration Examples ===\n")
    
    print("1. Old vs New Database Config:")
    try:
        old_db = old_get_database_config()
        print(f"   Old method: {old_db}")
    except Exception as e:
        print(f"   Old method error: {e}")
    
    try:
        new_db = new_get_database_config()
        print(f"   New method: {new_db}")
    except Exception as e:
        print(f"   New method error: {e}")
    
    print("\n2. Old vs New LLM Config:")
    try:
        old_llm = old_get_llm_config()
        print(f"   Old method: {old_llm}")
    except Exception as e:
        print(f"   Old method error: {e}")
    
    try:
        new_llm = new_get_llm_config()
        print(f"   New method: {new_llm}")
    except Exception as e:
        print(f"   New method error: {e}")
    
    print("\n3. Old vs New Vector DB Config:")
    try:
        old_vector = old_create_vector_db()
        print(f"   Old method: {old_vector}")
    except Exception as e:
        print(f"   Old method error: {e}")
    
    try:
        new_vector = new_create_vector_db()
        print(f"   New method: {new_vector}")
    except Exception as e:
        print(f"   New method error: {e}")
    
    print("\n4. Advanced Settings Examples:")
    try:
        advanced_config_examples()
        print("   Advanced config access successful")
    except Exception as e:
        print(f"   Advanced config error: {e}")
    
    print("\n5. Settings Validation:")
    try:
        validate_settings()
        print("   Settings validation passed")
    except Exception as e:
        print(f"   Settings validation error: {e}")
    
    print("\n6. Factory with Settings:")
    try:
        factory = SettingsAwareFactory()
        llm_config = factory.create_component('llm', {'temperature': 0.9})
        print(f"   Factory LLM config: {llm_config}")
    except Exception as e:
        print(f"   Factory error: {e}")
