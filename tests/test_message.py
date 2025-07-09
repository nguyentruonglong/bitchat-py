import pytest
from bitchat.message import BitchatMessage, encode_message, decode_message
from uuid import uuid4
import time

def test_message_encoding_decoding():
    """Test encoding and decoding a BitchatMessage with mentions."""
    message = BitchatMessage(
        id=str(uuid4()),
        sender="alice",
        content="Hello @bob and @charlie!",
        timestamp=time.time(),
        is_relay=False,
        original_sender=None,
        is_private=False,
        recipient_nickname=None,
        sender_peer_id="bitchat_peer1",
        mentions=["bob", "charlie"],
        channel="#general",
        is_encrypted=False,
        encrypted_content=None,
        delivery_status="pending"
    )
    
    # Encode and decode
    encoded = encode_message(message)
    decoded = decode_message(encoded)
    
    # Verify fields
    assert decoded is not None
    assert decoded.sender == message.sender
    assert decoded.content == message.content
    assert decoded.is_private == message.is_private
    assert decoded.mentions == message.mentions
    assert decoded.id == message.id
    assert abs(decoded.timestamp - message.timestamp) < 0.001  # Allow small float diffs
    assert decoded.sender_peer_id == message.sender_peer_id
    assert decoded.channel == message.channel
    assert decoded.is_encrypted == message.is_encrypted
    assert decoded.encrypted_content == message.encrypted_content
    assert decoded.delivery_status == message.delivery_status

def test_room_message():
    """Test a message with channel='#general', verifying channel and content."""
    message = BitchatMessage(
        id=str(uuid4()),
        sender="alice",
        content="Room message",
        timestamp=time.time(),
        is_relay=False,
        original_sender=None,
        is_private=False,
        recipient_nickname=None,
        sender_peer_id="bitchat_peer1",
        mentions=[],
        channel="#general",
        is_encrypted=False,
        encrypted_content=None,
        delivery_status="pending"
    )
    
    # Encode and decode
    encoded = encode_message(message)
    decoded = decode_message(encoded)
    
    # Verify channel and content
    assert decoded is not None
    assert decoded.channel == "#general"
    assert decoded.content == "Room message"
    assert decoded.is_private is False
    assert decoded.sender == "alice"

def test_encrypted_room_message():
    """Test a message with is_encrypted=True, encrypted_content, channel='#secret'."""
    encrypted_content = b"encrypted_data"
    message = BitchatMessage(
        id=str(uuid4()),
        sender="alice",
        content="",  # Empty content for encrypted message
        timestamp=time.time(),
        is_relay=False,
        original_sender=None,
        is_private=False,
        recipient_nickname=None,
        sender_peer_id="bitchat_peer1",
        mentions=[],
        channel="#secret",
        is_encrypted=True,
        encrypted_content=encrypted_content,
        delivery_status="pending"
    )
    
    # Encode and decode
    encoded = encode_message(message)
    decoded = decode_message(encoded)
    
    # Verify encrypted fields
    assert decoded is not None
    assert decoded.is_encrypted is True
    assert decoded.encrypted_content == encrypted_content
    assert decoded.content == ""  # Content should be empty
    assert decoded.channel == "#secret"
    assert decoded.sender == "alice"

def test_private_message():
    """Test a private message with is_private=True, recipient_nickname='bob'."""
    message = BitchatMessage(
        id=str(uuid4()),
        sender="alice",
        content="Private message to Bob",
        timestamp=time.time(),
        is_relay=False,
        original_sender=None,
        is_private=True,
        recipient_nickname="bob",
        sender_peer_id="bitchat_peer1",
        mentions=[],
        channel="#general",
        is_encrypted=False,
        encrypted_content=None,
        delivery_status="pending"
    )
    
    # Encode and decode
    encoded = encode_message(message)
    decoded = decode_message(encoded)
    
    # Verify private message fields
    assert decoded is not None
    assert decoded.is_private is True
    assert decoded.recipient_nickname == "bob"
    assert decoded.content == "Private message to Bob"
    assert decoded.sender == "alice"

def test_relay_message():
    """Test a relay message with is_relay=True, original_sender='alice'."""
    message = BitchatMessage(
        id=str(uuid4()),
        sender="bob",  # Current sender (relayer)
        content="Relayed message",
        timestamp=time.time(),
        is_relay=True,
        original_sender="alice",
        is_private=False,
        recipient_nickname=None,
        sender_peer_id="bitchat_peer2",
        mentions=[],
        channel="#general",
        is_encrypted=False,
        encrypted_content=None,
        delivery_status="pending"
    )
    
    # Encode and decode
    encoded = encode_message(message)
    decoded = decode_message(encoded)
    
    # Verify relay fields
    assert decoded is not None
    assert decoded.is_relay is True
    assert decoded.original_sender == "alice"
    assert decoded.sender == "bob"
    assert decoded.content == "Relayed message"

def test_empty_content():
    """Test a message with empty content."""
    message = BitchatMessage(
        id=str(uuid4()),
        sender="alice",
        content="",
        timestamp=time.time(),
        is_relay=False,
        original_sender=None,
        is_private=False,
        recipient_nickname=None,
        sender_peer_id="bitchat_peer1",
        mentions=[],
        channel="#general",
        is_encrypted=False,
        encrypted_content=None,
        delivery_status="pending"
    )
    
    # Encode and decode
    encoded = encode_message(message)
    decoded = decode_message(encoded)
    
    # Verify empty content
    assert decoded is not None
    assert decoded.content == ""
    assert decoded.sender == "alice"
    assert decoded.channel == "#general"

def test_long_content():
    """Test a message with 1000-byte content."""
    long_content = "x" * 1000  # 1000-byte string
    message = BitchatMessage(
        id=str(uuid4()),
        sender="alice",
        content=long_content,
        timestamp=time.time(),
        is_relay=False,
        original_sender=None,
        is_private=False,
        recipient_nickname=None,
        sender_peer_id="bitchat_peer1",
        mentions=[],
        channel="#general",
        is_encrypted=False,
        encrypted_content=None,
        delivery_status="pending"
    )
    
    # Encode and decode
    encoded = encode_message(message)
    decoded = decode_message(encoded)
    
    # Verify long content
    assert decoded is not None
    assert decoded.content == long_content
    assert len(decoded.content) == 1000
    assert decoded.sender == "alice"
    assert decoded.channel == "#general"