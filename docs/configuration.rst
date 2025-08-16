Configuration
=============

The fbapi library provides flexible configuration options through YAML/JSON files and environment variables.

Configuration Files
-------------------

You can create a configuration file using the CLI:

.. code-block:: bash

    fbapi create-config fbapi_config.json

This creates a JSON configuration file with default settings. You can also use YAML:

.. code-block:: bash

    fbapi create-config fbapi_config.yaml

Configuration Structure
----------------------

.. code-block:: yaml

    # fbapi_config.yaml
    directories:
      command_dir: "./commands"
      response_dir: "./responses"
    
    client:
      timeout_seconds: 30.0
      monitoring_strategy: "event"  # or "polling"
      polling_interval: 1.0
    
    server:
      monitoring_strategy: "event"
      polling_interval: 1.0
    
    security:
      max_file_size: 1048576  # 1MB
      allowed_extensions: [".json"]
      allowed_base_paths: []
    
    logging:
      level: "INFO"
      format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

Environment Variables
--------------------

All configuration options can be overridden with environment variables using the ``FBAPI_`` prefix:

.. code-block:: bash

    export FBAPI_CLIENT_TIMEOUT=60.0
    export FBAPI_CLIENT_MONITORING=polling
    export FBAPI_SECURITY_MAX_FILE_SIZE=2097152
    export FBAPI_LOG_LEVEL=DEBUG

Using Configuration
------------------

Load configuration in your application:

.. code-block:: python

    from fbapi.config import load_config
    
    # Load from file
    config = load_config('fbapi_config.yaml')
    
    # Use in client
    client = FileBasedAPIClient(
        command_dir=config.get('directories.command_dir'),
        response_dir=config.get('directories.response_dir'),
        timeout_seconds=config.get('client.timeout_seconds')
    )

Configuration Options
--------------------

directories.command_dir
    Directory where command files are written (default: "./commands")

directories.response_dir
    Directory where response files are written (default: "./responses")

client.timeout_seconds
    How long to wait for responses in seconds (default: 30.0)

client.monitoring_strategy
    File monitoring method: "event" or "polling" (default: "event")

client.polling_interval
    Polling interval in seconds when using polling strategy (default: 1.0)

server.monitoring_strategy
    Server file monitoring method (default: "event")

server.polling_interval
    Server polling interval in seconds (default: 1.0)

security.max_file_size
    Maximum allowed file size in bytes (default: 1048576)

security.allowed_extensions
    List of allowed file extensions (default: [".json"])

security.allowed_base_paths
    List of allowed base paths for security validation (default: [])

logging.level
    Log level: "DEBUG", "INFO", "WARNING", "ERROR" (default: "INFO")

logging.format
    Log message format string (default: standard format)