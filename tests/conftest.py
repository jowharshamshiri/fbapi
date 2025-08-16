"""
Pytest configuration and fixtures for fbapi tests.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from typing import Dict, Any

from fbapi.config import FBAPIConfig
from fbapi.security import SecurityValidator
from fbapi.schemas import SchemaManager


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def command_dir(temp_dir):
    """Create command directory for tests."""
    cmd_dir = temp_dir / "commands"
    cmd_dir.mkdir()
    return cmd_dir


@pytest.fixture
def response_dir(temp_dir):
    """Create response directory for tests."""
    resp_dir = temp_dir / "responses"
    resp_dir.mkdir()
    return resp_dir


@pytest.fixture
def schema_dir(temp_dir):
    """Create schema directory with test schemas."""
    schema_path = temp_dir / "schemas"
    schema_path.mkdir()
    
    # Create test request schema
    request_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["command", "params", "request_id"],
        "properties": {
            "command": {"type": "string"},
            "request_id": {"type": "string"},
            "params": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "type", "value"],
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "value": {}
                    }
                }
            }
        }
    }
    
    # Create test response schema
    response_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["request_id", "status"],
        "properties": {
            "request_id": {"type": "string"},
            "status": {"type": "string", "enum": ["success", "error"]},
            "response": {"type": "array"},
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"}
                }
            }
        }
    }
    
    with open(schema_path / "request_schema.json", "w") as f:
        json.dump(request_schema, f)
    
    with open(schema_path / "response_schema.json", "w") as f:
        json.dump(response_schema, f)
    
    return schema_path


@pytest.fixture
def test_config(command_dir, response_dir, schema_dir):
    """Create test configuration."""
    config_dict = {
        "client": {
            "timeout_seconds": 5.0,
            "monitoring_strategy": "polling",
            "polling_interval": 0.1,
        },
        "server": {
            "monitoring_strategy": "polling",
            "polling_interval": 0.1,
        },
        "directories": {
            "command_dir": str(command_dir),
            "response_dir": str(response_dir),
            "schema_dir": str(schema_dir),
        }
    }
    return FBAPIConfig(config_dict=config_dict)


@pytest.fixture
def security_validator(command_dir, response_dir):
    """Create security validator for tests."""
    return SecurityValidator(
        allowed_base_paths=[str(command_dir), str(response_dir)],
        max_file_size=1024 * 1024,  # 1MB for tests
    )


@pytest.fixture
def schema_manager(schema_dir):
    """Create schema manager for tests."""
    return SchemaManager(str(schema_dir))


@pytest.fixture
def sample_command_data():
    """Sample command data for tests."""
    return {
        "command": "test_command",
        "request_id": "test-request-123",
        "params": [
            {
                "name": "test_param",
                "type": "string",
                "value": "test_value"
            }
        ],
        "response_file": "test_response.json"
    }


@pytest.fixture
def sample_response_data():
    """Sample response data for tests."""
    return {
        "request_id": "test-request-123",
        "status": "success",
        "response": [
            {
                "name": "result",
                "type": "string",
                "value": "test_result"
            }
        ]
    }


@pytest.fixture
def sample_error_response():
    """Sample error response for tests."""
    return {
        "request_id": "test-request-123",
        "status": "error",
        "error": {
            "code": 500,
            "message": "Test error message"
        }
    }