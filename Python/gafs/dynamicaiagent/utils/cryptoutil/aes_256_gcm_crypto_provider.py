from __future__ import annotations

from base64 import b64decode, b64encode

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from .exceptions.crypto_util_exception import CryptoUtilException
from .i_crypto_provider import ICryptoProvider
from .key_pair import KeyPair


class Aes256GcmCryptoProvider(ICryptoProvider):
    """AES-256-GCM implementation of ICryptoProvider.

    This is a symmetric provider. Both ``encryption_key`` and ``decryption_key``
    in the returned ``KeyPair`` hold the same 32-byte shared key encoded as
    a base64 string.

    Encrypted payload layout (all base64-encoded together):
        | offset | length | content                             |
        |--------|--------|-------------------------------------|
        |      0 |     16 | Nonce (randomly generated per call) |
        |     16 |     16 | GCM authentication tag              |
        |     32 |    var | Ciphertext                          |
    """

    @property
    def name(self) -> str:
        """Identifier string for this provider.

        Returns:
            ``"aes-256-gcm"``
        """
        return "aes-256-gcm"

    def generate_key_pair(self) -> KeyPair:
        """Generate a new random 256-bit AES key and return it as a symmetric KeyPair.

        Returns:
            KeyPair where both ``encryption_key`` and ``decryption_key`` hold
            the same 32 random bytes encoded as a base64 string.
        """
        # Generate 32 random bytes (256 bits) as the shared AES key.
        key_bytes: bytes = get_random_bytes(32)
        key: str = b64encode(key_bytes).decode("utf-8")

        # For symmetric algorithms, encryption_key and decryption_key are identical.
        pair = KeyPair()
        pair.encryption_key = key
        pair.decryption_key = key
        return pair

    def encrypt(self, raw: str, encryption_key: str) -> str:
        """Encrypt a UTF-8 string using AES-256-GCM.

        Args:
            raw: Plaintext string to encrypt.
            encryption_key: 256-bit AES key encoded as a base64 string.

        Returns:
            ``nonce (16) || tag (16) || ciphertext`` encoded as a base64 string.

        Raises:
            CryptoUtilException: If encryption fails (e.g. invalid key format).
        """
        try:
            # Decode the base64 key to raw bytes.
            key_bytes: bytes = b64decode(encryption_key)

            # Encode the plaintext to UTF-8 bytes.
            raw_bytes: bytes = raw.encode("utf-8")

            # Create a new AES-GCM cipher with a randomly generated nonce.
            cipher: AES = AES.new(key_bytes, AES.MODE_GCM)

            # Encrypt the plaintext and obtain the ciphertext and 16-byte tag.
            ciphertext, tag = cipher.encrypt_and_digest(raw_bytes)

            # Retrieve the randomly generated nonce from the cipher instance.
            nonce: bytes = cipher.nonce

            # Concatenate nonce + tag + ciphertext and base64-encode the result.
            return b64encode(nonce + tag + ciphertext).decode("utf-8")

        except CryptoUtilException:
            raise
        except Exception as e:
            raise CryptoUtilException(f"AES-256-GCM encryption failed: {e}") from e

    def decrypt(self, encrypted: str, decryption_key: str) -> str:
        """Decrypt a payload produced by ``encrypt``.

        Args:
            encrypted: Base64-encoded payload produced by ``encrypt``.
            decryption_key: 256-bit AES key encoded as a base64 string.

        Returns:
            Decrypted plaintext as a UTF-8 string.

        Raises:
            CryptoUtilException: If the authentication tag does not match
                                 (data tampered or wrong key), or if any
                                 other decryption error occurs.
        """
        try:
            # Decode the base64 key and payload to raw bytes.
            key_bytes: bytes = b64decode(decryption_key)
            encrypted_bytes: bytes = b64decode(encrypted)

            # Parse the binary payload layout: nonce(16) || tag(16) || ciphertext.
            nonce: bytes = encrypted_bytes[:16]
            tag: bytes = encrypted_bytes[16:32]
            ciphertext: bytes = encrypted_bytes[32:]

            # Re-create the AES-GCM cipher with the stored nonce.
            cipher: AES = AES.new(key_bytes, AES.MODE_GCM, nonce=nonce)

            # Decrypt while simultaneously verifying the authentication tag.
            # Raises ValueError if the tag does not match.
            plaintext_bytes: bytes = cipher.decrypt_and_verify(ciphertext, tag)

            # Decode the resultant bytes back to a UTF-8 string.
            return plaintext_bytes.decode("utf-8")

        except CryptoUtilException:
            raise
        except Exception as e:
            raise CryptoUtilException(
                f"AES-256-GCM decryption failed (tag mismatch or wrong key): {e}"
            ) from e
