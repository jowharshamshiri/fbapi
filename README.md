# fbapi - File-Based API Communication Library

A Python library for file-based API communication between processes using the filesystem as a communication medium.

## Features

**Event-Driven Architecture**
- Event-driven file monitoring using `watchdog` library
- Automatic fallback to polling when `watchdog` unavailable
- Real-time command processing with minimal latency

**Security**
- Path traversal attack prevention
- File permission validation
- Content security scanning
- Configurable file size limits

**Configuration**
- YAML and JSON configuration file support
- Environment variable overrides
- Runtime configuration updates
- Default configuration templates

**Testing**
- Test suite with unit, integration, and performance tests
- Mock filesystem testing
- Cross-platform compatibility

**Developer Tools**
- Command-line interface for testing and debugging
- Error handling with typed exceptions
- Logging and monitoring
- Type hints and modern Python practices

## Quick Start

### Installation

```bash
pip install fbapi
```

For development with all features:
```bash
pip install fbapi[dev]
```

### Basic Usage

#### Server Setup

```python
from fbapi import FileBasedAPIServer, EventSystem

# Create event system and register handlers
event_system = EventSystem()

def hello_handler(command_data):
    params = command_data.get('params', [])
    name = next((p['value'] for p in params if p['name'] == 'name'), 'World')
    
    return {
        'name': 'greeting',
        'type': 'string', 
        'value': f'Hello, {name}!'
    }

event_system.on('hello', hello_handler)

# Start server
server = FileBasedAPIServer(
    command_dir="./commands",
    response_dir="./responses", 
    event_system=event_system
)

server.start()
```

#### Client Usage

```python
from fbapi import FileBasedAPIClient

# Create client
client = FileBasedAPIClient(
    command_dir="./commands",
    response_dir="./responses"
)

# Define response handler
def handle_response(response_data):
    if response_data['status'] == 'success':
        result = response_data['response'][0]['value']
        print(f"Received: {result}")

# Send command
client.call_command('hello', handle_response, name='Alice')

# Wait for completion
client.wait_for_completion()
```

### Configuration

Create a configuration file:

```bash
fbapi create-config fbapi_config.json
```

Use configuration in your application:

```python
from fbapi.config import load_config

config = load_config('fbapi_config.json')

client = FileBasedAPIClient(
    command_dir=config.get('directories.command_dir'),
    response_dir=config.get('directories.response_dir'),
    timeout_seconds=config.get('client.timeout_seconds')
)
```

### Environment Variables

Override configuration with environment variables:

```bash
export FBAPI_CLIENT_TIMEOUT=30.0
export FBAPI_CLIENT_MONITORING=event
export FBAPI_LOG_LEVEL=DEBUG
```

## Command Line Interface

### Test Client-Server Communication

```bash
# Start test server (in one terminal)
fbapi test-server --command echo

# Send test command (in another terminal)  
fbapi test-client --command echo --message "Hello fbapi!"
```

### Monitor Directory Activity

```bash
fbapi monitor --directory ./commands --strategy event
```

### Validate JSON Files

```bash
fbapi validate command1.json command2.json --schema-type request
```

## Advanced Features

### Security Configuration

```python
from fbapi.security import SecurityValidator

security_validator = SecurityValidator(
    allowed_base_paths=["/safe/directory"],
    max_file_size=1024*1024,  # 1MB limit
    allowed_extensions=[".json"]
)

client = FileBasedAPIClient(
    command_dir="./commands",
    response_dir="./responses",
    security_validator=security_validator
)
```

### Custom Monitoring Strategy

```python
# Force polling mode (useful for network filesystems)
client = FileBasedAPIClient(
    command_dir="./commands",
    response_dir="./responses", 
    monitoring_strategy="polling",
    polling_interval=0.5  # Poll every 500ms
)

# Force event-driven mode (requires watchdog)
client = FileBasedAPIClient(
    command_dir="./commands",
    response_dir="./responses",
    monitoring_strategy="event" 
)
```

### Error Handling

```python
from fbapi.exceptions import ValidationError, SecurityError, TimeoutError

try:
    client.call_command('test', callback, param="value")
except ValidationError as e:
    print(f"Validation failed: {e}")
except SecurityError as e:
    print(f"Security violation: {e}")
except TimeoutError as e:
    print(f"Operation timed out: {e}")
```

### Middleware and Event Processing

```python
event_system = EventSystem()

# Add middleware for logging
def logging_middleware(event_name, *args, **kwargs):
    print(f"Processing event: {event_name}")
    return args, kwargs

event_system.add_middleware(logging_middleware)

# Register multiple handlers
event_system.on('process_data', data_processor)
event_system.on('send_email', email_sender)
event_system.on('log_event', event_logger)
```

## Architecture

### Communication Flow

```
Client                    Filesystem                    Server
  │                          │                           │
  ├─ Create command.json ────┤                           │
  │                          ├─ Monitor for files ──────┤
  │                          │                           ├─ Process command
  │                          │                           ├─ Generate response
  │                          ├─ Create response.json ────┤
  ├─ Monitor for response ───┤                           │
  ├─ Process response        │                           │
```

### File Formats

#### Command Format
```json
{
  "command": "hello",
  "request_id": "uuid-string",
  "params": [
    {
      "name": "username", 
      "type": "string",
      "value": "alice"
    }
  ],
  "response_file": "cmd_uuid.json"
}
```

#### Response Format
```json
{
  "request_id": "uuid-string",
  "status": "success",
  "response": [
    {
      "name": "result",
      "type": "string", 
      "value": "Hello, alice!"
    }
  ]
}
```

#### Error Response Format
```json
{
  "request_id": "uuid-string", 
  "status": "error",
  "error": {
    "code": 400,
    "message": "Validation failed: missing required field"
  }
}
```

## Performance

### Benchmarks

| Feature | Event-Driven | Polling (1s) | Polling (0.1s) |
|---------|-------------|--------------|----------------|
| Response Time | ~10ms | ~500ms | ~50ms |
| CPU Usage | Low | Very Low | Low |
| File System Load | Minimal | Very Low | Low |

### Optimization

1. Use event-driven monitoring when possible for best performance
2. Tune polling intervals based on your latency requirements  
3. Implement connection pooling for high-frequency communication
4. Use appropriate file size limits to prevent resource exhaustion
5. Configure logging levels appropriately for production

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run all tests
pytest

# Run with coverage
pytest --cov=fbapi --cov-report=html

# Run only unit tests
pytest tests/ -m "not integration"

# Run integration tests
pytest tests/ -m integration
```

### Code Quality

```bash
# Format code
black fbapi/
isort fbapi/

# Lint code  
flake8 fbapi/
mypy fbapi/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [https://fbapi.readthedocs.io/](https://fbapi.readthedocs.io/)
- **Issues**: [https://github.com/your-username/fbapi/issues](https://github.com/your-username/fbapi/issues)
- **Discussions**: [https://github.com/your-username/fbapi/discussions](https://github.com/your-username/fbapi/discussions)

## Changelog

### v0.1.0 (2025-08-16)
- Initial release
- Event-driven and polling-based monitoring
- Security features
- Configuration management
- Command-line interface
- Test suite
- Documentation and examples