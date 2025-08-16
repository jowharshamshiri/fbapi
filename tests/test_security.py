"""
Unit tests for security validation functionality.
"""

import pytest
import tempfile
from pathlib import Path

from fbapi.security import SecurityValidator
from fbapi.exceptions import SecurityError


class TestSecurityValidator:
    """Test security validation functionality."""
    
    def test_init_default_settings(self):
        """Test SecurityValidator initialization with defaults."""
        validator = SecurityValidator()
        assert validator.allowed_base_paths == []
        assert validator.max_file_size == 10 * 1024 * 1024  # 10MB
        assert validator.allowed_extensions == ['.json']
    
    def test_init_custom_settings(self):
        """Test SecurityValidator initialization with custom settings."""
        validator = SecurityValidator(
            allowed_base_paths=['/tmp/test'],
            max_file_size=1024,
            allowed_extensions=['.json', '.yaml']
        )
        assert validator.allowed_base_paths == ['/tmp/test']
        assert validator.max_file_size == 1024
        assert validator.allowed_extensions == ['.json', '.yaml']
    
    def test_validate_file_path_valid(self, temp_dir):
        """Test validation of valid file paths."""
        validator = SecurityValidator(
            allowed_base_paths=[str(temp_dir)],
            allowed_extensions=['.json']
        )
        
        test_file = temp_dir / "test.json"
        test_file.touch()
        
        assert validator.validate_file_path(str(test_file)) is True
    
    def test_validate_file_path_traversal_attack(self, temp_dir):
        """Test detection of path traversal attacks."""
        validator = SecurityValidator(allowed_base_paths=[str(temp_dir)])
        
        # Test various path traversal patterns
        dangerous_paths = [
            str(temp_dir / "../etc/passwd"),
            str(temp_dir / "..\\windows\\system32"),
            "../sensitive_file.json",
            "..\\sensitive_file.json"
        ]
        
        for path in dangerous_paths:
            assert validator.validate_file_path(path) is False
    
    def test_validate_file_path_wrong_extension(self, temp_dir):
        """Test rejection of files with wrong extensions."""
        validator = SecurityValidator(
            allowed_base_paths=[str(temp_dir)],
            allowed_extensions=['.json']
        )
        
        test_file = temp_dir / "test.txt"
        test_file.touch()
        
        assert validator.validate_file_path(str(test_file)) is False
    
    def test_validate_file_path_too_large(self, temp_dir):
        """Test rejection of files that are too large."""
        validator = SecurityValidator(
            allowed_base_paths=[str(temp_dir)],
            max_file_size=100  # Very small limit
        )
        
        test_file = temp_dir / "large_file.json"
        with open(test_file, 'w') as f:
            f.write('x' * 200)  # Write more than max_file_size
        
        assert validator.validate_file_path(str(test_file)) is False
    
    def test_validate_file_path_outside_allowed_paths(self, temp_dir):
        """Test rejection of files outside allowed paths."""
        allowed_dir = temp_dir / "allowed"
        allowed_dir.mkdir()
        
        validator = SecurityValidator(allowed_base_paths=[str(allowed_dir)])
        
        # File in disallowed location
        disallowed_file = temp_dir / "disallowed.json"
        disallowed_file.touch()
        
        assert validator.validate_file_path(str(disallowed_file)) is False
    
    def test_validate_directory_access_valid(self, temp_dir):
        """Test validation of valid directory access."""
        validator = SecurityValidator()
        assert validator.validate_directory_access(str(temp_dir)) is True
    
    def test_validate_directory_access_nonexistent(self, temp_dir):
        """Test rejection of non-existent directory."""
        validator = SecurityValidator()
        nonexistent = temp_dir / "nonexistent"
        assert validator.validate_directory_access(str(nonexistent)) is False
    
    def test_validate_directory_access_not_directory(self, temp_dir):
        """Test rejection of file path when directory expected."""
        validator = SecurityValidator()
        test_file = temp_dir / "test.json"
        test_file.touch()
        assert validator.validate_directory_access(str(test_file)) is False
    
    def test_sanitize_filename_dangerous_chars(self):
        """Test filename sanitization removes dangerous characters."""
        validator = SecurityValidator()
        
        dangerous_name = "../evil/../file.json"
        sanitized = validator.sanitize_filename(dangerous_name)
        
        assert ".." not in sanitized
        assert "/" not in sanitized
        assert sanitized.endswith(".json")
    
    def test_sanitize_filename_empty_input(self):
        """Test sanitization of empty or whitespace-only filenames."""
        validator = SecurityValidator()
        
        assert validator.sanitize_filename("") == "sanitized_file.json"
        assert validator.sanitize_filename("   ") == "sanitized_file.json"
    
    def test_sanitize_filename_adds_extension(self):
        """Test that .json extension is added if missing."""
        validator = SecurityValidator()
        
        sanitized = validator.sanitize_filename("test_file")
        assert sanitized == "test_file.json"
    
    def test_validate_json_content_valid(self):
        """Test validation of safe JSON content."""
        validator = SecurityValidator()
        
        safe_content = '{"test": "value", "number": 123}'
        assert validator.validate_json_content(safe_content) is True
    
    def test_validate_json_content_too_large(self):
        """Test rejection of JSON content that's too large."""
        validator = SecurityValidator(max_file_size=100)
        
        large_content = '{"data": "' + 'x' * 200 + '"}'
        assert validator.validate_json_content(large_content) is False
    
    def test_validate_json_content_suspicious_patterns(self):
        """Test detection of suspicious patterns in JSON content."""
        validator = SecurityValidator()
        
        suspicious_contents = [
            '{"code": "eval(\\"malicious code\\")"}',
            '{"import": "os"}',
            '{"exec": "rm -rf /"}',
            '{"subprocess": "call"}',
            '{"system": "os.system(\\"bad\\")"}',
        ]
        
        for content in suspicious_contents:
            assert validator.validate_json_content(content) is False
    
    def test_has_path_traversal_detection(self):
        """Test internal path traversal detection method."""
        validator = SecurityValidator()
        
        # Test dangerous patterns
        dangerous_paths = [
            "../etc/passwd",
            "..\\windows\\system32",
            "/safe/path/../../../etc/passwd",
            "normal/../dangerous/file"
        ]
        
        for path in dangerous_paths:
            assert validator._has_path_traversal(path) is True
        
        # Test safe paths
        safe_paths = [
            "/safe/path/file.json",
            "relative/path/file.json",
            "/absolute/path/file.json"
        ]
        
        for path in safe_paths:
            assert validator._has_path_traversal(path) is False