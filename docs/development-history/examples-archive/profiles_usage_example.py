#!/usr/bin/env python3
"""
Example demonstrating the PROFILES functionality in the Settings system.

This shows how to control which configuration profiles get loaded
from the resources/application-*.yaml files.
"""

from app.core.config.framework.settings import Settings

def demonstrate_profiles_usage():
    """Demonstrate different ways to use the PROFILES functionality."""
    
    print("=" * 60)
    print("PROFILES FUNCTIONALITY DEMONSTRATION")
    print("=" * 60)
    
    # 1. Show current default behavior (load all profiles)
    print("\n1. Default behavior - Load all profiles:")
    print(f"   Current PROFILES setting: {Settings.get_profiles_setting()}")
    
    settings = Settings.instance()
    all_profiles = settings.get_profile_names()
    print(f"   Loaded profiles: {all_profiles}")
    print(f"   Available sections: {settings.list_sections()}")
    
    # 2. Load only specific profiles
    print("\n2. Load only specific profiles:")
    specific_profiles = ['db', 'llm', 'app']
    Settings.set_profiles_setting(specific_profiles)
    print(f"   Set PROFILES to: {specific_profiles}")
    
    # Reset to apply new setting
    Settings.reset()
    settings = Settings.instance()
    print(f"   Now loaded: {settings.get_profile_names()}")
    
    # Show that we can only access the loaded profiles
    print(f"   Can access settings.db.provider: {hasattr(settings, 'db')}")
    print(f"   Can access settings.llm.provider: {hasattr(settings, 'llm')}")
    print(f"   Can access settings.vector: {hasattr(settings, 'vector')}")  # Should be False
    
    # 3. Runtime profile reloading
    print("\n3. Runtime profile reloading:")
    Settings.set_profiles_setting(['vector', 'external'])
    print(f"   Changed PROFILES to: {Settings.get_profiles_setting()}")
    
    # Use reload instead of reset for existing instance
    settings.reload_profiles()
    print(f"   After reload: {settings.get_profile_names()}")
    
    # 4. Back to all profiles
    print("\n4. Back to all profiles:")
    Settings.set_profiles_setting(['*'])
    settings.reload_profiles()
    print(f"   With ['*']: {settings.get_profile_names()}")
    
    # 5. Use cases demonstration
    print("\n5. Common use cases:")
    
    # Minimal setup for testing
    print("\n   a) Minimal setup (testing/development):")
    Settings.set_profiles_setting(['app'])
    Settings.reset()
    minimal_settings = Settings.instance()
    print(f"      Only app config: {minimal_settings.get_profile_names()}")
    
    # Database-focused application
    print("\n   b) Database-focused application:")
    Settings.set_profiles_setting(['db', 'app'])
    Settings.reset()
    db_settings = Settings.instance()
    print(f"      Database focused: {db_settings.get_profile_names()}")
    
    # AI/ML service
    print("\n   c) AI/ML service:")
    Settings.set_profiles_setting(['llm', 'vector', 'embeddings', 'app'])
    Settings.reset()
    ai_settings = Settings.instance()
    print(f"      AI/ML service: {ai_settings.get_profile_names()}")
    
    # Full-featured application
    print("\n   d) Full-featured application:")
    Settings.set_profiles_setting(['*'])
    Settings.reset()
    full_settings = Settings.instance()
    print(f"      Full featured: {full_settings.get_profile_names()}")
    
    print("\n" + "=" * 60)
    print("PROFILES CONFIGURATION OPTIONS")
    print("=" * 60)
    
    print("""
Available configuration patterns:

1. Load all profiles (default):
   PROFILES = ['*']

2. Load specific profiles:
   PROFILES = ['db', 'llm', 'app']
   PROFILES = ['vector', 'embeddings']
   PROFILES = ['external', 'db']

3. Runtime changes:
   Settings.set_profiles_setting(['db', 'vector'])
   settings.reload_profiles()

4. Environment-specific loading:
   # In production - load everything
   PROFILES = ['*']
   
   # In testing - minimal
   PROFILES = ['app']
   
   # In development - database only
   PROFILES = ['db', 'app']

Available profiles (based on resources/ directory):
""")
    
    # Show available profile files
    import os
    from pathlib import Path
    
    # Find resources directory
    current_file = Path(__file__)
    project_root = current_file.parent.parent
    resources_dir = project_root / "resources"
    
    if resources_dir.exists():
        profile_files = list(resources_dir.glob("application-*.yaml"))
        for file in sorted(profile_files):
            profile_name = file.stem[12:]  # Remove "application-" prefix
            print(f"   - '{profile_name}' from {file.name}")
    
    print("\n" + "=" * 60)

def performance_comparison():
    """Compare loading times between all profiles vs specific profiles."""
    import time
    
    print("PERFORMANCE COMPARISON")
    print("=" * 40)
    
    # Test loading all profiles
    Settings.set_profiles_setting(['*'])
    start_time = time.time()
    Settings.reset()
    Settings.instance()
    all_profiles_time = time.time() - start_time
    
    # Test loading minimal profiles
    Settings.set_profiles_setting(['app'])
    start_time = time.time()
    Settings.reset()
    Settings.instance()
    minimal_time = time.time() - start_time
    
    print(f"All profiles load time: {all_profiles_time:.4f}s")
    print(f"Minimal profiles load time: {minimal_time:.4f}s")
    print(f"Performance improvement: {((all_profiles_time - minimal_time) / all_profiles_time * 100):.1f}%")

if __name__ == "__main__":
    demonstrate_profiles_usage()
    print()
    performance_comparison()
