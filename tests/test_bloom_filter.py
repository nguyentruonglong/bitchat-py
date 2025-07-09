import pytest
from bitchat.utils import OptimizedBloomFilter

def test_basic_bloom_filter():
    """Test insertion and lookup in OptimizedBloomFilter."""
    bf = OptimizedBloomFilter(100, 0.01)
    items = ["message1", "message2", "message3", "test123"]
    for item in items:
        bf.insert(item)
    assert all(bf.contains(item) for item in items)

def test_false_positive_rate():
    """Test false positive rate with 100 items and 1000 non-existent items."""
    bf = OptimizedBloomFilter(100, 0.01)
    # Insert 100 items
    for i in range(100):
        bf.insert(f"item{i}")
    
    # Test 1000 non-existent items
    false_positives = 0
    for i in range(1000):
        non_existent = f"nonexistent{i}"
        if bf.contains(non_existent):
            false_positives += 1
    
    # Verify false positive rate < 0.02
    rate = false_positives / 1000
    assert rate < 0.02, f"False positive rate {rate} exceeds 0.02"

def test_reset():
    """Test resetting the bloom filter clears all items."""
    bf = OptimizedBloomFilter(100, 0.01)
    items = ["message1", "message2", "message3"]
    for item in items:
        bf.insert(item)
    
    # Verify items exist
    assert all(bf.contains(item) for item in items)
    
    # Reset and verify absence
    bf.reset()
    assert not any(bf.contains(item) for item in items)

def test_hash_distribution():
    """Test hash distribution with 500 items in a 1000-item filter."""
    bf = OptimizedBloomFilter(1000, 0.01)
    # Insert 500 items
    for i in range(500):
        bf.insert(f"item{i}")
    
    # Verify estimated false positive rate and memory size
    assert bf.estimated_false_positive_rate < 0.01, f"Estimated FPR {bf.estimated_false_positive_rate} exceeds 0.01"
    assert bf.memory_size_bytes < 2048, f"Memory size {bf.memory_size_bytes} exceeds 2048 bytes"

def test_adaptive_bloom_filter():
    """Test adaptive bloom filter sizing for small and large capacities."""
    # Test small capacity (20 items)
    bf_small = OptimizedBloomFilter.adaptive(20)
    assert bf_small.memory_size_bytes < 1024, f"Small filter memory size {bf_small.memory_size_bytes} exceeds 1024 bytes"
    for i in range(20):
        bf_small.insert(f"item{i}")
    assert all(bf_small.contains(f"item{i}") for i in range(20))
    
    # Test large capacity (1000 items)
    bf_large = OptimizedBloomFilter.adaptive(1000)
    assert bf_large.memory_size_bytes > 2048, f"Large filter memory size {bf_large.memory_size_bytes} is not > 2048 bytes"
    for i in range(1000):
        bf_large.insert(f"item{i}")
    assert all(bf_large.contains(f"item{i}") for i in range(1000))