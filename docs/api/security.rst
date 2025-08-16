Security API
============

The security module provides comprehensive protection against common file-based attack vectors.

SecurityValidator
-----------------

.. automodule:: fbapi.security
   :members:
   :undoc-members:
   :show-inheritance:

Classes
-------

.. autoclass:: fbapi.security.SecurityValidator
   :members:
   :undoc-members:
   :show-inheritance:

Security Examples
-----------------

Basic Security Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.security import SecurityValidator

    # Create validator with default settings
    validator = SecurityValidator()

    # Validate file paths
    safe_path = "/app/data/file.json"
    dangerous_path = "../../../etc/passwd"

    if validator.validate_file_path(safe_path):
        print("Path is safe to use")
    else:
        print("Path failed security validation")

    # This will return False
    if not validator.validate_file_path(dangerous_path):
        print("Dangerous path detected and blocked")

Custom Security Policies
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.security import SecurityValidator

    # Create validator with custom settings
    validator = SecurityValidator(
        allowed_base_paths=['/safe/directory', '/another/safe/path'],
        max_file_size=1024 * 1024,  # 1MB limit
        allowed_extensions=['.json', '.yaml']
    )

    # Test path within allowed directories
    test_path = "/safe/directory/data.json"
    if validator.validate_file_path(test_path):
        print("Path within allowed directories")

    # Test file with wrong extension
    wrong_ext = "/safe/directory/data.txt"
    if not validator.validate_file_path(wrong_ext):
        print("File extension not allowed")

Directory Access Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.security import SecurityValidator
    import os

    validator = SecurityValidator(
        allowed_base_paths=['/app/commands', '/app/responses']
    )

    # Validate directory access
    for directory in ['/app/commands', '/app/responses', '/tmp']:
        if validator.validate_directory_access(directory):
            print(f"Directory {directory} is accessible")
        else:
            print(f"Directory {directory} access denied")

    # Create directories with proper permissions
    os.makedirs('/app/commands', mode=0o755, exist_ok=True)
    os.makedirs('/app/responses', mode=0o755, exist_ok=True)

Content Security Scanning
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.security import SecurityValidator
    import json

    validator = SecurityValidator()

    # Safe JSON content
    safe_content = json.dumps({
        "command": "process_data",
        "params": [{"name": "input", "value": "data.txt"}]
    })

    if validator.validate_json_content(safe_content):
        print("Content is safe")

    # Suspicious content (will be rejected)
    suspicious_content = json.dumps({
        "command": "eval(malicious_code)",
        "params": [{"name": "import", "value": "os"}]
    })

    if not validator.validate_json_content(suspicious_content):
        print("Suspicious content detected and blocked")

Filename Sanitization
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.security import SecurityValidator

    validator = SecurityValidator()

    # Sanitize dangerous filenames
    dangerous_names = [
        "../../../secret.json",
        "file:with:colons.json",
        "file*with*wildcards.json",
        "",  # Empty filename
        "   ",  # Whitespace only
    ]

    for name in dangerous_names:
        sanitized = validator.sanitize_filename(name)
        print(f"'{name}' -> '{sanitized}'")

    # Output:
    # '../../../secret.json' -> '______secret.json'
    # 'file:with:colons.json' -> 'file_with_colons.json'
    # 'file*with*wildcards.json' -> 'file_with_wildcards.json'
    # '' -> 'sanitized_file.json'
    # '   ' -> 'sanitized_file.json'

Integration with Client/Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIClient, FileBasedAPIServer
    from fbapi.security import SecurityValidator

    # Create security validator for production use
    security_validator = SecurityValidator(
        allowed_base_paths=[
            '/app/secure/commands',
            '/app/secure/responses'
        ],
        max_file_size=512 * 1024,  # 512KB limit for production
        allowed_extensions=['.json']
    )

    # Use with client
    client = FileBasedAPIClient(
        command_dir='/app/secure/commands',
        response_dir='/app/secure/responses',
        security_validator=security_validator
    )

    # Use with server
    from fbapi import EventSystem
    event_system = EventSystem()
    
    server = FileBasedAPIServer(
        command_dir='/app/secure/commands',
        response_dir='/app/secure/responses',
        event_system=event_system,
        security_validator=security_validator
    )

Security Best Practices
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.security import SecurityValidator
    from fbapi.config import FBAPIConfig
    import os
    import stat

    class SecureEnvironment:
        def __init__(self, base_directory):
            self.base_dir = base_directory
            self.setup_secure_directories()
            self.security_validator = self.create_validator()
            
        def setup_secure_directories(self):
            """Create directories with secure permissions."""
            directories = ['commands', 'responses', 'logs']
            
            for dir_name in directories:
                dir_path = os.path.join(self.base_dir, dir_name)
                os.makedirs(dir_path, exist_ok=True)
                
                # Set secure permissions (owner read/write/execute only)
                os.chmod(dir_path, stat.S_IRWXU)
                
        def create_validator(self):
            """Create security validator with strict settings."""
            return SecurityValidator(
                allowed_base_paths=[
                    os.path.join(self.base_dir, 'commands'),
                    os.path.join(self.base_dir, 'responses')
                ],
                max_file_size=256 * 1024,  # 256KB limit
                allowed_extensions=['.json']
            )
            
        def validate_file_operation(self, file_path, operation='read'):
            """Validate file operation with comprehensive checks."""
            # Basic path validation
            if not self.security_validator.validate_file_path(file_path):
                raise SecurityError(f"File path validation failed: {file_path}")
                
            # Check file exists for read operations
            if operation == 'read' and not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            # Check write permissions for write operations
            if operation == 'write':
                parent_dir = os.path.dirname(file_path)
                if not os.access(parent_dir, os.W_OK):
                    raise PermissionError(f"No write permission: {parent_dir}")
                    
            return True

    # Usage
    secure_env = SecureEnvironment('/app/secure')
    
    # Validate before file operations
    try:
        secure_env.validate_file_operation('/app/secure/commands/cmd.json', 'write')
        # Proceed with file operation
    except (SecurityError, PermissionError, FileNotFoundError) as e:
        print(f"Security validation failed: {e}")

Path Traversal Protection
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.security import SecurityValidator

    validator = SecurityValidator(
        allowed_base_paths=['/app/data']
    )

    # Test various path traversal attempts
    traversal_attempts = [
        '/app/data/../../../etc/passwd',
        '/app/data/..\\..\\..\\windows\\system32',
        '/app/data/normal/../../../secret',
        '../../../outside_directory/file.json',
        'app/data/../../../etc/shadow',
        '/app/data/subdir/../../other_dir/file.json'
    ]

    print("Path Traversal Protection Test:")
    for attempt in traversal_attempts:
        is_safe = validator.validate_file_path(attempt)
        status = "✅ BLOCKED" if not is_safe else "❌ ALLOWED"
        print(f"{status}: {attempt}")

    # All should be blocked in a properly secured environment

Content Filtering
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.security import SecurityValidator
    import json

    validator = SecurityValidator()

    # Test content filtering
    test_contents = [
        # Safe content
        {"command": "hello", "params": [{"name": "user", "value": "alice"}]},
        
        # Suspicious content that should be blocked
        {"command": "eval", "data": "malicious_code()"},
        {"import": "os", "command": "system"},
        {"exec": "rm -rf /", "type": "dangerous"},
        {"subprocess": "call", "args": ["rm", "-rf", "/"]},
        {"__import__": "os", "method": "system"}
    ]

    print("Content Security Filtering Test:")
    for content in test_contents:
        json_str = json.dumps(content)
        is_safe = validator.validate_json_content(json_str)
        status = "✅ SAFE" if is_safe else "🚨 BLOCKED"
        print(f"{status}: {content}")

Custom Security Policies
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.security import SecurityValidator
    import re

    class CustomSecurityValidator(SecurityValidator):
        """Extended security validator with custom policies."""
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.custom_patterns = [
                r'password',
                r'secret',
                r'token',
                r'api[_-]?key',
                r'private[_-]?key'
            ]
            
        def validate_json_content(self, content):
            """Enhanced content validation with custom patterns."""
            # Run base validation first
            if not super().validate_json_content(content):
                return False
                
            # Check for sensitive data patterns
            content_lower = content.lower()
            for pattern in self.custom_patterns:
                if re.search(pattern, content_lower):
                    return False
                    
            return True
            
        def validate_command_name(self, command_name):
            """Validate command names against whitelist."""
            allowed_commands = [
                'process_data',
                'convert_file',
                'send_notification',
                'get_status'
            ]
            return command_name in allowed_commands

    # Usage
    custom_validator = CustomSecurityValidator(
        allowed_base_paths=['/app/secure'],
        max_file_size=1024*1024
    )

    # Test custom validation
    sensitive_content = '{"user_password": "secret123"}'
    if not custom_validator.validate_json_content(sensitive_content):
        print("Sensitive content blocked by custom validator")