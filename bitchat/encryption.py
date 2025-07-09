from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from typing import Optional
import os

def generate_signature(data: bytes, key: bytes) -> bytes:
    """
    Create a 64-byte packet signature using HMAC-SHA512.
    
    Args:
        data (bytes): Data to sign.
        key (bytes): Key for signing (at least 32 bytes recommended).
    
    Returns:
        bytes: 64-byte HMAC-SHA512 signature.
    """
    try:
        h = hmac.HMAC(key, hashes.SHA512())
        h.update(data)
        return h.finalize()  # Returns 64 bytes
    except Exception as e:
        raise ValueError(f"Failed to generate signature: {str(e)}")

def verify_signature(data: bytes, signature: bytes, key: bytes) -> bool:
    """
    Verify a packet signature using HMAC-SHA512.
    
    Args:
        data (bytes): Data to verify.
        signature (bytes): 64-byte signature to check.
        key (bytes): Key used for signing.
    
    Returns:
        bool: True if the signature is valid, False otherwise.
    """
    try:
        if len(signature) != 64:
            return False
        h = hmac.HMAC(key, hashes.SHA512())
        h.update(data)
        h.verify(signature)
        return True
    except Exception:
        return False

def encrypt_content(content: str, key: bytes) -> bytes:
    """
    Encrypt message content using AES-GCM.
    
    Args:
        content (str): Content to encrypt.
        key (bytes): 32-byte encryption key.
    
    Returns:
        bytes: Encrypted data (nonce + ciphertext + tag).
    """
    try:
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes")
        
        # Generate a random 12-byte nonce
        nonce = os.urandom(12)
        
        # Create cipher and encrypt
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(content.encode('utf-8')) + encryptor.finalize()
        
        # Combine nonce, ciphertext, and tag
        return nonce + ciphertext + encryptor.tag
    except Exception as e:
        raise ValueError(f"Failed to encrypt content: {str(e)}")

def decrypt_content(data: bytes, key: bytes) -> Optional[str]:
    """
    Decrypt content using AES-GCM, return None on failure.
    
    Args:
        data (bytes): Encrypted data (nonce + ciphertext + tag).
        key (bytes): 32-byte decryption key.
    
    Returns:
        Optional[str]: Decrypted content, or None if decryption fails.
    """
    try:
        if len(key) != 32:
            return None
        if len(data) < 28:  # Minimum: 12-byte nonce + 16-byte tag
            return None
            
        # Split data into nonce, ciphertext, and tag
        nonce = data[:12]
        tag = data[-16:]
        ciphertext = data[12:-16]
        
        # Create cipher and decrypt
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext.decode('utf-8')
    except Exception:
        return None

def derive_channel_key(password: str, channel: str) -> bytes:
    """
    Derive 32-byte key using PBKDF2 with SHA256, 100000 iterations, and channel as salt.
    
    Args:
        password (str): Password for key derivation.
        channel (str): Channel name to use as salt.
    
    Returns:
        bytes: 32-byte derived key.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=channel.encode(),
        iterations=100000,
    )
    return kdf.derive(password.encode())