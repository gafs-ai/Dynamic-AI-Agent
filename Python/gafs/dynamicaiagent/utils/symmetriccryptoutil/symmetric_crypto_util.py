from __future__ import annotations
from enum import Enum

from .aes_256_crypto_provider import Aes256CryptoProvider


class SymmetricCryptoUtil:
    """Utility class that provides symmetric cryptography operations.

    This class works as a facade that selects the concrete crypto provider
    implementation based on `SymmetricCryptoType`.
    """

    def generate_key(self, crypto_type: "SymmetricCryptoType") -> str:
        """Generate a new key for the specified symmetric crypto type.

        Returns:
            A new key encoded as a base64 string.
        """
        match crypto_type:
            case SymmetricCryptoType.AES_256_GCM:
                return Aes256CryptoProvider().generate_key()
            case _:
                raise ValueError(f"Unsupported crypto type: {crypto_type}")

    def encrypt(self, crypto_type: "SymmetricCryptoType", raw: str, key: str) -> str:
        """Encrypt plain text using the given key and crypto type.

        Returns:
            The encrypted data as a base64 string.
        """
        match crypto_type:
            case SymmetricCryptoType.AES_256_GCM:
                return Aes256CryptoProvider().encrypt(raw, key)
            case _:
                raise ValueError(f"Unsupported crypto type: {crypto_type}")

    def decrypt(self, crypto_type: "SymmetricCryptoType", encrypted: str, key: str) -> str:
        """Decrypt encrypted text using the given key and crypto type.

        Returns:
            The decrypted data as a UTF-8 string.
        """
        match crypto_type:
            case SymmetricCryptoType.AES_256_GCM:
                return Aes256CryptoProvider().decrypt(encrypted, key)
            case _:
                raise ValueError(f"Unsupported crypto type: {crypto_type}")


class SymmetricCryptoType(Enum):
    """Supported symmetric cryptography algorithm t`ypes."""

    AES_256_GCM = "aes-256-gcm"
