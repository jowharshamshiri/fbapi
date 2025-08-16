"""
Command-line interface for fbapi testing and debugging.
"""

import argparse
import json
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from . import __version__
from .client import FileBasedAPIClient
from .server import FileBasedAPIServer, EventSystem
from .config import load_config, create_default_config_file
from .exceptions import FBAPIError

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO") -> None:
    """Setup basic logging for CLI."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def cmd_version(args) -> None:
    """Show version information."""
    print(f"fbapi version {__version__}")


def cmd_create_config(args) -> None:
    """Create default configuration file."""
    try:
        create_default_config_file(args.output)
        print(f"Default configuration created at: {args.output}")
    except Exception as e:
        print(f"Error creating config: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_test_client(args) -> None:
    """Test client functionality."""
    try:
        # Load configuration
        config = load_config(args.config) if args.config else load_config()
        
        # Setup logging
        if args.verbose:
            config.set('logging.level', 'DEBUG')
        config.setup_logging()
        
        # Get directories from config
        command_dir = config.get('directories.command_dir')
        response_dir = config.get('directories.response_dir')
        
        print(f"Testing client with command_dir={command_dir}, response_dir={response_dir}")
        
        # Create client
        client = FileBasedAPIClient(
            command_dir=command_dir,
            response_dir=response_dir,
            timeout_seconds=args.timeout,
            monitoring_strategy=args.strategy
        )
        
        # Prepare test command
        test_params = {
            'test_param': args.message or 'Hello from fbapi CLI!'
        }
        
        # Response handler
        response_received = False
        response_data = None
        
        def handle_response(data: Dict[str, Any]) -> None:
            nonlocal response_received, response_data
            response_received = True
            response_data = data
            print(f"Response received: {json.dumps(data, indent=2)}")
        
        # Send command
        print(f"Sending test command: {args.command}")
        request_id = client.call_command(args.command, handle_response, **test_params)
        print(f"Command sent with request ID: {request_id}")
        
        # Wait for response
        print("Waiting for response...")
        start_time = time.time()
        while not response_received and (time.time() - start_time) < args.timeout:
            time.sleep(0.1)
        
        if response_received:
            print("✅ Test completed successfully")
            if response_data and response_data.get('status') == 'error':
                print("⚠️  Response contains error:")
                print(json.dumps(response_data.get('error', {}), indent=2))
        else:
            print("❌ Test failed: No response received within timeout")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Test failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_test_server(args) -> None:
    """Test server functionality."""
    try:
        # Load configuration
        config = load_config(args.config) if args.config else load_config()
        
        # Setup logging
        if args.verbose:
            config.set('logging.level', 'DEBUG')
        config.setup_logging()
        
        # Get directories from config
        command_dir = config.get('directories.command_dir')
        response_dir = config.get('directories.response_dir')
        
        print(f"Starting test server with command_dir={command_dir}, response_dir={response_dir}")
        
        # Create event system and register test handler
        event_system = EventSystem()
        
        def test_handler(command_data: Dict[str, Any]) -> Dict[str, Any]:
            print(f"Test handler received command: {command_data.get('command')}")
            params = command_data.get('params', [])
            
            # Echo back the parameters
            return {
                'name': 'echo_response',
                'type': 'test_result',
                'value': {
                    'message': f"Echo: {params}",
                    'timestamp': time.time(),
                    'command': command_data.get('command')
                }
            }
        
        event_system.on(args.command, test_handler)
        
        # Create and start server
        server = FileBasedAPIServer(
            command_dir=command_dir,
            response_dir=response_dir,
            event_system=event_system,
            monitoring_strategy=args.strategy
        )
        
        print(f"✅ Server started and listening for '{args.command}' commands")
        print("Press Ctrl+C to stop...")
        
        try:
            server.start()
            # Keep server running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\\n🛑 Stopping server...")
        finally:
            server.stop()
            print("✅ Server stopped")
            
    except Exception as e:
        print(f"❌ Server test failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_monitor(args) -> None:
    """Monitor directories for activity."""
    try:
        # Load configuration
        config = load_config(args.config) if args.config else load_config()
        
        # Setup logging
        if args.verbose:
            config.set('logging.level', 'DEBUG')
        config.setup_logging()
        
        command_dir = Path(args.directory or config.get('directories.command_dir'))
        
        print(f"Monitoring directory: {command_dir}")
        print("Press Ctrl+C to stop...")
        
        def file_handler(file_path: str) -> None:
            print(f"📁 File detected: {file_path}")
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                print(f"📄 Content: {json.dumps(data, indent=2)}")
            except Exception as e:
                print(f"⚠️  Error reading file: {e}")
        
        from .monitoring import create_monitor
        monitor = create_monitor(
            str(command_dir),
            file_handler,
            monitoring_strategy=args.strategy
        )
        
        try:
            monitor.start()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\\n🛑 Stopping monitor...")
        finally:
            monitor.stop()
            print("✅ Monitor stopped")
            
    except Exception as e:
        print(f"❌ Monitor failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_validate_schema(args) -> None:
    """Validate JSON files against schemas."""
    try:
        from .schemas import SchemaManager
        
        schema_manager = SchemaManager()
        
        for file_path in args.files:
            path = Path(file_path)
            if not path.exists():
                print(f"❌ File not found: {file_path}")
                continue
            
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                
                # Try to determine schema type from content
                if 'command' in data and 'request_id' in data:
                    schema_type = 'request'
                elif 'request_id' in data and 'status' in data:
                    schema_type = 'response'
                else:
                    schema_type = args.schema_type
                
                schema = schema_manager.get_schema(schema_type)
                from jsonschema import validate
                validate(instance=data, schema=schema)
                
                print(f"✅ {file_path}: Valid {schema_type} schema")
                
            except json.JSONDecodeError as e:
                print(f"❌ {file_path}: Invalid JSON - {e}")
            except Exception as e:
                print(f"❌ {file_path}: Schema validation failed - {e}")
                
    except Exception as e:
        print(f"❌ Schema validation failed: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="fbapi - File-based API communication library CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')
    version_parser.set_defaults(func=cmd_version)
    
    # Create config command
    config_parser = subparsers.add_parser('create-config', help='Create default configuration file')
    config_parser.add_argument('output', help='Output configuration file path')
    config_parser.set_defaults(func=cmd_create_config)
    
    # Test client command
    client_parser = subparsers.add_parser('test-client', help='Test client functionality')
    client_parser.add_argument('--command', default='test_echo', help='Command to send (default: test_echo)')
    client_parser.add_argument('--message', help='Test message to send')
    client_parser.add_argument('--timeout', type=float, default=30.0, help='Timeout in seconds')
    client_parser.add_argument('--strategy', choices=['auto', 'event', 'polling'], default='auto', 
                              help='Monitoring strategy')
    client_parser.set_defaults(func=cmd_test_client)
    
    # Test server command
    server_parser = subparsers.add_parser('test-server', help='Test server functionality')
    server_parser.add_argument('--command', default='test_echo', help='Command to handle (default: test_echo)')
    server_parser.add_argument('--strategy', choices=['auto', 'event', 'polling'], default='auto',
                              help='Monitoring strategy')
    server_parser.set_defaults(func=cmd_test_server)
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor directory for file changes')
    monitor_parser.add_argument('--directory', help='Directory to monitor (default from config)')
    monitor_parser.add_argument('--strategy', choices=['auto', 'event', 'polling'], default='auto',
                               help='Monitoring strategy')
    monitor_parser.set_defaults(func=cmd_monitor)
    
    # Validate schema command
    validate_parser = subparsers.add_parser('validate', help='Validate JSON files against schemas')
    validate_parser.add_argument('files', nargs='+', help='JSON files to validate')
    validate_parser.add_argument('--schema-type', choices=['request', 'response'], default='request',
                                help='Schema type for validation')
    validate_parser.set_defaults(func=cmd_validate_schema)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)
    
    # Setup basic logging
    setup_logging('DEBUG' if args.verbose else 'INFO')
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\\n🛑 Interrupted by user")
        sys.exit(130)
    except FBAPIError as e:
        print(f"❌ fbapi error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()