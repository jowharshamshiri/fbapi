#!/usr/bin/env python3
"""
Basic usage example for fbapi.

This example demonstrates simple client-server communication
using the file-based API.
"""

import time
import logging
from pathlib import Path

from fbapi import FileBasedAPIClient, FileBasedAPIServer, EventSystem

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run basic client-server example."""
    
    # Setup directories
    base_dir = Path("./fbapi_example")
    command_dir = base_dir / "commands"
    response_dir = base_dir / "responses"
    
    # Create directories
    command_dir.mkdir(parents=True, exist_ok=True)
    response_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Using directories: {command_dir}, {response_dir}")
    
    # Create event system and register handlers
    event_system = EventSystem()
    
    def hello_handler(command_data):
        """Handle 'hello' commands."""
        params = command_data.get('params', [])
        name_param = next((p for p in params if p['name'] == 'name'), None)
        name = name_param['value'] if name_param else 'World'
        
        logger.info(f"Handling hello command for: {name}")
        
        return {
            'name': 'greeting',
            'type': 'string',
            'value': f'Hello, {name}! Welcome to fbapi.'
        }
    
    def math_handler(command_data):
        """Handle 'math' commands."""
        params = command_data.get('params', [])
        
        # Extract parameters
        operation = None
        num1 = None
        num2 = None
        
        for param in params:
            if param['name'] == 'operation':
                operation = param['value']
            elif param['name'] == 'num1':
                num1 = param['value']
            elif param['name'] == 'num2':
                num2 = param['value']
        
        if not all([operation, num1 is not None, num2 is not None]):
            raise ValueError("Missing required parameters: operation, num1, num2")
        
        logger.info(f"Handling math: {num1} {operation} {num2}")
        
        # Perform calculation
        if operation == 'add':
            result = num1 + num2
        elif operation == 'subtract':
            result = num1 - num2
        elif operation == 'multiply':
            result = num1 * num2
        elif operation == 'divide':
            if num2 == 0:
                raise ValueError("Cannot divide by zero")
            result = num1 / num2
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
        command_dir=str(command_dir),
        response_dir=str(response_dir),
        event_system=event_system,
        monitoring_strategy="auto"  # Use best available monitoring
    )
    
    logger.info("Starting server...")
    server.start()
    
    try:
        # Create client
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir),
            timeout_seconds=10.0,
            monitoring_strategy="auto"
        )
        
        # Example 1: Hello command
        logger.info("\\n=== Example 1: Hello Command ===")
        
        hello_response_received = False
        hello_response_data = None
        
        def handle_hello_response(data):
            nonlocal hello_response_received, hello_response_data
            hello_response_received = True
            hello_response_data = data
            logger.info(f"Hello response: {data}")
        
        client.call_command('hello', handle_hello_response, name='Alice')
        
        # Wait for response
        timeout = 5.0
        start_time = time.time()
        while not hello_response_received and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if hello_response_received:
            if hello_response_data['status'] == 'success':
                greeting = hello_response_data['response'][0]['value']
                print(f"✅ Received greeting: {greeting}")
            else:
                print(f"❌ Hello command failed: {hello_response_data.get('error', {}).get('message')}")
        else:
            print("❌ Hello command timed out")
        
        # Example 2: Math command
        logger.info("\\n=== Example 2: Math Command ===")
        
        math_response_received = False
        math_response_data = None
        
        def handle_math_response(data):
            nonlocal math_response_received, math_response_data
            math_response_received = True
            math_response_data = data
            logger.info(f"Math response: {data}")
        
        client.call_command('math', handle_math_response, 
                          operation='multiply', num1=15, num2=7)
        
        # Wait for response
        start_time = time.time()
        while not math_response_received and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if math_response_received:
            if math_response_data['status'] == 'success':
                result = math_response_data['response'][0]['value']
                print(f"✅ Calculation result: 15 × 7 = {result}")
            else:
                print(f"❌ Math command failed: {math_response_data.get('error', {}).get('message')}")
        else:
            print("❌ Math command timed out")
        
        # Example 3: Error handling
        logger.info("\\n=== Example 3: Error Handling ===")
        
        error_response_received = False
        error_response_data = None
        
        def handle_error_response(data):
            nonlocal error_response_received, error_response_data
            error_response_received = True
            error_response_data = data
            logger.info(f"Error response: {data}")
        
        # Send invalid command (divide by zero)
        client.call_command('math', handle_error_response,
                          operation='divide', num1=10, num2=0)
        
        # Wait for response
        start_time = time.time()
        while not error_response_received and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if error_response_received:
            if error_response_data['status'] == 'error':
                error_msg = error_response_data.get('error', {}).get('message', 'Unknown error')
                print(f"✅ Error handled correctly: {error_msg}")
            else:
                print("❌ Expected error response but got success")
        else:
            print("❌ Error handling timed out")
        
        # Wait for all responses to complete
        client.wait_for_completion(timeout_seconds=5.0)
        
        print("\\n=== Example completed successfully! ===")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        print(f"❌ Example failed: {e}")
    
    finally:
        # Cleanup
        logger.info("Stopping server...")
        server.stop()
        logger.info("Example finished")


if __name__ == '__main__':
    main()