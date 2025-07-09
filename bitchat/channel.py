import re
from uuid import uuid4
import time
from bitchat.encryption import derive_channel_key, encrypt_content, decrypt_content
from bitchat.keychain import store_key, retrieve_key
from bitchat.message import BitchatMessage

class ChannelManager:
    """Manage channels, including password-protected ones, for the bitchat protocol."""
    
    def __init__(self):
        self.joined_channels = set()  # Set of joined channel names
        self.current_channel = None  # Current active channel
        self.password_protected_channels = set()  # Set of password-protected channels
        self.channel_keys = {}  # Dict mapping channels to derived keys
        self.channel_passwords = {}  # Dict mapping channels to passwords
        self.channel_creators = {}  # Dict mapping channels to creator IDs
        self.system_messages = []  # List of system-generated messages

    def create_channel(self, channel: str, password: str = None, creator_id: str = None):
        """Create a new channel, optionally with a password."""
        if not re.match(r"^#[a-zA-Z0-9-]+$", channel):
            raise ValueError("Invalid channel name")
        if channel in self.joined_channels:
            raise ValueError(f"Channel {channel} already exists")
        if password:
            self.password_protected_channels.add(channel)
            key = derive_channel_key(password, channel)
            self.channel_keys[channel] = key
            self.channel_passwords[channel] = password
            store_key(key, f"channel:{channel}")
        self.channel_creators[channel] = creator_id
        self.joined_channels.add(channel)
        self.system_messages.append(BitchatMessage(
            id=str(uuid4()),
            sender="system",
            content=f"Created channel {channel}",
            timestamp=time.time(),
            is_relay=False,
            original_sender=None,
            is_private=False,
            recipient_nickname=None,
            sender_peer_id="system",
            mentions=[],
            channel=channel,
            is_encrypted=False,
            encrypted_content=None,
            delivery_status="delivered"
        ))

    def join_channel(self, channel: str, password: str = None, peer_id: str = None):
        """Join a channel, verifying password if required."""
        if not re.match(r"^#[a-zA-Z0-9-]+$", channel):
            raise ValueError("Invalid channel name")
        if channel in self.joined_channels:
            self.current_channel = channel
            return
        if channel in self.password_protected_channels:
            if not password:
                self.system_messages.append(BitchatMessage(
                    id=str(uuid4()),
                    sender="system",
                    content=f"Password required for {channel}",
                    timestamp=time.time(),
                    is_relay=False,
                    original_sender=None,
                    is_private=False,
                    recipient_nickname=None,
                    sender_peer_id="system",
                    mentions=[],
                    channel=channel,
                    is_encrypted=False,
                    encrypted_content=None,
                    delivery_status="delivered"
                ))
                return
            key = derive_channel_key(password, channel)
            if key != self.channel_keys.get(channel):
                self.system_messages.append(BitchatMessage(
                    id=str(uuid4()),
                    sender="system",
                    content=f"Key commitment verification failed for {channel}",
                    timestamp=time.time(),
                    is_relay=False,
                    original_sender=None,
                    is_private=False,
                    recipient_nickname=None,
                    sender_peer_id="system",
                    mentions=[],
                    channel=channel,
                    is_encrypted=False,
                    encrypted_content=None,
                    delivery_status="delivered"
                ))
                return
            store_key(key, f"peer:{peer_id}:{channel}")
        self.joined_channels.add(channel)
        self.current_channel = channel
        self.system_messages.append(BitchatMessage(
            id=str(uuid4()),
            sender="system",
            content=f"Joined {channel} successfully",
            timestamp=time.time(),
            is_relay=False,
            original_sender=None,
            is_private=False,
            recipient_nickname=None,
            sender_peer_id="system",
            mentions=[],
            channel=channel,
            is_encrypted=False,
            encrypted_content=None,
            delivery_status="delivered"
        ))

    def set_channel_password(self, channel: str, password: str, peer_id: str):
        """Set or update a channel's password (creator only)."""
        if channel not in self.channel_creators:
            raise ValueError(f"Channel {channel} does not exist")
        if self.channel_creators.get(channel) != peer_id:
            self.system_messages.append(BitchatMessage(
                id=str(uuid4()),
                sender="system",
                content=f"Only creator can set password for {channel}",
                timestamp=time.time(),
                is_relay=False,
                original_sender=None,
                is_private=False,
                recipient_nickname=None,
                sender_peer_id="system",
                mentions=[],
                channel=channel,
                is_encrypted=False,
                encrypted_content=None,
                delivery_status="delivered"
            ))
            raise ValueError("Only creator can set password")
        self.password_protected_channels.add(channel)
        key = derive_channel_key(password, channel)
        self.channel_keys[channel] = key
        self.channel_passwords[channel] = password
        store_key(key, f"channel:{channel}")
        self.system_messages.append(BitchatMessage(
            id=str(uuid4()),
            sender="system",
            content=f"Password set for {channel}",
            timestamp=time.time(),
            is_relay=False,
            original_sender=None,
            is_private=False,
            recipient_nickname=None,
            sender_peer_id="system",
            mentions=[],
            channel=channel,
            is_encrypted=False,
            encrypted_content=None,
            delivery_status="delivered"
        ))

    def remove_channel_password(self, channel: str, peer_id: str):
        """Remove a channel's password (creator only)."""
        if channel not in self.channel_creators:
            raise ValueError(f"Channel {channel} does not exist")
        if self.channel_creators.get(channel) != peer_id:
            self.system_messages.append(BitchatMessage(
                id=str(uuid4()),
                sender="system",
                content=f"Only creator can remove password for {channel}",
                timestamp=time.time(),
                is_relay=False,
                original_sender=None,
                is_private=False,
                recipient_nickname=None,
                sender_peer_id="system",
                mentions=[],
                channel=channel,
                is_encrypted=False,
                encrypted_content=None,
                delivery_status="delivered"
            ))
            raise ValueError("Only creator can remove password")
        self.password_protected_channels.discard(channel)
        self.channel_keys.pop(channel, None)
        self.channel_passwords.pop(channel, None)
        self.system_messages.append(BitchatMessage(
            id=str(uuid4()),
            sender="system",
            content=f"Password removed from {channel}",
            timestamp=time.time(),
            is_relay=False,
            original_sender=None,
            is_private=False,
            recipient_nickname=None,
            sender_peer_id="system",
            mentions=[],
            channel=channel,
            is_encrypted=False,
            encrypted_content=None,
            delivery_status="delivered"
        ))

    def receive_message(self, message: BitchatMessage):
        """Handle incoming messages, checking for encryption."""
        if message.is_encrypted and message.channel not in self.channel_keys:
            self.password_protected_channels.add(message.channel)
            self.system_messages.append(BitchatMessage(
                id=str(uuid4()),
                sender="system",
                content=f"Received encrypted message for {message.channel} without key",
                timestamp=time.time(),
                is_relay=False,
                original_sender=None,
                is_private=False,
                recipient_nickname=None,
                sender_peer_id="system",
                mentions=[],
                channel=message.channel,
                is_encrypted=False,
                encrypted_content=None,
                delivery_status="delivered"
            ))
        elif message.is_encrypted and message.channel in self.channel_keys:
            try:
                key = self.channel_keys[message.channel]
                message.content = decrypt_content(message.encrypted_content, key)
                message.encrypted_content = None
                message.is_encrypted = False
                self.system_messages.append(BitchatMessage(
                    id=str(uuid4()),
                    sender="system",
                    content=f"Decrypted message in {message.channel}",
                    timestamp=time.time(),
                    is_relay=False,
                    original_sender=None,
                    is_private=False,
                    recipient_nickname=None,
                    sender_peer_id="system",
                    mentions=[],
                    channel=message.channel,
                    is_encrypted=False,
                    encrypted_content=None,
                    delivery_status="delivered"
                ))
            except ValueError:
                self.system_messages.append(BitchatMessage(
                    id=str(uuid4()),
                    sender="system",
                    content=f"Failed to decrypt message in {message.channel}",
                    timestamp=time.time(),
                    is_relay=False,
                    original_sender=None,
                    is_private=False,
                    recipient_nickname=None,
                    sender_peer_id="system",
                    mentions=[],
                    channel=message.channel,
                    is_encrypted=False,
                    encrypted_content=None,
                    delivery_status="delivered"
                ))
        self.system_messages.append(message)

    def process_command(self, command: str, peer_id: str):
        """Process commands like /join or /j."""
        if command.startswith("/join ") or command.startswith("/j "):
            parts = command.split(" ", 1)
            if len(parts) < 2:
                raise ValueError("Channel name required")
            channel = parts[1]
            if not re.match(r"^#[a-zA-Z0-9-]+$", channel):
                self.system_messages.append(BitchatMessage(
                    id=str(uuid4()),
                    sender="system",
                    content=f"Invalid channel name: {channel}",
                    timestamp=time.time(),
                    is_relay=False,
                    original_sender=None,
                    is_private=False,
                    recipient_nickname=None,
                    sender_peer_id="system",
                    mentions=[],
                    channel=None,
                    is_encrypted=False,
                    encrypted_content=None,
                    delivery_status="delivered"
                ))
                raise ValueError(f"Invalid channel name: {channel}")
            self.join_channel(channel, peer_id=peer_id)
        else:
            self.system_messages.append(BitchatMessage(
                id=str(uuid4()),
                sender="system",
                content=f"Unknown command: {command}",
                timestamp=time.time(),
                is_relay=False,
                original_sender=None,
                is_private=False,
                recipient_nickname=None,
                sender_peer_id="system",
                mentions=[],
                channel=None,
                is_encrypted=False,
                encrypted_content=None,
                delivery_status="delivered"
            ))
            raise ValueError(f"Unknown command: {command}")

    def get_system_messages(self):
        """Return system-generated messages."""
        return self.system_messages

    def transfer_ownership(self, channel: str, new_owner_id: str, peer_id: str):
        """Transfer channel ownership (creator only)."""
        if channel not in self.channel_creators:
            raise ValueError(f"Channel {channel} does not exist")
        if self.channel_creators.get(channel) != peer_id:
            self.system_messages.append(BitchatMessage(
                id=str(uuid4()),
                sender="system",
                content=f"Only creator can transfer ownership of {channel}",
                timestamp=time.time(),
                is_relay=False,
                original_sender=None,
                is_private=False,
                recipient_nickname=None,
                sender_peer_id="system",
                mentions=[],
                channel=channel,
                is_encrypted=False,
                encrypted_content=None,
                delivery_status="delivered"
            ))
            raise ValueError("Only creator can transfer ownership")
        self.channel_creators[channel] = new_owner_id
        self.system_messages.append(BitchatMessage(
            id=str(uuid4()),
            sender="system",
            content=f"Ownership of {channel} transferred to {new_owner_id}",
            timestamp=time.time(),
            is_relay=False,
            original_sender=None,
            is_private=False,
            recipient_nickname=None,
            sender_peer_id="system",
            mentions=[],
            channel=channel,
            is_encrypted=False,
            encrypted_content=None,
            delivery_status="delivered"
        ))