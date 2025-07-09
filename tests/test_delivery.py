import pytest
from uuid import uuid4
from bitchat.delivery_tracker import DeliveryTracker, DeliveryStatus, DeliveryAck

@pytest.fixture
def delivery_tracker():
    """Create a DeliveryTracker instance for testing."""
    return DeliveryTracker()

def test_track_message(delivery_tracker):
    """Test tracking a message’s status (PENDING, DELIVERED)."""
    message_id = str(uuid4())
    
    # Track as PENDING
    delivery_tracker.track_message(message_id, DeliveryStatus.PENDING)
    assert delivery_tracker.get_status(message_id) == DeliveryStatus.PENDING, "Message status should be PENDING"
    
    # Update to DELIVERED
    delivery_tracker.track_message(message_id, DeliveryStatus.DELIVERED)
    assert delivery_tracker.get_status(message_id) == DeliveryStatus.DELIVERED, "Message status should be updated to DELIVERED"
    
    # Test invalid inputs
    with pytest.raises(ValueError, match="message_id cannot be empty"):
        delivery_tracker.track_message("", DeliveryStatus.PENDING)
    with pytest.raises(ValueError, match="status must be a DeliveryStatus enum"):
        delivery_tracker.track_message(message_id, "invalid")

def test_generate_ack(delivery_tracker):
    """Test generating a DeliveryAck with correct fields."""
    message_id = str(uuid4())
    recipient_id = str(uuid4())
    nickname = "alice"
    hop_count = 2
    
    ack = delivery_tracker.generate_ack(message_id, recipient_id, nickname, hop_count)
    
    assert isinstance(ack, DeliveryAck), "Generated object should be a DeliveryAck"
    assert uuid4(hex=ack.ack_id), "ack_id should be a valid UUID"
    assert ack.message_id == message_id, "message_id should match input"
    assert ack.recipient_id == recipient_id, "recipient_id should match input"
    assert ack.nickname == nickname, "nickname should match input"
    assert ack.hop_count == hop_count, "hop_count should match input"
    
    # Test invalid inputs
    with pytest.raises(ValueError, match="message_id cannot be empty"):
        delivery_tracker.generate_ack("", recipient_id, nickname, hop_count)
    with pytest.raises(ValueError, match="nickname cannot be empty"):
        delivery_tracker.generate_ack(message_id, recipient_id, "", hop_count)
    with pytest.raises(ValueError, match="hop_count cannot be negative"):
        delivery_tracker.generate_ack(message_id, recipient_id, nickname, -1)
    with pytest.raises(ValueError, match="message_id must be a valid UUID"):
        delivery_tracker.generate_ack("invalid-uuid", recipient_id, nickname, hop_count)
    with pytest.raises(ValueError, match="recipient_id must be a valid UUID"):
        delivery_tracker.generate_ack(message_id, "invalid-uuid", nickname, hop_count)

def test_multiple_acks(delivery_tracker):
    """Test processing multiple ACKs for a message, verify stored ACKs."""
    message_id = str(uuid4())
    recipient_id1 = str(uuid4())
    recipient_id2 = str(uuid4())
    
    ack1 = delivery_tracker.generate_ack(message_id, recipient_id1, "alice", 1)
    ack2 = delivery_tracker.generate_ack(message_id, recipient_id2, "bob", 2)
    
    delivery_tracker.process_ack(ack1)
    delivery_tracker.process_ack(ack2)
    
    acks = delivery_tracker.get_acks(message_id)
    assert len(acks) == 2, "Two ACKs should be stored"
    assert ack1 in acks, "First ACK should be in stored ACKs"
    assert ack2 in acks, "Second ACK should be in stored ACKs"
    assert delivery_tracker.get_status(message_id) == DeliveryStatus.DELIVERED, "Status should be DELIVERED after processing ACKs"

def test_unknown_message_status(delivery_tracker):
    """Test status of an unknown message returns None."""
    message_id = str(uuid4())
    assert delivery_tracker.get_status(message_id) is None, "Status of unknown message should be None"
    
    with pytest.raises(ValueError, match="message_id cannot be empty"):
        delivery_tracker.get_status("")

def test_process_ack_updates_status(delivery_tracker):
    """Test processing an ACK updates message status to DELIVERED."""
    message_id = str(uuid4())
    recipient_id = str(uuid4())
    
    # Set initial status to PENDING
    delivery_tracker.track_message(message_id, DeliveryStatus.PENDING)
    assert delivery_tracker.get_status(message_id) == DeliveryStatus.PENDING, "Initial status should be PENDING"
    
    # Process ACK
    ack = delivery_tracker.generate_ack(message_id, recipient_id, "alice", 1)
    delivery_tracker.process_ack(ack)
    
    assert delivery_tracker.get_status(message_id) == DeliveryStatus.DELIVERED, "Status should be updated to DELIVERED"
    assert ack in delivery_tracker.get_acks(message_id), "ACK should be stored"
    
    # Test invalid ACK
    with pytest.raises(ValueError, match="ack must be a DeliveryAck object"):
        delivery_tracker.process_ack("invalid")
    with pytest.raises(ValueError, match="ack.message_id cannot be empty"):
        delivery_tracker.process_ack(DeliveryAck(str(uuid4()), "", recipient_id, "alice", 1))