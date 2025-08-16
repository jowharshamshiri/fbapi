"""
Enhanced file-based API server with event-driven monitoring and robust error handling.
"""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List
from collections.abc import Iterable, Mapping

from jsonschema import validate, ValidationError as JsonSchemaValidationError

from .exceptions import (
    ValidationError, CommandError, SecurityError, 
    FileSystemError, ConfigurationError
)
from .monitoring import create_monitor, FileMonitor
from .security import SecurityValidator
from .schemas import SchemaManager

logger = logging.getLogger(__name__)


class EventSystem:
    """Enhanced event system with better error handling and logging."""
    
    def __init__(self):
        self._listeners: Dict[str, Callable] = {}
        self._middleware: List[Callable] = []
    
    def on(self, event_name: str, callback: Callable) -> None:
        """
        Register a callback for an event.
        
        Args:
            event_name: Name of the event to listen for
            callback: Function to call when event is triggered
        """
        self._listeners[event_name] = callback
        logger.debug(f"Registered handler for event: {event_name}")
    
    def add_middleware(self, middleware: Callable) -> None:
        """
        Add middleware that processes all events.
        
        Args:
            middleware: Function that takes (event_name, *args, **kwargs) and returns modified args
        """
        self._middleware.append(middleware)
        logger.debug("Added middleware to event system")
    
    def trigger(self, event_name: str, *args, **kwargs) -> List[Any]:
        """
        Trigger an event and return results.
        
        Args:
            event_name: Name of event to trigger
            *args: Positional arguments for the event handler
            **kwargs: Keyword arguments for the event handler
            
        Returns:
            List of results from event handler
        """
        # Apply middleware
        for middleware in self._middleware:
            try:
                args, kwargs = middleware(event_name, *args, **kwargs)
            except Exception as e:
                logger.warning(f"Middleware error for event {event_name}: {e}")
        
        # Get the handler
        callback = self._listeners.get(event_name)
        
        if not callback:
            logger.warning(f"No listener registered for event: {event_name}")
            return []
        
        try:
            # Call the handler
            logger.debug(f"Triggering event: {event_name}")
            result = callback(*args, **kwargs)
            
            # Process results
            if result is None:
                return []
            elif isinstance(result, Iterable) and not isinstance(result, Mapping):
                return list(result)
            else:
                return [result]
                
        except Exception as e:
            logger.error(f"Error in event handler for {event_name}: {e}")
            logger.debug(traceback.format_exc())
            raise CommandError(f"Event handler failed: {e}", event_name)
    
    def get_registered_events(self) -> List[str]:
        """Get list of registered event names."""
        return list(self._listeners.keys())


class CommandHandler:
    """Handles command processing with enhanced monitoring and error handling."""
    
    def __init__(self, command_dir: str, response_dir: str, event_system: EventSystem,
                 monitoring_strategy: str = "auto",
                 security_validator: Optional[SecurityValidator] = None,
                 schema_manager: Optional[SchemaManager] = None):
        """
        Initialize command handler.
        
        Args:
            command_dir: Directory to monitor for commands
            response_dir: Directory to write responses
            event_system: Event system for command handling
            monitoring_strategy: "auto", "event", or "polling"
            security_validator: Security validator instance
            schema_manager: Schema manager for validation
        """
        self.command_dir = Path(command_dir)
        self.response_dir = Path(response_dir)
        self.event_system = event_system
        self.security_validator = security_validator or SecurityValidator(
            allowed_base_paths=[str(self.command_dir), str(self.response_dir)]
        )
        self.schema_manager = schema_manager or SchemaManager()
        self.stop_requested = False
        
        # Setup monitoring
        self.monitor = create_monitor(
            str(self.command_dir),
            self._handle_command_file,
            monitoring_strategy=monitoring_strategy,
            security_validator=self.security_validator
        )
        
        # Validate directories
        self._setup_directories()
        
        logger.info(f"CommandHandler initialized with {monitoring_strategy} monitoring")
    
    def _setup_directories(self) -> None:
        """Setup and validate directories."""
        for directory in [self.command_dir, self.response_dir]:
            if not self.security_validator.validate_directory_access(str(directory)):
                raise SecurityError(f"Invalid directory access: {directory}")
            directory.mkdir(parents=True, exist_ok=True)
    
    def start_monitoring(self) -> None:
        """Start monitoring for command files."""
        logger.info(f"Starting command monitoring on {self.command_dir}")
        self.stop_requested = False
        self.monitor.start()
    
    def stop_monitoring(self) -> None:
        """Stop monitoring for command files."""
        logger.info(f"Stopping command monitoring on {self.command_dir}")
        self.stop_requested = True
        self.monitor.stop()
    
    def _handle_command_file(self, command_path: str) -> None:
        """Handle incoming command file."""
        if self.stop_requested:
            return
            
        try:
            # Validate file path
            if not self.security_validator.validate_file_path(command_path):
                raise SecurityError(f"Security validation failed for: {command_path}")
            
            # Process the command
            self._process_command(command_path)
            
        except Exception as e:
            logger.error(f"Error handling command file {command_path}: {e}")
            # Try to send error response if we can extract request info
            try:
                self._send_error_response(command_path, e)
            except Exception as cleanup_error:
                logger.error(f"Failed to send error response: {cleanup_error}")
        finally:
            # Always try to clean up the command file
            try:
                Path(command_path).unlink(missing_ok=True)
            except OSError as e:
                logger.warning(f"Failed to cleanup command file {command_path}: {e}")
    
    def _process_command(self, command_path: str) -> None:
        """Process a command file."""
        command_data = None
        
        try:
            # Read and parse command file
            with open(command_path, 'r') as f:
                command_data = json.load(f)
            
            logger.debug(f"Processing command: {command_path} - {command_data}")
            
            # Validate command structure
            self.schema_manager.get_schema("request")  # Ensure schema is loaded
            self._validate_command(command_data)
            
            # Extract command details
            event_name = command_data.get('command')
            request_id = command_data.get('request_id')
            response_file_name = command_data.get('response_file', 
                                                  f"response_{request_id}_{datetime.now().timestamp()}.json")
            
            if not event_name:
                raise CommandError("Command name is missing", request_id=request_id)
            
            # Trigger the event
            logger.debug(f"Triggering event: {event_name} for request: {request_id}")
            results = self.event_system.trigger(event_name, command_data)
            
            # Send success response
            self._send_success_response(request_id, response_file_name, results)
            
        except Exception as e:
            # Send error response
            request_id = command_data.get('request_id') if command_data else None
            response_file = command_data.get('response_file') if command_data else None
            self._send_error_response_data(request_id, response_file, e)
            raise
    
    def _validate_command(self, command_data: Dict[str, Any]) -> None:
        """
        Validate command data against schema.
        
        Args:
            command_data: Command data to validate
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            schema = self.schema_manager.get_schema("request")
            validate(instance=command_data, schema=schema)
            
            # Additional security validation
            command_json = json.dumps(command_data)
            if not self.security_validator.validate_json_content(command_json):
                raise SecurityError("Command content failed security validation")
                
        except JsonSchemaValidationError as e:
            raise ValidationError(f"Command validation failed: {e.message}", str(e))
    
    def _send_success_response(self, request_id: str, response_file_name: str, 
                             results: List[Any]) -> None:
        """Send success response."""
        try:
            # Format response data
            response_data = []
            for item in results:
                if isinstance(item, dict) and all(k in item for k in ['name', 'type', 'value']):
                    response_data.append(item)
                else:
                    # Wrap simple results in proper format
                    response_data.append({
                        "name": "result",
                        "type": "generic",
                        "value": item
                    })
            
            response_content = {
                "request_id": request_id,
                "status": "success",
                "response": response_data
            }
            
            # Validate response format
            schema = self.schema_manager.get_schema("response")
            validate(instance=response_content, schema=schema)
            
            # Write response file
            response_path = self.response_dir / response_file_name
            with open(response_path, 'w') as f:
                json.dump(response_content, f, indent=2)
            
            logger.debug(f"Success response written: {response_path}")
            
        except Exception as e:
            logger.error(f"Failed to send success response: {e}")
            raise FileSystemError(f"Response write failed: {e}")
    
    def _send_error_response_data(self, request_id: Optional[str], 
                                response_file_name: Optional[str], 
                                error: Exception) -> None:
        """Send error response with error details."""
        try:
            # Determine error code based on exception type
            if isinstance(error, ValidationError):
                error_code = 400
            elif isinstance(error, SecurityError):
                error_code = 403
            elif isinstance(error, CommandError):
                error_code = 500
            elif isinstance(error, TimeoutError):
                error_code = 408
            else:
                error_code = 500
            
            response_content = {
                "request_id": request_id or "unknown",
                "status": "error",
                "error": {
                    "code": error_code,
                    "message": str(error)
                }
            }
            
            # Use fallback filename if not provided
            if not response_file_name:
                response_file_name = f"error_response_{datetime.now().timestamp()}.json"
            
            # Write error response
            response_path = self.response_dir / response_file_name
            with open(response_path, 'w') as f:
                json.dump(response_content, f, indent=2)
            
            logger.debug(f"Error response written: {response_path}")
            
        except Exception as write_error:
            logger.error(f"Failed to write error response: {write_error}")
    
    def _send_error_response(self, command_path: str, error: Exception) -> None:
        """Send error response by extracting info from command file."""
        try:
            # Try to extract request info from command file
            with open(command_path, 'r') as f:
                command_data = json.load(f)
            
            request_id = command_data.get('request_id')
            response_file = command_data.get('response_file')
            
        except Exception:
            # If we can't read the command file, use defaults
            request_id = None
            response_file = None
        
        self._send_error_response_data(request_id, response_file, error)


class FileBasedAPIServer:
    """Enhanced file-based API server with robust error handling."""
    
    def __init__(self, command_dir: str, response_dir: str, 
                 event_system: Optional[EventSystem] = None,
                 monitoring_strategy: str = "auto",
                 security_validator: Optional[SecurityValidator] = None,
                 schema_manager: Optional[SchemaManager] = None):
        """
        Initialize the file-based API server.
        
        Args:
            command_dir: Directory to monitor for commands
            response_dir: Directory to write responses
            event_system: Event system for command handling
            monitoring_strategy: "auto", "event", or "polling"
            security_validator: Security validator instance
            schema_manager: Schema manager for validation
        """
        self.command_dir = command_dir
        self.response_dir = response_dir
        self.event_system = event_system or EventSystem()
        
        self.command_handler = CommandHandler(
            command_dir, response_dir, self.event_system,
            monitoring_strategy, security_validator, schema_manager
        )
        
        logger.info("FileBasedAPIServer initialized")
    
    def start(self) -> None:
        """Start the server."""
        logger.info("Starting FileBasedAPIServer")
        self.command_handler.start_monitoring()
    
    def stop(self) -> None:
        """Stop the server."""
        logger.info("Stopping FileBasedAPIServer")
        self.command_handler.stop_monitoring()
    
    def register_command(self, command_name: str, handler: Callable) -> None:
        """
        Register a command handler.
        
        Args:
            command_name: Name of the command
            handler: Function to handle the command
        """
        self.event_system.on(command_name, handler)
        logger.info(f"Registered command handler: {command_name}")
    
    def get_registered_commands(self) -> List[str]:
        """Get list of registered command names."""
        return self.event_system.get_registered_events()
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()