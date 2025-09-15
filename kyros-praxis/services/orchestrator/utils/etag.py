"""
ETag Generation Utilities for HTTP Caching

This module provides utilities for generating ETags (Entity Tags) for HTTP responses in the Kyros Orchestrator service.
ETags are used for caching and conditional requests to improve performance and reduce bandwidth usage.

In the Kyros Orchestrator service, ETags are particularly important for:
- Reducing unnecessary data transfers for API responses
- Enabling client-side caching mechanisms
- Supporting conditional requests (If-None-Match, If-Match headers)
- Improving overall system responsiveness

The module includes a function for generating SHA256-based ETags from data dictionaries, with proper handling
of datetime objects and other data types. ETags are returned wrapped in quotes as per the HTTP specification.

FUNCTIONS:
1. generate_etag - Generate an ETag from data using SHA256 hashing
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict


def generate_etag(data: Dict[str, Any]) -> str:
    """
    Generate an ETag from the data by sorting keys and using SHA256.
    
    This function creates a SHA256 hash of the provided data dictionary to generate
    an ETag for HTTP caching and conditional requests. The data is first serialized
    to handle special data types like datetime objects, then sorted to ensure
    consistent ETag generation regardless of key order. The resulting ETag is
    wrapped in quotes as per the HTTP specification.
    
    Args:
        data (Dict[str, Any]): Dictionary containing data to generate ETag from
        
    Returns:
        str: ETag wrapped in quotes (e.g., "a1b2c3d4...")
        
    Example:
        >>> from datetime import datetime
        >>> data = {"name": "example", "timestamp": datetime(2023, 1, 1)}
        >>> etag = generate_etag(data)
        >>> print(etag)
        "a1b2c3d4e5f6..."
        
    Note:
        - Datetime objects are serialized to ISO format strings
        - Nested dictionaries and lists are recursively processed
        - Keys are sorted to ensure consistent ETags for equivalent data
    """
    
    def serialize_value(value: Any) -> Any:
        """
        Recursively serialize values for JSON compatibility.
        
        This helper function converts special data types like datetime objects
        to JSON-compatible formats, and recursively processes dictionaries and
        lists to ensure all values are properly serialized. This is necessary
        for consistent ETag generation since the hashing process requires a
        string representation of the data.
        
        In the Kyros Orchestrator service, this function ensures that ETags
        can be consistently generated regardless of the data types present
        in the response objects, which may include complex nested structures
        with datetime objects or other non-JSON-native types.
        
        Args:
            value (Any): Value to serialize
            
        Returns:
            Any: JSON-compatible serialized value
            
        Example:
            >>> from datetime import datetime
            >>> # Serialize datetime
            >>> dt = datetime(2023, 1, 1, 12, 0, 0)
            >>> result = serialize_value(dt)
            >>> print(result)
            "2023-01-01T12:00:00"
            
            >>> # Serialize nested dictionary
            >>> data = {"name": "test", "timestamp": datetime(2023, 1, 1)}
            >>> result = serialize_value(data)
            >>> print(result)
            {"name": "test", "timestamp": "2023-01-01T00:00:00"}
        """
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, dict):
            return {k: serialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [serialize_value(item) for item in value]
        else:
            return value

    # Serialize the data to handle datetime objects
    serialized_data = serialize_value(data)
    sorted_data = json.dumps(serialized_data, sort_keys=True)
    etag = hashlib.sha256(sorted_data.encode()).hexdigest()
    return f'"{etag}"'
