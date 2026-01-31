"""
Generic YAML loader utility for configuration files.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Use standard logging to avoid circular import
logger = logging.getLogger(__name__)


class YamlLoader:
    """Generic utility for loading YAML configuration files."""
    
    @staticmethod
    def load_file(file_path: str, raise_on_missing: bool = True) -> Dict[str, Any]:
        """
        Load a YAML file and return its contents as a dictionary.
        
        Args:
            file_path: Path to the YAML file (can be relative or absolute)
            raise_on_missing: Whether to raise an exception if file doesn't exist
            
        Returns:
            Dictionary containing the YAML file contents
            
        Raises:
            FileNotFoundError: If file doesn't exist and raise_on_missing is True
            yaml.YAMLError: If YAML parsing fails
        """
        try:
            # Convert to absolute path if relative
            if not os.path.isabs(file_path):
                # Look for file relative to project root
                project_root = YamlLoader._find_project_root()
                file_path = os.path.join(project_root, file_path)
            
            path = Path(file_path)
            
            if not path.exists():
                if raise_on_missing:
                    raise FileNotFoundError(f"YAML file not found: {file_path}")
                logger.warning(f"YAML file not found: {file_path}. Returning empty dict.")
                return {}
            
            logger.debug(f"Loading YAML file: {file_path}")
            
            with open(path, 'r', encoding='utf-8') as file:
                content = yaml.safe_load(file)
                
            if content is None:
                logger.warning(f"YAML file is empty: {file_path}")
                return {}
                
            logger.debug(f"Successfully loaded YAML file: {file_path}")
            return content
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading YAML file {file_path}: {e}")
            raise
    
    @staticmethod
    def load_multiple_files(*file_paths: str, merge: bool = True) -> Dict[str, Any]:
        """
        Load multiple YAML files and optionally merge them.
        
        Args:
            *file_paths: Variable number of file paths to load
            merge: Whether to merge all files into a single dictionary
            
        Returns:
            Dictionary containing merged contents or dict with filename keys
        """
        if not file_paths:
            return {}
        
        results = {}
        
        for file_path in file_paths:
            try:
                content = YamlLoader.load_file(file_path, raise_on_missing=False)
                if merge:
                    # Deep merge dictionaries
                    results = YamlLoader._deep_merge(results, content)
                else:
                    # Use filename as key
                    filename = Path(file_path).stem
                    results[filename] = content
                    
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
                
        return results
    
    @staticmethod
    def _find_project_root() -> str:
        """Find the project root directory by looking for common project files."""
        current = Path(__file__).absolute()
        
        # Look for project indicators
        indicators = ['pyproject.toml', 'setup.py', 'requirements.txt', '.git']
        
        for parent in current.parents:
            if any((parent / indicator).exists() for indicator in indicators):
                return str(parent)
                
        # Fallback to current directory
        return str(Path.cwd())
    
    @staticmethod
    def _deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.
        
        Args:
            dict1: Base dictionary
            dict2: Dictionary to merge into dict1
            
        Returns:
            Merged dictionary
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = YamlLoader._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
