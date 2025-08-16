"""
Security validation and protection for fbapi.

This module provides security features including path traversal protection,
file permission validation, and input sanitization.
"""

import os
import logging
from pathlib import Path
from typing import Optional

from .exceptions import SecurityError

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Validates file operations for security compliance."""
    
    def __init__(self, allowed_base_paths: Optional[list] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB default
                 allowed_extensions: Optional[list] = None):
        """
        Initialize security validator.
        
        Args:
            allowed_base_paths: List of allowed base directory paths
            max_file_size: Maximum allowed file size in bytes
            allowed_extensions: List of allowed file extensions (default: ['.json'])
        """
        self.allowed_base_paths = allowed_base_paths or []
        self.max_file_size = max_file_size
        self.allowed_extensions = allowed_extensions or ['.json']
    
    def validate_file_path(self, file_path: str) -> bool:
        """
        Validate file path for security compliance.
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if path is valid and safe
            
        Raises:
            SecurityError: If path is dangerous
        """
        try:
            # Convert to Path object for safer handling
            path = Path(file_path).resolve()
            
            # Check for path traversal attempts
            if self._has_path_traversal(str(path)):
                logger.warning(f"Path traversal detected in: {file_path}")
                return False
            
            # Validate against allowed base paths if configured
            if self.allowed_base_paths and not self._is_within_allowed_paths(path):
                logger.warning(f"Path outside allowed directories: {file_path}")
                return False
            
            # Check file extension
            if path.suffix not in self.allowed_extensions:
                logger.warning(f"Invalid file extension: {path.suffix}")
                return False
            
            # Check file size if file exists
            if path.exists() and path.is_file():
                if path.stat().st_size > self.max_file_size:
                    logger.warning(f"File too large: {path.stat().st_size} bytes")
                    return False
            
            return True
            
        except (OSError, ValueError) as e:
            logger.error(f"Error validating path {file_path}: {e}")
            return False
    
    def _has_path_traversal(self, file_path: str) -> bool:
        """Check for path traversal patterns."""
        dangerous_patterns = ['../', '..\\', '../', '..\\\\']
        normalized_path = os.path.normpath(file_path)
        
        return any(pattern in file_path for pattern in dangerous_patterns) or \
               any(pattern in normalized_path for pattern in dangerous_patterns)
    
    def _is_within_allowed_paths(self, path: Path) -> bool:
        """Check if path is within allowed base directories."""
        try:
            for allowed_base in self.allowed_base_paths:
                allowed_path = Path(allowed_base).resolve()
                if path.is_relative_to(allowed_path):
                    return True
            return False
        except (OSError, ValueError):
            return False
    
    def validate_directory_access(self, directory: str) -> bool:
        """
        Validate directory access permissions.
        
        Args:
            directory: Directory path to validate
            
        Returns:
            True if directory access is safe
        """
        try:
            path = Path(directory).resolve()
            
            # Check if directory exists
            if not path.exists():
                logger.error(f"Directory does not exist: {directory}")
                return False
            
            # Check if it's actually a directory
            if not path.is_dir():
                logger.error(f"Path is not a directory: {directory}")
                return False
            
            # Check read/write permissions
            if not os.access(path, os.R_OK | os.W_OK):
                logger.error(f"Insufficient permissions for directory: {directory}")
                return False
            
            # Validate against allowed paths
            if self.allowed_base_paths and not self._is_within_allowed_paths(path):
                logger.error(f"Directory outside allowed paths: {directory}")
                return False
            
            return True
            
        except (OSError, ValueError) as e:
            logger.error(f"Error validating directory {directory}: {e}")
            return False
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing dangerous characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        sanitized = filename
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Ensure filename is not empty after sanitization
        if not sanitized or sanitized.isspace():
            sanitized = 'sanitized_file.json'
        
        # Ensure proper extension
        if not sanitized.endswith('.json'):
            sanitized += '.json'
        
        return sanitized
    
    def validate_json_content(self, content: str) -> bool:
        """
        Basic validation of JSON content for security.
        
        Args:
            content: JSON content to validate
            
        Returns:
            True if content appears safe
        """
        # Check content length
        if len(content) > self.max_file_size:
            logger.warning("JSON content exceeds maximum size")
            return False
        
        # Check for suspicious patterns (basic)
        suspicious_patterns = [
            'eval(',
            'exec(',
            'import ',
            '__import__',
            'subprocess',
            'os.system'
        ]
        
        content_lower = content.lower()
        for pattern in suspicious_patterns:
            if pattern in content_lower:
                logger.warning(f"Suspicious pattern detected: {pattern}")
                return False
        
        return True