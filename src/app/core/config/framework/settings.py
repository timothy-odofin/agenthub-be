"""
Settings manager with profile-based configuration loading and placeholder resolution.

Loads multiple YAML files using the pattern: application-{profile}.yaml,
automatically resolves environment variable placeholders with Spring Boot-style syntax,
and provides dot notation access to configuration values.
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from .yaml_loader import YamlLoader
from .dynamic_config import DynamicConfig
from ...utils import property_resolver, PropertyResolver

# Use standard logging to avoid circular import
logger = logging.getLogger(__name__)

# Configuration: Control which profiles to load
# Use ['*'] to load all profiles, or specify exact profile names like ['db', 'external', 'llm']
PROFILES = ['*']  # Default: load all available profiles


class Settings:
    """
    Settings manager with profile-based configuration loading.
    
    Automatically discovers and loads application-{profile}.yaml files from the resources directory.
    Profile loading can be controlled via the PROFILES variable for performance and customization.
    Provides dot notation access to profile-based configuration values.
    
    Profile Control:
        PROFILES = ['*']                    # Load all available profiles (default)
        PROFILES = ['db', 'llm', 'app']     # Load only specific profiles
        
    Example:
        # Set specific profiles before creating instance
        Settings.set_profiles_setting(['db', 'llm', 'app'])
        
        # Create settings instance
        settings = Settings.instance()
        
        # Access configuration values
        provider = settings.llm.provider      # From application-llm.yaml
        app_name = settings.app.name          # From application-app.yaml  
        db_timeout = settings.db.timeout      # From application-db.yaml
        
        # Runtime profile changes
        Settings.set_profiles_setting(['vector', 'embeddings'])
        settings.reload_profiles()  # Apply new profile selection
    """
    
    _instance: Optional['Settings'] = None
    _initialized: bool = False
    
    def __init__(self, resolver: Optional[PropertyResolver] = None):
        """Private constructor. Use instance() to get singleton.
        
        Args:
            resolver: PropertyResolver instance for placeholder resolution
        """
        if Settings._initialized:
            return
            
        # Ensure environment variables are loaded first
        from ...utils.env_utils import env
        env.reload_env()  # This will load .env file if available
            
        self._config_cache: Dict[str, DynamicConfig] = {}
        self._profile_files: Dict[str, str] = {}
        self._property_resolver = resolver or property_resolver
        self._load_profile_configurations()
        Settings._initialized = True
    
    @classmethod
    def instance(cls) -> 'Settings':
        """
        Get or create the singleton instance.
        
        Returns:
            Settings singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
        cls._initialized = False
    
    def _load_profile_configurations(self):
        """Discover and load all profile-based configuration files."""
        try:
            logger.info("Loading profile-based configurations...")
            
            # Get resources directory path
            resources_dir = self._get_resources_directory()
            
            # Discover all application-*.yaml files
            profile_files = self._discover_profile_files(resources_dir)
            
            if not profile_files:
                logger.warning("No profile configuration files found. Using empty configuration.")
                self._create_dynamic_attributes({})
                return
            
            # Load all profile configurations
            all_profiles_data = {}
            for profile_name, file_path in profile_files.items():
                try:
                    profile_data = YamlLoader.load_file(file_path, raise_on_missing=False)
                    if profile_data:
                        # Resolve environment variable placeholders
                        resolved_data = self._property_resolver.resolve_dict(profile_data)
                        all_profiles_data[profile_name] = resolved_data
                        self._profile_files[profile_name] = file_path
                        logger.debug(f"Loaded and resolved profile '{profile_name}' from {file_path}")
                    else:
                        logger.warning(f"Profile file {file_path} is empty")
                except Exception as e:
                    logger.error(f"Error loading profile '{profile_name}' from {file_path}: {e}")
            
            # Create dynamic configuration attributes
            self._create_dynamic_attributes(all_profiles_data)
            
            logger.info(f"Successfully loaded {len(all_profiles_data)} profile configurations: {list(all_profiles_data.keys())}")
            
        except Exception as e:
            logger.error(f"Error loading profile configurations: {e}")
            # Initialize with empty config to prevent crashes
            self._create_dynamic_attributes({})
    
    def _get_resources_directory(self) -> Path:
        """Get the resources directory path."""
        # Look for resources directory relative to project root
        current_file = Path(__file__)
        
        # Navigate up from src/app/core/config/settings.py to project root
        project_root = current_file.parent.parent.parent.parent.parent  
        resources_dir = project_root / "resources"
        
        if not resources_dir.exists():
            # Fallback: look for resources in current working directory
            resources_dir = Path.cwd() / "resources"
            
            if not resources_dir.exists():
                # Second fallback: create empty path for graceful handling
                logger.warning(f"Could not find resources directory. Checked: {project_root / 'resources'} and {Path.cwd() / 'resources'}")
        
        return resources_dir
    
    def _discover_profile_files(self, resources_dir: Path) -> Dict[str, str]:
        """
        Discover application-*.yaml files in the resources directory.
        Respects the PROFILES setting to control which profiles to load.
        
        Args:
            resources_dir: Path to the resources directory
            
        Returns:
            Dictionary mapping profile names to file paths
        """
        profile_files = {}
        
        if not resources_dir.exists():
            logger.warning(f"Resources directory not found: {resources_dir}")
            return profile_files
        
        # Check if we should load all profiles or specific ones
        load_all = '*' in PROFILES
        target_profiles = set() if load_all else set(PROFILES)
        
        if load_all:
            logger.debug("Loading all available profiles (PROFILES contains '*')")
        else:
            logger.debug(f"Loading specific profiles: {PROFILES}")
        
        # Look for application-*.yaml pattern
        pattern = "application-*.yaml"
        try:
            for yaml_file in resources_dir.glob(pattern):
                if yaml_file.is_file():
                    # Extract profile name from filename
                    # application-llm.yaml -> llm
                    filename = yaml_file.stem  # Remove .yaml extension
                    if filename.startswith("application-"):
                        profile_name = filename[12:]  # Remove "application-" prefix
                        if profile_name:  # Make sure there's a profile name
                            # Check if this profile should be loaded
                            if load_all or profile_name in target_profiles:
                                profile_files[profile_name] = str(yaml_file)
                                logger.debug(f"Discovered profile '{profile_name}' at {yaml_file}")
                            else:
                                logger.debug(f"Skipping profile '{profile_name}' (not in PROFILES list)")
                            
        except Exception as e:
            logger.error(f"Error discovering profile files in {resources_dir}: {e}")
        
        # Warn about missing requested profiles
        if not load_all:
            missing_profiles = target_profiles - set(profile_files.keys())
            if missing_profiles:
                logger.warning(f"Requested profiles not found: {missing_profiles}")
        
        return profile_files
    
    def _create_dynamic_attributes(self, data: Dict[str, Any]):
        """
        Dynamically create attributes from configuration data.
        
        Args:
            data: Configuration data dictionary
        """
        # Clear existing dynamic attributes (except private ones)
        for attr in list(self.__dict__.keys()):
            if not attr.startswith('_'):
                delattr(self, attr)
        
        # Create new attributes from data
        for key, value in data.items():
            attr_name = self._sanitize_attribute_name(key)
            
            if isinstance(value, dict):
                setattr(self, attr_name, DynamicConfig(value))
            else:
                # For non-dict values, wrap in DynamicConfig for consistency
                setattr(self, attr_name, value)
    
    def _sanitize_attribute_name(self, name: str) -> str:
        """
        Sanitize attribute names to be valid Python identifiers.
        
        Args:
            name: Original attribute name
            
        Returns:
            Sanitized attribute name
        """
        # Replace invalid characters
        sanitized = name.replace('-', '_').replace('.', '_').replace(' ', '_')
        
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = f"_{sanitized}"
            
        # Handle reserved keywords
        python_keywords = ['class', 'def', 'return', 'if', 'else', 'for', 'while', 'import', 'from']
        if sanitized in python_keywords:
            sanitized = f"{sanitized}_config"
            
        return sanitized
    
    def get_section(self, section_name: str) -> Optional[DynamicConfig]:
        """
        Get a specific configuration section.
        
        Args:
            section_name: Name of the configuration section
            
        Returns:
            DynamicConfig object for the section or None if not found
        """
        attr_name = self._sanitize_attribute_name(section_name)
        return getattr(self, attr_name, None)
    
    def has_section(self, section_name: str) -> bool:
        """
        Check if a configuration section exists.
        
        Args:
            section_name: Name of the configuration section
            
        Returns:
            True if section exists, False otherwise
        """
        attr_name = self._sanitize_attribute_name(section_name)
        return hasattr(self, attr_name)
    
    def get_value(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value by path.
        
        Args:
            path: Dot-separated path to the value (e.g., "llm.provider")
            default: Default value if path is not found
            
        Returns:
            Configuration value or default
        """
        try:
            parts = path.split('.')
            if not parts:
                return default
                
            section_name = parts[0]
            section = self.get_section(section_name)
            
            if section is None:
                return default
                
            if len(parts) == 1:
                return section
                
            # Get nested value
            nested_path = '.'.join(parts[1:])
            return section.get(nested_path, default)
            
        except Exception as e:
            logger.error(f"Error getting configuration value for path '{path}': {e}")
            return default
    
    def reload(self):
        """Reload all profile configurations from files."""
        logger.info("Reloading profile configurations...")
        self._load_profile_configurations()
    
    def reload_profile(self, profile_name: str):
        """
        Reload a specific profile configuration.
        
        Args:
            profile_name: Name of the profile to reload
        """
        if profile_name not in self._profile_files:
            logger.warning(f"Profile '{profile_name}' not found in loaded profiles")
            return
            
        file_path = self._profile_files[profile_name]
        try:
            profile_data = YamlLoader.load_file(file_path, raise_on_missing=False)
            if profile_data:
                # Resolve environment variable placeholders
                resolved_data = self._property_resolver.resolve_dict(profile_data)
                
                # Update the specific profile
                attr_name = self._sanitize_attribute_name(profile_name)
                setattr(self, attr_name, DynamicConfig(resolved_data))
                logger.info(f"Reloaded and resolved profile '{profile_name}' from {file_path}")
            else:
                logger.warning(f"Profile file {file_path} is empty after reload")
        except Exception as e:
            logger.error(f"Error reloading profile '{profile_name}' from {file_path}: {e}")
    
    def get_profile_names(self) -> List[str]:
        """
        Get list of all loaded profile names.
        
        Returns:
            List of profile names
        """
        return list(self._profile_files.keys())
    
    def get_profile_file_path(self, profile_name: str) -> Optional[str]:
        """
        Get the file path for a specific profile.
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            File path if profile exists, None otherwise
        """
        return self._profile_files.get(profile_name)
    
    def list_sections(self) -> list[str]:
        """
        List all available configuration sections.
        
        Returns:
            List of section names
        """
        sections = []
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                sections.append(attr_name)
        return sections
    
    def validate_environment_variables(self) -> Dict[str, List[str]]:
        """
        Validate that all required environment variables are available.
        
        Returns:
            Dictionary with validation results:
            {
                'missing': List of missing required variables,
                'available': List of available variables,
                'with_defaults': List of variables that have defaults
            }
        """
        from ...utils.env_utils import env
        
        all_vars = set()
        vars_with_defaults = set()
        
        # Scan all profile files for placeholder variables
        for profile_name, file_path in self._profile_files.items():
            try:
                # Load raw YAML without resolution
                raw_data = YamlLoader.load_file(file_path, raise_on_missing=False)
                if raw_data:
                    # Extract variables
                    profile_vars = self._property_resolver._extract_all_variables(raw_data)
                    all_vars.update(profile_vars)
                    
                    # Check which have defaults
                    for var in profile_vars:
                        if self._property_resolver._variable_has_default_in_data(var, raw_data):
                            vars_with_defaults.add(var)
                            
            except Exception as e:
                logger.warning(f"Could not scan profile '{profile_name}' for variables: {e}")
        
        # Check availability
        available_vars = [var for var in all_vars if env.has(var)]
        missing_vars = [var for var in all_vars if not env.has(var) and var not in vars_with_defaults]
        
        return {
            'missing': missing_vars,
            'available': available_vars,
            'with_defaults': list(vars_with_defaults),
            'all_referenced': list(all_vars)
        }
    
    def get_placeholder_info(self) -> Dict[str, Any]:
        """
        Get information about placeholders used in configuration.
        
        Returns:
            Dictionary with placeholder usage information
        """
        placeholder_info = {
            'profiles_with_placeholders': {},
            'total_placeholders': 0,
            'unique_variables': set()
        }
        
        for profile_name, file_path in self._profile_files.items():
            try:
                raw_data = YamlLoader.load_file(file_path, raise_on_missing=False)
                if raw_data:
                    profile_vars = self._property_resolver._extract_all_variables(raw_data)
                    if profile_vars:
                        placeholder_info['profiles_with_placeholders'][profile_name] = profile_vars
                        placeholder_info['total_placeholders'] += len(profile_vars)
                        placeholder_info['unique_variables'].update(profile_vars)
                        
            except Exception as e:
                logger.warning(f"Could not analyze placeholders in profile '{profile_name}': {e}")
        
        placeholder_info['unique_variables'] = list(placeholder_info['unique_variables'])
        return placeholder_info
    
    @staticmethod
    def get_profiles_setting() -> List[str]:
        """
        Get the current PROFILES setting.
        
        Returns:
            List of profile names to load, or ['*'] for all profiles
        """
        return PROFILES.copy()
    
    @staticmethod
    def set_profiles_setting(profiles: List[str]):
        """
        Set the PROFILES setting for controlling which profiles to load.
        Note: This affects new Settings instances, not existing ones.
        Use reload_profiles() to apply changes to existing instance.
        
        Args:
            profiles: List of profile names to load, or ['*'] for all profiles
            
        Examples:
            Settings.set_profiles_setting(['*'])  # Load all profiles
            Settings.set_profiles_setting(['db', 'llm', 'app'])  # Load specific profiles
        """
        global PROFILES
        PROFILES = profiles.copy()
        logger.info(f"PROFILES setting updated to: {PROFILES}")
    
    def reload_profiles(self):
        """
        Reload profile configurations using current PROFILES setting.
        This re-discovers and reloads profiles, useful after changing PROFILES setting.
        """
        logger.info("Reloading profile configurations...")
        self._profile_files.clear()
        self._config_cache.clear()
        self._load_profile_configurations()
        logger.info(f"Profile reload complete. Active profiles: {self.get_profile_names()}")
    
    def __repr__(self) -> str:
        """String representation of the settings manager."""
        profiles = self.get_profile_names()
        sections = self.list_sections()
        return f"Settings(profiles={profiles}, sections={sections})"


# Module-level instance for convenient access throughout the application
settings = Settings.instance()
