Configuration API
=================

The config module provides flexible configuration management with support for YAML/JSON files and environment variables.

FBAPIConfig
-----------

.. automodule:: fbapi.config
   :members:
   :undoc-members:
   :show-inheritance:

Classes
-------

.. autoclass:: fbapi.config.FBAPIConfig
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

.. autofunction:: fbapi.config.load_config

.. autofunction:: fbapi.config.create_default_config_file

Configuration Examples
----------------------

Basic Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.config import FBAPIConfig

    # Load from default locations
    config = FBAPIConfig()

    # Access configuration values
    timeout = config.get('client.timeout_seconds')
    command_dir = config.get('directories.command_dir')
    log_level = config.get('logging.level')

Configuration File Loading
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.config import FBAPIConfig, create_default_config_file

    # Create default configuration file
    create_default_config_file('fbapi_config.yaml')

    # Load from specific file
    config = FBAPIConfig(config_path='fbapi_config.yaml')

    # Load from dictionary
    config_dict = {
        'client': {
            'timeout_seconds': 30.0,
            'monitoring_strategy': 'event'
        },
        'directories': {
            'command_dir': '/app/commands',
            'response_dir': '/app/responses'
        }
    }
    config = FBAPIConfig(config_dict=config_dict)

Environment Variable Overrides
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Set environment variables
    export FBAPI_CLIENT_TIMEOUT=45.0
    export FBAPI_CLIENT_MONITORING=polling
    export FBAPI_LOG_LEVEL=DEBUG
    export FBAPI_COMMAND_DIR=/custom/commands

.. code-block:: python

    from fbapi.config import FBAPIConfig

    # Environment variables automatically override config file values
    config = FBAPIConfig(config_path='config.yaml')

    # These will reflect environment variable values
    print(config.get('client.timeout_seconds'))  # 45.0
    print(config.get('client.monitoring_strategy'))  # 'polling'
    print(config.get('logging.level'))  # 'DEBUG'

Runtime Configuration Updates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.config import FBAPIConfig

    config = FBAPIConfig()

    # Update individual values
    config.set('client.timeout_seconds', 120.0)
    config.set('logging.level', 'WARNING')

    # Update multiple values
    updates = {
        'client': {
            'timeout_seconds': 60.0,
            'polling_interval': 0.5
        },
        'security': {
            'max_file_size': 2097152  # 2MB
        }
    }
    config.update_config(updates)

    # Save updated configuration
    config.save_to_file('updated_config.yaml')

Configuration Sections
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.config import FBAPIConfig

    config = FBAPIConfig()

    # Get entire configuration sections
    client_config = config.get_section('client')
    server_config = config.get_section('server')
    security_config = config.get_section('security')

    # Use section configuration
    from fbapi import FileBasedAPIClient

    client = FileBasedAPIClient(
        command_dir=config.get('directories.command_dir'),
        response_dir=config.get('directories.response_dir'),
        **client_config  # Unpack client configuration
    )

Logging Setup
~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.config import FBAPIConfig
    import logging

    # Load configuration
    config = FBAPIConfig(config_path='logging_config.yaml')

    # Setup logging based on configuration
    config.setup_logging()

    # Now logging is configured according to config file
    logger = logging.getLogger(__name__)
    logger.info("Application started")

Configuration Schema
~~~~~~~~~~~~~~~~~~~~

**Default Configuration Structure:**

.. code-block:: yaml

    client:
      timeout_seconds: 60.0
      monitoring_strategy: "auto"  # auto, event, polling
      polling_interval: 1.0
      max_file_size: 10485760  # 10MB

    server:
      monitoring_strategy: "auto"
      polling_interval: 1.0
      max_file_size: 10485760

    security:
      allowed_extensions: [".json"]
      path_validation: true
      content_validation: true
      max_file_size: 10485760

    logging:
      level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
      format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
      file: null  # Optional log file path

    directories:
      command_dir: "./commands"
      response_dir: "./responses"
      schema_dir: null  # Optional custom schema directory

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

**Supported Environment Variables:**

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Environment Variable
     - Type
     - Description
   * - FBAPI_CLIENT_TIMEOUT
     - float
     - Client timeout in seconds
   * - FBAPI_CLIENT_MONITORING
     - string
     - Client monitoring strategy
   * - FBAPI_SERVER_MONITORING
     - string
     - Server monitoring strategy
   * - FBAPI_SECURITY_MAX_SIZE
     - int
     - Maximum file size in bytes
   * - FBAPI_LOG_LEVEL
     - string
     - Logging level
   * - FBAPI_LOG_FILE
     - string
     - Log file path
   * - FBAPI_COMMAND_DIR
     - string
     - Command directory path
   * - FBAPI_RESPONSE_DIR
     - string
     - Response directory path
   * - FBAPI_SCHEMA_DIR
     - string
     - Schema directory path

Configuration Validation
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.config import FBAPIConfig
    from fbapi.exceptions import ConfigurationError

    try:
        # Invalid configuration will raise ConfigurationError
        invalid_config = {
            'client': {
                'timeout_seconds': -10.0,  # Invalid: negative timeout
                'monitoring_strategy': 'invalid_strategy'  # Invalid strategy
            }
        }
        config = FBAPIConfig(config_dict=invalid_config)
        
    except ConfigurationError as e:
        print(f"Configuration validation failed: {e}")

    # Validate individual values
    try:
        config = FBAPIConfig()
        config.set('client.timeout_seconds', 'not_a_number')  # Will fail validation
    except ConfigurationError as e:
        print(f"Invalid value: {e}")

Advanced Configuration Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.config import FBAPIConfig
    import os

    class ApplicationConfig:
        def __init__(self, env='development'):
            self.env = env
            self.config = self._load_config()
            
        def _load_config(self):
            # Load base configuration
            config_file = f'config_{self.env}.yaml'
            config = FBAPIConfig(config_path=config_file)
            
            # Apply environment-specific overrides
            if self.env == 'production':
                config.set('logging.level', 'WARNING')
                config.set('client.timeout_seconds', 30.0)
            elif self.env == 'development':
                config.set('logging.level', 'DEBUG')
                config.set('client.timeout_seconds', 10.0)
                
            return config
            
        def get_client_config(self):
            return {
                'command_dir': self.config.get('directories.command_dir'),
                'response_dir': self.config.get('directories.response_dir'),
                'timeout_seconds': self.config.get('client.timeout_seconds'),
                'monitoring_strategy': self.config.get('client.monitoring_strategy')
            }
            
        def get_server_config(self):
            return {
                'command_dir': self.config.get('directories.command_dir'),
                'response_dir': self.config.get('directories.response_dir'),
                'monitoring_strategy': self.config.get('server.monitoring_strategy')
            }

    # Usage
    app_config = ApplicationConfig(env=os.environ.get('APP_ENV', 'development'))
    
    # Configure logging
    app_config.config.setup_logging()
    
    # Create client with environment-specific config
    from fbapi import FileBasedAPIClient
    client = FileBasedAPIClient(**app_config.get_client_config())