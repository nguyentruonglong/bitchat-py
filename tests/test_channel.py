import pytest
from bitchat.encryption import derive_channel_key, encrypt_content, decrypt_content
from bitchat.keychain import store_key, retrieve_key
from bitchat.message import BitchatMessage
from bitchat.channel import ChannelManager
from uuid import uuid4
import time

@pytest.fixture
def channel_manager():
    """Create a ChannelManager instance for testing."""
    return ChannelManager()

def test_password_key_derivation():
    """Test derive_channel_key for same/different passwords and channels."""
    key1 = derive_channel_key("password", "#test")
    key2 = derive_channel_key("password", "#test")
    key3 = derive_channel_key("different", "#test")
    key4 = derive_channel_key("password", "#other")
    assert key1 == key2, "Same password and channel should produce same key"
    assert key1 != key3, "Different passwords should produce different keys"
    assert key1 != key4, "Different channels should produce different keys"

def test_join_unprotected_channel(channel_manager):
    """Test joining an unprotected channel."""
    peer_id = "bitchat_peer1"
    channel_manager.create_channel("#public", creator_id=peer_id)
    channel_manager.join_channel("#public", peer_id="bitchat_peer2")
    assert "#public" in channel_manager.joined_channels, "Channel should be in joined_channels"
    assert channel_manager.current_channel == "#public", "Current channel should be #public"
    assert "#public" not in channel_manager.password_protected_channels, "Channel should not be password-protected"
    messages = channel_manager.get_system_messages()
    assert any("Joined #public successfully" in msg.content for msg in messages), "System message for join should be present"

def test_create_password_protected_channel(channel_manager):
    """Test creating a password-protected channel."""
    peer_id = "bitchat_peer1"
    channel_manager.create_channel("#secret", password="password", creator_id=peer_id)
    assert "#secret" in channel_manager.password_protected_channels, "Channel should be password-protected"
    assert channel_manager.channel_keys.get("#secret") == derive_channel_key("password", "#secret"), "Channel key should match derived key"
    assert channel_manager.channel_passwords.get("#secret") == "password", "Channel password should be stored"
    assert channel_manager.channel_creators.get("#secret") == peer_id, "Channel creator should be set"
    messages = channel_manager.get_system_messages()
    assert any("Created channel #secret" in msg.content for msg in messages), "System message for creation should be present"

def test_join_password_protected_empty_channel(channel_manager):
    """Test joining an empty password-protected channel."""
    creator_id = "bitchat_peer1"
    peer_id = "bitchat_peer2"
    channel_manager.create_channel("#secret", password="password", creator_id=creator_id)
    channel_manager.join_channel("#secret", password="password", peer_id=peer_id)
    assert "#secret" in channel_manager.joined_channels, "Channel should be in joined_channels"
    assert channel_manager.current_channel == "#secret", "Current channel should be #secret"
    assert channel_manager.channel_keys.get("#secret") == derive_channel_key("password", "#secret"), "Channel key should match"
    assert retrieve_key(f"peer:{peer_id}:#secret") == derive_channel_key("password", "#secret"), "Key should be stored for peer"
    messages = channel_manager.get_system_messages()
    assert any("Joined #secret successfully" in msg.content for msg in messages), "System message for successful join should be present"

def test_join_password_protected_channel_with_messages(channel_manager):
    """Test joining a protected channel with messages using correct/wrong password."""
    creator_id = "bitchat_peer1"
    channel_manager.create_channel("#secret", password="password", creator_id=creator_id)
    key = derive_channel_key("password", "#secret")
    
    # Add an encrypted message
    encrypted_content = encrypt_content("Secret message", key)
    message = BitchatMessage(
        id=str(uuid4()),
        sender="alice",
        content="",
        timestamp=time.time(),
        is_relay=False,
        original_sender=None,
        is_private=False,
        recipient_nickname=None,
        sender_peer_id=creator_id,
        mentions=[],
        channel="#secret",
        is_encrypted=True,
        encrypted_content=encrypted_content,
        delivery_status="delivered"
    )
    channel_manager.receive_message(message)
    
    # Join with correct password
    peer_id = "bitchat_peer2"
    channel_manager.join_channel("#secret", password="password", peer_id=peer_id)
    assert "#secret" in channel_manager.joined_channels, "Channel should be in joined_channels"
    assert channel_manager.current_channel == "#secret", "Current channel should be #secret"
    assert retrieve_key(f"peer:{peer_id}:#secret") == key, "Key should be stored for peer"
    messages = channel_manager.get_system_messages()
    assert any("Joined #secret successfully" in msg.content for msg in messages), "System message for join should be present"
    assert any("Decrypted message in #secret" in msg.content for msg in messages), "System message for decryption should be present"
    
    # Join with wrong password
    with pytest.raises(ValueError, match="Key commitment verification failed for #secret"):
        channel_manager.join_channel("#secret", password="wrong", peer_id="bitchat_peer3")
    messages = channel_manager.get_system_messages()
    assert any("Key commitment verification failed for #secret" in msg.content for msg in messages), "System message for failed join should be present"

def test_encrypt_decrypt_channel_message(channel_manager):
    """Test encrypting and decrypting a channel message."""
    peer_id = "bitchat_peer1"
    channel_manager.create_channel("#secret", password="password", creator_id=peer_id)
    key = derive_channel_key("password", "#secret")
    
    content = "Secret message"
    encrypted_content = encrypt_content(content, key)
    decrypted_content = decrypt_content(encrypted_content, key)
    assert decrypted_content == content, "Decrypted content should match original"

def test_wrong_password_fails_decryption(channel_manager):
    """Test decryption failure with wrong password."""
    peer_id = "bitchat_peer1"
    channel_manager.create_channel("#secret", password="password", creator_id=peer_id)
    key = derive_channel_key("password", "#secret")
    wrong_key = derive_channel_key("wrong", "#secret")
    
    content = "Secret message"
    encrypted_content = encrypt_content(content, key)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt_content(encrypted_content, wrong_key)

def test_only_creator_can_set_password(channel_manager):
    """Test that only the creator can set a channel password."""
    creator_id = "bitchat_peer1"
    channel_manager.create_channel("#secret", password="password", creator_id=creator_id)
    
    # Non-creator tries to set password
    with pytest.raises(ValueError, match="Only creator can set password"):
        channel_manager.set_channel_password("#secret", "newpassword", peer_id="bitchat_peer2")
    messages = channel_manager.get_system_messages()
    assert any("Only creator can set password for #secret" in msg.content for msg in messages), "System message for permission error should be present"
    
    # Creator sets new password
    channel_manager.set_channel_password("#secret", "newpassword", peer_id=creator_id)
    assert channel_manager.channel_passwords.get("#secret") == "newpassword", "Password should be updated"
    assert channel_manager.channel_keys.get("#secret") == derive_channel_key("newpassword", "#secret"), "Key should be updated"
    messages = channel_manager.get_system_messages()
    assert any("Password set for #secret" in msg.content for msg in messages), "System message for password set should be present"

def test_creator_can_remove_password(channel_manager):
    """Test creator removing a channel password."""
    creator_id = "bitchat_peer1"
    channel_manager.create_channel("#secret", password="password", creator_id=creator_id)
    channel_manager.remove_channel_password("#secret", peer_id=creator_id)
    assert "#secret" not in channel_manager.password_protected_channels, "Channel should not be password-protected"
    assert "#secret" not in channel_manager.channel_passwords, "Password should be removed"
    assert "#secret" not in channel_manager.channel_keys, "Key should be removed"
    messages = channel_manager.get_system_messages()
    assert any("Password removed from #secret" in msg.content for msg in messages), "System message for password removal should be present"

def test_receive_encrypted_message_without_key(channel_manager):
    """Test receiving an encrypted message without the key."""
    creator_id = "bitchat_peer1"
    channel_manager.create_channel("#secret", password="password", creator_id=creator_id)
    key = derive_channel_key("password", "#secret")
    
    encrypted_content = encrypt_content("Secret message", key)
    message = BitchatMessage(
        id=str(uuid4()),
        sender="alice",
        content="",
        timestamp=time.time(),
        is_relay=False,
        original_sender=None,
        is_private=False,
        recipient_nickname=None,
        sender_peer_id=creator_id,
        mentions=[],
        channel="#secret",
        is_encrypted=True,
        encrypted_content=encrypted_content,
        delivery_status="delivered"
    )
    
    channel_manager.channel_keys.pop("#secret", None)  # Remove key to simulate no access
    channel_manager.receive_message(message)
    assert "#secret" in channel_manager.password_protected_channels, "Channel should be marked as password-protected"
    messages = channel_manager.get_system_messages()
    assert any("Received encrypted message for #secret without key" in msg.content for msg in messages), "System message for missing key should be present"

def test_join_command(channel_manager):
    """Test /join #testchannel command."""
    peer_id = "bitchat_peer1"
    channel_manager.process_command("/join #testchannel", peer_id)
    assert "#testchannel" in channel_manager.joined_channels, "Channel should be in joined_channels"
    assert channel_manager.current_channel == "#testchannel", "Current channel should be #testchannel"
    messages = channel_manager.get_system_messages()
    assert any("Joined #testchannel successfully" in msg.content for msg in messages), "System message for join should be present"

def test_join_command_alias(channel_manager):
    """Test /j #quick command."""
    peer_id = "bitchat_peer1"
    channel_manager.process_command("/j #quick", peer_id)
    assert "#quick" in channel_manager.joined_channels, "Channel should be in joined_channels"
    assert channel_manager.current_channel == "#quick", "Current channel should be #quick"
    messages = channel_manager.get_system_messages()
    assert any("Joined #quick successfully" in msg.content for msg in messages), "System message for join should be present"

def test_invalid_channel_name(channel_manager):
    """Test /j #invalid-channel! command."""
    peer_id = "bitchat_peer1"
    with pytest.raises(ValueError, match="Invalid channel name"):
        channel_manager.process_command("/j #invalid-channel!", peer_id)
    messages = channel_manager.get_system_messages()
    assert any("Invalid channel name: #invalid-channel!" in msg.content for msg in messages), "System message for invalid channel name should be present"

def test_key_commitment_verification(channel_manager):
    """Test joining with correct/wrong password against key commitment."""
    creator_id = "bitchat_peer1"
    channel_manager.create_channel("#secret", password="password", creator_id=creator_id)
    
    # Join with correct password
    peer_id = "bitchat_peer2"
    channel_manager.join_channel("#secret", password="password", peer_id=peer_id)
    assert "#secret" in channel_manager.joined_channels, "Channel should be in joined_channels"
    assert channel_manager.current_channel == "#secret", "Current channel should be #secret"
    assert channel_manager.channel_keys.get("#secret") == derive_channel_key("password", "#secret"), "Key should match"
    messages = channel_manager.get_system_messages()
    assert any("Joined #secret successfully" in msg.content for msg in messages), "System message for join should be present"
    
    # Join with wrong password
    with pytest.raises(ValueError, match="Key commitment verification failed for #secret"):
        channel_manager.join_channel("#secret", password="wrong", peer_id="bitchat_peer3")
    messages = channel_manager.get_system_messages()
    assert any("Key commitment verification failed for #secret" in msg.content for msg in messages), "System message for failed verification should be present"

def test_ownership_transfer(channel_manager):
    """Test transferring channel ownership."""
    creator_id = "bitchat_peer1"
    new_owner_id = "bitchat_peer2"
    channel_manager.create_channel("#secret", password="password", creator_id=creator_id)
    
    # Non-creator tries to transfer ownership
    with pytest.raises(ValueError, match="Only creator can transfer ownership"):
        channel_manager.transfer_ownership("#secret", new_owner_id, peer_id="bitchat_peer3")
    messages = channel_manager.get_system_messages()
    assert any("Only creator can transfer ownership of #secret" in msg.content for msg in messages), "System message for permission error should be present"
    
    # Creator transfers ownership
    channel_manager.transfer_ownership("#secret", new_owner_id, peer_id=creator_id)
    assert channel_manager.channel_creators.get("#secret") == new_owner_id, "Ownership should be transferred"
    messages = channel_manager.get_system_messages()
    assert any(f"Ownership of #secret transferred to {new_owner_id}" in msg.content for msg in messages), "System message for ownership transfer should be present"