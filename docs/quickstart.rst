Quick Start Guide
=================

This guide will get you up and running with fbapi in minutes.

Basic Example
-------------

Here's a complete example showing client-server communication:

**1. Install fbapi:**

.. code-block:: bash

    pip install fbapi

**2. Create a simple server (server.py):**

.. code-block:: python

    from fbapi import FileBasedAPIServer, EventSystem
    import time

    # Create event system
    event_system = EventSystem()

    # Define command handlers
    def hello_handler(command_data):
        params = command_data.get('params', [])
        name = next((p['value'] for p in params if p['name'] == 'name'), 'World')
        
        return {
            'name': 'greeting',
            'type': 'string',
            'value': f'Hello, {name}!'
        }

    def add_numbers(command_data):
        params = command_data.get('params', [])
        num1 = next((p['value'] for p in params if p['name'] == 'num1'), 0)
        num2 = next((p['value'] for p in params if p['name'] == 'num2'), 0)
        
        return {
            'name': 'sum',
            'type': 'number',
            'value': num1 + num2
        }

    # Register handlers
    event_system.on('hello', hello_handler)
    event_system.on('add', add_numbers)

    # Create and start server
    server = FileBasedAPIServer(
        command_dir="./commands",
        response_dir="./responses",
        event_system=event_system
    )

    print("Starting server... Press Ctrl+C to stop")
    try:
        server.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping server...")
    finally:
        server.stop()

**3. Create a client (client.py):**

.. code-block:: python

    from fbapi import FileBasedAPIClient
    import time

    # Create client
    client = FileBasedAPIClient(
        command_dir="./commands",
        response_dir="./responses"
    )

    # Response handlers
    def print_response(response):
        if response['status'] == 'success':
            result = response['response'][0]['value']
            print(f"✅ Success: {result}")
        else:
            error = response['error']
            print(f"❌ Error: {error['message']}")

    try:
        # Send hello command
        print("Sending hello command...")
        client.call_command('hello', print_response, name='Alice')

        # Send math command
        print("Sending add command...")
        client.call_command('add', print_response, num1=15, num2=27)

        # Wait for responses
        client.wait_for_completion(timeout_seconds=10)

    finally:
        client.cleanup()

**4. Run the example:**

.. code-block:: bash

    # Terminal 1: Start server
    python server.py

    # Terminal 2: Run client
    python client.py

You should see:

.. code-block:: text

    Sending hello command...
    Sending add command...
    ✅ Success: Hello, Alice!
    ✅ Success: 42

Using the CLI
-------------

fbapi includes command-line tools for testing:

**1. Test the server:**

.. code-block:: bash

    # Start test server
    fbapi test-server --command echo

**2. Test the client (in another terminal):**

.. code-block:: bash

    # Send test command
    fbapi test-client --command echo --message "Hello from CLI!"

**3. Monitor directory activity:**

.. code-block:: bash

    # Watch for file changes
    fbapi monitor --directory ./commands

Configuration
-------------

Create a configuration file for your application:

.. code-block:: bash

    # Generate default configuration
    fbapi create-config my_config.yaml

Edit the configuration:

.. code-block:: yaml

    client:
      timeout_seconds: 30.0
      monitoring_strategy: "auto"

    server:
      monitoring_strategy: "auto"

    directories:
      command_dir: "./my_app/commands"
      response_dir: "./my_app/responses"

    logging:
      level: "INFO"

Use the configuration:

.. code-block:: python

    from fbapi.config import load_config
    from fbapi import FileBasedAPIClient

    # Load configuration
    config = load_config('my_config.yaml')

    # Create client with config
    client = FileBasedAPIClient(
        command_dir=config.get('directories.command_dir'),
        response_dir=config.get('directories.response_dir'),
        timeout_seconds=config.get('client.timeout_seconds')
    )

Next Steps
----------

- Read the :doc:`configuration` guide for advanced configuration options
- Check out :doc:`examples` for more complex use cases  
- Review the :doc:`api/index` for detailed API documentation
- Learn about :doc:`security` features for production use

Common Patterns
---------------

**Async Response Handling:**

.. code-block:: python

    import asyncio
    from fbapi import FileBasedAPIClient

    async def async_example():
        client = FileBasedAPIClient("./commands", "./responses")
        
        # Create future for response
        future = asyncio.Future()
        
        def handle_response(data):
            future.set_result(data)
        
        # Send command
        client.call_command('process', handle_response, data='test')
        
        # Wait for response
        response = await asyncio.wait_for(future, timeout=30)
        print(f"Response: {response}")
        
        client.cleanup()

    asyncio.run(async_example())

**Error Handling:**

.. code-block:: python

    from fbapi import FileBasedAPIClient
    from fbapi.exceptions import ValidationError, TimeoutError

    client = FileBasedAPIClient("./commands", "./responses")

    try:
        def handle_response(data):
            print(f"Response: {data}")
        
        client.call_command('test', handle_response)
        client.wait_for_completion()
        
    except ValidationError as e:
        print(f"Validation failed: {e}")
    except TimeoutError as e:
        print(f"Request timed out: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        client.cleanup()

**Context Manager:**

.. code-block:: python

    from fbapi import FileBasedAPIClient

    # Automatic cleanup
    with FileBasedAPIClient("./commands", "./responses") as client:
        def handle_response(data):
            print(f"Response: {data}")
        
        client.call_command('test', handle_response)
        client.wait_for_completion()
    # Client automatically cleaned up here