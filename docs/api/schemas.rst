Schemas API
===========

The schemas module provides JSON schema management with caching and validation capabilities.

SchemaManager
-------------

.. automodule:: fbapi.schemas
   :members:
   :undoc-members:
   :show-inheritance:

Classes
-------

.. autoclass:: fbapi.schemas.SchemaManager
   :members:
   :undoc-members:
   :show-inheritance:

Schema Examples
---------------

Basic Schema Usage
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.schemas import SchemaManager
    from jsonschema import validate, ValidationError

    # Create schema manager
    schema_manager = SchemaManager()

    # Get built-in schemas
    request_schema = schema_manager.get_schema('request')
    response_schema = schema_manager.get_schema('response')

    # Validate request data
    request_data = {
        "command": "hello",
        "request_id": "req-123",
        "params": [
            {
                "name": "username",
                "type": "string",
                "value": "alice"
            }
        ]
    }

    try:
        validate(instance=request_data, schema=request_schema)
        print("Request data is valid")
    except ValidationError as e:
        print(f"Validation failed: {e}")

Custom Schema Directory
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.schemas import SchemaManager
    import json
    import os

    # Create custom schema directory
    schema_dir = "./custom_schemas"
    os.makedirs(schema_dir, exist_ok=True)

    # Create custom request schema
    custom_request_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["command", "user_id", "timestamp"],
        "properties": {
            "command": {
                "type": "string",
                "enum": ["login", "logout", "process", "status"]
            },
            "user_id": {
                "type": "string",
                "pattern": "^[a-zA-Z0-9_]+$"
            },
            "timestamp": {
                "type": "number",
                "minimum": 0
            },
            "params": {
                "type": "object",
                "additionalProperties": True
            }
        }
    }

    # Save custom schema
    with open(f"{schema_dir}/request_schema.json", 'w') as f:
        json.dump(custom_request_schema, f, indent=2)

    # Use custom schema manager
    schema_manager = SchemaManager(schema_dir=schema_dir)

    # Validate with custom schema
    custom_request = {
        "command": "login",
        "user_id": "alice_123",
        "timestamp": 1640995200,
        "params": {
            "password": "secret",
            "remember_me": True
        }
    }

    try:
        validate(instance=custom_request, schema=schema_manager.get_schema('request'))
        print("Custom request is valid")
    except ValidationError as e:
        print(f"Custom validation failed: {e}")

Adding Custom Schemas
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.schemas import SchemaManager

    schema_manager = SchemaManager()

    # Define custom schemas for specific commands
    user_command_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["action", "user_data"],
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "update", "delete", "get"]
            },
            "user_data": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "minLength": 3,
                        "maxLength": 50
                    },
                    "email": {
                        "type": "string",
                        "format": "email"
                    },
                    "age": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 150
                    }
                },
                "required": ["username", "email"]
            }
        }
    }

    file_command_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["operation", "file_path"],
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["read", "write", "delete", "copy", "move"]
            },
            "file_path": {
                "type": "string",
                "pattern": "^[^<>:\"|?*]*$"  # Valid file path
            },
            "content": {
                "type": "string"
            },
            "destination": {
                "type": "string"
            }
        }
    }

    # Add custom schemas
    schema_manager.add_custom_schema('user_command', user_command_schema)
    schema_manager.add_custom_schema('file_command', file_command_schema)

    # Use custom schemas for validation
    user_request = {
        "action": "create",
        "user_data": {
            "username": "john_doe",
            "email": "john@example.com",
            "age": 30
        }
    }

    file_request = {
        "operation": "copy",
        "file_path": "/source/file.txt",
        "destination": "/destination/file.txt"
    }

    # Validate against custom schemas
    from jsonschema import validate

    try:
        validate(instance=user_request, schema=schema_manager.get_schema('user_command'))
        print("User command is valid")
        
        validate(instance=file_request, schema=schema_manager.get_schema('file_command'))
        print("File command is valid")
        
    except ValidationError as e:
        print(f"Validation failed: {e}")

Schema Caching and Performance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.schemas import SchemaManager
    import time
    import json

    # Measure schema loading performance
    def benchmark_schema_loading():
        # Create schema manager (loads schemas on init)
        start_time = time.time()
        schema_manager = SchemaManager()
        init_time = time.time() - start_time
        
        print(f"Schema manager initialization: {init_time:.3f}s")
        
        # Test schema retrieval (should be cached)
        iterations = 1000
        
        start_time = time.time()
        for _ in range(iterations):
            schema = schema_manager.get_schema('request')
        cached_time = time.time() - start_time
        
        print(f"Retrieved schema {iterations} times: {cached_time:.3f}s")
        print(f"Average per retrieval: {cached_time/iterations*1000:.3f}ms")
        
        # Test schema reload
        start_time = time.time()
        schema_manager.reload_schemas()
        reload_time = time.time() - start_time
        
        print(f"Schema reload: {reload_time:.3f}s")

    benchmark_schema_loading()

Schema Validation with Error Details
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.schemas import SchemaManager
    from jsonschema import validate, ValidationError
    import json

    def detailed_validation_example():
        schema_manager = SchemaManager()
        request_schema = schema_manager.get_schema('request')
        
        # Test various invalid requests
        invalid_requests = [
            # Missing required field
            {
                "command": "test",
                "params": []
                # Missing request_id
            },
            
            # Invalid parameter structure
            {
                "command": "test",
                "request_id": "req-123",
                "params": [
                    {
                        "name": "param1",
                        # Missing type and value
                    }
                ]
            },
            
            # Wrong type
            {
                "command": 123,  # Should be string
                "request_id": "req-123",
                "params": []
            },
            
            # Invalid additional property
            {
                "command": "test",
                "request_id": "req-123",
                "params": [],
                "invalid_field": "not_allowed"
            }
        ]
        
        for i, request_data in enumerate(invalid_requests):
            try:
                validate(instance=request_data, schema=request_schema)
                print(f"Request {i+1}: Valid (unexpected)")
                
            except ValidationError as e:
                print(f"Request {i+1}: Invalid")
                print(f"  Error: {e.message}")
                print(f"  Path: {'.'.join(str(p) for p in e.absolute_path)}")
                print(f"  Failed value: {e.instance}")
                print(f"  Schema path: {'.'.join(str(p) for p in e.schema_path)}")
                print()

    detailed_validation_example()

Integration with Client/Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi import FileBasedAPIClient, FileBasedAPIServer, EventSystem
    from fbapi.schemas import SchemaManager
    from jsonschema import validate, ValidationError
    import json

    # Custom schema for business commands
    business_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["business_command", "data"],
        "properties": {
            "business_command": {
                "type": "string",
                "enum": ["calculate", "report", "export"]
            },
            "data": {
                "type": "object",
                "properties": {
                    "values": {
                        "type": "array",
                        "items": {"type": "number"}
                    },
                    "operation": {
                        "type": "string",
                        "enum": ["sum", "average", "max", "min"]
                    }
                },
                "required": ["values", "operation"]
            }
        }
    }

    def create_validating_server():
        # Create schema manager with custom schema
        schema_manager = SchemaManager()
        schema_manager.add_custom_schema('business', business_schema)
        
        event_system = EventSystem()
        
        def validating_handler(command_data):
            """Handler that validates business data."""
            try:
                # Extract business data from command params
                params = command_data.get('params', [])
                business_data = None
                
                for param in params:
                    if param.get('name') == 'business_data':
                        business_data = param.get('value')
                        break
                
                if not business_data:
                    raise ValueError("Missing business_data parameter")
                
                # Validate against business schema
                validate(instance=business_data, schema=schema_manager.get_schema('business'))
                
                # Process validated data
                cmd = business_data['business_command']
                data = business_data['data']
                
                if cmd == 'calculate':
                    values = data['values']
                    operation = data['operation']
                    
                    if operation == 'sum':
                        result = sum(values)
                    elif operation == 'average':
                        result = sum(values) / len(values) if values else 0
                    elif operation == 'max':
                        result = max(values) if values else 0
                    elif operation == 'min':
                        result = min(values) if values else 0
                    
                    return {
                        'name': 'calculation_result',
                        'type': 'number',
                        'value': result
                    }
                
                return {
                    'name': 'status',
                    'type': 'string',
                    'value': f'Processed {cmd} command'
                }
                
            except ValidationError as e:
                raise ValueError(f"Business data validation failed: {e.message}")
            except Exception as e:
                raise ValueError(f"Business logic error: {e}")
        
        event_system.on('business_process', validating_handler)
        
        return FileBasedAPIServer(
            command_dir="./commands",
            response_dir="./responses",
            event_system=event_system
        )

    def test_business_validation():
        server = create_validating_server()
        client = FileBasedAPIClient("./commands", "./responses")
        
        try:
            server.start()
            
            # Valid business data
            valid_business_data = {
                "business_command": "calculate",
                "data": {
                    "values": [1, 2, 3, 4, 5],
                    "operation": "sum"
                }
            }
            
            def handle_response(response):
                print(f"Response: {json.dumps(response, indent=2)}")
            
            # Send valid request
            client.call_command(
                'business_process',
                handle_response,
                business_data=valid_business_data
            )
            
            # Send invalid request (will be rejected)
            invalid_business_data = {
                "business_command": "invalid_command",  # Not in enum
                "data": {
                    "values": "not_an_array",  # Wrong type
                    "operation": "sum"
                }
            }
            
            client.call_command(
                'business_process',
                handle_response,
                business_data=invalid_business_data
            )
            
            client.wait_for_completion()
            
        finally:
            server.stop()
            client.cleanup()

Schema Evolution and Versioning
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.schemas import SchemaManager
    import json

    class VersionedSchemaManager(SchemaManager):
        """Schema manager that supports versioning."""
        
        def __init__(self, schema_dir=None, default_version='v1'):
            super().__init__(schema_dir)
            self.default_version = default_version
            self.versioned_schemas = {}
            
        def add_versioned_schema(self, schema_type, version, schema):
            """Add a versioned schema."""
            key = f"{schema_type}_{version}"
            self.versioned_schemas[key] = schema
            
        def get_versioned_schema(self, schema_type, version=None):
            """Get schema by type and version."""
            version = version or self.default_version
            key = f"{schema_type}_{version}"
            
            if key in self.versioned_schemas:
                return self.versioned_schemas[key]
            
            # Fallback to base schema
            return self.get_schema(schema_type)
            
        def validate_with_version(self, data, schema_type, version=None):
            """Validate data against versioned schema."""
            schema = self.get_versioned_schema(schema_type, version)
            from jsonschema import validate
            validate(instance=data, schema=schema)

    # Usage example
    versioned_manager = VersionedSchemaManager()

    # Add v1 schema
    user_schema_v1 = {
        "type": "object",
        "required": ["name", "email"],
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"}
        }
    }

    # Add v2 schema (with additional required field)
    user_schema_v2 = {
        "type": "object",
        "required": ["name", "email", "age"],
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "age": {"type": "integer", "minimum": 0}
        }
    }

    versioned_manager.add_versioned_schema('user', 'v1', user_schema_v1)
    versioned_manager.add_versioned_schema('user', 'v2', user_schema_v2)

    # Test data
    user_data_v1 = {
        "name": "John Doe",
        "email": "john@example.com"
    }

    user_data_v2 = {
        "name": "Jane Doe", 
        "email": "jane@example.com",
        "age": 30
    }

    # Validate against different versions
    try:
        versioned_manager.validate_with_version(user_data_v1, 'user', 'v1')
        print("User data valid for v1 schema")
        
        versioned_manager.validate_with_version(user_data_v2, 'user', 'v2')
        print("User data valid for v2 schema")
        
        # This will fail - v1 data against v2 schema
        versioned_manager.validate_with_version(user_data_v1, 'user', 'v2')
        
    except Exception as e:
        print(f"Validation failed: {e}")