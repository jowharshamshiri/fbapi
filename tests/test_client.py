"""
Unit tests for file-based API client functionality.
"""

import pytest
import json
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch

from fbapi.client import FileBasedAPIClient, ResponseHandler
from fbapi.security import SecurityValidator
from fbapi.schemas import SchemaManager
from fbapi.exceptions import ValidationError, SecurityError, TimeoutError


class TestResponseHandler:
    """Test ResponseHandler functionality."""
    
    def test_init(self, temp_dir):
        """Test ResponseHandler initialization."""
        callback = Mock()
        handler = ResponseHandler(
            "test_response.json",
            str(temp_dir / "responses"),
            str(temp_dir / "commands"),
            callback,
            timeout_seconds=30.0
        )
        
        assert handler.response_file == "test_response.json"
        assert handler.response_dir == temp_dir / "responses"
        assert handler.command_dir == temp_dir / "commands"
        assert handler.callback == callback
        assert handler.timeout_seconds == 30.0
        assert not handler.completed
    
    def test_file_event_handling(self, temp_dir):
        """Test handling of file events."""
        response_dir = temp_dir / "responses"
        command_dir = temp_dir / "commands"
        response_dir.mkdir()
        command_dir.mkdir()
        
        callback = Mock()
        handler = ResponseHandler(
            "test_response.json",
            str(response_dir),
            str(command_dir),
            callback,
            timeout_seconds=30.0,
            monitoring_strategy="polling"
        )
        
        # Create response file
        response_file = response_dir / "test_response.json"
        response_file.write_text('{"test": "response"}')
        
        # Handle the file event
        handler._handle_file_event(str(response_file))
        
        # Verify callback was called
        callback.assert_called_once_with(str(response_file))
        assert handler.completed
    
    def test_timeout_monitoring(self, temp_dir):
        """Test timeout monitoring functionality."""
        response_dir = temp_dir / "responses"
        command_dir = temp_dir / "commands"
        response_dir.mkdir()
        command_dir.mkdir()
        
        callback = Mock()
        handler = ResponseHandler(
            "test_response.json",
            str(response_dir),
            str(command_dir),
            callback,
            timeout_seconds=0.1,  # Very short timeout
            monitoring_strategy="polling"
        )
        
        # Start timeout monitoring
        handler._timeout_monitor()
        
        # Should be completed due to timeout
        assert handler.completed


class TestFileBasedAPIClient:
    """Test FileBasedAPIClient functionality."""
    
    def test_init_with_defaults(self, command_dir, response_dir):
        """Test client initialization with default settings."""
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir)
        )
        
        assert client.command_dir == command_dir
        assert client.response_dir == response_dir
        assert client.timeout_seconds == 60.0
        assert client.monitoring_strategy == "auto"
        assert isinstance(client.security_validator, SecurityValidator)
        assert isinstance(client.schema_manager, SchemaManager)
    
    def test_init_with_custom_settings(self, command_dir, response_dir):
        """Test client initialization with custom settings."""
        security_validator = SecurityValidator()
        schema_manager = SchemaManager()
        
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir),
            timeout_seconds=30.0,
            monitoring_strategy="polling",
            security_validator=security_validator,
            schema_manager=schema_manager
        )
        
        assert client.timeout_seconds == 30.0
        assert client.monitoring_strategy == "polling"
        assert client.security_validator == security_validator
        assert client.schema_manager == schema_manager
    
    def test_directory_setup(self, temp_dir):
        """Test that directories are created if they don't exist."""
        command_dir = temp_dir / "new_commands"
        response_dir = temp_dir / "new_responses"
        
        # Directories don't exist yet
        assert not command_dir.exists()
        assert not response_dir.exists()
        
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir)
        )
        
        # Directories should be created
        assert command_dir.exists()
        assert response_dir.exists()
    
    def test_security_validation_failure_on_init(self, temp_dir):
        """Test that security validation failure raises error on init."""
        # Create a file where directory should be
        fake_dir = temp_dir / "fake_dir"
        fake_dir.write_text("not a directory")
        
        with pytest.raises(SecurityError, match="Invalid directory access"):
            FileBasedAPIClient(
                command_dir=str(fake_dir),
                response_dir=str(temp_dir / "responses")
            )
    
    def test_validate_json_valid_request(self, command_dir, response_dir, sample_command_data):
        """Test JSON validation with valid request data."""
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir)
        )
        
        # Should not raise exception
        client.validate_json(sample_command_data, "request")
    
    def test_validate_json_invalid_request(self, command_dir, response_dir):
        """Test JSON validation with invalid request data."""
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir)
        )
        
        invalid_data = {"invalid": "request", "missing": "required_fields"}
        
        with pytest.raises(ValidationError, match="Schema validation failed"):
            client.validate_json(invalid_data, "request")
    
    def test_is_monitoring(self, command_dir, response_dir):
        """Test monitoring status checking."""
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir)
        )
        
        # Initially no monitoring
        assert not client.is_monitoring()
        
        # Add a mock handler
        mock_handler = Mock()
        mock_handler.completed = False
        client.response_handlers["test"] = mock_handler
        
        assert client.is_monitoring()
        
        # Mark handler as completed
        mock_handler.completed = True
        assert not client.is_monitoring()
    
    def test_call_command_creates_command_file(self, command_dir, response_dir):
        """Test that call_command creates a command file."""
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir),
            monitoring_strategy="polling"
        )
        
        callback = Mock()
        request_id = client.call_command(
            "test_command",
            callback,
            test_param="test_value"
        )
        
        # Verify command file was created
        command_files = list(command_dir.glob("cmd_*.json"))
        assert len(command_files) == 1
        
        # Verify command file content
        with open(command_files[0], 'r') as f:
            command_data = json.load(f)
        
        assert command_data["command"] == "test_command"
        assert command_data["request_id"] == request_id
        assert len(command_data["params"]) == 1
        assert command_data["params"][0]["name"] == "test_param"
        assert command_data["params"][0]["value"] == "test_value"
    
    def test_call_command_with_security_violation(self, temp_dir):
        """Test that call_command raises SecurityError for security violations."""
        # Create client with very restrictive security validator
        security_validator = Mock()
        security_validator.validate_file_path.return_value = False
        security_validator.validate_directory_access.return_value = True
        
        command_dir = temp_dir / "commands"
        response_dir = temp_dir / "responses"
        command_dir.mkdir()
        response_dir.mkdir()
        
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir),
            security_validator=security_validator
        )
        
        callback = Mock()
        with pytest.raises(SecurityError, match="Invalid command file path"):
            client.call_command("test_command", callback)
    
    def test_call_command_with_json_content_security_failure(self, command_dir, response_dir):
        """Test that call_command raises SecurityError for malicious JSON content."""
        # Create security validator that rejects JSON content
        security_validator = Mock()
        security_validator.validate_directory_access.return_value = True
        security_validator.validate_file_path.return_value = True
        security_validator.validate_json_content.return_value = False
        
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir),
            security_validator=security_validator
        )
        
        callback = Mock()
        with pytest.raises(SecurityError, match="Command content failed security validation"):
            client.call_command("test_command", callback)
    
    def test_process_response_valid_json(self, command_dir, response_dir, sample_response_data):
        """Test processing valid response JSON."""
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir)
        )
        
        # Create response file
        response_file = response_dir / "test_response.json"
        with open(response_file, 'w') as f:
            json.dump(sample_response_data, f)
        
        callback = Mock()
        client._process_response(str(response_file), callback)
        
        # Verify callback was called with response data
        callback.assert_called_once_with(sample_response_data)
    
    def test_process_response_invalid_json(self, command_dir, response_dir):
        """Test processing invalid JSON response."""
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir)
        )
        
        # Create response file with invalid JSON
        response_file = response_dir / "invalid_response.json"
        response_file.write_text('{"invalid": json}')
        
        callback = Mock()
        
        # Should not raise exception, but should not call callback
        client._process_response(str(response_file), callback)
        callback.assert_not_called()
    
    def test_wait_for_completion_no_handlers(self, command_dir, response_dir):
        """Test wait_for_completion when no handlers are active."""
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir)
        )
        
        # Should return immediately
        start_time = time.time()
        client.wait_for_completion(timeout_seconds=1.0)
        elapsed = time.time() - start_time
        
        assert elapsed < 0.5  # Should be much faster than timeout
    
    def test_wait_for_completion_timeout(self, command_dir, response_dir):
        """Test wait_for_completion timeout."""
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir)
        )
        
        # Add a mock handler that never completes
        mock_handler = Mock()
        mock_handler.completed = False
        client.response_handlers["test"] = mock_handler
        
        with pytest.raises(TimeoutError, match="Wait timeout after"):
            client.wait_for_completion(timeout_seconds=0.1)
    
    def test_cleanup(self, command_dir, response_dir):
        """Test cleanup functionality."""
        client = FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir)
        )
        
        # Add mock handlers
        mock_handler1 = Mock()
        mock_handler2 = Mock()
        client.response_handlers["test1"] = mock_handler1
        client.response_handlers["test2"] = mock_handler2
        
        client.cleanup()
        
        # Verify all handlers were stopped
        mock_handler1.stop_monitoring.assert_called_once()
        mock_handler2.stop_monitoring.assert_called_once()
        
        # Verify handlers dictionary was cleared
        assert len(client.response_handlers) == 0
    
    def test_context_manager(self, command_dir, response_dir):
        """Test client as context manager."""
        with FileBasedAPIClient(
            command_dir=str(command_dir),
            response_dir=str(response_dir)
        ) as client:
            assert isinstance(client, FileBasedAPIClient)
        
        # Cleanup should have been called automatically
        assert len(client.response_handlers) == 0