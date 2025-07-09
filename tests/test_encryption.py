import pytest
from bitchat.encryption import generate_signature, verify_signature, encrypt_content, decrypt_content, derive_channel_key
from cryptography.exceptions import InvalidSignature

@pytest.fixture
def key():
    return b"\x01" * 32  # 32-byte key for testing

@pytest.fixture
def data():
    return b"test data"

def test_generate_signature(data, key):
    signature1 = generate_signature(data, key)
    assert len(signature1) == 64, f"Expected 64-byte signature, got {len(signature1)} bytes"
    
    # Test different data produces different signatures
    different_data = b"different data"
    signature2 = generate_signature(different_data, key)
    assert signature1 != signature2, "Signatures for different data should be different"
    
    # Test same data and key produces consistent signatures
    signature3 = generate_signature(data, key)
    assert signature1 == signature3, "Signatures for same data and key should be identical"

def test_verify_signature(data, key):
    signature = generate_signature(data, key)
    
    # Test valid signature
    assert verify_signature(data, signature, key), "Valid signature should verify"
    
    # Test invalid signature
    invalid_signature = b"\xFF" * 64
    assert not verify_signature(data, invalid_signature, key), "Invalid signature should not verify"
    
    # Test incorrect key
    wrong_key = b"\x02" * 32
    assert not verify_signature(data, signature, wrong_key), "Signature with wrong key should not verify"
    
    # Test tampered data
    tampered_data = b"tampered data"
    assert not verify_signature(tampered_data, signature, key), "Signature with tampered data should not verify"

def test_encrypt_decrypt_content(key):
    content = "Hello, world!"
    encrypted_data = encrypt_content(content, key)
    decrypted_content = decrypt_content(encrypted_data, key)
    
    assert decrypted_content == content, f"Expected decrypted content '{content}', got '{decrypted_content}'"
    assert len(encrypted_data) >= len(content.encode()), "Encrypted data should be at least as long as input"
    assert encrypted_data != content.encode(), "Encrypted data should differ from plaintext"

def test_decrypt_content_failure(key):
    content = "Hello, world!"
    encrypted_data = encrypt_content(content, key)
    
    # Test wrong key
    wrong_key = b"\x02" * 32
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt_content(encrypted_data, wrong_key)
    
    # Test invalid data
    invalid_data = b"\xFF" * len(encrypted_data)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt_content(invalid_data, key)

def test_derive_channel_key():
    password = "secure123"
    channel = "#secret"
    
    # Test consistent key derivation
    key1 = derive_channel_key(password, channel)
    key2 = derive_channel_key(password, channel)
    assert len(key1) == 32, f"Expected 32-byte key, got {len(key1)} bytes"
    assert key1 == key2, "Keys for same password and channel should be identical"
    
    # Test different passwords
    different_password = "other456"
    key3 = derive_channel_key(different_password, channel)
    assert key1 != key3, "Keys for different passwords should be different"
    
    # Test different channels
    different_channel = "#public"
    key4 = derive_channel_key(password, different_channel)
    assert key1 != key4, "Keys for different channels should be different"