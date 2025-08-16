"""
Enhanced file-based API client with event-driven monitoring and security features.
"""

import json
import os
import uuid
import time
import logging
from pathlib import Path
from typing import Callable, Optional, Dict, Any

from jsonschema import validate, ValidationError as JsonSchemaValidationError

from .exceptions import ValidationError, TimeoutError, SecurityError, FileSystemError
from .monitoring import create_monitor, FileMonitor
from .security import SecurityValidator
from .schemas import SchemaManager

logger = logging.getLogger(__name__)


class ResponseHandler:
    """Handles response processing with event-driven monitoring."""
    
    def __init__(self, response_file: str, response_dir: str, command_dir: str,
                 callback: Callable[[str], None], timeout_seconds: float = 60.0,
                 monitoring_strategy: str = "auto",
                 security_validator: Optional[SecurityValidator] = None):
        self.response_file = response_file
        self.response_dir = Path(response_dir)
        self.command_dir = Path(command_dir)
        self.callback = callback
        self.timeout_seconds = timeout_seconds
        self.security_validator = security_validator or SecurityValidator()
        self.start_time = time.time()
        self.completed = False
        
        # Create monitor for response directory
        self.monitor = create_monitor(
            str(self.response_dir),
            self._handle_file_event,
            monitoring_strategy=monitoring_strategy,
            security_validator=security_validator
        )
    
    def start_monitoring(self) -> None:
        """Start monitoring for response file."""
        logger.debug(f"Starting response monitoring for {self.response_file}")
        self.monitor.start()
        
        # Start timeout monitoring in separate thread
        import threading
        timeout_thread = threading.Thread(target=self._timeout_monitor, daemon=True)
        timeout_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop monitoring for response file."""
        self.monitor.stop()
        self.completed = True
    
    def _handle_file_event(self, file_path: str) -> None:
        """Handle file system events."""
        file_name = os.path.basename(file_path)
        
        if file_name == self.response_file and not self.completed:
            logger.debug(f"Processing response: {file_name}")
            try:
                self.callback(file_path)
                self.completed = True
                
                # Cleanup files
                self._cleanup_files()
                
            except Exception as e:
                logger.error(f"Error processing response {file_path}: {e}")
            finally:
                self.stop_monitoring()
    
    def _timeout_monitor(self) -> None:
        """Monitor for timeout conditions."""
        while not self.completed:
            if time.time() - self.start_time > self.timeout_seconds:
                logger.warning(f"Timeout reached for response {self.response_file}")
                self.completed = True
                self._cleanup_files()
                self.stop_monitoring()
                break
            time.sleep(1.0)
    
    def _cleanup_files(self) -> None:
        """Clean up command and response files."""
        try:
            command_file = self.command_dir / self.response_file
            if command_file.exists():
                command_file.unlink()
                
            response_file = self.response_dir / self.response_file
            if response_file.exists():
                response_file.unlink()
                
        except OSError as e:
            logger.warning(f"Error cleaning up files: {e}")


class FileBasedAPIClient:
    """Enhanced file-based API client with event-driven monitoring."""
    
    def __init__(self, command_dir: str, response_dir: str,
                 timeout_seconds: float = 60.0,
                 monitoring_strategy: str = "auto",
                 security_validator: Optional[SecurityValidator] = None,
                 schema_manager: Optional[SchemaManager] = None):
        """
        Initialize the file-based API client.
        
        Args:
            command_dir: Directory to write command files
            response_dir: Directory to monitor for responses
            timeout_seconds: Default timeout for commands
            monitoring_strategy: "auto", "event", or "polling"
            security_validator: Security validator instance
            schema_manager: Schema manager for validation
        """
        self.command_dir = Path(command_dir)
        self.response_dir = Path(response_dir)
        self.timeout_seconds = timeout_seconds
        self.monitoring_strategy = monitoring_strategy
        self.security_validator = security_validator or SecurityValidator(
            allowed_base_paths=[str(self.command_dir), str(self.response_dir)]
        )
        self.schema_manager = schema_manager or SchemaManager()
        
        # Response handlers tracking
        self.response_handlers: Dict[str, ResponseHandler] = {}
        
        # Initialize directories
        self._setup_directories()
        
        logger.info(f"FileBasedAPIClient initialized with {monitoring_strategy} monitoring")
    
    def _setup_directories(self) -> None:
        """Setup and validate directories."""
        for directory in [self.command_dir, self.response_dir]:
            if not self.security_validator.validate_directory_access(str(directory)):
                raise SecurityError(f"Invalid directory access: {directory}")
            
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate_json(self, data: Dict[str, Any], schema_type: str) -> None:
        """
        Validate JSON data against schema.
        
        Args:
            data: Data to validate
            schema_type: Type of schema ("request" or "response")
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            schema = self.schema_manager.get_schema(schema_type)
            validate(instance=data, schema=schema)
        except JsonSchemaValidationError as e:
            raise ValidationError(f"Schema validation failed: {e.message}", str(e))
    
    def is_monitoring(self) -> bool:
        """Check if any response handlers are actively monitoring."""
        return any(not handler.completed for handler in self.response_handlers.values())
    
    def call_command(self, command_name: str, callback: Callable[[Dict[str, Any]], None],
                     timeout_seconds: Optional[float] = None, **kwargs) -> str:
        """
        Call a command and handle the response asynchronously.
        
        Args:
            command_name: Name of the command to execute
            callback: Function to call with response data
            timeout_seconds: Command-specific timeout override
            **kwargs: Command parameters
            
        Returns:
            Request ID for tracking
            
        Raises:
            ValidationError: If command validation fails
            SecurityError: If security validation fails
            FileSystemError: If file operations fail
        """
        request_id = str(uuid.uuid4())
        command_file = f"cmd_{request_id}.json"
        command_path = self.command_dir / command_file
        
        # Use command-specific timeout or default
        timeout = timeout_seconds or self.timeout_seconds
        
        logger.debug(f"Calling command: {command_name} with ID: {request_id}")
        
        # Validate command file path
        if not self.security_validator.validate_file_path(str(command_path)):
            raise SecurityError(f"Invalid command file path: {command_path}")
        
        # Prepare command data - simplified parameter handling for now
        params_list = []
        for key, value in kwargs.items():
            params_list.append({
                "name": key,
                "type": "generic",
                "value": value
            })
        
        command_data = {
            "command": command_name,
            "params": params_list,
            "request_id": request_id,
            "response_file": command_file
        }
        
        # Validate command data
        self.validate_json(command_data, "request")
        
        # Validate JSON content security
        command_json = json.dumps(command_data)
        if not self.security_validator.validate_json_content(command_json):
            raise SecurityError("Command content failed security validation")
        
        try:
            # Write command file
            with open(command_path, 'w') as f:
                json.dump(command_data, f, indent=2)
            
            # Setup response handler
            response_handler = ResponseHandler(
                command_file,
                str(self.response_dir),
                str(self.command_dir),
                lambda path: self._process_response(path, callback),
                timeout,
                self.monitoring_strategy,
                self.security_validator
            )
            
            self.response_handlers[request_id] = response_handler
            response_handler.start_monitoring()
            
            return request_id
            
        except OSError as e:
            raise FileSystemError(f"Failed to write command file: {e}")
    
    def _process_response(self, response_path: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Process response file and call user callback."""
        try:
            with open(response_path, 'r') as f:
                response_data = json.load(f)
            
            # Validate response data
            self.validate_json(response_data, "response")
            
            # Call user callback with response data
            callback(response_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in response file {response_path}: {e}")
        except ValidationError as e:
            logger.error(f"Response validation failed for {response_path}: {e}")
        except Exception as e:
            logger.error(f"Error processing response {response_path}: {e}")
    
    def wait_for_completion(self, timeout_seconds: Optional[float] = None) -> None:
        """
        Wait for all pending commands to complete.
        
        Args:
            timeout_seconds: Maximum time to wait
            
        Raises:
            TimeoutError: If timeout is reached
        """
        start_time = time.time()
        max_timeout = timeout_seconds or (self.timeout_seconds * 2)
        
        while self.is_monitoring():
            if time.time() - start_time > max_timeout:
                raise TimeoutError(f"Wait timeout after {max_timeout} seconds")
            time.sleep(0.1)
    
    def cleanup(self) -> None:
        """Clean up all response handlers and resources."""
        logger.info("Cleaning up FileBasedAPIClient")
        
        for handler in self.response_handlers.values():
            handler.stop_monitoring()
        
        self.response_handlers.clear()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()