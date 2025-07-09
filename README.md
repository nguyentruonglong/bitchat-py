# Bitchat Python Library

A secure, decentralized mesh networking library implementing the Bitchat protocol, as described in [Jack Dorsey’s Bitchat Whitepaper](https://github.com/jackjackbits/bitchat/blob/main/WHITEPAPER.md). It supports Bluetooth Low Energy (BLE) communication, message encryption, delivery tracking, channel management, and password-protected channels for privacy-preserving, peer-to-peer messaging.

<img src="https://badge.fury.io/py/bitchat.svg" alt="PyPI Version">
<img src="https://readthedocs.org/projects/bitchat-py/badge/?version=latest" alt="Documentation">

## Installation

Install the library using pip:

<code>pip3 install bitchat</code>

## Usage

The Bitchat Python Library provides a robust set of tools for building decentralized, secure messaging applications with BLE-based mesh networking. Below are comprehensive examples and parameter explanations for all public methods and classes, designed to guide Python GUI developers (e.g., using Tkinter, PyQt, or Kivy) in integrating the library. The examples avoid redundancy by covering distinct use cases: public channel messaging, private messaging, encrypted channel messaging, and delivery tracking.

### Key Classes and Structures

The library exports the following classes from the `bitchat` module, used to construct and manage messages, packets, and channels:

- **BitchatPacket**: Represents a network packet for BLE transmission.
  - `version: int`: Protocol version (must be 1).
  - `type: str`: Packet type (`"message"`, `"ack"`, `"receipt"`).
  - `sender_id: str`: 8-byte unique sender identifier (e.g., `"peer123"`).
  - `recipient_id: str`: 8-byte recipient identifier or `"\xFF" * 8` for broadcast.
  - `timestamp: int`: Unix timestamp (seconds).
  - `payload: bytes`: Encoded message, ACK, or receipt.
  - `signature: bytes`: 64-byte signature for authenticity.
  - `ttl: int`: Time-to-live (hops, e.g., 5).

- **BitchatMessage**: Represents a message in the Bitchat protocol.
  - `id: str`: Unique message ID (e.g., UUID from `uuid4()`).
  - `sender: str`: Sender’s display name (e.g., `"alice"`).
  - `content: str`: Message text (empty for encrypted messages).
  - `timestamp: int`: Unix timestamp (seconds).
  - `is_relay: bool`: True if message is relayed by another peer.
  - `original_sender: str | None`: Original sender’s name for relayed messages.
  - `is_private: bool`: True for private messages to a specific recipient.
  - `recipient_nickname: str | None`: Recipient’s display name for private messages.
  - `sender_peer_id: str`: Sender’s unique peer ID (e.g., `"bitchat_peer1"`).
  - `mentions: List[str]`: List of mentioned user names (e.g., `["bob", "charlie"]`).
  - `channel: str | None`: Channel name (e.g., `"#general"`, regex: `^#[a-zA-Z0-9-]+$`).
  - `encrypted_content: bytes | None`: Encrypted message content for secure channels.
  - `is_encrypted: bool`: True if message uses `encrypted_content`.
  - `delivery_status: str`: Status (`"PENDING"`, `"DELIVERED"`, `"READ"`).

- **DeliveryAck**: Acknowledgment of message delivery.
  - `message_id: str`: ID of the acknowledged message.
  - `recipient_id: str`: Recipient’s peer ID.
  - `nickname: str`: Recipient’s display name.
  - `hop_count: int`: Number of hops the message traveled.

- **ReadReceipt**: Confirmation of message read.
  - `message_id: str`: ID of the read message.
  - `recipient_id: str`: Recipient’s peer ID.
  - `nickname: str`: Recipient’s display name.
  - `timestamp: int`: Unix timestamp of read event.

- **OptimizedBloomFilter**: Bloom filter for efficient message tracking.
  - `expected_items: int`: Expected number of items (e.g., 100).
  - `false_positive_rate: float`: Desired false positive rate (e.g., 0.01).
  - Methods: `insert(item: str)`, `contains(item: str) -> bool`, `reset()`, `estimated_false_positive_rate() -> float`, `memory_size_bytes() -> int`, `adaptive(network_size: int) -> OptimizedBloomFilter`.

- **ChannelManager**: Manages channels and their properties.
  - `joined_channels: Set[str]`: Set of joined channel names.
  - `current_channel: str`: Active channel name.
  - `password_protected_channels: Set[str]`: Channels requiring passwords.
  - `channel_keys: Dict[str, bytes]`: Derived encryption keys for channels.
  - `channel_passwords: Dict[str, str]`: Passwords for protected channels.
  - `channel_creators: Dict[str, str]`: Creator peer IDs for channels.
  - `system_messages: List[BitchatMessage]`: System-generated messages.

### Core Methods

Below are the public methods exported by the `bitchat` module, with detailed parameter explanations and usage examples.

#### BLE Communication (bitchat.ble_service)

- **start_advertising(peer_id: str) -> None**:
  - Initiates BLE advertising to announce the device’s presence.
  - `peer_id: str`: Unique 8-byte identifier for the device (e.g., `"bitchat_peer1"`).
  - Raises `ValueError` if `peer_id` is invalid (e.g., wrong length or format).
  - **Use Case**: Start advertising to join the mesh network.

- **scan_peers() -> List[str]**:
  - Scans for nearby peers and returns their IDs.
  - Returns a list of peer IDs (e.g., `["peer1", "peer2"]`).
  - **Use Case**: Discover peers for direct messaging or channel communication.

- **send_packet(packet: BitchatPacket, peer_id: str) -> None**:
  - Sends a packet to a specific peer or broadcasts it.
  - `packet: BitchatPacket`: Packet to send (e.g., message, ACK, or receipt).
  - `peer_id: str`: Recipient’s peer ID or `"\xFF" * 8` for broadcast.
  - Raises `ValueError` for invalid `peer_id`.
  - **Use Case**: Low-level packet transmission (typically internal).

- **receive_packet() -> BitchatPacket**:
  - Receives a packet from the BLE network.
  - Returns a `BitchatPacket` or raises an exception on failure.
  - **Use Case**: Handle incoming packets in a GUI event loop.

- **send_message(message: BitchatMessage, recipient: str | None = None) -> None**:
  - Sends a message to a recipient or broadcasts to a channel.
  - `message: BitchatMessage`: Message to send.
  - `recipient: str | None`: Peer ID for private messages; `None` for channel or broadcast.
  - Raises `ValueError` for invalid `recipient` or message format.
  - **Use Case**: Send public, private, or channel messages.

- **send_encrypted_channel_message(message: BitchatMessage, channel: str) -> None**:
  - Sends an encrypted message to a password-protected channel.
  - `message: BitchatMessage`: Message with `channel` set and `content` to encrypt.
  - `channel: str`: Target channel (e.g., `"#secret"`).
  - Raises `ValueError` if channel is invalid or key derivation fails.
  - **Use Case**: Secure channel communication.

- **send_delivery_ack(ack: DeliveryAck) -> None**:
  - Sends a delivery acknowledgment to a peer.
  - `ack: DeliveryAck`: Acknowledgment to send.
  - **Use Case**: Confirm message delivery.

- **send_read_receipt(receipt: ReadReceipt) -> None**:
  - Sends a read receipt to a peer.
  - `receipt: ReadReceipt`: Receipt to send.
  - **Use Case**: Confirm message read status.

#### Protocol Encoding/Decoding (bitchat.protocol)

- **encode_packet(packet: BitchatPacket) -> bytes**:
  - Serializes a packet to bytes for BLE transmission.
  - `packet: BitchatPacket`: Packet to encode.
  - Returns serialized bytes.
  - **Use Case**: Prepare packets for low-level transmission (typically internal).

- **decode_packet(data: bytes) -> BitchatPacket**:
  - Deserializes bytes into a `BitchatPacket`.
  - `data: bytes`: Raw packet data.
  - Returns `BitchatPacket` or `None` if invalid.
  - **Use Case**: Process received packets (typically internal).

- **encode_message(message: BitchatMessage) -> bytes**:
  - Serializes a message to bytes.
  - `message: BitchatMessage`: Message to encode.
  - Returns serialized bytes.
  - **Use Case**: Prepare messages for packet payloads.

- **decode_message(data: bytes) -> BitchatMessage**:
  - Deserializes bytes into a `BitchatMessage`.
  - `data: bytes`: Raw message data.
  - Returns `BitchatMessage` or raises `ValueError` if invalid.
  - **Use Case**: Process received message payloads.

#### Message Padding (bitchat.message)

- **pad(data: bytes, target_size: int) -> bytes**:
  - Applies PKCS#7 padding with random bytes to reach `target_size`.
  - `data: bytes`: Data to pad.
  - `target_size: int`: Desired size (up to 255 bytes).
  - Returns padded bytes.
  - **Use Case**: Pad messages for consistent size in privacy-sensitive contexts.

- **unpad(data: bytes) -> bytes**:
  - Removes PKCS#7 padding.
  - `data: bytes`: Padded data.
  - Returns unpadded bytes or original data if invalid.
  - **Use Case**: Unpad received message payloads.

- **optimal_block_size(data_size: int) -> int**:
  - Selects optimal block size for padding.
  - `data_size: int`: Size of data to pad.
  - Returns size from `[256, 512, 1024, 2048]` or `data_size`.
  - **Use Case**: Determine padding size for messages.

#### Encryption (bitchat.encryption)

- **generate_signature(data: bytes, key: bytes) -> bytes**:
  - Creates a 64-byte signature for data authenticity.
  - `data: bytes`: Data to sign.
  - `key: bytes`: 32-byte signing key.
  - Returns 64-byte signature.
  - **Use Case**: Sign packets for verification.

- **verify_signature(data: bytes, signature: bytes, key: bytes) -> bool**:
  - Verifies a signature for data.
  - `data: bytes`: Original data.
  - `signature: bytes`: 64-byte signature.
  - `key: bytes`: 32-byte signing key.
  - Returns `True` if valid, `False` otherwise.
  - **Use Case**: Verify packet authenticity.

- **encrypt_content(content: str, key: bytes) -> bytes**:
  - Encrypts content using AES-GCM.
  - `content: str`: Text to encrypt.
  - `key: bytes`: 32-byte encryption key.
  - Returns encrypted bytes.
  - **Use Case**: Encrypt messages for secure channels.

- **decrypt_content(data: bytes, key: bytes) -> str**:
  - Decrypts content using AES-GCM.
  - `data: bytes`: Encrypted data.
  - `key: bytes`: 32-byte decryption key.
  - Returns decrypted text or raises `ValueError` on failure.
  - **Use Case**: Decrypt received channel messages.

- **derive_channel_key(password: str, channel: str) -> bytes**:
  - Derives a 32-byte key using PBKDF2 with SHA256 and channel as salt.
  - `password: str`: Channel password.
  - `channel: str`: Channel name (e.g., `"#secret"`).
  - Returns 32-byte key.
  - **Use Case**: Generate keys for password-protected channels.

#### Key Management (bitchat.keychain)

- **store_key(key: bytes, identifier: str) -> None**:
  - Stores an encryption key securely.
  - `key: bytes`: Key to store (e.g., 32-byte channel key).
  - `identifier: str`: Key identifier (e.g., `"channel:#secret"`).
  - **Use Case**: Save channel or peer keys.

- **retrieve_key(identifier: str) -> bytes**:
  - Retrieves a stored key.
  - `identifier: str`: Key identifier.
  - Returns key bytes or raises `KeyError` if not found.
  - **Use Case**: Access keys for encryption/decryption.

- **generate_channel_key(channel: str, password: str) -> bytes**:
  - Derives and stores a channel key.
  - `channel: str`: Channel name.
  - `password: str`: Channel password.
  - Returns 32-byte key.
  - **Use Case**: Initialize keys for new channels.

#### Channel Management (bitchat.channel)

- **ChannelManager.create_channel(channel: str, password: str | None = None, creator_id: str | None = None) -> None**:
  - Creates a new channel, optionally password-protected.
  - `channel: str`: Channel name (regex: `^#[a-zA-Z0-9-]+$`).
  - `password: str | None`: Password for protection; `None` for public.
  - `creator_id: str | None`: Peer ID of creator; defaults to current peer.
  - Raises `ValueError` for invalid channel name.
  - **Use Case**: Set up a new channel.

- **ChannelManager.join_channel(channel: str, password: str | None = None, peer_id: str | None = None) -> None**:
  - Joins a channel, handling password if required.
  - `channel: str`: Channel to join.
  - `password: str | None`: Password for protected channel.
  - `peer_id: str | None`: Peer ID; defaults to current peer.
  - Raises `ValueError` for invalid channel or wrong password.
  - **Use Case**: Join existing channels.

- **ChannelManager.set_channel_password(channel: str, password: str, peer_id: str) -> None**:
  - Sets or updates a channel’s password (creator only).
  - `channel: str`: Channel name.
  - `password: str`: New password.
  - `peer_id: str`: Peer ID of requester.
  - Raises `ValueError` if not creator or channel invalid.
  - **Use Case**: Secure an existing channel.

- **ChannelManager.remove_channel_password(channel: str, peer_id: str) -> None**:
  - Removes a channel’s password (creator only).
  - `channel: str`: Channel name.
  - `peer_id: str`: Peer ID of requester.
  - Raises `ValueError` if not creator or channel invalid.
  - **Use Case**: Make a channel public.

- **ChannelManager.receive_message(message: BitchatMessage) -> None**:
  - Processes a received message, updating channel state.
  - `message: BitchatMessage`: Received message.
  - **Use Case**: Handle incoming messages in GUI.

- **ChannelManager.process_command(command: str, peer_id: str) -> None**:
  - Processes commands like `/join #channel` or `/j #channel`.
  - `command: str`: Command string.
  - `peer_id: str`: Peer ID of requester.
  - Raises `ValueError` for invalid commands.
  - **Use Case**: Handle user commands in GUI.

- **ChannelManager.get_system_messages() -> List[BitchatMessage]**:
  - Returns system-generated messages (e.g., join notifications).
  - Returns list of `BitchatMessage`.
  - **Use Case**: Display system messages in GUI.

- **ChannelManager.transfer_ownership(channel: str, new_owner_id: str, peer_id: str) -> None**:
  - Transfers channel ownership (creator only).
  - `channel: str`: Channel name.
  - `new_owner_id: str`: New owner’s peer ID.
  - `peer_id: str`: Current peer ID.
  - Raises `ValueError` if not creator or invalid channel.
  - **Use Case**: Reassign channel administration.

#### Delivery Tracking (bitchat.delivery_tracker)

- **DeliveryTracker.track_message(message_id: str, status: str) -> None**:
  - Tracks a message’s delivery status.
  - `message_id: str`: Message ID.
  - `status: str`: Status (`"PENDING"`, `"DELIVERED"`, `"READ"`).
  - **Use Case**: Update message status in GUI.

- **DeliveryTracker.generate_ack(message_id: str, recipient_id: str, nickname: str, hop_count: int) -> DeliveryAck**:
  - Creates a delivery acknowledgment.
  - `message_id: str`: Message ID.
  - `recipient_id: str`: Recipient’s peer ID.
  - `nickname: str`: Recipient’s display name.
  - `hop_count: int`: Number of hops.
  - Returns `DeliveryAck`.
  - **Use Case**: Generate ACKs for received messages.

- **DeliveryTracker.process_ack(ack: DeliveryAck) -> None**:
  - Processes a received ACK, updating status.
  - `ack: DeliveryAck`: Acknowledgment to process.
  - **Use Case**: Update GUI with delivery confirmation.

- **DeliveryTracker.get_status(message_id: str) -> str | None**:
  - Retrieves a message’s delivery status.
  - `message_id: str`: Message ID.
  - Returns status or `None` if unknown.
  - **Use Case**: Display message status in GUI.

- **DeliveryTracker.get_acks(message_id: str) -> List[DeliveryAck]**:
  - Retrieves all ACKs for a message.
  - `message_id: str`: Message ID.
  - Returns list of `DeliveryAck`.
  - **Use Case**: Show delivery confirmations.

### Example Usage for GUI Applications

The following example demonstrates how to integrate the library into a Python GUI application (e.g., Tkinter) for public channel messaging, private messaging, encrypted channel messaging, and delivery tracking. It includes an event loop for receiving messages and handling system events.

```python
import asyncio
from uuid import uuid4
import time
from tkinter import Tk, Text, Entry, Button, END
from bitchat import (
    BitchatMessage, ChannelManager, DeliveryTracker, OptimizedBloomFilter,
    start_advertising, scan_peers, send_message, send_encrypted_channel_message,
    receive_packet, decode_packet, decode_message, generate_signature, verify_signature,
    encrypt_content, decrypt_content, derive_channel_key, store_key, retrieve_key,
    send_delivery_ack, send_read_receipt
)

# Initialize components
peer_id = "bitchat_peer1"
channel_manager = ChannelManager()
delivery_tracker = DeliveryTracker()
bloom_filter = OptimizedBloomFilter(expected_items=100, false_positive_rate=0.01)
signing_key = b"\x01" * 32
store_key(signing_key, f"peer:{peer_id}")

# Tkinter GUI setup
root = Tk()
root.title("Bitchat Messenger")
chat_display = Text(root, height=20, width=50)
chat_display.pack()
message_entry = Entry(root, width=50)
message_entry.pack()
channel_entry = Entry(root, width=20)
channel_entry.pack()
channel_entry.insert(0, "#general")

# Start BLE advertising
async def start_network():
    await start_advertising(peer_id)
    chat_display.insert(END, "Started advertising as {}\n".format(peer_id))

# Send a public or private message
def send_message_gui():
    content = message_entry.get()
    channel = channel_entry.get()
    message_id = str(uuid4())
    timestamp = int(time.time())
    
    # Create message
    message = BitchatMessage(
        id=message_id,
        sender="alice",
        content=content,
        timestamp=timestamp,
        is_relay=False,
        original_sender=None,
        is_private=False,
        recipient_nickname=None,
        sender_peer_id=peer_id,
        mentions=[],
        channel=channel,
        is_encrypted=False,
        encrypted_content=None,
        delivery_status="PENDING"
    )
    
    # Track message
    delivery_tracker.track_message(message_id, "PENDING")
    
    # Send message (public channel or broadcast)
    asyncio.run(send_message(message))
    chat_display.insert(END, f"[{channel}] alice: {content}\n")
    message_entry.delete(0, END)

# Send an encrypted channel message
def send_encrypted_message_gui():
    content = message_entry.get()
    channel = channel_entry.get()
    password = "secure123"  # Replace with GUI input
    message_id = str(uuid4())
    timestamp = int(time.time())
    
    # Derive and store channel key
    key = derive_channel_key(password, channel)
    store_key(key, f"channel:{channel}")
    
    # Encrypt content
    encrypted_content = encrypt_content(content, key)
    
    # Create encrypted message
    message = BitchatMessage(
        id=message_id,
        sender="alice",
        content="",
        timestamp=timestamp,
        is_relay=False,
        original_sender=None,
        is_private=False,
        recipient_nickname=None,
        sender_peer_id=peer_id,
        mentions=[],
        channel=channel,
        is_encrypted=True,
        encrypted_content=encrypted_content,
        delivery_status="PENDING"
    )
    
    # Track and send message
    delivery_tracker.track_message(message_id, "PENDING")
    asyncio.run(send_encrypted_channel_message(message, channel))
    chat_display.insert(END, f"[{channel}] alice: [Encrypted]\n")
    message_entry.delete(0, END)

# Join a channel (public or password-protected)
def join_channel_gui():
    channel = channel_entry.get()
    password = None  # Replace with GUI input for password
    try:
        channel_manager.join_channel(channel, password, peer_id)
        chat_display.insert(END, f"Joined channel {channel}\n")
    except ValueError as e:
        chat_display.insert(END, f"Error joining {channel}: {e}\n")

# Async event loop for receiving messages
async def receive_messages():
    while True:
        try:
            packet = await receive_packet()
            if verify_signature(packet.payload, packet.signature, signing_key):
                message = decode_message(packet.payload)
                
                # Handle delivery ACK
                delivery_tracker.process_ack(DeliveryAck(
                    message_id=message.id,
                    recipient_id=peer_id,
                    nickname="alice",
                    hop_count=1
                ))
                asyncio.run(send_delivery_ack(DeliveryAck(
                    message_id=message.id,
                    recipient_id=packet.sender_id,
                    nickname="alice",
                    hop_count=1
                )))
                
                # Handle read receipt
                delivery_tracker.track_message(message.id, "READ")
                asyncio.run(send_read_receipt(ReadReceipt(
                    message_id=message.id,
                    recipient_id=peer_id,
                    nickname="alice",
                    timestamp=int(time.time())
                )))
                
                # Process message
                channel_manager.receive_message(message)
                
                # Decrypt if needed
                if message.is_encrypted:
                    key = retrieve_key(f"channel:{message.channel}")
                    content = decrypt_content(message.encrypted_content, key)
                else:
                    content = message.content
                
                chat_display.insert(END, f"[{message.channel}] {message.sender}: {content}\n")
                
                # Update bloom filter for message tracking
                bloom_filter.insert(message.id)
                
                # Display system messages
                for sys_msg in channel_manager.get_system_messages():
                    chat_display.insert(END, f"[System] {sys_msg.content}\n")
        except Exception as e:
            chat_display.insert(END, f"Error receiving message: {e}\n")
        await asyncio.sleep(0.1)

# GUI buttons
send_button = Button(root, text="Send Message", command=send_message_gui)
send_button.pack()
send_encrypted_button = Button(root, text="Send Encrypted", command=send_encrypted_message_gui)
send_encrypted_button.pack()
join_button = Button(root, text="Join Channel", command=join_channel_gui)
join_button.pack()

# Run event loop
loop = asyncio.get_event_loop()
loop.create_task(start_network())
loop.create_task(receive_messages())
root.mainloop()
```

### Notes for GUI Developers
- **Asynchronous Operations**: Methods like `start_advertising`, `send_message`, `send_encrypted_channel_message`, `send_delivery_ack`, `send_read_receipt`, and `receive_packet` are asynchronous due to BLE operations (using `bleak`). Use `asyncio.run()` for one-off calls or integrate with an event loop (as shown).
- **Error Handling**: Wrap calls in try-except blocks to handle `ValueError` (e.g., invalid peer IDs, channel names, or decryption failures) and display errors in the GUI.
- **Real-Time Updates**: Use `receive_packet` in an async loop to update the GUI with incoming messages, ACKs, and system messages.
- **Thread Safety**: Ensure Tkinter updates (e.g., `chat_display.insert`) are thread-safe by using `root.after` or a similar mechanism if running async tasks.
- **Channel Management**: Use `ChannelManager` to track joined channels and handle password-protected channels. Validate channel names with regex (`^#[a-zA-Z0-9-]+$`).
- **Privacy**: Use `pad` and `unpad` for consistent message sizes, and `OptimizedBloomFilter` to track seen messages efficiently.
- **Security**: Always verify signatures with `verify_signature` before processing packets, and store keys securely with `store_key`.

For further details, refer to the [API documentation](https://bitchat-py.readthedocs.io/) and the [Bitchat Whitepaper](https://github.com/jackjackbits/bitchat/blob/main/WHITEPAPER.md).

## Testing

Run unit tests to verify functionality:

<code>pytest tests/</code>

Generate coverage report:

<code>pytest tests/ --cov --cov-report=html</code>

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/nguyentruonglong/bitchat-py).

## License

This project is released under the [Unlicense](LICENSE).