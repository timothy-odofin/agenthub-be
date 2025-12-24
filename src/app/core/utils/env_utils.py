"""
Environment variable utility for centralized environment access.

Provides a clean interface for accessing environment variables with
type conversion, validation, and fallback support.
"""
import os
from typing import Any, Optional, Union, List, Dict, Type, TypeVar
from pathlib import Path

T = TypeVar('T')


class EnvironmentManager:
    """Centralized environment variable manager."""
    
    def __init__(self, load_dotenv: bool = True):
        """Initialize environment manager.
        
        Args:
            load_dotenv: Whether to load .env file if available
        """
        self._cache: Dict[str, Any] = {}
        self._load_dotenv = load_dotenv
        
        if load_dotenv:
            self._load_env_file()
    
    def _load_env_file(self) -> None:
        """Load .env file if it exists."""
        try:
            from dotenv import load_dotenv
            env_path = self._find_env_file()
            if env_path and env_path.exists():
                load_dotenv(env_path, override=False)  # Don't override existing env vars
                logger = self._get_logger()
                logger.info(f"Loaded environment variables from {env_path}")
        except ImportError:
            # python-dotenv not installed, skip
            logger = self._get_logger()
            logger.warning("python-dotenv not installed, skipping .env file loading")
        except Exception as e:
            logger = self._get_logger()
            logger.warning(f"Error loading .env file: {e}")
    
    def _get_logger(self):
        """Get logger instance, avoiding import issues."""
        import logging
        return logging.getLogger(__name__)
    
    def _find_env_file(self) -> Optional[Path]:
        """Find .env file in current or parent directories."""
        current = Path.cwd()
        
        # Check current directory and up to 3 parent levels
        for _ in range(4):
            env_file = current / '.env'
            if env_file.exists():
                return env_file
            
            parent = current.parent
            if parent == current:  # Reached root
                break
            current = parent
        
        return None
    
    def get(self, 
            key: str, 
            default: Optional[T] = None, 
            required: bool = False,
            var_type: Optional[Type[T]] = None) -> Optional[T]:
        """Get environment variable with type conversion and validation.
        
        Args:
            key: Environment variable name
            default: Default value if variable not found
            required: Whether the variable is required (raises if missing)
            var_type: Type to convert the value to
            
        Returns:
            Environment variable value, converted to specified type
            
        Raises:
            ValueError: If required variable is missing or conversion fails
        """
        # Check cache first
        cache_key = f"{key}:{var_type.__name__ if var_type else 'str'}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get raw value
        raw_value = os.getenv(key)
        
        if raw_value is None:
            if required:
                raise ValueError(f"Required environment variable '{key}' is not set")
            result = default
        else:
            # Determine target type with proper precedence
            if var_type is not None:
                target_type = var_type
            elif default is not None:
                target_type = type(default)
            else:
                target_type = str
            
            result = self._convert_value(raw_value, target_type)
        
        # Cache the result
        self._cache[cache_key] = result
        return result
    
    def get_string(self, key: str, default: str = "", required: bool = False) -> str:
        """Get string environment variable."""
        return self.get(key, default, required, str) or ""
    
    def get_int(self, key: str, default: int = 0, required: bool = False) -> int:
        """Get integer environment variable."""
        return self.get(key, default, required, int) or 0
    
    def get_float(self, key: str, default: float = 0.0, required: bool = False) -> float:
        """Get float environment variable."""
        return self.get(key, default, required, float) or 0.0
    
    def get_bool(self, key: str, default: bool = False, required: bool = False) -> bool:
        """Get boolean environment variable."""
        return self.get(key, default, required, bool) or False
    
    def get_list(self, key: str, default: Optional[List[str]] = None, 
                 separator: str = ",", required: bool = False) -> List[str]:
        """Get list environment variable (comma-separated by default)."""
        if default is None:
            default = []
            
        raw_value = self.get_string(key, "", required)
        if not raw_value:
            return default
            
        return [item.strip() for item in raw_value.split(separator) if item.strip()]
    
    def _convert_value(self, value: str, target_type: Type[T]) -> T:
        """Convert string value to target type.
        
        Args:
            value: String value to convert
            target_type: Target type for conversion
            
        Returns:
            Converted value
            
        Raises:
            ValueError: If conversion fails
        """
        if target_type == str:
            return value  # type: ignore
        
        if target_type == bool:
            return self._parse_bool(value)  # type: ignore
        
        if target_type == int:
            try:
                return int(value)  # type: ignore
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to integer")
        
        if target_type == float:
            try:
                return float(value)  # type: ignore
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to float")
        
        if target_type == list:
            return value.split(',')  # type: ignore
        
        # Try direct conversion for other types
        try:
            return target_type(value)  # type: ignore
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert '{value}' to {target_type.__name__}: {e}")
    
    def _parse_bool(self, value: str) -> bool:
        """Parse boolean value from string."""
        value_lower = value.lower().strip()
        
        if value_lower in ('true', '1', 'yes', 'on', 'enabled'):
            return True
        elif value_lower in ('false', '0', 'no', 'off', 'disabled', ''):
            return False
        else:
            raise ValueError(f"Cannot convert '{value}' to boolean. "
                           f"Expected: true/false, 1/0, yes/no, on/off, enabled/disabled")
    
    def has(self, key: str) -> bool:
        """Check if environment variable exists."""
        return key in os.environ
    
    def list_variables(self, prefix: str = "") -> Dict[str, str]:
        """List all environment variables with optional prefix filter."""
        if prefix:
            return {k: v for k, v in os.environ.items() if k.startswith(prefix)}
        return dict(os.environ)
    
    def clear_cache(self) -> None:
        """Clear the internal cache."""
        self._cache.clear()
    
    def reload_env(self) -> None:
        """Reload environment variables from .env file."""
        self.clear_cache()
        if self._load_dotenv:
            self._load_env_file()


# Global instance for convenience
env = EnvironmentManager()
