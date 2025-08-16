"""
Schema management for fbapi JSON validation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages JSON schemas with caching for performance."""
    
    def __init__(self, schema_dir: Optional[str] = None):
        """
        Initialize schema manager.
        
        Args:
            schema_dir: Directory containing schema files
        """
        self.schema_dir = Path(schema_dir) if schema_dir else self._get_default_schema_dir()
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        self._load_schemas()
    
    def _get_default_schema_dir(self) -> Path:
        """Get default schema directory."""
        # Use schemas from the original json_schemas directory
        current_dir = Path(__file__).parent.parent
        return current_dir / "json_schemas"
    
    def _load_schemas(self) -> None:
        """Load schemas into cache."""
        try:
            if not self.schema_dir.exists():
                logger.warning(f"Schema directory not found: {self.schema_dir}")
                self._create_default_schemas()
                return
            
            # Load request schema
            request_schema_file = self.schema_dir / "request_schema.json"
            if request_schema_file.exists():
                with open(request_schema_file, 'r') as f:
                    self._schema_cache["request"] = json.load(f)
            
            # Load response schema
            response_schema_file = self.schema_dir / "response_schema.json"
            if response_schema_file.exists():
                with open(response_schema_file, 'r') as f:
                    self._schema_cache["response"] = json.load(f)
            
            logger.info(f"Loaded {len(self._schema_cache)} schemas from {self.schema_dir}")
            
        except Exception as e:
            logger.error(f"Error loading schemas: {e}")
            self._create_default_schemas()
    
    def _create_default_schemas(self) -> None:
        """Create default schemas if none exist."""
        logger.info("Creating default schemas")
        
        # Default request schema
        self._schema_cache["request"] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["command", "params", "request_id"],
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The name of the command to be executed."
                },
                "request_id": {
                    "type": "string",
                    "description": "A unique identifier for the request."
                },
                "params": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "type", "value"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The name of the param."
                            },
                            "type": {
                                "type": "string",
                                "description": "The type of the resource packet."
                            },
                            "value": {
                                "description": "The value of the resource, structure depends on the type."
                            }
                        }
                    },
                    "description": "List of parameters for the command."
                },
                "response_file": {
                    "type": "string",
                    "description": "Expected response file name."
                }
            }
        }
        
        # Default response schema
        self._schema_cache["response"] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["request_id", "status"],
            "properties": {
                "request_id": {
                    "type": "string",
                    "description": "The unique identifier of the request this response corresponds to."
                },
                "status": {
                    "type": "string",
                    "enum": ["success", "error"],
                    "description": "Indicates whether the command was executed successfully or if an error occurred."
                },
                "response": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "type", "value"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The name of the param."
                            },
                            "type": {
                                "type": "string",
                                "description": "The type of the resource packet."
                            },
                            "value": {
                                "description": "The value of the resource, structure depends on the type."
                            }
                        }
                    },
                    "description": "The data returned by the command. Present only if status is 'success'."
                },
                "error": {
                    "type": "object",
                    "required": ["code", "message"],
                    "properties": {
                        "code": {
                            "type": "integer",
                            "description": "A code representing the type of error that occurred."
                        },
                        "message": {
                            "type": "string",
                            "description": "A human-readable message providing more details about the error."
                        }
                    },
                    "description": "Details of the error, if any occurred during command execution. Present only if status is 'error'."
                }
            }
        }
    
    def get_schema(self, schema_type: str) -> Dict[str, Any]:
        """
        Get schema by type.
        
        Args:
            schema_type: Type of schema ("request" or "response")
            
        Returns:
            Schema dictionary
            
        Raises:
            ConfigurationError: If schema type is unknown
        """
        if schema_type not in self._schema_cache:
            raise ConfigurationError(f"Unknown schema type: {schema_type}")
        
        return self._schema_cache[schema_type]
    
    def reload_schemas(self) -> None:
        """Reload schemas from disk."""
        self._schema_cache.clear()
        self._load_schemas()
    
    def add_custom_schema(self, schema_type: str, schema: Dict[str, Any]) -> None:
        """
        Add a custom schema.
        
        Args:
            schema_type: Type identifier for the schema
            schema: Schema dictionary
        """
        self._schema_cache[schema_type] = schema
        logger.info(f"Added custom schema: {schema_type}")
    
    def get_available_schemas(self) -> list:
        """Get list of available schema types."""
        return list(self._schema_cache.keys())