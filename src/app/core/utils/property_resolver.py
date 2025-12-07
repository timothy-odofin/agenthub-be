"""
Property placeholder resolution utility.

Handles Spring Boot-style property placeholders in configuration values,
resolving them with environment variables and providing fallback support.
"""
import re
from typing import Any, Dict, Optional, Union, List
from .env_utils import env


class PropertyResolver:
    """Resolves property placeholders in configuration values."""
    
    # Spring Boot style: ${VARIABLE_NAME:default_value}
    PLACEHOLDER_PATTERN = re.compile(r'\$\{([^}:]+)(?::([^}]*))?\}')
    
    def __init__(self, environment_manager: Optional[Any] = None):
        """Initialize property resolver.
        
        Args:
            environment_manager: Environment manager instance (defaults to global env)
        """
        self.env_manager = environment_manager or env
        self._resolution_cache: Dict[str, Any] = {}
    
    def resolve_value(self, value: Any) -> Any:
        """Resolve placeholders in a single value.
        
        Args:
            value: Value that may contain placeholders
            
        Returns:
            Value with placeholders resolved
        """
        if not isinstance(value, str):
            return value
        
        # Check cache first
        if value in self._resolution_cache:
            return self._resolution_cache[value]
        
        resolved = self._resolve_string_placeholders(value)
        
        # Convert to appropriate type if the entire value was a placeholder
        if value != resolved:
            resolved = self._convert_resolved_value(resolved, value)
        
        # Cache the result
        self._resolution_cache[value] = resolved
        return resolved
    
    def resolve_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively resolve placeholders in a dictionary.
        
        Args:
            data: Dictionary containing values with potential placeholders
            
        Returns:
            Dictionary with all placeholders resolved
        """
        resolved = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                resolved[key] = self.resolve_dict(value)
            elif isinstance(value, list):
                resolved[key] = self.resolve_list(value)
            else:
                resolved[key] = self.resolve_value(value)
        
        return resolved
    
    def resolve_list(self, data: List[Any]) -> List[Any]:
        """Resolve placeholders in a list.
        
        Args:
            data: List containing values with potential placeholders
            
        Returns:
            List with all placeholders resolved
        """
        return [
            self.resolve_dict(item) if isinstance(item, dict)
            else self.resolve_list(item) if isinstance(item, list)
            else self.resolve_value(item)
            for item in data
        ]
    
    def _resolve_string_placeholders(self, value: str) -> str:
        """Resolve all placeholders in a string value.
        
        Args:
            value: String value containing placeholders
            
        Returns:
            String with placeholders resolved
        """
        def replace_placeholder(match) -> str:
            var_name = match.group(1).strip()
            default_value = match.group(2) if match.group(2) is not None else None
            
            # Get environment variable
            env_value = self.env_manager.get_string(var_name, "")
            
            # Return actual value, default, or empty string (which converts to None later)
            if env_value:
                return env_value
            elif default_value is not None:
                return default_value
            else:
                # No env value and no default - return special marker for None
                return "__PLACEHOLDER_NONE__"
        
        resolved = self.PLACEHOLDER_PATTERN.sub(replace_placeholder, value)
        
        # Convert special None marker to actual None if the entire value was a placeholder
        if resolved == "__PLACEHOLDER_NONE__" and self.PLACEHOLDER_PATTERN.fullmatch(value):
            return None
        
        # Replace any None markers in partial strings with empty strings
        return resolved.replace("__PLACEHOLDER_NONE__", "")
    
    def _convert_resolved_value(self, resolved_value: Any, original_value: str) -> Any:
        """Convert resolved string to appropriate type based on content.
        
        Args:
            resolved_value: The resolved value (could be None, string, etc.)
            original_value: The original value with placeholders
            
        Returns:
            Value converted to appropriate type
        """
        # Handle None values
        if resolved_value is None:
            return None
            
        # If not a string, return as-is
        if not isinstance(resolved_value, str):
            return resolved_value
            
        # If the original value was entirely a placeholder, try type conversion
        if self.PLACEHOLDER_PATTERN.fullmatch(original_value):
            return self._auto_convert_type(resolved_value)
        
        # If partial replacement, keep as string
        return resolved_value
    
    def _auto_convert_type(self, value: str) -> Any:
        """Automatically convert string to appropriate type.
        
        Args:
            value: String value to convert
            
        Returns:
            Value converted to detected type
        """
        if not value:
            return value
        
        # Try boolean
        if value.lower() in ('true', 'false', 'yes', 'no', 'on', 'off', 'enabled', 'disabled'):
            try:
                return self.env_manager._parse_bool(value)
            except ValueError:
                pass
        
        # Try integer
        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            try:
                return int(value)
            except ValueError:
                pass
        
        # Try float
        try:
            if '.' in value:
                return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def has_placeholders(self, value: Any) -> bool:
        """Check if a value contains placeholders.
        
        Args:
            value: Value to check
            
        Returns:
            True if value contains placeholders
        """
        if not isinstance(value, str):
            return False
        
        return bool(self.PLACEHOLDER_PATTERN.search(value))
    
    def extract_placeholder_variables(self, value: str) -> List[str]:
        """Extract all placeholder variable names from a value.
        
        Args:
            value: String value to analyze
            
        Returns:
            List of variable names found in placeholders
        """
        if not isinstance(value, str):
            return []
        
        matches = self.PLACEHOLDER_PATTERN.findall(value)
        return [match[0].strip() for match in matches]
    
    def validate_required_variables(self, data: Dict[str, Any], 
                                   required_vars: Optional[List[str]] = None) -> List[str]:
        """Validate that all required environment variables are available.
        
        Args:
            data: Configuration data to scan for placeholders
            required_vars: List of required variable names (if None, extract from data)
            
        Returns:
            List of missing required variables
        """
        if required_vars is None:
            required_vars = self._extract_all_variables(data)
        
        missing_vars = []
        for var_name in required_vars:
            if not self.env_manager.has(var_name):
                # Check if it has a default value in any placeholder
                has_default = self._variable_has_default_in_data(var_name, data)
                if not has_default:
                    missing_vars.append(var_name)
        
        return missing_vars
    
    def _extract_all_variables(self, data: Any) -> List[str]:
        """Recursively extract all placeholder variable names from data."""
        variables = []
        
        if isinstance(data, dict):
            for value in data.values():
                variables.extend(self._extract_all_variables(value))
        elif isinstance(data, list):
            for item in data:
                variables.extend(self._extract_all_variables(item))
        elif isinstance(data, str):
            variables.extend(self.extract_placeholder_variables(data))
        
        return list(set(variables))  # Remove duplicates
    
    def _variable_has_default_in_data(self, var_name: str, data: Any) -> bool:
        """Check if a variable has a default value in any placeholder within the data."""
        if isinstance(data, dict):
            return any(self._variable_has_default_in_data(var_name, value) for value in data.values())
        elif isinstance(data, list):
            return any(self._variable_has_default_in_data(var_name, item) for item in data)
        elif isinstance(data, str):
            matches = self.PLACEHOLDER_PATTERN.findall(data)
            for match in matches:
                if match[0].strip() == var_name and len(match) > 1 and match[1] is not None:
                    return True
        
        return False
    
    def clear_cache(self) -> None:
        """Clear the resolution cache."""
        self._resolution_cache.clear()


# Global instance for convenience
property_resolver = PropertyResolver()
