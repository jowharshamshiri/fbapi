Client API
==========

The client module provides the main interface for sending commands and receiving responses in the fbapi system.

FileBasedAPIClient
------------------

.. automodule:: fbapi.client
   :members:
   :undoc-members:
   :show-inheritance:

Classes
-------

.. autoclass:: fbapi.client.FileBasedAPIClient
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fbapi.client.ResponseHandler
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Basic Client Usage
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIClient

    # Create client with default settings
    client = FileBasedAPIClient(
        command_dir="./commands",
        response_dir="./responses"
    )

    # Define response handler
    def handle_response(response_data):
        if response_data['status'] == 'success':
            result = response_data['response'][0]['value']
            print(f"Success: {result}")
        else:
            error = response_data['error']
            print(f"Error {error['code']}: {error['message']}")

    # Send command
    request_id = client.call_command(
        'process_data',
        handle_response,
        input_file='data.txt',
        output_format='json'
    )

    # Wait for completion
    client.wait_for_completion(timeout_seconds=30)

Advanced Configuration
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIClient
    from fbapi.security import SecurityValidator
    from fbapi.config import FBAPIConfig

    # Load configuration
    config = FBAPIConfig(config_path='fbapi.yaml')

    # Custom security settings
    security_validator = SecurityValidator(
        allowed_base_paths=['/safe/directory'],
        max_file_size=1024*1024,  # 1MB
        allowed_extensions=['.json']
    )

    # Create client with custom settings
    client = FileBasedAPIClient(
        command_dir=config.get('directories.command_dir'),
        response_dir=config.get('directories.response_dir'),
        timeout_seconds=config.get('client.timeout_seconds'),
        monitoring_strategy='event',
        security_validator=security_validator
    )

Asynchronous Usage
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import asyncio
    from fbapi import FileBasedAPIClient

    async def async_command_example():
        client = FileBasedAPIClient("./commands", "./responses")
        
        # Create future for response
        response_future = asyncio.Future()
        
        def handle_response(data):
            response_future.set_result(data)
        
        # Send command
        client.call_command('async_task', handle_response, data='test')
        
        # Wait for response
        try:
            response = await asyncio.wait_for(response_future, timeout=30)
            print(f"Response: {response}")
        except asyncio.TimeoutError:
            print("Command timed out")
        finally:
            client.cleanup()

    asyncio.run(async_command_example())

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIClient
    from fbapi.exceptions import ValidationError, SecurityError, TimeoutError

    client = FileBasedAPIClient("./commands", "./responses")

    try:
        def error_handler(response):
            print(f"Received response: {response}")

        client.call_command(
            'risky_command',
            error_handler,
            potentially_dangerous_param='value'
        )
        
        client.wait_for_completion()
        
    except ValidationError as e:
        print(f"Validation failed: {e}")
        print(f"Validation details: {e.validation_error}")
        
    except SecurityError as e:
        print(f"Security violation: {e}")
        
    except TimeoutError as e:
        print(f"Operation timed out after {e.timeout_seconds} seconds")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        
    finally:
        client.cleanup()

Context Manager Usage
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIClient

    # Automatic cleanup with context manager
    with FileBasedAPIClient("./commands", "./responses") as client:
        response_received = False
        
        def handle_response(data):
            nonlocal response_received
            response_received = True
            print(f"Response: {data}")
        
        client.call_command('test_command', handle_response)
        
        # Wait for response
        import time
        timeout = 10
        start_time = time.time()
        while not response_received and (time.time() - start_time) < timeout:
            time.sleep(0.1)
    
    # Client automatically cleaned up here