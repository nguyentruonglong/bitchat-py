from typing import Optional
from .encryption import derive_channel_key

# In-memory store for encryption keys
_key_store: dict[str, bytes] = {}

def store_key(key: bytes, identifier: str) -> None:
    """
    Save encryption key securely in an in-memory store.
    
    Args:
        key (bytes): Encryption key to store.
        identifier (str): Unique identifier for the key.
    
    Raises:
        ValueError: If key or identifier is invalid.
    """
    try:
        if not key:
            raise ValueError("Key cannot be empty")
        if not identifier:
            raise ValueError("Identifier cannot be empty")
        _key_store[identifier] = key
    except Exception as e:
        raise ValueError(f"Failed to store key: {str(e)}")

def retrieve_key(identifier: str) -> Optional[bytes]:
    """
    Retrieve encryption key from the in-memory store.
    
    Args:
        identifier (str): Unique identifier for the key.
    
    Returns:
        Optional[bytes]: The stored key, or None if not found.
    """
    try:
        if not identifier:
            raise ValueError("Identifier cannot be empty")
        return _key_store.get(identifier)
    except Exception as e:
        print(f"Error retrieving key: {str(e)}")
        return None

def generate_channel_key(channel: str, password: str) -> bytes:
    """
    Derive and store channel key using PBKDF2.
    
    Args:
        channel (str): Channel name to use as salt.
        password (str): Password for key derivation.
    
    Returns:
        bytes: 32-byte derived key.
    
    Raises:
        ValueError: If channel or password is invalid.
    """
    try:
        key = derive_channel_key(password, channel)
        store_key(key, f"channel:{channel}")
        return key
    except Exception as e:
        raise ValueError(f"Failed to generate channel key: {str(e)}")