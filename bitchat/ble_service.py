import asyncio
from typing import List, Optional
from uuid import uuid4
from bleak import BleakScanner, BleakClient, BleakGATTCharacteristic
from bleak.exc import BleakError
from .message import BitchatPacket, BitchatMessage, DeliveryAck, ReadReceipt
from .protocol import encode_packet, decode_packet, encode_message, decode_message
from .message import pad, unpad, optimal_block_size
from .encryption import generate_signature, verify_signature
from .keychain import retrieve_key

# BLE service and characteristic UUIDs (based on Bitchat protocol)
SERVICE_UUID = "0000183f-0000-1000-8000-00805f9b34fb"
MESSAGE_CHAR_UUID = "00002a3f-0000-1000-8000-00805f9b34fb"
ACK_CHAR_UUID = "00002b3f-0000-1000-8000-00805f9b34fb"
RECEIPT_CHAR_UUID = "00002c3f-0000-1000-8000-00805f9b34fb"

async def start_advertising(peer_id: str) -> None:
    """
    Advertise device presence using BLE.
    
    Args:
        peer_id (str): Unique identifier for the advertising peer (must start with 'bitchat_').
    
    Raises:
        ValueError: If peer_id is invalid.
        RuntimeError: If advertising fails.
    """
    try:
        if not peer_id.startswith("bitchat_"):
            raise ValueError("peer_id must start with 'bitchat_'")
        # Note: Bleak does not support advertising directly. For production, use platform-specific solutions:
        # - Linux: `hciconfig` or `bluetoothctl` for advertising setup.
        # - macOS/Windows: Use `pygatt` or native APIs (CoreBluetooth for macOS, WinRT for Windows).
        print(f"Advertising peer_id: {peer_id} on service {SERVICE_UUID}")
        # Placeholder: Implement platform-specific advertising here
    except Exception as e:
        raise RuntimeError(f"Failed to start advertising: {str(e)}")

async def scan_peers() -> List[str]:
    """
    Discover nearby peers advertising the Bitchat service.
    
    Returns:
        List[str]: List of peer IDs discovered.
    """
    try:
        devices = await BleakScanner.discover(service_uuids=[SERVICE_UUID], timeout=5.0)
        peer_ids = [device.name for device in devices if device.name and device.name.startswith("bitchat_")]
        return peer_ids
    except BleakError as e:
        print(f"Error scanning peers: {str(e)}")
        return []

async def send_packet(packet: BitchatPacket, peer_id: str) -> None:
    """
    Send a packet to a specific peer over BLE.
    
    Args:
        packet (BitchatPacket): Packet to send.
        peer_id (str): Target peer ID (must start with 'bitchat_').
    
    Raises:
        ValueError: If peer_id is invalid or peer not found.
        RuntimeError: If sending fails.
    """
    try:
        if not peer_id.startswith("bitchat_"):
            raise ValueError("peer_id must start with 'bitchat_'")
        
        # Retrieve signing key (e.g., from keychain)
        key = retrieve_key(f"peer:{packet.sender_id.decode('utf-8', errors='ignore')}")
        if not key:
            raise ValueError("No signing key found for sender")
        
        # Sign packet payload
        packet.signature = generate_signature(packet.payload, key)
        
        # Encode packet
        data = encode_packet(packet)
        
        # Pad data to optimal block size
        block_size = optimal_block_size(len(data))
        padded_data = pad(data, block_size)
        
        # Find device by peer_id
        async with BleakScanner() as scanner:
            devices = await scanner.discover(service_uuids=[SERVICE_UUID], timeout=5.0)
            target_device = next((d for d in devices if d.name == peer_id), None)
            if not target_device:
                raise ValueError(f"Peer {peer_id} not found")
            
            # Connect and send
            async with BleakClient(target_device.address) as client:
                await client.write_gatt_char(MESSAGE_CHAR_UUID, padded_data)
                print(f"Sent packet to {peer_id}")
    except (BleakError, ValueError) as e:
        raise RuntimeError(f"Failed to send packet to {peer_id}: {str(e)}")

async def receive_packet() -> Optional[BitchatPacket]:
    """
    Handle incoming packets over BLE from any available peer.
    
    Returns:
        Optional[BitchatPacket]: Received packet or None if no packet is available.
    """
    try:
        received_packet = None
        
        async def notification_handler(characteristic: BleakGATTCharacteristic, data: bytes):
            nonlocal received_packet
            unpadded_data = unpad(data)
            packet = decode_packet(unpadded_data)
            if packet:
                # Verify signature
                key = retrieve_key(f"peer:{packet.sender_id.decode('utf-8', errors='ignore')}")
                if key and verify_signature(packet.payload, packet.signature, key):
                    print(f"Received valid packet: {packet}")
                    received_packet = packet
                else:
                    print(f"Invalid signature for packet from {packet.sender_id}")

        async with BleakScanner() as scanner:
            devices = await scanner.discover(service_uuids=[SERVICE_UUID], timeout=5.0)
            if not devices:
                return None
            for device in devices:  # Try all discovered devices
                try:
                    async with BleakClient(device.address) as client:
                        await client.start_notify(MESSAGE_CHAR_UUID, notification_handler)
                        await asyncio.sleep(2.0)  # Reduced wait per device
                        await client.stop_notify(MESSAGE_CHAR_UUID)
                        if received_packet:
                            break
                except BleakError:
                    continue
        return received_packet
    except BleakError as e:
        print(f"Error receiving packet: {str(e)}")
        return None

async def send_message(message: BitchatMessage, recipient: str = None) -> None:
    """
    Send a message (private or broadcast).
    
    Args:
        message (BitchatMessage): Message to send.
        recipient (str, optional): Target peer ID for private messages (must start with 'bitchat_').
    
    Raises:
        ValueError: If recipient is invalid.
        RuntimeError: If sending fails.
    """
    try:
        if recipient and not recipient.startswith("bitchat_"):
            raise ValueError("recipient must start with 'bitchat_'")
        
        # Create packet
        packet_type = "private_message" if recipient else "broadcast_message"
        packet = BitchatPacket(
            version=1,
            type=packet_type,
            sender_id=message.sender_peer_id.encode('utf-8').ljust(16)[:16],
            recipient_id=recipient.encode('utf-8').ljust(16)[:16] if recipient else b'\x00' * 16,
            timestamp=message.timestamp,
            payload=encode_message(message),
            signature=b'\x00' * 64,  # Updated in send_packet
            ttl=100
        )
        
        if recipient:
            # Send to specific peer
            await send_packet(packet, recipient)
        else:
            # Broadcast to all discovered peers
            peers = await scan_peers()
            if not peers:
                raise ValueError("No peers found for broadcast")
            for peer_id in peers:
                await send_packet(packet, peer_id)
    except Exception as e:
        raise RuntimeError(f"Failed to send message: {str(e)}")

async def send_encrypted_channel_message(message: BitchatMessage, channel: str) -> None:
    """
    Send an encrypted message to a specific channel.
    
    Args:
        message (BitchatMessage): Encrypted message to send.
        channel (str): Target channel name.
    
    Raises:
        ValueError: If message is not encrypted or channel mismatches.
        RuntimeError: If sending fails.
    """
    try:
        if not message.is_encrypted or not message.encrypted_content:
            raise ValueError("Message must be encrypted with encrypted_content")
        if message.channel != channel:
            raise ValueError("Message channel does not match target channel")
        
        # Create packet
        packet = BitchatPacket(
            version=1,
            type="channel_message",
            sender_id=message.sender_peer_id.encode('utf-8').ljust(16)[:16],
            recipient_id=channel.encode('utf-8').ljust(16)[:16],
            timestamp=message.timestamp,
            payload=encode_message(message),
            signature=b'\x00' * 64,  # Updated in send_packet
            ttl=100
        )
        
        # Broadcast to all peers
        peers = await scan_peers()
        if not peers:
            raise ValueError("No peers found for channel broadcast")
        for peer_id in peers:
            await send_packet(packet, peer_id)
    except Exception as e:
        raise RuntimeError(f"Failed to send encrypted channel message: {str(e)}")

async def send_delivery_ack(ack: DeliveryAck) -> None:
    """
    Send a delivery acknowledgment to the sender.
    
    Args:
        ack (DeliveryAck): Acknowledgment to send.
    
    Raises:
        ValueError: If recipient_id is invalid.
        RuntimeError: If sending fails.
    """
    try:
        if not ack.recipient_id.startswith("bitchat_"):
            raise ValueError("recipient_id must start with 'bitchat_'")
        
        # Create packet
        packet = BitchatPacket(
            version=1,
            type="delivery_ack",
            sender_id=ack.recipient_id.encode('utf-8').ljust(16)[:16],
            recipient_id=ack.message_id.encode('utf-8').ljust(16)[:16],
            timestamp=asyncio.get_event_loop().time(),
            payload=ack.encode(),
            signature=b'\x00' * 64,  # Updated in send_packet
            ttl=10
        )
        
        # Send to the original sender
        await send_packet(packet, ack.recipient_id)
    except Exception as e:
        raise RuntimeError(f"Failed to send delivery acknowledgment: {str(e)}")

async def send_read_receipt(receipt: ReadReceipt) -> None:
    """
    Send a read receipt to the sender.
    
    Args:
        receipt (ReadReceipt): Read receipt to send.
    
    Raises:
        ValueError: If recipient_id is invalid.
        RuntimeError: If sending fails.
    """
    try:
        if not receipt.recipient_id.startswith("bitchat_"):
            raise ValueError("recipient_id must start with 'bitchat_'")
        
        # Create packet
        packet = BitchatPacket(
            version=1,
            type="read_receipt",
            sender_id=receipt.recipient_id.encode('utf-8').ljust(16)[:16],
            recipient_id=receipt.message_id.encode('utf-8').ljust(16)[:16],
            timestamp=receipt.timestamp,
            payload=receipt.encode(),
            signature=b'\x00' * 64,  # Updated in send_packet
            ttl=10
        )
        
        # Send to the original sender
        await send_packet(packet, receipt.recipient_id)
    except Exception as e:
        raise RuntimeError(f"Failed to send read receipt: {str(e)}")

def start_advertising(peer_id: str) -> None:
    """
    Synchronous wrapper for start_advertising.
    """
    asyncio.run(start_advertising(peer_id))

def scan_peers() -> List[str]:
    """
    Synchronous wrapper for scan_peers.
    """
    return asyncio.run(scan_peers())

def send_packet(packet: BitchatPacket, peer_id: str) -> None:
    """
    Synchronous wrapper for send_packet.
    """
    asyncio.run(send_packet(packet, peer_id))

def receive_packet() -> Optional[BitchatPacket]:
    """
    Synchronous wrapper for receive_packet.
    """
    return asyncio.run(receive_packet())

def send_message(message: BitchatMessage, recipient: str = None) -> None:
    """
    Synchronous wrapper for send_message.
    """
    asyncio.run(send_message(message, recipient))

def send_encrypted_channel_message(message: BitchatMessage, channel: str) -> None:
    """
    Synchronous wrapper for send_encrypted_channel_message.
    """
    asyncio.run(send_encrypted_channel_message(message, channel))

def send_delivery_ack(ack: DeliveryAck) -> None:
    """
    Synchronous wrapper for send_delivery_ack.
    """
    asyncio.run(send_delivery_ack(ack))

def send_read_receipt(receipt: ReadReceipt) -> None:
    """
    Synchronous wrapper for send_read_receipt.
    """
    asyncio.run(send_read_receipt(receipt))