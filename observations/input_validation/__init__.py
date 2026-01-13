"""
Input validation for observations.
"""
from pathlib import Path
from typing import Union

def validate_filesystem_access(path: Union[str, Path]) -> bool:
    """Check if filesystem path is accessible."""
    path = Path(path)
    return path.exists()

def validate_binary_file(path: Union[str, Path]) -> bool:
    """
    Check if file is binary.
    Returns True if valid (not binary or binary allowed), False if invalid binary.
    Actually the name suggests 'validate THAT it is a binary file' or 'validate AGAINST being a binary file'?
    Context in observations usually means 'check if we can read it as text'.
    
    If it returns True, it means 'validated', i.e. OK to proceed?
    
    Let's assume it checks if it's safe to read.
    """
    # Simple check for null bytes
    path = Path(path)
    if not path.is_file():
        return True
        
    try:
        with open(path, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return False # Is binary
    except Exception:
        return False
        
    return True

def validate_size_limits(path: Union[str, Path], limit_mb: int = 100) -> bool:
    """Check if file size is within limits."""
    path = Path(path)
    if not path.is_file():
        return True
    
    try:
        size = path.stat().st_size
        return size <= limit_mb * 1024 * 1024
    except Exception:
        return False

def is_safe_to_observe(path: Union[str, Path]) -> bool:
    """
    Comprehensive safety check.
    """
    path = Path(path)
    if not validate_filesystem_access(path):
        return False
        
    # If it's a directory, it's generally safe to observe structure
    if path.is_dir():
        return True
        
    # Check size
    if not validate_size_limits(path):
        return False
        
    # We might allow binary files for FileSight but maybe not for content eyes.
    # But this is a general check.
    
    return True

__all__ = [
    "validate_filesystem_access",
    "validate_binary_file",
    "validate_size_limits",
    "is_safe_to_observe",
]
