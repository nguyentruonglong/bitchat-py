from dataclasses import dataclass
from typing import List, Optional
import struct

@dataclass
class BitchatPacket:
    version: int
    type: str
    sender_id: bytes
    recipient_id: bytes
    timestamp: float
    payload: bytes
    signature: bytes
    ttl: int

@dataclass
class BitchatMessage:
    id: str
    sender: str
    content: str
    timestamp: float
    is_relay: bool
    original_sender: Optional[str]
    is_private: bool
    recipient_nickname: Optional[str]
    sender_peer_id: str
    mentions: List[str]
    channel: Optional[str]
    encrypted_content: Optional[bytes]
    is_encrypted: bool
    delivery_status: str

@dataclass
class DeliveryAck:
    message_id: str
    recipient_id: str
    nickname: str
    hop_count: int

    def encode(self) -> bytes:
        """
        Encode DeliveryAck into bytes.
        
        Format:
        - message_id: uint8 (length) + string
        - recipient_id: uint8 (length) + string
        - nickname: uint8 (length) + string
        - hop_count: uint32 (4 bytes)
        """
        try:
            message_id_bytes = self.message_id.encode('utf-8')
            recipient_id_bytes = self.recipient_id.encode('utf-8')
            nickname_bytes = self.nickname.encode('utf-8')
            
            # Validate lengths
            for field, length in [
                (message_id_bytes, len(message_id_bytes)),
                (recipient_id_bytes, len(recipient_id_bytes)),
                (nickname_bytes, len(nickname_bytes)),
            ]:
                if length > 255:
                    raise ValueError(f"Field length exceeds 255 bytes: {length}")
            
            # Pack fields
            return (
                struct.pack('!B', len(message_id_bytes)) + message_id_bytes +
                struct.pack('!B', len(recipient_id_bytes)) + recipient_id_bytes +
                struct.pack('!B', len(nickname_bytes)) + nickname_bytes +
                struct.pack('!I', self.hop_count)
            )
        except (struct.error, UnicodeEncodeError, ValueError) as e:
            raise ValueError(f"Failed to encode DeliveryAck: {str(e)}")

    @classmethod
    def decode(cls, data: bytes) -> Optional['DeliveryAck']:
        """
        Decode bytes into a DeliveryAck.
        
        Returns None if the data is invalid.
        """
        try:
            offset = 0
            
            # message_id: uint8 (length) + string
            if offset + 1 > len(data):
                return None
            message_id_length = struct.unpack('!B', data[offset:offset+1])[0]
            offset += 1
            if offset + message_id_length > len(data):
                return None
            message_id = data[offset:offset+message_id_length].decode('utf-8')
            offset += message_id_length
            
            # recipient_id: uint8 (length) + string
            if offset + 1 > len(data):
                return None
            recipient_id_length = struct.unpack('!B', data[offset:offset+1])[0]
            offset += 1
            if offset + recipient_id_length > len(data):
                return None
            recipient_id = data[offset:offset+recipient_id_length].decode('utf-8')
            offset += recipient_id_length
            
            # nickname: uint8 (length) + string
            if offset + 1 > len(data):
                return None
            nickname_length = struct.unpack('!B', data[offset:offset+1])[0]
            offset += 1
            if offset + nickname_length > len(data):
                return None
            nickname = data[offset:offset+nickname_length].decode('utf-8')
            offset += nickname_length
            
            # hop_count: uint32 (4 bytes)
            if offset + 4 > len(data):
                return None
            hop_count = struct.unpack('!I', data[offset:offset+4])[0]
            offset += 4
            
            # Ensure no extra data
            if offset != len(data):
                return None
                
            return cls(
                message_id=message_id,
                recipient_id=recipient_id,
                nickname=nickname,
                hop_count=hop_count
            )
        except (struct.error, UnicodeDecodeError, ValueError):
            return None

@dataclass
class ReadReceipt:
    message_id: str
    recipient_id: str
    timestamp: float

    def encode(self) -> bytes:
        """
        Encode ReadReceipt into bytes.
        
        Format:
        - message_id: uint8 (length) + string
        - recipient_id: uint8 (length) + string
        - timestamp: double (8 bytes)
        """
        try:
            message_id_bytes = self.message_id.encode('utf-8')
            recipient_id_bytes = self.recipient_id.encode('utf-8')
            
            # Validate lengths
            for field, length in [
                (message_id_bytes, len(message_id_bytes)),
                (recipient_id_bytes, len(recipient_id_bytes)),
            ]:
                if length > 255:
                    raise ValueError(f"Field length exceeds 255 bytes: {length}")
            
            # Pack fields
            return (
                struct.pack('!B', len(message_id_bytes)) + message_id_bytes +
                struct.pack('!B', len(recipient_id_bytes)) + recipient_id_bytes +
                struct.pack('!d', self.timestamp)
            )
        except (struct.error, UnicodeEncodeError, ValueError) as e:
            raise ValueError(f"Failed to encode ReadReceipt: {str(e)}")

    @classmethod
    def decode(cls, data: bytes) -> Optional['ReadReceipt']:
        """
        Decode bytes into a ReadReceipt.
        
        Returns None if the data is invalid.
        """
        try:
            offset = 0
            
            # message_id: uint8 (length) + string
            if offset + 1 > len(data):
                return None
            message_id_length = struct.unpack('!B', data[offset:offset+1])[0]
            offset += 1
            if offset + message_id_length > len(data):
                return None
            message_id = data[offset:offset+message_id_length].decode('utf-8')
            offset += message_id_length
            
            # recipient_id: uint8 (length) + string
            if offset + 1 > len(data):
                return None
            recipient_id_length = struct.unpack('!B', data[offset:offset+1])[0]
            offset += 1
            if offset + recipient_id_length > len(data):
                return None
            recipient_id = data[offset:offset+recipient_id_length].decode('utf-8')
            offset += recipient_id_length
            
            # timestamp: double (8 bytes)
            if offset + 8 > len(data):
                return None
            timestamp = struct.unpack('!d', data[offset:offset+8])[0]
            offset += 8
            
            # Ensure no extra data
            if offset != len(data):
                return None
                
            return cls(
                message_id=message_id,
                recipient_id=recipient_id,
                timestamp=timestamp
            )
        except (struct.error, UnicodeDecodeError, ValueError):
            return None

def pad(data: bytes, target_size: int) -> bytes:
    """
    Apply PKCS#7 padding with PKCS#7 bytes, up to 255 bytes.
    """
    if target_size < len(data):
        return data
    padding_length = target_size - len(data)
    if padding_length > 255:
        padding_length = 255
    padding = bytes([padding_length]) * padding_length
    return data + padding

def unpad(data: bytes) -> bytes:
    """
    Remove PKCS#7 padding, return original if invalid.
    """
    if not data:
        return data
    padding_length = data[-1]
    if padding_length > len(data) or padding_length == 0:
        return None
    if all(b == padding_length for b in data[-padding_length:]):
        return data[:-padding_length]
    return data

def optimal_block_size(data_size: int) -> int:
    """
    Select optimal block size from [256, 512, 1024, 2048] or return original size.
    """
    block_sizes = [256, 512, 1024, 2048]
    for size in block_sizes:
        if data_size <= size:
            return size
    return data_size