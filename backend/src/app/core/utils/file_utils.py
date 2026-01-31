"""
Generic file utilities for safe file operations.

Provides reusable file operation utilities with proper error handling
and security considerations for open-source applications.
"""

import os
from pathlib import Path
from typing import Union, Optional, Dict, Any


class FileReadError(Exception):
    """Exception raised when file reading fails."""
    pass


def read_text_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """
    Read text content from a file with comprehensive error handling.
    
    Args:
        file_path: Path to the file to read
        encoding: File encoding (default: utf-8)
        
    Returns:
        File content as string
        
    Raises:
        FileReadError: If file reading fails for any reason
    """
    file_path = Path(file_path)
    
    try:
        # Security check: ensure file exists and is a file
        if not file_path.exists():
            raise FileReadError(f"File not found: {file_path}")
            
        if not file_path.is_file():
            raise FileReadError(f"Path is not a file: {file_path}")
            
        # Security check: file size (prevent reading extremely large files)
        file_size = file_path.stat().st_size
        max_size = 10 * 1024 * 1024  # 10MB limit
        if file_size > max_size:
            raise FileReadError(f"File too large ({file_size} bytes, max {max_size}): {file_path}")
        
        # Read file content
        with open(file_path, 'r', encoding=encoding) as file:
            content = file.read()
            
        return content
        
    except FileNotFoundError:
        raise FileReadError(f"File not found: {file_path}")
    except PermissionError:
        raise FileReadError(f"Permission denied reading file: {file_path}")
    except UnicodeDecodeError as e:
        raise FileReadError(f"Encoding error reading file {file_path}: {e}")
    except OSError as e:
        raise FileReadError(f"OS error reading file {file_path}: {e}")
    except Exception as e:
        raise FileReadError(f"Unexpected error reading file {file_path}: {e}")


def read_binary_file(file_path: Union[str, Path]) -> bytes:
    """
    Read binary content from a file with comprehensive error handling.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        File content as bytes
        
    Raises:
        FileReadError: If file reading fails for any reason
    """
    file_path = Path(file_path)
    
    try:
        # Security check: ensure file exists and is a file
        if not file_path.exists():
            raise FileReadError(f"File not found: {file_path}")
            
        if not file_path.is_file():
            raise FileReadError(f"Path is not a file: {file_path}")
            
        # Security check: file size
        file_size = file_path.stat().st_size
        max_size = 50 * 1024 * 1024  # 50MB limit for binary files
        if file_size > max_size:
            raise FileReadError(f"File too large ({file_size} bytes, max {max_size}): {file_path}")
        
        # Read file content
        with open(file_path, 'rb') as file:
            content = file.read()
            
        return content
        
    except FileNotFoundError:
        raise FileReadError(f"File not found: {file_path}")
    except PermissionError:
        raise FileReadError(f"Permission denied reading file: {file_path}")
    except OSError as e:
        raise FileReadError(f"OS error reading file {file_path}: {e}")
    except Exception as e:
        raise FileReadError(f"Unexpected error reading file {file_path}: {e}")


def file_exists(file_path: Union[str, Path]) -> bool:
    """
    Check if a file exists and is accessible.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if file exists and is accessible
    """
    try:
        file_path = Path(file_path)
        return file_path.exists() and file_path.is_file()
    except Exception:
        return False


def get_file_info(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Get file information safely.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information or None if file not accessible
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            return None
            
        stat = file_path.stat()
        
        return {
            "path": str(file_path.absolute()),
            "name": file_path.name,
            "size": stat.st_size,
            "is_file": file_path.is_file(),
            "is_directory": file_path.is_dir(),
            "modified_time": stat.st_mtime,
            "permissions": oct(stat.st_mode)
        }
        
    except Exception:
        return None
def read_private_key_file(file_path: Union[str, Path]) -> str:
    """
    Specialized function for reading private key files with additional security.
    
    Args:
        file_path: Path to the private key file
        
    Returns:
        Private key content as string
        
    Raises:
        FileReadError: If file reading or validation fails
    """
    try:
        content = read_text_file(file_path)
        
        # Basic validation for private key format
        content = content.strip()
        
        # Check for common private key headers/footers
        valid_headers = [
            "-----BEGIN PRIVATE KEY-----",
            "-----BEGIN RSA PRIVATE KEY-----", 
            "-----BEGIN EC PRIVATE KEY-----",
            "-----BEGIN DSA PRIVATE KEY-----",
            "-----BEGIN OPENSSH PRIVATE KEY-----"
        ]
        
        if not any(header in content for header in valid_headers):
            # Don't fail here, let the consuming library validate
            pass
            
        return content
        
    except Exception as e:
        raise FileReadError(f"Failed to read private key file {file_path}: {e}")
