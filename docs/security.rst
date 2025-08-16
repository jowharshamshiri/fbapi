Security
========

The fbapi library includes comprehensive security features to protect against common vulnerabilities in file-based communication systems.

Security Features
----------------

Path Traversal Protection
~~~~~~~~~~~~~~~~~~~~~~~~~

The library automatically prevents path traversal attacks:

.. code-block:: python

    from fbapi.security import SecurityValidator
    
    # Create validator with restricted paths
    validator = SecurityValidator(
        allowed_base_paths=["/safe/directory", "/another/safe/path"]
    )
    
    # This will raise SecurityError for paths outside allowed areas
    client = FileBasedAPIClient(
        command_dir="./commands",
        response_dir="./responses",
        security_validator=validator
    )

File Size Limits
~~~~~~~~~~~~~~~~

Prevent resource exhaustion with file size limits:

.. code-block:: python

    validator = SecurityValidator(
        max_file_size=1024*1024  # 1MB limit
    )

File Extension Validation
~~~~~~~~~~~~~~~~~~~~~~~~

Restrict allowed file types:

.. code-block:: python

    validator = SecurityValidator(
        allowed_extensions=[".json", ".txt"]
    )

Content Security Scanning
~~~~~~~~~~~~~~~~~~~~~~~~~

The library scans file content for potential security issues:

- Validates JSON structure for .json files
- Checks for suspicious patterns
- Prevents oversized payloads

Configuration Security
---------------------

Environment Variable Protection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use environment variables for sensitive configuration:

.. code-block:: bash

    # Don't put secrets in config files
    export FBAPI_API_KEY=your-secret-key
    export FBAPI_ENCRYPTION_KEY=your-encryption-key

Secure Defaults
~~~~~~~~~~~~~~

The library uses secure defaults:

- Maximum file size: 1MB
- Allowed extensions: .json only
- Path traversal protection enabled
- Content validation enabled

Best Practices
--------------

Directory Permissions
~~~~~~~~~~~~~~~~~~~~

Set restrictive permissions on communication directories:

.. code-block:: bash

    # Create directories with restricted access
    mkdir -p commands responses
    chmod 750 commands responses
    
    # Ensure only your application can read/write
    chown your-app:your-app commands responses

Temporary File Cleanup
~~~~~~~~~~~~~~~~~~~~~

The library automatically cleans up temporary files, but you should monitor:

.. code-block:: python

    import os
    import glob
    
    # Periodic cleanup of old files
    def cleanup_old_files(directory, max_age_seconds=3600):
        pattern = os.path.join(directory, "*.json")
        current_time = time.time()
        
        for filepath in glob.glob(pattern):
            if current_time - os.path.getctime(filepath) > max_age_seconds:
                os.remove(filepath)

Network File Systems
~~~~~~~~~~~~~~~~~~~

Be cautious when using network file systems:

.. code-block:: python

    # Force polling for network filesystems
    client = FileBasedAPIClient(
        command_dir="./commands",
        response_dir="./responses",
        monitoring_strategy="polling",  # More reliable over network
        polling_interval=2.0  # Slower polling for network latency
    )

Input Validation
~~~~~~~~~~~~~~~

Always validate data received through the API:

.. code-block:: python

    def secure_handler(command_data):
        # Validate input structure
        if not isinstance(command_data, dict):
            raise ValueError("Invalid command data format")
        
        # Validate required fields
        if 'command' not in command_data:
            raise ValueError("Missing command field")
        
        # Sanitize string inputs
        command = str(command_data['command']).strip()
        if len(command) > 100:  # Reasonable limit
            raise ValueError("Command too long")
        
        # Your secure processing here
        return process_command(command)

Security Exceptions
------------------

The library raises specific security exceptions:

:class:`~fbapi.exceptions.SecurityError`
    Raised when security validation fails

:class:`~fbapi.exceptions.ValidationError`
    Raised when data validation fails

Example of handling security errors:

.. code-block:: python

    from fbapi.exceptions import SecurityError, ValidationError
    
    try:
        client.call_command('test', callback, data=user_input)
    except SecurityError as e:
        logger.error(f"Security violation: {e}")
        # Don't expose details to user
        return {"error": "Invalid request"}
    except ValidationError as e:
        logger.warning(f"Validation failed: {e}")
        return {"error": "Invalid data format"}

Audit Logging
-------------

Enable audit logging for security monitoring:

.. code-block:: python

    import logging
    
    # Configure security audit logger
    security_logger = logging.getLogger('fbapi.security')
    security_logger.setLevel(logging.INFO)
    
    handler = logging.FileHandler('/var/log/fbapi-security.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)

This will log all security-related events for monitoring and compliance.