"""
Unit tests for configuration management functionality.
"""

import pytest
import json
import os
import tempfile
from pathlib import Path

from fbapi.config import FBAPIConfig, load_config, create_default_config_file
from fbapi.exceptions import ConfigurationError


class TestFBAPIConfig:
    """Test configuration management functionality."""
    
    def test_init_with_defaults(self):
        """Test initialization with default configuration."""
        config = FBAPIConfig()
        
        # Check default values
        assert config.get('client.timeout_seconds') == 60.0
        assert config.get('client.monitoring_strategy') == 'auto'
        assert config.get('server.monitoring_strategy') == 'auto'
        assert config.get('security.max_file_size') == 10485760
        assert config.get('directories.command_dir') == './commands'
        assert config.get('directories.response_dir') == './responses'
    
    def test_init_with_config_dict(self):
        """Test initialization with custom configuration dictionary."""
        custom_config = {
            'client': {
                'timeout_seconds': 30.0,
                'monitoring_strategy': 'polling'
            },
            'directories': {
                'command_dir': '/custom/commands'
            }
        }
        
        config = FBAPIConfig(config_dict=custom_config)
        
        # Check custom values override defaults
        assert config.get('client.timeout_seconds') == 30.0
        assert config.get('client.monitoring_strategy') == 'polling'
        assert config.get('directories.command_dir') == '/custom/commands'
        
        # Check defaults are preserved where not overridden
        assert config.get('server.monitoring_strategy') == 'auto'
        assert config.get('directories.response_dir') == './responses'
    
    def test_load_from_json_file(self, temp_dir):
        """Test loading configuration from JSON file."""
        config_file = temp_dir / "config.json"
        config_data = {
            'client': {'timeout_seconds': 45.0},
            'logging': {'level': 'DEBUG'}
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        config = FBAPIConfig(config_path=str(config_file))
        
        assert config.get('client.timeout_seconds') == 45.0
        assert config.get('logging.level') == 'DEBUG'
    
    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent file raises error."""
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            FBAPIConfig(config_path="/nonexistent/config.json")
    
    def test_load_from_invalid_json(self, temp_dir):
        """Test loading from invalid JSON file raises error."""
        config_file = temp_dir / "invalid.json"
        with open(config_file, 'w') as f:
            f.write('{"invalid": json}')  # Invalid JSON
        
        with pytest.raises(ConfigurationError, match="Error parsing configuration file"):
            FBAPIConfig(config_path=str(config_file))
    
    def test_get_with_dot_notation(self):
        """Test getting values using dot notation."""
        config = FBAPIConfig()
        
        assert config.get('client.timeout_seconds') == 60.0
        assert config.get('directories.command_dir') == './commands'
        assert config.get('nonexistent.key', 'default') == 'default'
    
    def test_set_with_dot_notation(self):
        """Test setting values using dot notation."""
        config = FBAPIConfig()
        
        config.set('client.timeout_seconds', 120.0)
        config.set('new.nested.key', 'value')
        
        assert config.get('client.timeout_seconds') == 120.0
        assert config.get('new.nested.key') == 'value'
    
    def test_get_section(self):
        """Test getting entire configuration sections."""
        config = FBAPIConfig()
        
        client_section = config.get_section('client')
        assert 'timeout_seconds' in client_section
        assert 'monitoring_strategy' in client_section
        
        # Test that returned section is a copy
        client_section['timeout_seconds'] = 999.0
        assert config.get('client.timeout_seconds') == 60.0
    
    def test_update_config_deep_merge(self):
        """Test that update_config performs deep merge of nested dictionaries."""
        config = FBAPIConfig()
        
        update_data = {
            'client': {
                'timeout_seconds': 120.0,
                'new_setting': 'value'
            },
            'new_section': {
                'key': 'value'
            }
        }
        
        config.update_config(update_data)
        
        # Check merged values
        assert config.get('client.timeout_seconds') == 120.0
        assert config.get('client.new_setting') == 'value'
        assert config.get('client.monitoring_strategy') == 'auto'  # Preserved
        assert config.get('new_section.key') == 'value'
    
    def test_environment_variable_loading(self, monkeypatch):
        """Test loading configuration from environment variables."""
        # Set environment variables
        monkeypatch.setenv('FBAPI_CLIENT_TIMEOUT', '90.0')
        monkeypatch.setenv('FBAPI_CLIENT_MONITORING', 'event')
        monkeypatch.setenv('FBAPI_COMMAND_DIR', '/env/commands')
        monkeypatch.setenv('FBAPI_LOG_LEVEL', 'WARNING')
        
        config = FBAPIConfig()
        
        assert config.get('client.timeout_seconds') == 90.0
        assert config.get('client.monitoring_strategy') == 'event'
        assert config.get('directories.command_dir') == '/env/commands'
        assert config.get('logging.level') == 'WARNING'
    
    def test_environment_variable_type_conversion(self, monkeypatch):
        """Test type conversion for environment variables."""
        monkeypatch.setenv('FBAPI_CLIENT_TIMEOUT', 'invalid_float')
        
        # Should not crash, but should log warning and skip invalid value
        config = FBAPIConfig()
        assert config.get('client.timeout_seconds') == 60.0  # Default preserved
    
    def test_validation_invalid_monitoring_strategy(self):
        """Test validation catches invalid monitoring strategies."""
        with pytest.raises(ConfigurationError, match="Invalid client monitoring strategy"):
            FBAPIConfig(config_dict={
                'client': {'monitoring_strategy': 'invalid_strategy'}
            })
    
    def test_validation_invalid_timeout(self):
        """Test validation catches invalid timeout values."""
        with pytest.raises(ConfigurationError, match="timeout_seconds must be a positive number"):
            FBAPIConfig(config_dict={
                'client': {'timeout_seconds': -10.0}
            })
        
        with pytest.raises(ConfigurationError, match="timeout_seconds must be a positive number"):
            FBAPIConfig(config_dict={
                'client': {'timeout_seconds': 'invalid'}
            })
    
    def test_validation_invalid_file_size(self):
        """Test validation catches invalid file size values."""
        with pytest.raises(ConfigurationError, match="max_file_size must be a positive integer"):
            FBAPIConfig(config_dict={
                'security': {'max_file_size': -1000}
            })
    
    def test_validation_missing_required_directories(self):
        """Test validation catches missing required directories."""
        with pytest.raises(ConfigurationError, match="command_dir is required"):
            FBAPIConfig(config_dict={
                'directories': {'command_dir': None}
            })
        
        with pytest.raises(ConfigurationError, match="response_dir is required"):
            FBAPIConfig(config_dict={
                'directories': {'response_dir': ''}
            })
    
    def test_save_to_json_file(self, temp_dir):
        """Test saving configuration to JSON file."""
        config = FBAPIConfig()
        config.set('client.timeout_seconds', 120.0)
        
        save_path = temp_dir / "saved_config.json"
        config.save_to_file(str(save_path))
        
        # Verify file was created and contains correct data
        assert save_path.exists()
        with open(save_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['client']['timeout_seconds'] == 120.0
    
    def test_save_to_unsupported_format(self, temp_dir):
        """Test saving to unsupported file format raises error."""
        config = FBAPIConfig()
        save_path = temp_dir / "config.xml"
        
        with pytest.raises(ConfigurationError, match="Unsupported format"):
            config.save_to_file(str(save_path))
    
    def test_to_dict(self):
        """Test converting configuration to dictionary."""
        config = FBAPIConfig()
        config.set('test.key', 'value')
        
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['test']['key'] == 'value'
        
        # Test that returned dict is a copy
        config_dict['test']['key'] = 'modified'
        assert config.get('test.key') == 'value'


class TestConfigurationUtilities:
    """Test configuration utility functions."""
    
    def test_load_config_function(self, temp_dir):
        """Test load_config utility function."""
        config_file = temp_dir / "test_config.json"
        config_data = {'client': {'timeout_seconds': 100.0}}
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        config = load_config(str(config_file))
        assert isinstance(config, FBAPIConfig)
        assert config.get('client.timeout_seconds') == 100.0
    
    def test_create_default_config_file(self, temp_dir):
        """Test creating default configuration file."""
        config_path = temp_dir / "default_config.json"
        
        create_default_config_file(str(config_path))
        
        assert config_path.exists()
        
        # Verify it's valid JSON with expected structure
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        assert 'client' in config_data
        assert 'server' in config_data
        assert 'directories' in config_data
        assert config_data['client']['timeout_seconds'] == 60.0