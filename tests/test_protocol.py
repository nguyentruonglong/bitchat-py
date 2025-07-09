import pytest
from bitchat.protocol import encode_packet, decode_packet
from bitchat.message import BitchatPacket
import time

def test_packet_encoding_decoding():
    """Test encoding and decoding a BitchatPacket with MessageType.message."""
    # Create a packet
    packet = BitchatPacket(
        version=1,
        type="message",
        sender_id=b"peer1" + b"\x00" * 11,  # 16 bytes
        recipient_id=b"peer2" + b"\x00" * 11,  # 16 bytes
        timestamp=time.time(),
        payload=b"Hello, world!",
        signature=b"\x00" * 64,  # Placeholder signature
        ttl=100
    )
    
    # Encode and decode
    encoded = encode_packet(packet)
    decoded = decode_packet(encoded)
    
    # Verify fields
    assert decoded is not None
    assert decoded.version == packet.version
    assert decoded.type == packet.type
    assert decoded.sender_id == packet.sender_id
    assert decoded.recipient_id == packet.recipient_id
    assert abs(decoded.timestamp - packet.timestamp) < 0.001  # Allow small float diffs
    assert decoded.payload == packet.payload
    assert decoded.signature == packet.signature
    assert decoded.ttl == packet.ttl

def test_broadcast_packet():
    """Test encoding/decoding a broadcast packet with SpecialRecipients.broadcast."""
    # Broadcast recipient_id: 8 bytes 0xFF, padded to 16 bytes
    broadcast_id = b"\xFF" * 8 + b"\x00" * 8
    packet = BitchatPacket(
        version=1,
        type="broadcast_message",
        sender_id=b"peer1" + b"\x00" * 11,
        recipient_id=broadcast_id,
        timestamp=time.time(),
        payload=b"Broadcast message",
        signature=b"\x00" * 64,
        ttl=100
    )
    
    # Encode and decode
    encoded = encode_packet(packet)
    decoded = decode_packet(encoded)
    
    # Verify fields, especially recipient_id
    assert decoded is not None
    assert decoded.recipient_id == broadcast_id
    assert decoded.type == "broadcast_message"
    assert decoded.payload == b"Broadcast message"
    assert decoded.version == 1
    assert decoded.ttl == 100

def test_packet_with_signature():
    """Test encoding/decoding a packet with a 64-byte signature (repeating 0xAB)."""
    signature = b"\xAB" * 64
    packet = BitchatPacket(
        version=1,
        type="message",
        sender_id=b"peer1" + b"\x00" * 11,
        recipient_id=b"peer2" + b"\x00" * 11,
        timestamp=time.time(),
        payload=b"Signed message",
        signature=signature,
        ttl=100
    )
    
    # Encode and decode
    encoded = encode_packet(packet)
    decoded = decode_packet(encoded)
    
    # Verify signature and other fields
    assert decoded is not None
    assert decoded.signature == signature
    assert len(decoded.signature) == 64
    assert decoded.payload == b"Signed message"
    assert decoded.version == 1
    assert decoded.ttl == 100

def test_invalid_packet_handling():
    """Test decode_packet with empty, truncated, and invalid-version data."""
    # Empty data
    assert decode_packet(b"") is None
    
    # Truncated data (e.g., partial packet)
    valid_packet = BitchatPacket(
        version=1,
        type="message",
        sender_id=b"peer1" + b"\x00" * 11,
        recipient_id=b"peer2" + b"\x00" * 11,
        timestamp=time.time(),
        payload=b"Test",
        signature=b"\x00" * 64,
        ttl=100
    )
    encoded = encode_packet(valid_packet)
    truncated = encoded[:len(encoded) // 2]  # Cut in half
    assert decode_packet(truncated) is None
    
    # Invalid version (e.g., 99)
    invalid_packet = BitchatPacket(
        version=99,  # Invalid version
        type="message",
        sender_id=b"peer1" + b"\x00" * 11,
        recipient_id=b"peer2" + b"\x00" * 11,
        timestamp=time.time(),
        payload=b"Test",
        signature=b"\x00" * 64,
        ttl=100
    )
    encoded_invalid = encode_packet(invalid_packet)
    assert decode_packet(encoded_invalid) is None