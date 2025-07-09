Bitchat Python Library
======================

The Bitchat Python Library is a secure, decentralized mesh networking protocol
implementation, supporting BLE communication, message encryption, and channel
management, as described in the Bitchat whitepaper.

Installation
------------

.. code-block:: bash

   pip3 install bitchat

Quickstart
----------

.. code-block:: python

   from bitchat import BitchatMessage, send_message, derive_channel_key, generate_channel_key

   # Send a message
   message = BitchatMessage(id="msg1", sender="alice", content="Hello", timestamp=1234567890.0,
                            is_relay=False, is_private=False, sender_peer_id="peer1", mentions=[],
                            channel="#general", is_encrypted=False, delivery_status="pending")
   send_message(message)

   # Join a password-protected channel
   key = generate_channel_key("#secret", "password")
   # Further channel operations...

.. toctree::
   :maxdepth: 2

   api