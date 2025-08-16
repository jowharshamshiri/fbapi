"""
fbapi - A general-purpose file-based API communication library

This library provides a robust, event-driven file-based API system for
inter-process communication using the filesystem as a communication medium.
"""

__version__ = "0.1.0"
__author__ = "fbapi contributors"

from .client import FileBasedAPIClient
from .server import FileBasedAPIServer, EventSystem
from .monitoring import EventDrivenMonitor, PollingMonitor
from .exceptions import (
    FBAPIError,
    ValidationError,
    TimeoutError,
    SecurityError,
    ConfigurationError,
)

__all__ = [
    "FileBasedAPIClient", 
    "FileBasedAPIServer",
    "EventSystem",
    "EventDrivenMonitor",
    "PollingMonitor", 
    "FBAPIError",
    "ValidationError",
    "TimeoutError",
    "SecurityError",
    "ConfigurationError",
]