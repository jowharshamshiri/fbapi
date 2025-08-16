"""
Custom exceptions for the fbapi library.
"""


class FBAPIError(Exception):
    """Base exception for all fbapi errors."""
    pass


class ValidationError(FBAPIError):
    """Raised when JSON schema validation fails."""
    
    def __init__(self, message: str, validation_error: str = None):
        super().__init__(message)
        self.validation_error = validation_error


class TimeoutError(FBAPIError):
    """Raised when operations timeout."""
    
    def __init__(self, message: str, timeout_seconds: float = None):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


class SecurityError(FBAPIError):
    """Raised when security violations are detected."""
    pass


class ConfigurationError(FBAPIError):
    """Raised when configuration is invalid."""
    pass


class FileSystemError(FBAPIError):
    """Raised when filesystem operations fail."""
    pass


class CommandError(FBAPIError):
    """Raised when command processing fails."""
    
    def __init__(self, message: str, command_name: str = None, request_id: str = None):
        super().__init__(message)
        self.command_name = command_name
        self.request_id = request_id