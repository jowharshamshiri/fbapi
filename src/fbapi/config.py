"""
Configuration management for fbapi.

Supports YAML and JSON configuration files with validation and defaults.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class FBAPIConfig:
    """Configuration manager for fbapi settings."""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "client": {
            "timeout_seconds": 60.0,
            "monitoring_strategy": "auto",
            "polling_interval": 1.0,
            "max_file_size": 10485760,  # 10MB
        },
        "server": {
            "monitoring_strategy": "auto",
            "polling_interval": 1.0,
            "max_file_size": 10485760,  # 10MB
        },
        "security": {
            "allowed_extensions": [".json"],
            "path_validation": True,
            "content_validation": True,
            "max_file_size": 10485760,  # 10MB
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": None,
        },
        "directories": {
            "command_dir": "./commands",
            "response_dir": "./responses",
            "schema_dir": None,
        }
    }
    
    def __init__(self, config_path: Optional[str] = None, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
            config_dict: Configuration dictionary (overrides file)
        """
        self._config = self.DEFAULT_CONFIG.copy()
        
        if config_path:
            self.load_from_file(config_path)
        
        if config_dict:
            self.update_config(config_dict)
        
        # Load from environment variables
        self._load_from_env()
        
        # Validate configuration
        self._validate_config()
    
    def load_from_file(self, config_path: str) -> None:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_file, 'r') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    if not YAML_AVAILABLE:
                        raise ConfigurationError(
                            "YAML configuration requires PyYAML. "
                            "Install with: pip install PyYAML"
                        )
                    config_data = yaml.safe_load(f)
                elif config_file.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    raise ConfigurationError(
                        f"Unsupported configuration file format: {config_file.suffix}. "
                        "Use .json, .yaml, or .yml"
                    )
            
            self.update_config(config_data)
            logger.info(f"Loaded configuration from: {config_path}")
            
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ConfigurationError(f"Error parsing configuration file {config_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration file {config_path}: {e}")
    
    def update_config(self, config_dict: Dict[str, Any]) -> None:
        """
        Update configuration with new values.
        
        Args:
            config_dict: Dictionary of configuration values
        """
        self._deep_update(self._config, config_dict)
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
        """Recursively update nested dictionaries."""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _load_from_env(self) -> None:
        """Load configuration overrides from environment variables."""
        env_mappings = {
            'FBAPI_CLIENT_TIMEOUT': ('client', 'timeout_seconds', float),
            'FBAPI_CLIENT_MONITORING': ('client', 'monitoring_strategy', str),
            'FBAPI_SERVER_MONITORING': ('server', 'monitoring_strategy', str),
            'FBAPI_SECURITY_MAX_SIZE': ('security', 'max_file_size', int),
            'FBAPI_LOG_LEVEL': ('logging', 'level', str),
            'FBAPI_LOG_FILE': ('logging', 'file', str),
            'FBAPI_COMMAND_DIR': ('directories', 'command_dir', str),
            'FBAPI_RESPONSE_DIR': ('directories', 'response_dir', str),
            'FBAPI_SCHEMA_DIR': ('directories', 'schema_dir', str),
        }
        
        for env_var, (section, key, type_func) in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    if section not in self._config:
                        self._config[section] = {}
                    self._config[section][key] = type_func(value)
                    logger.debug(f"Loaded from env: {env_var} = {value}")
                except ValueError as e:
                    logger.warning(f"Invalid environment variable {env_var}: {e}")
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        # Validate monitoring strategies
        valid_strategies = ['auto', 'event', 'polling']
        
        client_strategy = self.get('client.monitoring_strategy')
        if client_strategy not in valid_strategies:
            raise ConfigurationError(
                f"Invalid client monitoring strategy: {client_strategy}. "
                f"Must be one of: {valid_strategies}"
            )
        
        server_strategy = self.get('server.monitoring_strategy')
        if server_strategy not in valid_strategies:
            raise ConfigurationError(
                f"Invalid server monitoring strategy: {server_strategy}. "
                f"Must be one of: {valid_strategies}"
            )
        
        # Validate timeouts
        client_timeout = self.get('client.timeout_seconds')
        if not isinstance(client_timeout, (int, float)) or client_timeout <= 0:
            raise ConfigurationError("client.timeout_seconds must be a positive number")
        
        # Validate file sizes
        for section in ['client', 'server', 'security']:
            max_size = self.get(f'{section}.max_file_size')
            if not isinstance(max_size, int) or max_size <= 0:
                raise ConfigurationError(f"{section}.max_file_size must be a positive integer")
        
        # Validate directories
        required_dirs = ['command_dir', 'response_dir']
        for dir_key in required_dirs:
            dir_path = self.get(f'directories.{dir_key}')
            if not dir_path:
                raise ConfigurationError(f"directories.{dir_key} is required")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'client.timeout_seconds')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the final value
        config[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Configuration section dictionary
        """
        return self._config.get(section, {}).copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary."""
        return self._config.copy()
    
    def save_to_file(self, config_path: str) -> None:
        """
        Save configuration to file.
        
        Args:
            config_path: Path to save configuration
        """
        config_file = Path(config_path)
        
        try:
            with open(config_file, 'w') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    if not YAML_AVAILABLE:
                        raise ConfigurationError("YAML saving requires PyYAML")
                    yaml.safe_dump(self._config, f, indent=2, default_flow_style=False)
                elif config_file.suffix.lower() == '.json':
                    json.dump(self._config, f, indent=2)
                else:
                    raise ConfigurationError(f"Unsupported format: {config_file.suffix}")
            
            logger.info(f"Configuration saved to: {config_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Error saving configuration to {config_path}: {e}")
    
    def setup_logging(self) -> None:
        """Setup logging based on configuration."""
        log_config = self.get_section('logging')
        
        level = getattr(logging, log_config.get('level', 'INFO').upper())
        format_str = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_file = log_config.get('file')
        
        # Configure root logger
        logging.basicConfig(
            level=level,
            format=format_str,
            filename=log_file,
            force=True
        )
        
        logger.info(f"Logging configured: level={logging.getLevelName(level)}, file={log_file}")


def load_config(config_path: Optional[str] = None, 
                config_dict: Optional[Dict[str, Any]] = None) -> FBAPIConfig:
    """
    Load configuration from file or dictionary.
    
    Args:
        config_path: Path to configuration file
        config_dict: Configuration dictionary
        
    Returns:
        FBAPIConfig instance
    """
    return FBAPIConfig(config_path, config_dict)


def create_default_config_file(config_path: str) -> None:
    """
    Create a default configuration file.
    
    Args:
        config_path: Path where to create the configuration file
    """
    config = FBAPIConfig()
    config.save_to_file(config_path)
    logger.info(f"Default configuration created at: {config_path}")