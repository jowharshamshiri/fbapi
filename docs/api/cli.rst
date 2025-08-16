CLI API
=======

The CLI module provides command-line tools for testing, monitoring, and debugging fbapi systems.

Command Line Interface
----------------------

.. automodule:: fbapi.cli
   :members:
   :undoc-members:
   :show-inheritance:

CLI Commands
------------

The fbapi CLI provides several commands for testing and debugging:

- ``fbapi version`` - Show version information
- ``fbapi create-config`` - Create default configuration file
- ``fbapi test-client`` - Test client functionality
- ``fbapi test-server`` - Test server functionality  
- ``fbapi monitor`` - Monitor directory for file changes
- ``fbapi validate`` - Validate JSON files against schemas

CLI Usage Examples
------------------

Version Information
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Show fbapi version
    fbapi version

    # Show version with verbose flag
    fbapi --version

Create Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Create default configuration file
    fbapi create-config fbapi_config.yaml

    # Create JSON configuration
    fbapi create-config fbapi_config.json

    # Use created configuration
    fbapi --config fbapi_config.yaml test-client

Test Client
~~~~~~~~~~~

.. code-block:: bash

    # Basic client test
    fbapi test-client

    # Test with custom command and message
    fbapi test-client --command hello --message "Hello from CLI"

    # Test with custom timeout
    fbapi test-client --command process --timeout 60

    # Test with event-driven monitoring
    fbapi test-client --strategy event

    # Test with polling strategy
    fbapi test-client --strategy polling --command test

    # Verbose output
    fbapi --verbose test-client --command debug

Test Server
~~~~~~~~~~~

.. code-block:: bash

    # Start test server (runs until Ctrl+C)
    fbapi test-server

    # Test server with specific command handler
    fbapi test-server --command hello

    # Server with event monitoring
    fbapi test-server --strategy event

    # Server with polling and verbose output
    fbapi --verbose test-server --strategy polling

Monitor Directory
~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Monitor default directories from config
    fbapi monitor

    # Monitor specific directory
    fbapi monitor --directory ./watch_me

    # Monitor with event-driven strategy
    fbapi monitor --directory ./files --strategy event

    # Monitor with polling strategy
    fbapi monitor --directory ./files --strategy polling

    # Monitor with verbose output
    fbapi --verbose monitor --directory ./debug

Validate JSON Files
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Validate request files
    fbapi validate command1.json command2.json

    # Validate response files
    fbapi validate response1.json response2.json --schema-type response

    # Validate with custom configuration
    fbapi --config custom.yaml validate *.json

Configuration Integration
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Use custom configuration file
    fbapi --config production.yaml test-client

    # Override with environment variables
    export FBAPI_CLIENT_TIMEOUT=30
    export FBAPI_LOG_LEVEL=DEBUG
    fbapi test-client

    # Create and use configuration
    fbapi create-config my_config.yaml
    fbapi --config my_config.yaml test-server

Advanced CLI Usage
------------------

Automated Testing Scripts
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    #!/bin/bash
    # test_fbapi_system.sh

    set -e  # Exit on any error

    echo "Setting up fbapi test environment..."

    # Create configuration
    fbapi create-config test_config.yaml

    # Create test directories
    mkdir -p test_commands test_responses

    # Start server in background
    echo "Starting test server..."
    fbapi --config test_config.yaml test-server --command echo &
    SERVER_PID=$!

    # Wait for server to start
    sleep 2

    # Test client communication
    echo "Testing client communication..."
    fbapi --config test_config.yaml test-client --command echo --message "Automated test"

    # Stop server
    echo "Stopping test server..."
    kill $SERVER_PID

    # Cleanup
    rm -rf test_commands test_responses test_config.yaml

    echo "Test completed successfully!"

Monitoring Script
~~~~~~~~~~~~~~~~~

.. code-block:: bash

    #!/bin/bash
    # monitor_production.sh

    # Production monitoring setup
    export FBAPI_LOG_LEVEL=INFO
    export FBAPI_COMMAND_DIR=/app/production/commands
    export FBAPI_RESPONSE_DIR=/app/production/responses

    # Create log directory
    mkdir -p /var/log/fbapi

    # Start monitoring with logging
    fbapi monitor --strategy event 2>&1 | tee /var/log/fbapi/monitor.log

Validation Pipeline
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    #!/bin/bash
    # validate_pipeline.sh

    # Validate all JSON files in processing pipeline
    echo "Validating input commands..."
    fbapi validate input/*.json --schema-type request

    echo "Validating output responses..."
    fbapi validate output/*.json --schema-type response

    # Return appropriate exit code
    if [ $? -eq 0 ]; then
        echo "All validations passed"
        exit 0
    else
        echo "Validation failures detected"
        exit 1
    fi

Development Workflow
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Development setup script
    #!/bin/bash

    # Create development environment
    echo "Setting up fbapi development environment..."

    # Create configuration for development
    fbapi create-config dev_config.yaml

    # Edit configuration for development settings
    # (modify timeouts, enable debug logging, etc.)

    # Start development server
    echo "Starting development server..."
    fbapi --config dev_config.yaml --verbose test-server &
    DEV_SERVER_PID=$!

    # Function to cleanup on exit
    cleanup() {
        echo "Cleaning up development environment..."
        kill $DEV_SERVER_PID 2>/dev/null
        exit 0
    }

    # Set trap for cleanup
    trap cleanup INT TERM

    echo "Development server running (PID: $DEV_SERVER_PID)"
    echo "Test with: fbapi --config dev_config.yaml test-client"
    echo "Press Ctrl+C to stop"

    # Wait for interrupt
    wait $DEV_SERVER_PID

CLI Configuration Examples
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Development Configuration (dev_config.yaml):**

.. code-block:: yaml

    client:
      timeout_seconds: 10.0
      monitoring_strategy: "event"
      polling_interval: 0.1

    server:
      monitoring_strategy: "event"
      polling_interval: 0.1

    security:
      max_file_size: 1048576  # 1MB for development

    logging:
      level: "DEBUG"
      format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    directories:
      command_dir: "./dev_commands"
      response_dir: "./dev_responses"

**Production Configuration (prod_config.yaml):**

.. code-block:: yaml

    client:
      timeout_seconds: 60.0
      monitoring_strategy: "event"
      polling_interval: 1.0

    server:
      monitoring_strategy: "event"
      polling_interval: 1.0

    security:
      max_file_size: 10485760  # 10MB for production

    logging:
      level: "INFO"
      format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
      file: "/var/log/fbapi/fbapi.log"

    directories:
      command_dir: "/app/production/commands"
      response_dir: "/app/production/responses"

Integration with Process Managers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Systemd Service (fbapi-server.service):**

.. code-block:: ini

    [Unit]
    Description=FBAPI Server
    After=network.target

    [Service]
    Type=simple
    User=fbapi
    WorkingDirectory=/app/fbapi
    Environment=FBAPI_CONFIG=/etc/fbapi/production.yaml
    ExecStart=/usr/local/bin/fbapi --config /etc/fbapi/production.yaml test-server
    ExecReload=/bin/kill -HUP $MAINPID
    Restart=always
    RestartSec=5

    [Install]
    WantedBy=multi-user.target

**Supervisor Configuration:**

.. code-block:: ini

    [program:fbapi-server]
    command=/usr/local/bin/fbapi --config /etc/fbapi/production.yaml test-server
    directory=/app/fbapi
    user=fbapi
    autostart=true
    autorestart=true
    redirect_stderr=true
    stdout_logfile=/var/log/fbapi/supervisor.log

**Docker Usage:**

.. code-block:: bash

    # Build image with fbapi
    FROM python:3.9-slim
    RUN pip install fbapi
    COPY fbapi_config.yaml /app/
    WORKDIR /app
    CMD ["fbapi", "--config", "fbapi_config.yaml", "test-server"]

    # Run container
    docker run -d \
      -v /host/commands:/app/commands \
      -v /host/responses:/app/responses \
      --name fbapi-server \
      my-fbapi-image

Error Handling in CLI
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Robust CLI usage with error handling
    #!/bin/bash

    set -o pipefail  # Fail on pipe errors

    # Function to handle errors
    handle_error() {
        local exit_code=$?
        echo "Error: Command failed with exit code $exit_code" >&2
        
        # Log error details
        echo "Failed command: $BASH_COMMAND" >&2
        echo "Timestamp: $(date)" >&2
        
        exit $exit_code
    }

    # Set error trap
    trap handle_error ERR

    # Test fbapi installation
    if ! command -v fbapi &> /dev/null; then
        echo "Error: fbapi is not installed" >&2
        exit 1
    fi

    # Validate configuration before use
    if [[ -f "fbapi_config.yaml" ]]; then
        echo "Using existing configuration..."
    else
        echo "Creating default configuration..."
        fbapi create-config fbapi_config.yaml || {
            echo "Error: Failed to create configuration" >&2
            exit 1
        }
    fi

    # Test client with error handling
    echo "Testing fbapi client..."
    if fbapi --config fbapi_config.yaml test-client --timeout 10; then
        echo "Client test successful"
    else
        echo "Client test failed - check logs" >&2
        exit 1
    fi

    echo "All tests completed successfully"

Debugging with CLI
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Enable maximum verbosity for debugging
    export FBAPI_LOG_LEVEL=DEBUG

    # Run with verbose output
    fbapi --verbose test-client --command debug_command

    # Monitor with detailed output
    fbapi --verbose monitor --directory ./debug_files

    # Validate with detailed error messages
    fbapi --verbose validate broken_file.json

    # Check configuration loading
    fbapi --verbose --config debug_config.yaml version