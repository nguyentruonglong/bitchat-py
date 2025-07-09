import pytest
from bitchat.message import pad, unpad, optimal_block_size

def test_basic_padding():
    """Test padding and unpadding of 'Hello' to 256 bytes."""
    data = "Hello".encode()
    padded = pad(data, 256)
    assert len(padded) == 256
    assert unpad(padded) == data

def test_multiple_block_sizes():
    """Test padding/unpadding and optimal_block_size for varying message sizes."""
    test_cases = [
        (10, 256),   # Small data
        (200, 256),  # Near block boundary
        (300, 512),  # Next block size
        (600, 1024), # Larger block
    ]
    
    for data_size, expected_block in test_cases:
        data = b"x" * data_size
        block_size = optimal_block_size(data_size)
        assert block_size == expected_block, f"Expected block size {expected_block} for {data_size} bytes, got {block_size}"
        padded = pad(data, block_size)
        assert len(padded) == block_size, f"Padded size {len(padded)} does not match {block_size}"
        assert unpad(padded) == data, f"Unpadded data does not match original for size {data_size}"

def test_padding_with_large_data():
    """Test padding 1500-byte and 1800-byte data to 2048-byte block."""
    test_cases = [1500, 1800]
    block_size = 2048
    
    for data_size in test_cases:
        data = b"x" * data_size
        assert optimal_block_size(data_size) == block_size, f"Expected block size {block_size} for {data_size} bytes"
        padded = pad(data, block_size)
        assert len(padded) == block_size, f"Padded size {len(padded)} does not match {block_size} for {data_size} bytes"
        assert unpad(padded) == data, f"Unpadded data does not match original for {data_size} bytes"

def test_invalid_padding():
    """Test unpadding empty and invalid padding data."""
    # Empty data
    assert unpad(b"") == b"", "Expected empty data to return empty"
    
    # Invalid padding (no length header or malformed)
    invalid_data = b"random_data"
    assert unpad(invalid_data) == invalid_data, "Expected invalid data to return unchanged"
    
    # Truncated padding (e.g., partial header)
    valid_data = b"x" * 50
    padded = pad(valid_data, 256)
    truncated = padded[:10]  # Truncate to invalid length
    assert unpad(truncated) == truncated, "Expected truncated data to return unchanged"

def test_padding_randomness():
    """Test that padding the same data twice produces different padding bytes."""
    data = b"Hello"
    block_size = 256
    
    # Pad twice
    padded1 = pad(data, block_size)
    padded2 = pad(data, block_size)
    
    # Verify size and unpadded result
    assert len(padded1) == block_size
    assert len(padded2) == block_size
    assert unpad(padded1) == data
    assert unpad(padded2) == data
    
    # Verify padding bytes differ (assuming padding includes random bytes)
    assert padded1 != padded2, "Expected different padding bytes for same input"