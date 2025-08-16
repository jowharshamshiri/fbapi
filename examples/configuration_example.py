#!/usr/bin/env python3
"""
Configuration example for fbapi.

This example demonstrates how to use configuration files
and environment variables with fbapi.
"""

import json
import logging
from pathlib import Path

from fbapi import FileBasedAPIClient, FileBasedAPIServer, EventSystem
from fbapi.config import FBAPIConfig, create_default_config_file

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_example_config():
    """Create an example configuration file."""
    
    config_path = Path("./fbapi_config_example.json")
    
    # Create custom configuration
    custom_config = {
        "client": {
            "timeout_seconds": 30.0,
            "monitoring_strategy": "auto",
            "polling_interval": 0.5,
            "max_file_size": 5242880  # 5MB
        },
        "server": {
            "monitoring_strategy": "auto",
            "polling_interval": 0.5,
            "max_file_size": 5242880  # 5MB
        },
        "security": {
            "allowed_extensions": [".json"],
            "path_validation": True,
            "content_validation": True,
            "max_file_size": 5242880  # 5MB
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": None
        },
        "directories": {
            "command_dir": "./config_example/commands",
            "response_dir": "./config_example/responses",
            "schema_dir": None
        }
    }
    
    # Save configuration
    with open(config_path, 'w') as f:
        json.dump(custom_config, f, indent=2)
    
    logger.info(f"Created example configuration: {config_path}")
    return config_path


def main():
    """Run configuration example."""
    
    # Create example configuration file
    config_path = create_example_config()
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = FBAPIConfig(config_path=str(config_path))
        
        # Setup logging from config
        config.setup_logging()
        
        # Display loaded configuration
        print("\\n=== Loaded Configuration ===")
        print(f"Client timeout: {config.get('client.timeout_seconds')} seconds")
        print(f"Client monitoring: {config.get('client.monitoring_strategy')}")
        print(f"Server monitoring: {config.get('server.monitoring_strategy')}")
        print(f"Command directory: {config.get('directories.command_dir')}")
        print(f"Response directory: {config.get('directories.response_dir')}")
        print(f"Max file size: {config.get('security.max_file_size')} bytes")
        print(f"Log level: {config.get('logging.level')}")
        
        # Create directories
        command_dir = Path(config.get('directories.command_dir'))
        response_dir = Path(config.get('directories.response_dir'))
        command_dir.mkdir(parents=True, exist_ok=True)
        response_dir.mkdir(parents=True, exist_ok=True)
        
        # Create event system with handlers
        event_system = EventSystem()
        
        def config_info_handler(command_data):
            """Return information about current configuration."""
            return {
                'name': 'config_info',
                'type': 'object',
                'value': {
                    'client_timeout': config.get('client.timeout_seconds'),
                    'monitoring_strategy': config.get('client.monitoring_strategy'),
                    'max_file_size': config.get('security.max_file_size'),
                    'command_dir': config.get('directories.command_dir'),
                    'response_dir': config.get('directories.response_dir')
                }
            }
        
        def update_config_handler(command_data):
            """Handle configuration updates."""
            params = command_data.get('params', [])
            
            updates = {}
            for param in params:
                if param['name'] == 'timeout':
                    config.set('client.timeout_seconds', param['value'])
                    updates['timeout'] = param['value']
                elif param['name'] == 'log_level':
                    config.set('logging.level', param['value'])
                    updates['log_level'] = param['value']
            
            return {
                'name': 'config_updated',
                'type': 'object',
                'value': {
                    'updates_applied': updates,
                    'message': f'Configuration updated with {len(updates)} changes'
                }
            }
        
        event_system.on('get_config', config_info_handler)
        event_system.on('update_config', update_config_handler)
        
        # Create server using configuration
        server = FileBasedAPIServer(
            command_dir=config.get('directories.command_dir'),
            response_dir=config.get('directories.response_dir'),
            event_system=event_system,
            monitoring_strategy=config.get('server.monitoring_strategy')
        )
        
        # Create client using configuration
        client = FileBasedAPIClient(
            command_dir=config.get('directories.command_dir'),
            response_dir=config.get('directories.response_dir'),
            timeout_seconds=config.get('client.timeout_seconds'),
            monitoring_strategy=config.get('client.monitoring_strategy')
        )
        
        logger.info("Starting server...")
        server.start()
        
        try:
            # Example 1: Get configuration info
            print("\\n=== Example 1: Get Configuration Info ===")
            
            info_received = False
            info_data = None
            
            def handle_info_response(data):
                nonlocal info_received, info_data
                info_received = True
                info_data = data
            
            client.call_command('get_config', handle_info_response)
            
            # Wait for response
            import time
            timeout = config.get('client.timeout_seconds')
            start_time = time.time()
            while not info_received and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if info_received and info_data['status'] == 'success':
                config_info = info_data['response'][0]['value']
                print(f"✅ Server configuration info:")
                for key, value in config_info.items():
                    print(f"   {key}: {value}")
            else:
                print("❌ Failed to get configuration info")
            
            # Example 2: Update configuration
            print("\\n=== Example 2: Update Configuration ===")
            
            update_received = False
            update_data = None
            
            def handle_update_response(data):
                nonlocal update_received, update_data
                update_received = True
                update_data = data
            
            client.call_command('update_config', handle_update_response,
                              timeout=15.0, log_level='DEBUG')
            
            # Wait for response
            start_time = time.time()
            while not update_received and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if update_received and update_data['status'] == 'success':
                result = update_data['response'][0]['value']
                print(f"✅ Configuration updated:")
                print(f"   Updates: {result['updates_applied']}")
                print(f"   Message: {result['message']}")
            else:
                print("❌ Failed to update configuration")
            
            # Example 3: Save updated configuration
            print("\\n=== Example 3: Save Updated Configuration ===")
            
            updated_config_path = Path("./fbapi_updated_config.json")
            config.save_to_file(str(updated_config_path))
            print(f"✅ Updated configuration saved to: {updated_config_path}")
            
            # Show the difference
            print("\\nConfiguration changes:")
            print(f"   Original timeout: 30.0 seconds")
            print(f"   Updated timeout: {config.get('client.timeout_seconds')} seconds")
            print(f"   Original log level: INFO")
            print(f"   Updated log level: {config.get('logging.level')}")
            
            # Wait for completion
            client.wait_for_completion()
            
            print("\\n=== Configuration example completed successfully! ===")
            
        finally:
            server.stop()
            client.cleanup()
    
    except Exception as e:
        logger.error(f"Configuration example failed: {e}")
        print(f"❌ Configuration example failed: {e}")
    
    finally:
        # Cleanup example files
        if config_path.exists():
            config_path.unlink()
            logger.info(f"Cleaned up: {config_path}")


def demonstrate_environment_variables():
    """Demonstrate environment variable configuration."""
    
    print("\\n=== Environment Variable Configuration ===")
    print("You can override configuration using environment variables:")
    print("")
    print("  export FBAPI_CLIENT_TIMEOUT=45.0")
    print("  export FBAPI_CLIENT_MONITORING=polling")
    print("  export FBAPI_LOG_LEVEL=DEBUG")
    print("  export FBAPI_COMMAND_DIR=/custom/commands")
    print("  export FBAPI_RESPONSE_DIR=/custom/responses")
    print("")
    print("Environment variables take precedence over config files.")
    print("Available environment variables:")
    
    env_vars = [
        "FBAPI_CLIENT_TIMEOUT",
        "FBAPI_CLIENT_MONITORING", 
        "FBAPI_SERVER_MONITORING",
        "FBAPI_SECURITY_MAX_SIZE",
        "FBAPI_LOG_LEVEL",
        "FBAPI_LOG_FILE",
        "FBAPI_COMMAND_DIR",
        "FBAPI_RESPONSE_DIR",
        "FBAPI_SCHEMA_DIR"
    ]
    
    for var in env_vars:
        print(f"  - {var}")


if __name__ == '__main__':
    main()
    demonstrate_environment_variables()