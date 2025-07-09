from enum import Enum
from typing import Dict, List
from dataclasses import dataclass
from uuid import uuid4
from .message import DeliveryAck

class DeliveryStatus(Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"

@dataclass
class DeliveryAck:
    ack_id: str
    message_id: str
    recipient_id: str
    nickname: str
    hop_count: int

class DeliveryTracker:
    """Manage delivery status and acknowledgments for messages in the bitchat protocol."""
    
    def __init__(self):
        self.statuses: Dict[str, DeliveryStatus] = {}  # Map message_id to status
        self.acks: Dict[str, List[DeliveryAck]] = {}  # Map message_id to list of ACKs

    def track_message(self, message_id: str, status: DeliveryStatus) -> None:
        """
        Update delivery status for a message.

        Args:
            message_id (str): Unique identifier of the message.
            status (DeliveryStatus): Delivery status (PENDING, DELIVERED, FAILED).

        Raises:
            ValueError: If message_id is empty or status is invalid.
        """
        if not message_id:
            raise ValueError("message_id cannot be empty")
        if not isinstance(status, DeliveryStatus):
            raise ValueError("status must be a DeliveryStatus enum")
        self.statuses[message_id] = status

    def generate_ack(self, message_id: str, recipient_id: str, nickname: str, hop_count: int) -> DeliveryAck:
        """
        Create a DeliveryAck with validated or generated UUIDs.

        Args:
            message_id (str): UUID of the message being acknowledged.
            recipient_id (str): UUID of the recipient peer.
            nickname (str): Nickname of the recipient.
            hop_count (int): Number of hops the message has traversed.

        Returns:
            DeliveryAck: Acknowledgment object with validated fields.

        Raises:
            ValueError: If inputs are invalid (empty message_id, nickname, or negative hop_count).
        """
        if not message_id:
            raise ValueError("message_id cannot be empty")
        if not nickname:
            raise ValueError("nickname cannot be empty")
        if hop_count < 0:
            raise ValueError("hop_count cannot be negative")
        
        # Validate or generate UUIDs
        try:
            uuid4(hex=message_id)
        except ValueError:
            raise ValueError("message_id must be a valid UUID")
        try:
            uuid4(hex=recipient_id)
        except ValueError:
            raise ValueError("recipient_id must be a valid UUID")
        
        return DeliveryAck(
            ack_id=str(uuid4()),
            message_id=message_id,
            recipient_id=recipient_id,
            nickname=nickname,
            hop_count=hop_count
        )

    def process_ack(self, ack: DeliveryAck) -> None:
        """
        Process a received DeliveryAck and update message status.

        Args:
            ack (DeliveryAck): Acknowledgment object to process.

        Raises:
            ValueError: If ack or its fields are invalid.
        """
        if not isinstance(ack, DeliveryAck):
            raise ValueError("ack must be a DeliveryAck object")
        if not ack.message_id:
            raise ValueError("ack.message_id cannot be empty")
        
        # Update status to DELIVERED
        self.statuses[ack.message_id] = DeliveryStatus.DELIVERED
        
        # Store ACK
        if ack.message_id not in self.acks:
            self.acks[ack.message_id] = []
        self.acks[ack.message_id].append(ack)

    def get_status(self, message_id: str) -> DeliveryStatus:
        """
        Retrieve the delivery status of a message.

        Args:
            message_id (str): Unique identifier of the message.

        Returns:
            DeliveryStatus: The status of the message, or None if not found.
        """
        if not message_id:
            raise ValueError("message_id cannot be empty")
        return self.statuses.get(message_id)

    def get_acks(self, message_id: str) -> List[DeliveryAck]:
        """
        Retrieve all ACKs for a message.

        Args:
            message_id (str): Unique identifier of the message.

        Returns:
            List[DeliveryAck]: List of ACKs for the message, or empty list if none.

        Raises:
            ValueError: If message_id is empty.
        """
        if not message_id:
            raise ValueError("message_id cannot be empty")
        return self.acks.get(message_id, [])