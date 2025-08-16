Server API
==========

The server module provides the command processing infrastructure for the fbapi system.

FileBasedAPIServer
------------------

.. automodule:: fbapi.server
   :members:
   :undoc-members:
   :show-inheritance:

Classes
-------

.. autoclass:: fbapi.server.FileBasedAPIServer
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fbapi.server.EventSystem
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fbapi.server.CommandHandler
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Basic Server Setup
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIServer, EventSystem

    # Create event system
    event_system = EventSystem()

    # Register command handlers
    def hello_handler(command_data):
        params = command_data.get('params', [])
        name = next((p['value'] for p in params if p['name'] == 'name'), 'World')
        
        return {
            'name': 'greeting',
            'type': 'string',
            'value': f'Hello, {name}!'
        }

    def math_handler(command_data):
        params = command_data.get('params', [])
        
        # Extract parameters
        operation = next((p['value'] for p in params if p['name'] == 'operation'), None)
        num1 = next((p['value'] for p in params if p['name'] == 'num1'), None)
        num2 = next((p['value'] for p in params if p['name'] == 'num2'), None)
        
        if operation == 'add':
            result = num1 + num2
        elif operation == 'subtract':
            result = num1 - num2
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return {
            'name': 'calculation_result',
            'type': 'number',
            'value': result
        }

    # Register handlers
    event_system.on('hello', hello_handler)
    event_system.on('math', math_handler)

    # Create and start server
    server = FileBasedAPIServer(
        command_dir="./commands",
        response_dir="./responses",
        event_system=event_system
    )

    try:
        server.start()
        print("Server started. Press Ctrl+C to stop...")
        
        # Keep server running
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Stopping server...")
    finally:
        server.stop()

Advanced Handler Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIServer, EventSystem
    import json
    import time
    import logging

    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    event_system = EventSystem()

    # Handler with error handling
    def robust_handler(command_data):
        try:
            # Log incoming command
            logger.info(f"Processing command: {command_data.get('command')}")
            
            # Validate required parameters
            params = command_data.get('params', [])
            if not params:
                raise ValueError("No parameters provided")
            
            # Process command
            result = process_business_logic(params)
            
            return {
                'name': 'result',
                'type': 'object',
                'value': {
                    'status': 'success',
                    'data': result,
                    'processed_at': time.time()
                }
            }
            
        except Exception as e:
            logger.error(f"Handler error: {e}")
            raise  # Re-raise to trigger error response

    # Handler with multiple return values
    def multi_result_handler(command_data):
        params = command_data.get('params', [])
        
        # Return multiple results
        return [
            {
                'name': 'summary',
                'type': 'object',
                'value': {'total_params': len(params)}
            },
            {
                'name': 'timestamp',
                'type': 'string',
                'value': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        ]

    # Async-style handler (using generators)
    def streaming_handler(command_data):
        # Process in chunks
        for i in range(5):
            yield {
                'name': f'chunk_{i}',
                'type': 'object',
                'value': {'chunk_id': i, 'data': f'chunk_data_{i}'}
            }

    # Register handlers
    event_system.on('robust_process', robust_handler)
    event_system.on('multi_result', multi_result_handler)
    event_system.on('streaming', streaming_handler)

Middleware and Event Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import EventSystem
    import time
    import json

    event_system = EventSystem()

    # Add logging middleware
    def logging_middleware(event_name, *args, **kwargs):
        print(f"[{time.strftime('%H:%M:%S')}] Processing event: {event_name}")
        return args, kwargs

    # Add authentication middleware
    def auth_middleware(event_name, *args, **kwargs):
        command_data = args[0] if args else {}
        
        # Check for auth token in command
        params = command_data.get('params', [])
        auth_token = next((p['value'] for p in params if p['name'] == 'auth_token'), None)
        
        if not auth_token or not validate_token(auth_token):
            raise PermissionError("Invalid or missing authentication token")
        
        return args, kwargs

    # Add performance monitoring middleware
    def performance_middleware(event_name, *args, **kwargs):
        start_time = time.time()
        
        try:
            result = args, kwargs
            return result
        finally:
            duration = time.time() - start_time
            print(f"Event {event_name} took {duration:.3f}s")

    # Register middleware
    event_system.add_middleware(logging_middleware)
    event_system.add_middleware(auth_middleware)
    event_system.add_middleware(performance_middleware)

    def protected_handler(command_data):
        # This handler will only be called if auth middleware passes
        return {
            'name': 'protected_result',
            'type': 'string',
            'value': 'Access granted to protected resource'
        }

    event_system.on('protected_command', protected_handler)

Server Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIServer, EventSystem
    from fbapi.config import FBAPIConfig
    from fbapi.security import SecurityValidator

    # Load configuration
    config = FBAPIConfig(config_path='server_config.yaml')

    # Custom security settings
    security_validator = SecurityValidator(
        allowed_base_paths=[
            config.get('directories.command_dir'),
            config.get('directories.response_dir')
        ],
        max_file_size=config.get('security.max_file_size'),
        allowed_extensions=['.json']
    )

    # Create event system with handlers
    event_system = EventSystem()
    register_all_handlers(event_system)  # Your handler registration

    # Create server with configuration
    server = FileBasedAPIServer(
        command_dir=config.get('directories.command_dir'),
        response_dir=config.get('directories.response_dir'),
        event_system=event_system,
        monitoring_strategy=config.get('server.monitoring_strategy'),
        security_validator=security_validator
    )

    # Configure logging
    config.setup_logging()

    # Start server
    with server:
        print(f"Server started with {len(event_system.get_registered_events())} registered commands")
        
        try:
            import signal
            import sys
            
            def signal_handler(sig, frame):
                print("Gracefully shutting down...")
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Keep running
            while True:
                time.sleep(1)
                
        except SystemExit:
            pass

Production Deployment
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIServer, EventSystem
    import logging
    import os
    import sys
    import signal
    import threading
    import time

    class ProductionServer:
        def __init__(self, config_path):
            self.config = FBAPIConfig(config_path=config_path)
            self.config.setup_logging()
            self.logger = logging.getLogger(__name__)
            
            self.event_system = EventSystem()
            self.server = None
            self.shutdown_event = threading.Event()
            
            # Register signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
        def register_handlers(self):
            # Import and register all your command handlers
            from myapp.handlers import (
                data_processor,
                file_converter,
                notification_sender
            )
            
            self.event_system.on('process_data', data_processor)
            self.event_system.on('convert_file', file_converter)
            self.event_system.on('send_notification', notification_sender)
            
        def start(self):
            try:
                self.register_handlers()
                
                self.server = FileBasedAPIServer(
                    command_dir=self.config.get('directories.command_dir'),
                    response_dir=self.config.get('directories.response_dir'),
                    event_system=self.event_system,
                    monitoring_strategy=self.config.get('server.monitoring_strategy')
                )
                
                self.logger.info("Starting production server...")
                self.server.start()
                
                # Health check thread
                health_thread = threading.Thread(target=self._health_check, daemon=True)
                health_thread.start()
                
                # Main loop
                while not self.shutdown_event.is_set():
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Server startup failed: {e}")
                sys.exit(1)
            finally:
                self.stop()
                
        def stop(self):
            self.logger.info("Shutting down server...")
            if self.server:
                self.server.stop()
            self.shutdown_event.set()
            
        def _signal_handler(self, signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown_event.set()
            
        def _health_check(self):
            while not self.shutdown_event.is_set():
                try:
                    # Perform health checks
                    self._check_directories()
                    self._check_disk_space()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    self.logger.warning(f"Health check failed: {e}")
                    
        def _check_directories(self):
            # Verify directories are accessible
            for dir_path in [self.config.get('directories.command_dir'),
                           self.config.get('directories.response_dir')]:
                if not os.access(dir_path, os.R_OK | os.W_OK):
                    raise RuntimeError(f"Directory not accessible: {dir_path}")
                    
        def _check_disk_space(self):
            # Check available disk space
            import shutil
            _, _, free = shutil.disk_usage(self.config.get('directories.command_dir'))
            if free < 100 * 1024 * 1024:  # Less than 100MB
                self.logger.warning("Low disk space detected")

    if __name__ == '__main__':
        server = ProductionServer('production_config.yaml')
        server.start()