Exceptions API
==============

The exceptions module provides a comprehensive hierarchy of typed exceptions for error handling throughout the fbapi library.

Exception Classes
-----------------

.. automodule:: fbapi.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

Base Exception
--------------

.. autoclass:: fbapi.exceptions.FBAPIError
   :members:
   :undoc-members:
   :show-inheritance:

Specific Exceptions
-------------------

.. autoclass:: fbapi.exceptions.ValidationError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fbapi.exceptions.TimeoutError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fbapi.exceptions.SecurityError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fbapi.exceptions.ConfigurationError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fbapi.exceptions.FileSystemError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fbapi.exceptions.CommandError
   :members:
   :undoc-members:
   :show-inheritance:

Exception Handling Examples
---------------------------

Basic Exception Handling
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIClient
    from fbapi.exceptions import (
        FBAPIError, ValidationError, SecurityError, 
        TimeoutError, ConfigurationError
    )

    def safe_client_operation():
        try:
            client = FileBasedAPIClient(
                command_dir="./commands",
                response_dir="./responses"
            )
            
            def response_handler(data):
                print(f"Response: {data}")
            
            client.call_command('test', response_handler, param='value')
            client.wait_for_completion()
            
        except ValidationError as e:
            print(f"Validation failed: {e}")
            if hasattr(e, 'validation_error'):
                print(f"Details: {e.validation_error}")
                
        except SecurityError as e:
            print(f"Security violation: {e}")
            # Log security incident
            
        except TimeoutError as e:
            print(f"Operation timed out: {e}")
            if hasattr(e, 'timeout_seconds'):
                print(f"Timeout was: {e.timeout_seconds} seconds")
                
        except ConfigurationError as e:
            print(f"Configuration error: {e}")
            
        except FBAPIError as e:
            print(f"fbapi error: {e}")
            
        except Exception as e:
            print(f"Unexpected error: {e}")

Validation Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIClient
    from fbapi.exceptions import ValidationError
    import json

    def handle_validation_errors():
        client = FileBasedAPIClient("./commands", "./responses")
        
        try:
            # This might fail validation
            client.call_command(
                'invalid_command',
                lambda x: None,
                malformed_param=object()  # Non-serializable
            )
            
        except ValidationError as e:
            print(f"Validation Error: {e}")
            
            # Access validation details if available
            if hasattr(e, 'validation_error') and e.validation_error:
                print(f"Schema validation failed: {e.validation_error}")
                
            # Handle specific validation failures
            if "required" in str(e).lower():
                print("Missing required fields")
            elif "format" in str(e).lower():
                print("Invalid data format")
            elif "type" in str(e).lower():
                print("Invalid data type")

Security Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIClient
    from fbapi.exceptions import SecurityError
    from fbapi.security import SecurityValidator
    import logging

    # Setup security logging
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.WARNING)

    def handle_security_errors():
        # Create client with strict security
        security_validator = SecurityValidator(
            allowed_base_paths=['/safe/directory'],
            max_file_size=1024*1024  # 1MB
        )
        
        try:
            client = FileBasedAPIClient(
                command_dir='/potentially/unsafe/commands',
                response_dir='/potentially/unsafe/responses',
                security_validator=security_validator
            )
            
        except SecurityError as e:
            # Log security incident
            security_logger.warning(f"Security violation detected: {e}")
            
            # Handle specific security issues
            if "path traversal" in str(e).lower():
                print("Path traversal attack blocked")
            elif "file size" in str(e).lower():
                print("File size limit exceeded")
            elif "permission" in str(e).lower():
                print("Insufficient permissions")
            else:
                print(f"General security violation: {e}")
                
            # Notify security team in production
            # notify_security_team(str(e))

Timeout Error Handling
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIClient
    from fbapi.exceptions import TimeoutError
    import time

    def handle_timeout_errors():
        client = FileBasedAPIClient(
            command_dir="./commands",
            response_dir="./responses",
            timeout_seconds=5.0  # Short timeout for demo
        )
        
        response_received = False
        
        def slow_response_handler(data):
            nonlocal response_received
            response_received = True
            print(f"Response: {data}")
        
        try:
            # Send command that might timeout
            client.call_command('slow_command', slow_response_handler)
            
            # Wait with custom timeout handling
            client.wait_for_completion(timeout_seconds=10.0)
            
        except TimeoutError as e:
            print(f"Operation timed out: {e}")
            
            if hasattr(e, 'timeout_seconds'):
                print(f"Timeout duration: {e.timeout_seconds} seconds")
                
            # Implement retry logic
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries and not response_received:
                try:
                    print(f"Retry attempt {retry_count + 1}")
                    client.call_command('slow_command', slow_response_handler)
                    client.wait_for_completion(timeout_seconds=20.0)  # Longer timeout
                    break
                    
                except TimeoutError:
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(2 ** retry_count)  # Exponential backoff
                    else:
                        print("Max retries exceeded - giving up")

Command Error Handling
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIServer, EventSystem
    from fbapi.exceptions import CommandError

    def handle_command_errors():
        event_system = EventSystem()
        
        def error_prone_handler(command_data):
            """Handler that might raise various errors."""
            command_name = command_data.get('command')
            params = command_data.get('params', [])
            
            try:
                # Validate command
                if command_name == 'divide':
                    num1 = next((p['value'] for p in params if p['name'] == 'num1'), None)
                    num2 = next((p['value'] for p in params if p['name'] == 'num2'), None)
                    
                    if num2 == 0:
                        raise CommandError(
                            "Division by zero not allowed",
                            command_name=command_name,
                            request_id=command_data.get('request_id')
                        )
                    
                    return {
                        'name': 'result',
                        'type': 'number',
                        'value': num1 / num2
                    }
                    
                elif command_name == 'process_file':
                    file_path = next((p['value'] for p in params if p['name'] == 'file'), None)
                    if not file_path:
                        raise CommandError(
                            "File parameter is required",
                            command_name=command_name,
                            request_id=command_data.get('request_id')
                        )
                    
                    # Process file...
                    return {'name': 'status', 'type': 'string', 'value': 'processed'}
                    
                else:
                    raise CommandError(
                        f"Unknown command: {command_name}",
                        command_name=command_name,
                        request_id=command_data.get('request_id')
                    )
                    
            except CommandError:
                raise  # Re-raise CommandError as-is
            except Exception as e:
                # Wrap other exceptions in CommandError
                raise CommandError(
                    f"Command execution failed: {e}",
                    command_name=command_name,
                    request_id=command_data.get('request_id')
                ) from e
        
        # Register error-prone handler
        event_system.on('divide', error_prone_handler)
        event_system.on('process_file', error_prone_handler)
        event_system.on('unknown_command', error_prone_handler)
        
        # Create server
        server = FileBasedAPIServer(
            command_dir="./commands",
            response_dir="./responses",
            event_system=event_system
        )
        
        # Error handling is automatically done by the server
        # CommandErrors will be converted to proper error responses

Configuration Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.config import FBAPIConfig
    from fbapi.exceptions import ConfigurationError

    def handle_config_errors():
        try:
            # Attempt to load configuration
            config = FBAPIConfig(config_path='invalid_config.yaml')
            
        except ConfigurationError as e:
            print(f"Configuration error: {e}")
            
            # Handle specific configuration issues
            if "file not found" in str(e).lower():
                print("Creating default configuration...")
                from fbapi.config import create_default_config_file
                create_default_config_file('default_config.yaml')
                config = FBAPIConfig(config_path='default_config.yaml')
                
            elif "invalid" in str(e).lower():
                print("Invalid configuration format")
                # Use default configuration
                config = FBAPIConfig()
                
            elif "validation" in str(e).lower():
                print("Configuration validation failed")
                # Fix configuration and retry
                
        # Test configuration values
        try:
            timeout = config.get('client.timeout_seconds')
            if timeout <= 0:
                raise ConfigurationError("Timeout must be positive")
                
        except ConfigurationError as e:
            print(f"Configuration value error: {e}")
            # Set safe default
            config.set('client.timeout_seconds', 60.0)

Exception Context and Logging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIClient
    from fbapi.exceptions import FBAPIError
    import logging
    import traceback
    import sys

    # Setup comprehensive logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('fbapi_errors.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)

    def comprehensive_error_handling():
        client = None
        
        try:
            client = FileBasedAPIClient("./commands", "./responses")
            
            def error_handler(response):
                if response.get('status') == 'error':
                    error_info = response.get('error', {})
                    logger.error(f"Command failed: {error_info}")
                    
            client.call_command('test_command', error_handler)
            client.wait_for_completion()
            
        except FBAPIError as e:
            # Log fbapi-specific errors with context
            logger.error(f"FBAPI Error: {type(e).__name__}: {e}")
            
            # Log additional context if available
            if hasattr(e, 'validation_error'):
                logger.error(f"Validation details: {e.validation_error}")
            if hasattr(e, 'timeout_seconds'):
                logger.error(f"Timeout was: {e.timeout_seconds} seconds")
            if hasattr(e, 'command_name'):
                logger.error(f"Command: {e.command_name}")
            if hasattr(e, 'request_id'):
                logger.error(f"Request ID: {e.request_id}")
                
            # Log stack trace for debugging
            logger.debug("Stack trace:", exc_info=True)
            
        except Exception as e:
            # Log unexpected errors
            logger.critical(f"Unexpected error: {type(e).__name__}: {e}")
            logger.critical("Full traceback:", exc_info=True)
            
        finally:
            # Cleanup
            if client:
                try:
                    client.cleanup()
                except Exception as cleanup_error:
                    logger.warning(f"Cleanup failed: {cleanup_error}")

Custom Exception Handling
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.exceptions import FBAPIError
    import logging

    class CustomFBAPIError(FBAPIError):
        """Custom application-specific fbapi error."""
        
        def __init__(self, message, error_code=None, context=None):
            super().__init__(message)
            self.error_code = error_code
            self.context = context or {}
            
    class BusinessLogicError(CustomFBAPIError):
        """Error in business logic processing."""
        pass

    class DataValidationError(CustomFBAPIError):
        """Error in business data validation."""
        pass

    def custom_error_handling():
        logger = logging.getLogger(__name__)
        
        try:
            # Your business logic here
            data = {"user_id": "invalid"}
            
            # Custom validation
            if not data.get('user_id', '').isdigit():
                raise DataValidationError(
                    "User ID must be numeric",
                    error_code="INVALID_USER_ID",
                    context={'provided_value': data.get('user_id')}
                )
                
            # Business logic that might fail
            result = process_user_data(data)
            
        except DataValidationError as e:
            logger.error(f"Data validation failed: {e}")
            logger.error(f"Error code: {e.error_code}")
            logger.error(f"Context: {e.context}")
            
        except BusinessLogicError as e:
            logger.error(f"Business logic error: {e}")
            
        except CustomFBAPIError as e:
            logger.error(f"Custom fbapi error: {e}")
            
        except FBAPIError as e:
            logger.error(f"General fbapi error: {e}")
            
    def process_user_data(data):
        # Placeholder for business logic
        if data['user_id'] == '999':
            raise BusinessLogicError(
                "User not found in system",
                error_code="USER_NOT_FOUND",
                context={'user_id': data['user_id']}
            )
        return {"status": "processed"}