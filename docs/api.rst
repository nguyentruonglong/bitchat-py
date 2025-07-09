API Reference
=============

.. automodule:: bitchat
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: bitchat.message.BitchatPacket
   :members:
   :undoc-members:

.. autoclass:: bitchat.message.BitchatMessage
   :members:
   :undoc-members:

.. autoclass:: bitchat.message.DeliveryAck
   :members:
   :undoc-members:

.. autoclass:: bitchat.message.ReadReceipt
   :members:
   :undoc-members:

.. autoclass:: bitchat.utils.OptimizedBloomFilter
   :members:
   :undoc-members:

Examples
--------

Sending a Message
~~~~~~~~~~~~~~~~~

The following example demonstrates sending a message to a public channel:

.. code-block:: python

   from bitchat import BitchatMessage, send_message
   import time

   # Create a message for the #general channel
   message = BitchatMessage(
       id="msg123",
       sender="alice",
       content="Hello, everyone!",
       timestamp=time.time(),
       is_relay=False,
       is_private=False,
       sender_peer_id="peer1",
       mentions=["bob"],
       channel="#general",
       is_encrypted=False,
       delivery_status="pending"
   )
   send_message(message)

Joining a Password-Protected Channel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example shows how to join a password-protected channel and send an encrypted message:

.. code-block:: python

   from bitchat import generate_channel_key, send_encrypted_channel_message, BitchatMessage
   import time

   # Generate key for a password-protected channel
   key = generate_channel_key("#secret", "mysecurepassword")

   # Create an encrypted message
   message = BitchatMessage(
       id="msg456",
       sender="alice",
       content="",
       timestamp=time.time(),
       is_relay=False,
       is_private=False,
       sender_peer_id="peer1",
       mentions=[],
       channel="#secret",
       is_encrypted=True,
       encrypted_content=b"encrypted_data",  # Placeholder for encrypted content
       delivery_status="pending"
   )
   send_encrypted_channel_message(message, "#secret")

Handling Encryption
~~~~~~~~~~~~~~~~~~~

This example demonstrates encrypting and decrypting message content:

.. code-block:: python

   from bitchat import derive_channel_key, encrypt_content, decrypt_content

   # Derive a channel key
   key = derive_channel_key("mysecurepassword", "#secret")

   # Encrypt message content
   content = "This is a secret message"
   encrypted = encrypt_content(content, key)

   # Decrypt message content
   decrypted = decrypt_content(encrypted, key)
   print(decrypted)  # Output: This is a secret message