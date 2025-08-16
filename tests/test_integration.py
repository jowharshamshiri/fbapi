"""
Integration tests for fbapi client-server communication.
"""

import pytest
import json
import time
import threading
from pathlib import Path

from fbapi.client import FileBasedAPIClient
from fbapi.server import FileBasedAPIServer, EventSystem
from fbapi.config import FBAPIConfig


@pytest.mark.integration
class TestClientServerIntegration:
    """Test complete client-server communication."""
    
    def test_basic_client_server_communication(self, command_dir, response_dir):
        """Test basic command-response cycle."""
        # Setup event system with test handler
        event_system = EventSystem()
        
        def echo_handler(command_data):
            """Simple echo handler for testing."""
            params = command_data.get('params', [])
            return {
                'name': 'echo_result',
                'type': 'test',
                'value': {
                    'original_params': params,
                    'message': 'Echo successful'
                }
            }
        
        event_system.on('echo', echo_handler)
        
        # Create server
        server = FileBasedAPIServer(
            command_dir=str(command_dir),
            response_dir=str(response_dir),
            event_system=event_system,
            monitoring_strategy="polling"
        )
        
        # Create client
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir),
            timeout_seconds=5.0,
            monitoring_strategy="polling"
        )
        
        # Start server
        server.start()
        
        try:
            # Track response
            response_received = False
            response_data = None
            
            def handle_response(data):
                nonlocal response_received, response_data
                response_received = True
                response_data = data
            
            # Send command
            request_id = client.call_command(
                'echo',
                handle_response,
                test_message='Hello World'
            )
            
            # Wait for response
            timeout = 10.0
            start_time = time.time()
            while not response_received and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            # Verify response
            assert response_received, "Response not received within timeout"
            assert response_data is not None
            assert response_data['status'] == 'success'
            assert response_data['request_id'] == request_id
            
            # Verify response content
            response_payload = response_data['response'][0]
            assert response_payload['name'] == 'echo_result'
            assert 'Echo successful' in str(response_payload['value'])
            
        finally:
            server.stop()
            client.cleanup()
    
    def test_error_handling_integration(self, command_dir, response_dir):
        """Test error handling in client-server communication."""
        # Setup event system with error handler
        event_system = EventSystem()
        
        def error_handler(command_data):
            """Handler that always raises an error."""
            raise Exception("Test error from handler")
        
        event_system.on('error_command', error_handler)
        
        # Create server and client
        server = FileBasedAPIServer(
            command_dir=str(command_dir),
            response_dir=str(response_dir),
            event_system=event_system,
            monitoring_strategy="polling"
        )
        
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir),
            timeout_seconds=5.0,
            monitoring_strategy="polling"
        )
        
        server.start()
        
        try:
            # Track response
            response_received = False
            response_data = None
            
            def handle_response(data):
                nonlocal response_received, response_data
                response_received = True
                response_data = data
            
            # Send command that will cause error
            request_id = client.call_command(
                'error_command',
                handle_response,
                test_param='error_test'
            )
            
            # Wait for response
            timeout = 10.0
            start_time = time.time()
            while not response_received and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            # Verify error response
            assert response_received, "Error response not received within timeout"
            assert response_data is not None
            assert response_data['status'] == 'error'
            assert response_data['request_id'] == request_id
            assert 'error' in response_data
            assert response_data['error']['code'] == 500
            
        finally:
            server.stop()
            client.cleanup()
    
    def test_multiple_concurrent_commands(self, command_dir, response_dir):
        """Test handling multiple concurrent commands."""
        # Setup event system
        event_system = EventSystem()
        
        def numbered_handler(command_data):
            """Handler that returns numbered responses."""
            params = command_data.get('params', [])
            number_param = next((p for p in params if p['name'] == 'number'), None)
            number = number_param['value'] if number_param else 0
            
            # Small delay to simulate processing
            time.sleep(0.1)
            
            return {
                'name': 'numbered_result',
                'type': 'test',
                'value': f'Response number {number}'
            }
        
        event_system.on('numbered', numbered_handler)
        
        # Create server and client
        server = FileBasedAPIServer(
            command_dir=str(command_dir),
            response_dir=str(response_dir),
            event_system=event_system,
            monitoring_strategy="polling"
        )
        
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir),
            timeout_seconds=10.0,
            monitoring_strategy="polling"
        )
        
        server.start()
        
        try:
            # Track responses
            responses = {}
            
            def make_response_handler(expected_number):
                def handle_response(data):
                    responses[expected_number] = data
                return handle_response
            
            # Send multiple commands
            request_ids = []
            for i in range(5):
                request_id = client.call_command(
                    'numbered',
                    make_response_handler(i),
                    number=i
                )
                request_ids.append(request_id)
            
            # Wait for all responses
            timeout = 15.0
            start_time = time.time()
            while len(responses) < 5 and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            # Verify all responses received
            assert len(responses) == 5, f"Expected 5 responses, got {len(responses)}"
            
            # Verify response content
            for i in range(5):
                assert i in responses
                response = responses[i]
                assert response['status'] == 'success'
                response_value = response['response'][0]['value']
                assert f'Response number {i}' == response_value
                
        finally:
            server.stop()
            client.cleanup()
    
    def test_timeout_handling(self, command_dir, response_dir):
        """Test client timeout when server doesn't respond."""
        # Create client without server (no one to handle commands)
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir),
            timeout_seconds=1.0,  # Short timeout
            monitoring_strategy="polling"
        )
        
        try:
            # Track response
            response_received = False
            
            def handle_response(data):
                nonlocal response_received
                response_received = True
            
            # Send command
            client.call_command(
                'nonexistent_command',
                handle_response,
                test_param='timeout_test'
            )
            
            # Wait longer than timeout
            time.sleep(2.0)
            
            # Verify no response received
            assert not response_received
            
            # Verify command file was cleaned up by timeout
            command_files = list(command_dir.glob("cmd_*.json"))
            assert len(command_files) == 0
            
        finally:
            client.cleanup()
    
    def test_invalid_command_handling(self, command_dir, response_dir):
        """Test handling of invalid command data."""
        # Setup server
        event_system = EventSystem()
        server = FileBasedAPIServer(
            command_dir=str(command_dir),
            response_dir=str(response_dir),
            event_system=event_system,
            monitoring_strategy="polling"
        )
        
        server.start()
        
        try:
            # Create invalid command file manually
            invalid_command = {
                "invalid": "structure",
                "missing": "required_fields"
            }
            
            command_file = command_dir / "invalid_cmd.json"
            with open(command_file, 'w') as f:
                json.dump(invalid_command, f)
            
            # Wait for server to process
            time.sleep(2.0)
            
            # Verify command file was removed (cleanup after error)
            assert not command_file.exists()
            
            # Check if error response was generated
            response_files = list(response_dir.glob("*.json"))
            if response_files:
                # If error response exists, verify it's an error
                with open(response_files[0], 'r') as f:
                    response_data = json.load(f)
                assert response_data['status'] == 'error'
                
        finally:
            server.stop()


@pytest.mark.integration 
class TestConfigurationIntegration:
    """Test integration with configuration system."""
    
    def test_client_server_with_config(self, temp_dir):
        """Test client-server communication using configuration."""
        # Create config
        config_data = {
            "client": {
                "timeout_seconds": 5.0,
                "monitoring_strategy": "polling"
            },
            "server": {
                "monitoring_strategy": "polling"
            },
            "directories": {
                "command_dir": str(temp_dir / "commands"),
                "response_dir": str(temp_dir / "responses")
            }
        }
        
        config = FBAPIConfig(config_dict=config_data)
        
        # Setup directories
        command_dir = Path(config.get('directories.command_dir'))
        response_dir = Path(config.get('directories.response_dir'))
        command_dir.mkdir(parents=True)
        response_dir.mkdir(parents=True)
        
        # Setup event system
        event_system = EventSystem()
        
        def config_test_handler(command_data):
            return {
                'name': 'config_result',
                'type': 'test',
                'value': 'Configuration test successful'
            }
        
        event_system.on('config_test', config_test_handler)
        
        # Create server with config
        server = FileBasedAPIServer(
            command_dir=config.get('directories.command_dir'),
            response_dir=config.get('directories.response_dir'),
            event_system=event_system,
            monitoring_strategy=config.get('server.monitoring_strategy')
        )
        
        # Create client with config
        client = FileBasedAPIClient(
            command_dir=config.get('directories.command_dir'),
            response_dir=config.get('directories.response_dir'),
            timeout_seconds=config.get('client.timeout_seconds'),
            monitoring_strategy=config.get('client.monitoring_strategy')
        )
        
        server.start()
        
        try:
            # Test communication
            response_received = False
            response_data = None
            
            def handle_response(data):
                nonlocal response_received, response_data
                response_received = True
                response_data = data
            
            client.call_command('config_test', handle_response)
            
            # Wait for response
            timeout = 10.0
            start_time = time.time()
            while not response_received and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            # Verify
            assert response_received
            assert response_data['status'] == 'success'
            
        finally:
            server.stop()
            client.cleanup()