import struct
from typing import Optional
from .message import BitchatPacket, BitchatMessage

def encode_packet(packet: BitchatPacket) -> bytes:
    """
    Serialize a BitchatPacket into bytes per BinaryProtocol.swift.
    
    Format:
    - version: uint16 (2 bytes)
    - type: uint8 (1 byte, length of type string) + string
    - sender_id: 16 bytes (fixed-length UUID)
    - recipient_id: 16 bytes (fixed-length UUID)
    - timestamp: double (8 bytes)
    - ttl: uint32 (4 bytes)
    - payload_length: uint32 (4 bytes)
    - payload: variable length
    - signature: 64 bytes (fixed-length)
    """
    try:
        # Encode type string (UTF-8, prefixed with length)
        type_bytes = packet.type.encode('utf-8')
        if len(type_bytes) > 255:
            raise ValueError("Packet type string exceeds 255 bytes")
        type_length = len(type_bytes)
        
        # Validate fixed-length fields
        if len(packet.sender_id) != 16:
            raise ValueError("sender_id must be 16 bytes")
        if len(packet.recipient_id) != 16:
            raise ValueError("recipient_id must be 16 bytes")
        if len(packet.signature) != 64:
            raise ValueError("signature must be 64 bytes")
        
        # Pack header: version (H), type_length (B), type (variable), sender_id (16s), recipient_id (16s), timestamp (d), ttl (I), payload_length (I)
        header = struct.pack(
            '!H B 16s 16s d I I',
            packet.version,
            type_length,
            packet.sender_id,
            packet.recipient_id,
            packet.timestamp,
            packet.ttl,
            len(packet.payload)
        )
        
        # Combine header, type string, payload, and signature
        return header + type_bytes + packet.payload + packet.signature
    except (struct.error, ValueError) as e:
        raise ValueError(f"Failed to encode packet: {str(e)}")

def decode_packet(data: bytes) -> Optional[BitchatPacket]:
    """
    Deserialize bytes into a BitchatPacket, handling invalid inputs.
    
    Returns None if the data is invalid or cannot be deserialized.
    """
    try:
        # Minimum length: version (2) + type_length (1) + sender_id (16) + recipient_id (16) + timestamp (8) + ttl (4) + payload_length (4) = 51 bytes
        if len(data) < 51:
            return None
            
        # Unpack header
        header = struct.unpack('!H B 16s 16s d I I', data[:51])
        version, type_length, sender_id, recipient_id, timestamp, ttl, payload_length = header
        
        # Validate type length and extract type string
        type_end = 51 + type_length
        if type_end > len(data) or type_length > 255:
            return None
        type_str = data[51:type_end].decode('utf-8')
        
        # Validate payload and signature
        payload_end = type_end + payload_length
        if payload_end + 64 > len(data):
            return None
        payload = data[type_end:payload_end]
        signature = data[payload_end:payload_end + 64]
        
        # Ensure no extra data
        if payload_end + 64 != len(data):
            return None
            
        return BitchatPacket(
            version=version,
            type=type_str,
            sender_id=sender_id,
            recipient_id=recipient_id,
            timestamp=timestamp,
            payload=payload,
            signature=signature,
            ttl=ttl
        )
    except (struct.error, UnicodeDecodeError, ValueError):
        return None

def encode_message(message: BitchatMessage) -> bytes:
    """
    Serialize a BitchatMessage into bytes.
    
    Format:
    - id: uint8 (length) + string
    - sender: uint8 (length) + string
    - content: uint16 (length) + string
    - timestamp: double (8 bytes)
    - is_relay: bool (1 byte)
    - original_sender: uint8 (length) + string (or 0 if None)
    - is_private: bool (1 byte)
    - recipient_nickname: uint8 (length) + string (or 0 if None)
    - sender_peer_id: uint8 (length) + string
    - mentions_count: uint8 (count) + [uint8 (length) + string] * count
    - channel: uint8 (length) + string (or 0 if None)
    - is_encrypted: bool (1 byte)
    - encrypted_content: uint32 (length) + bytes (or 0 if None)
    - delivery_status: uint8 (length) + string
    """
    try:
        # Encode strings with length prefixes
        id_bytes = message.id.encode('utf-8')
        sender_bytes = message.sender.encode('utf-8')
        content_bytes = message.content.encode('utf-8')
        sender_peer_id_bytes = message.sender_peer_id.encode('utf-8')
        delivery_status_bytes = message.delivery_status.encode('utf-8')
        
        original_sender_bytes = b'' if message.original_sender is None else message.original_sender.encode('utf-8')
        recipient_nickname_bytes = b'' if message.recipient_nickname is None else message.recipient_nickname.encode('utf-8')
        channel_bytes = b'' if message.channel is None else message.channel.encode('utf-8')
        encrypted_content_bytes = b'' if message.encrypted_content is None else message.encrypted_content
        
        # Validate lengths
        for field, length, max_length in [
            (id_bytes, len(id_bytes), 255),
            (sender_bytes, len(sender_bytes), 255),
            (content_bytes, len(content_bytes), 65535),
            (sender_peer_id_bytes, len(sender_peer_id_bytes), 255),
            (delivery_status_bytes, len(delivery_status_bytes), 255),
            (original_sender_bytes, len(original_sender_bytes), 255),
            (recipient_nickname_bytes, len(recipient_nickname_bytes), 255),
            (channel_bytes, len(channel_bytes), 255),
            (encrypted_content_bytes, len(encrypted_content_bytes), 4294967295),
        ]:
            if length > max_length:
                raise ValueError(f"Field length exceeds maximum: {length} > {max_length}")
        
        # Encode mentions
        mentions_bytes = b''
        mentions_count = len(message.mentions)
        if mentions_count > 255:
            raise ValueError("Too many mentions")
        for mention in message.mentions:
            mention_bytes = mention.encode('utf-8')
            if len(mention_bytes) > 255:
                raise ValueError("Mention length exceeds 255 bytes")
            mentions_bytes += struct.pack('!B', len(mention_bytes)) + mention_bytes
        
        # Pack header and fields
        return (
            struct.pack('!B', len(id_bytes)) + id_bytes +
            struct.pack('!B', len(sender_bytes)) + sender_bytes +
            struct.pack('!H', len(content_bytes)) + content_bytes +
            struct.pack('!d', message.timestamp) +
            struct.pack('!?', message.is_relay) +
            struct.pack('!B', len(original_sender_bytes)) + original_sender_bytes +
            struct.pack('!?', message.is_private) +
            struct.pack('!B', len(recipient_nickname_bytes)) + recipient_nickname_bytes +
            struct.pack('!B', len(sender_peer_id_bytes)) + sender_peer_id_bytes +
            struct.pack('!B', mentions_count) + mentions_bytes +
            struct.pack('!B', len(channel_bytes)) + channel_bytes +
            struct.pack('!?', message.is_encrypted) +
            struct.pack('!I', len(encrypted_content_bytes)) + encrypted_content_bytes +
            struct.pack('!B', len(delivery_status_bytes)) + delivery_status_bytes
        )
    except (struct.error, ValueError, UnicodeEncodeError) as e:
        raise ValueError(f"Failed to encode message: {str(e)}")

def decode_message(data: bytes) -> Optional[BitchatMessage]:
    """
    Deserialize bytes into a BitchatMessage.
    
    Returns None if the data is invalid or cannot be deserialized.
    """
    try:
        offset = 0
        
        # id: uint8 (length) + string
        if offset + 1 > len(data):
            return None
        id_length = struct.unpack('!B', data[offset:offset+1])[0]
        offset += 1
        if offset + id_length > len(data):
            return None
        id_str = data[offset:offset+id_length].decode('utf-8')
        offset += id_length
        
        # sender: uint8 (length) + string
        if offset + 1 > len(data):
            return None
        sender_length = struct.unpack('!B', data[offset:offset+1])[0]
        offset += 1
        if offset + sender_length > len(data):
            return None
        sender = data[offset:offset+sender_length].decode('utf-8')
        offset += sender_length
        
        # content: uint16 (length) + string
        if offset + 2 > len(data):
            return None
        content_length = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        if offset + content_length > len(data):
            return None
        content = data[offset:offset+content_length].decode('utf-8')
        offset += content_length
        
        # timestamp: double (8 bytes)
        if offset + 8 > len(data):
            return None
        timestamp = struct.unpack('!d', data[offset:offset+8])[0]
        offset += 8
        
        # is_relay: bool (1 byte)
        if offset + 1 > len(data):
            return None
        is_relay = struct.unpack('!?', data[offset:offset+1])[0]
        offset += 1
        
        # original_sender: uint8 (length) + string
        if offset + 1 > len(data):
            return None
        original_sender_length = struct.unpack('!B', data[offset:offset+1])[0]
        offset += 1
        original_sender = None
        if original_sender_length > 0:
            if offset + original_sender_length > len(data):
                return None
            original_sender = data[offset:offset+original_sender_length].decode('utf-8')
            offset += original_sender_length
        
        # is_private: bool (1 byte)
        if offset + 1 > len(data):
            return None
        is_private = struct.unpack('!?', data[offset:offset+1])[0]
        offset += 1
        
        # recipient_nickname: uint8 (length) + string
        if offset + 1 > len(data):
            return None
        recipient_nickname_length = struct.unpack('!B', data[offset:offset+1])[0]
        offset += 1
        recipient_nickname = None
        if recipient_nickname_length > 0:
            if offset + recipient_nickname_length > len(data):
                return None
            recipient_nickname = data[offset:offset+recipient_nickname_length].decode('utf-8')
            offset += recipient_nickname_length
        
        # sender_peer_id: uint8 (length) + string
        if offset + 1 > len(data):
            return None
        sender_peer_id_length = struct.unpack('!B', data[offset:offset+1])[0]
        offset += 1
        if offset + sender_peer_id_length > len(data):
            return None
        sender_peer_id = data[offset:offset+sender_peer_id_length].decode('utf-8')
        offset += sender_peer_id_length
        
        # mentions: uint8 (count) + [uint8 (length) + string] * count
        if offset + 1 > len(data):
            return None
        mentions_count = struct.unpack('!B', data[offset:offset+1])[0]
        offset += 1
        mentions = []
        for _ in range(mentions_count):
            if offset + 1 > len(data):
                return None
            mention_length = struct.unpack('!B', data[offset:offset+1])[0]
            offset += 1
            if offset + mention_length > len(data):
                return None
            mention = data[offset:offset+mention_length].decode('utf-8')
            mentions.append(mention)
            offset += mention_length
        
        # channel: uint8 (length) + string
        if offset + 1 > len(data):
            return None
        channel_length = struct.unpack('!B', data[offset:offset+1])[0]
        offset += 1
        channel = None
        if channel_length > 0:
            if offset + channel_length > len(data):
                return None
            channel = data[offset:offset+channel_length].decode('utf-8')
            offset += channel_length
        
        # is_encrypted: bool (1 byte)
        if offset + 1 > len(data):
            return None
        is_encrypted = struct.unpack('!?', data[offset:offset+1])[0]
        offset += 1
        
        # encrypted_content: uint32 (length) + bytes
        if offset + 4 > len(data):
            return None
        encrypted_content_length = struct.unpack('!I', data[offset:offset+4])[0]
        offset += 4
        encrypted_content = None
        if encrypted_content_length > 0:
            if offset + encrypted_content_length > len(data):
                return None
            encrypted_content = data[offset:offset+encrypted_content_length]
            offset += encrypted_content_length
        
        # delivery_status: uint8 (length) + string
        if offset + 1 > len(data):
            return None
        delivery_status_length = struct.unpack('!B', data[offset:offset+1])[0]
        offset += 1
        if offset + delivery_status_length > len(data):
            return None
        delivery_status = data[offset:offset+delivery_status_length].decode('utf-8')
        offset += delivery_status_length
        
        # Ensure no extra data
        if offset != len(data):
            return None
            
        return BitchatMessage(
            id=id_str,
            sender=sender,
            content=content,
            timestamp=timestamp,
            is_relay=is_relay,
            original_sender=original_sender,
            is_private=is_private,
            recipient_nickname=recipient_nickname,
            sender_peer_id=sender_peer_id,
            mentions=mentions,
            channel=channel,
            is_encrypted=is_encrypted,
            encrypted_content=encrypted_content,
            delivery_status=delivery_status
        )
    except (struct.error, UnicodeDecodeError, ValueError):
        return None