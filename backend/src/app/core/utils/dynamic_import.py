"""
Generic utility for dynamic module imports with graceful error handling.

This module provides a reusable pattern for importing optional dependencies
that may not be available in all environments.
"""

import importlib
import warnings
from typing import List, Tuple, Dict, Any, Optional, Callable


class DynamicImporter:
    """
    A utility class for dynamically importing modules with graceful error handling.
    
    Useful for packages with optional dependencies where some modules may not
    be available depending on the installation.
    """
    
    def __init__(self, package_name: str, suppress_warnings: bool = False):
        """
        Initialize the dynamic importer.
        
        Args:
            package_name: The name of the package (for relative imports)
            suppress_warnings: Whether to suppress import warnings
        """
        self.package_name = package_name
        self.suppress_warnings = suppress_warnings
        self.imported_classes = []
        self.failed_imports = []
    
    def import_modules(
        self,
        modules: List[Tuple[str, str]],
        error_handler: Optional[Callable[[str, str, Exception], None]] = None
    ) -> List[Any]:
        """
        Import multiple modules dynamically.
        
        Args:
            modules: List of (module_name, class_name) tuples
            error_handler: Optional custom error handler function
            
        Returns:
            List of successfully imported classes
        """
        imported_classes = []
        
        for module_name, class_name in modules:
            try:
                # Try relative import first, then absolute
                try:
                    module = importlib.import_module(f'.{module_name}', package=self.package_name)
                except ImportError:
                    # Fallback to absolute import
                    full_module_name = f"{self.package_name}.{module_name}"
                    module = importlib.import_module(full_module_name)
                
                provider_class = getattr(module, class_name)
                imported_classes.append(provider_class)
                
                # Add to global namespace if needed
                if hasattr(self, '_target_globals'):
                    self._target_globals[class_name] = provider_class
                
            except ImportError as e:
                # Expected for optional dependencies
                self.failed_imports.append((module_name, class_name, str(e)))
                if not self.suppress_warnings:
                    warnings.warn(
                        f"Optional dependency not available: {module_name} ({e})",
                        ImportWarning
                    )
            except AttributeError as e:
                # Class not found in module
                error_msg = f"{class_name} not found in {module_name}: {e}"
                self.failed_imports.append((module_name, class_name, error_msg))
                if error_handler:
                    error_handler(module_name, class_name, e)
                elif not self.suppress_warnings:
                    warnings.warn(error_msg, ImportWarning)
            except Exception as e:
                # Unexpected errors
                error_msg = f"Unexpected error importing {class_name} from {module_name}: {e}"
                self.failed_imports.append((module_name, class_name, error_msg))
                if error_handler:
                    error_handler(module_name, class_name, e)
                else:
                    print(f"Warning: {error_msg}")
        
        self.imported_classes = imported_classes
        return imported_classes
    
    def update_globals(self, target_globals: Dict[str, Any]) -> None:
        """
        Update the target globals dictionary with imported classes.
        
        Args:
            target_globals: The globals() dictionary to update
        """
        self._target_globals = target_globals
        for cls in self.imported_classes:
            target_globals[cls.__name__] = cls
    
    def get_all_names(self) -> List[str]:
        """Get list of successfully imported class names for __all__."""
        return [cls.__name__ for cls in self.imported_classes]
    
    def get_import_summary(self) -> Dict[str, Any]:
        """Get a summary of import results."""
        return {
            'successful': len(self.imported_classes),
            'failed': len(self.failed_imports),
            'imported_classes': [cls.__name__ for cls in self.imported_classes],
            'failed_imports': self.failed_imports
        }


def import_providers(
    package_name: str,
    provider_modules: List[Tuple[str, str]],
    target_globals: Dict[str, Any],
    suppress_warnings: bool = False
) -> List[str]:
    """
    Convenience function for importing providers in __init__.py files.
    
    Args:
        package_name: The package name for relative imports
        provider_modules: List of (module_name, class_name) tuples
        target_globals: The globals() dictionary to update
        suppress_warnings: Whether to suppress import warnings
        
    Returns:
        List of successfully imported class names (for __all__)
        
    Example:
        # In __init__.py
        PROVIDER_MODULES = [
            ('openai_provider', 'OpenAILLM'),
            ('anthropic_provider', 'AnthropicLLM'),
        ]
        
        __all__ = import_providers(__name__, PROVIDER_MODULES, globals())
    """
    importer = DynamicImporter(package_name, suppress_warnings)
    importer.import_modules(provider_modules)
    importer.update_globals(target_globals)
    return importer.get_all_names()
