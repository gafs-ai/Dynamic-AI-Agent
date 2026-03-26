from __future__ import annotations
from base64 import b64decode, b64encode

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from .i_symmetric_crypto_provider import ISymmetricCryptoProvider


class Aes256CryptoProvider(ISymmetricCryptoProvider):
    """AES-256-GCM implementation of `ISymmetricCryptoProvider`.

    This provider generates 256-bit keys and performs encryption and
    decryption using AES in Galois/Counter Mode (GCM).
    """

    @property
    def name(self) -> str:
        """Get the identifier of this provider.

        Returns:
            The identifier of this provider.
        """
        return "aes-256-gcm"

    def generate_key(self) -> str:
        """Generate a new random 256-bit key as a base64 string.

        Returns:
            A new random 256-bit key encoded as a base64 string.
        """
        key: bytes = get_random_bytes(32)
        return b64encode(key).decode("utf-8")

    def encrypt(self, raw: str, key: str) -> str:
        """Encrypt UTF-8 text using AES-256-GCM.

        The output is a base64 string containing nonce, authentication tag,
        and ciphertext concatenated in this order.

        Returns:
            The encrypted data as a base64 string.
        """
        key_bytes: bytes = b64decode(key)
        raw_bytes: bytes = raw.encode("utf-8")

        cipher: AES = AES.new(key_bytes, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(raw_bytes)
        nonce: bytes = cipher.nonce

        return b64encode(nonce + tag + ciphertext).decode("utf-8")

    def decrypt(self, encrypted: str, key: str) -> str:
        """Decrypt a base64 string produced by `encrypt`.

        Returns:
            The decrypted data as a UTF-8 string.
        """
        key_bytes: bytes = b64decode(key)
        encrypted_bytes: bytes = b64decode(encrypted)

        nonce: bytes = encrypted_bytes[:16]
        tag: bytes = encrypted_bytes[16:32]
        ct: bytes = encrypted_bytes[32:]

        cipher: AES = AES.new(key_bytes, AES.MODE_GCM, nonce=nonce)
        data: bytes = cipher.decrypt_and_verify(ct, tag)
        return data.decode("utf-8")