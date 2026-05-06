"""
Request ID generation utilities
"""

import uuid


def generate_request_id() -> str:
    """
    Generate a unique request ID
    
    Returns:
        Unique request ID string
    """
    return f"req_{uuid.uuid4().hex[:12]}"
