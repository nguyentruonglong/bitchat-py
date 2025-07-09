"""
Python implementation of the bitchat mesh networking protocol for secure, decentralized communication.
"""

__version__ = "1.0.0"

from .protocol import encode_packet, decode_packet, encode_message, decode_message
from .message import BitchatPacket, BitchatMessage, DeliveryAck, ReadReceipt
from .ble_service import start_advertising, send_message, send_encrypted_channel_message
from .encryption import derive_channel_key
from .utils import OptimizedBloomFilter, pad, unpad, optimal_block_size

__all__ = [
    "BitchatPacket",
    "BitchatMessage",
    "DeliveryAck",
    "ReadReceipt",
    "OptimizedBloomFilter",
    "encode_packet",
    "decode_packet",
    "encode_message",
    "decode_message",
    "pad",
    "unpad",
    "optimal_block_size",
    "derive_channel_key",
    "start_advertising",
    "send_message",
    "send_encrypted_channel_message",
]