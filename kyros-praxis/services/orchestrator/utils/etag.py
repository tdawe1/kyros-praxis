import hashlib
import json


def generate_etag(data: dict) -> str:
    """
    Generate an ETag from the data by sorting keys and using SHA256.
    """
    sorted_data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(sorted_data.encode()).hexdigest()
