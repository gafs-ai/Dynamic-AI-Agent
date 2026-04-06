from __future__ import annotations
from abc import ABC, abstractmethod


class ISymmetricCryptoProvider(ABC):
    """Interface for symmetric key cryptography providers.

    Implementations of this interface must provide a concrete algorithm
    (for example AES-256-GCM) that can generate keys and encrypt / decrypt data.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this crypto provider.

        Returns:
            The name of this crypto provider.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_key(self) -> str:
        """Generate a new shared key encoded as a base64 string.

        Returns:
            A new shared key encoded as a base64 string.
        """
        raise NotImplementedError

    @abstractmethod
    def encrypt(self, raw: str, key: str) -> str:
        """Encrypt plain text data using the given base64-encoded key.
        
        Returns:
            The encrypted data.
        """
        raise NotImplementedError

    @abstractmethod
    def decrypt(self, encrypted: str, key: str) -> str:
        """Decrypt encrypted data using the given base64-encoded key.

        Returns:
            The decrypted data.
        """
        raise NotImplementedError
