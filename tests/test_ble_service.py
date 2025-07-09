import pytest
from unittest.mock import AsyncMock, patch
from bitchat.ble_service import start_advertising, scan_peers, send_packet, receive_packet, send_message, send_encrypted_channel_message, send_delivery_ack, send_read_receipt
from bitchat.message import BitchatPacket, BitchatMessage, DeliveryAck, ReadReceipt
from bitchat.protocol import encode_packet, encode_message
from bitchat.encryption import encrypt_content, derive_channel_key
from datetime import datetime

@pytest.mark.asyncio
async def test_start_advertising():
    peer_id = "peer123"
    with patch("bleak.BleakClient") as mock_bleak_client:
        mock_bleak_client.return_value.__aenter__.return_value = AsyncMock()
        await start_advertising(peer_id)
        mock_bleak_client.assert_called_once()
        assert mock_bleak_client.call_args[0][0].startswith(peer_id), "Advertisement should include peer_id"

@pytest.mark.asyncio
async def test_scan_peers():
    mock_peers = ["peer1", "peer2", "peer3"]
    with patch("bleak.BleakScanner") as mock_scanner:
        mock_scanner.return_value.__aenter__.return_value.discover.return_value = [
            type("Device", (), {"address": peer})() for peer in mock_peers
        ]
        peers = await scan_peers()
        assert peers == mock_peers, f"Expected peers {mock_peers}, got {peers}"
        mock_scanner.assert_called_once()

@pytest.mark.asyncio
async def test_send_packet():
    peer_id = "peer456"
    packet = BitchatPacket(
        version=1,
        type="message",
        sender_id="sender123",
        recipient_id=peer_id,
        timestamp=int(datetime.now().timestamp()),
        payload=b"test payload",
        signature=b"\xAB" * 64,
        ttl=5
    )
    with patch("bleak.BleakClient") as mock_bleak_client:
        mock_client = AsyncMock()
        mock_bleak_client.return_value.__aenter__.return_value = mock_client
        await send_packet(packet, peer_id)
        mock_bleak_client.assert_called_once_with(peer_id)
        mock_client.write_data.assert_called_once()
        sent_data = mock_client.write_data.call_args[0][0]
        assert sent_data == encode_packet(packet), "Sent data should match encoded packet"

@pytest.mark.asyncio
async def test_receive_packet():
    packet = BitchatPacket(
        version=1,
        type="message",
        sender_id="sender123",
        recipient_id="peer456",
        timestamp=int(datetime.now().timestamp()),
        payload=b"test payload",
        signature=b"\xAB" * 64,
        ttl=5
    )
    encoded_packet = encode_packet(packet)
    with patch("bleak.BleakClient") as mock_bleak_client:
        mock_client = AsyncMock()
        mock_client.read_data = AsyncMock(return_value=encoded_packet)
        mock_bleak_client.return_value.__aenter__.return_value = mock_client
        received_packet = await receive_packet()
        assert received_packet == packet, f"Expected packet {packet}, got {received_packet}"
        mock_client.read_data.assert_called_once()

@pytest.mark.asyncio
async def test_send_message():
    message = BitchatMessage(
        id="msg123",
        sender="alice",
        content="Hello, world!",
        timestamp=int(datetime.now().timestamp()),
        is_relay=False,
        original_sender=None,
        is_private=False,
        recipient_nickname=None,
        sender_peer_id="sender123",
        mentions=[],
        channel="#general",
        encrypted_content=None,
        is_encrypted=False,
        delivery_status="PENDING"
    )
    broadcast_packet = BitchatPacket(
        version=1,
        type="message",
        sender_id="sender123",
        recipient_id=b"\xFF" * 8,
        timestamp=message.timestamp,
        payload=encode_message(message),
        signature=b"\xAB" * 64,
        ttl=5
    )
    private_packet = BitchatPacket(
        version=1,
        type="message",
        sender_id="sender123",
        recipient_id="peer456",
        timestamp=message.timestamp,
        payload=encode_message(message),
        signature=b"\xAB" * 64,
        ttl=5
    )
    with patch("bitchat.ble_service.send_packet", new=AsyncMock()) as mock_send_packet:
        # Test broadcast message
        await send_message(message, recipient=None)
        mock_send_packet.assert_called_once_with(broadcast_packet, b"\xFF" * 8)
        mock_send_packet.reset_mock()
        # Test private message
        await send_message(message, recipient="peer456")
        mock_send_packet.assert_called_once_with(private_packet, "peer456")

@pytest.mark.asyncio
async def test_send_encrypted_channel_message():
    message = BitchatMessage(
        id="msg456",
        sender="alice",
        content="Secret message",
        timestamp=int(datetime.now().timestamp()),
        is_relay=False,
        original_sender=None,
        is_private=False,
        recipient_nickname=None,
        sender_peer_id="sender123",
        mentions=[],
        channel="#secret",
        encrypted_content=None,
        is_encrypted=False,
        delivery_status="PENDING"
    )
    channel = "#secret"
    password = "secure123"
    key = derive_channel_key(password, channel)
    encrypted_content = encrypt_content(message.content, key)
    encrypted_message = BitchatMessage(
        id=message.id,
        sender=message.sender,
        content="",
        timestamp=message.timestamp,
        is_relay=message.is_relay,
        original_sender=message.original_sender,
        is_private=message.is_private,
        recipient_nickname=message.recipient_nickname,
        sender_peer_id=message.sender_peer_id,
        mentions=message.mentions,
        channel=message.channel,
        encrypted_content=encrypted_content,
        is_encrypted=True,
        delivery_status=message.delivery_status
    )
    packet = BitchatPacket(
        version=1,
        type="message",
        sender_id="sender123",
        recipient_id=b"\xFF" * 8,
        timestamp=message.timestamp,
        payload=encode_message(encrypted_message),
        signature=b"\xAB" * 64,
        ttl=5
    )
    with patch("bitchat.ble_service.send_packet", new=AsyncMock()) as mock_send_packet:
        with patch("bitchat.ble_service.derive_channel_key", return_value=key):
            with patch("bitchat.ble_service.encrypt_content", return_value=encrypted_content):
                await send_encrypted_channel_message(message, channel)
                mock_send_packet.assert_called_once_with(packet, b"\xFF" * 8)

@pytest.mark.asyncio
async def test_send_delivery_ack():
    ack = DeliveryAck(
        message_id="msg123",
        recipient_id="peer456",
        nickname="bob",
        hop_count=2
    )
    packet = BitchatPacket(
        version=1,
        type="ack",
        sender_id="sender123",
        recipient_id="peer456",
        timestamp=int(datetime.now().timestamp()),
        payload=ack.encode(),
        signature=b"\xAB" * 64,
        ttl=5
    )
    with patch("bitchat.ble_service.send_packet", new=AsyncMock()) as mock_send_packet:
        await send_delivery_ack(ack)
        mock_send_packet.assert_called_once_with(packet, "peer456")

@pytest.mark.asyncio
async def test_send_read_receipt():
    receipt = ReadReceipt(
        message_id="msg123",
        recipient_id="peer456",
        nickname="bob",
        timestamp=int(datetime.now().timestamp())
    )
    packet = BitchatPacket(
        version=1,
        type="receipt",
        sender_id="sender123",
        recipient_id="peer456",
        timestamp=receipt.timestamp,
        payload=receipt.encode(),
        signature=b"\xAB" * 64,
        ttl=5
    )
    with patch("bitchat.ble_service.send_packet", new=AsyncMock()) as mock_send_packet:
        await send_read_receipt(receipt)
        mock_send_packet.assert_called_once_with(packet, "peer456")

@pytest.mark.asyncio
async def test_invalid_peer_id():
    packet = BitchatPacket(
        version=1,
        type="message",
        sender_id="sender123",
        recipient_id="invalid_peer",
        timestamp=int(datetime.now().timestamp()),
        payload=b"test payload",
        signature=b"\xAB" * 64,
        ttl=5
    )
    message = BitchatMessage(
        id="msg123",
        sender="alice",
        content="Hello, world!",
        timestamp=int(datetime.now().timestamp()),
        is_relay=False,
        original_sender=None,
        is_private=True,
        recipient_nickname="bob",
        sender_peer_id="sender123",
        mentions=[],
        channel=None,
        encrypted_content=None,
        is_encrypted=False,
        delivery_status="PENDING"
    )
    with patch("bleak.BleakClient") as mock_bleak_client:
        mock_bleak_client.side_effect = ValueError("Invalid peer ID")
        with pytest.raises(ValueError, match="Invalid peer ID"):
            await send_packet(packet, "invalid_peer")
        with pytest.raises(ValueError, match="Invalid peer ID"):
            await send_message(message, recipient="invalid_peer")