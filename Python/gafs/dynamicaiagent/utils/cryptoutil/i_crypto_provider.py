from __future__ import annotations

from abc import ABC, abstractmethod

from .key_pair import KeyPair


class ICryptoProvider(ABC):
    """Abstract interface for all cryptography providers.

    Each concrete provider encapsulates a single algorithm and exposes a
    consistent three-method interface: ``generate_key_pair``, ``encrypt``,
    and ``decrypt``.

    Both symmetric and asymmetric providers implement this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier string for this provider.

        Returns:
            Provider identifier (e.g. ``"aes-256-gcm"``, ``"rsa-oaep"``,
            ``"ecies-p256"``).
        """
        raise NotImplementedError

    @abstractmethod
    def generate_key_pair(self) -> KeyPair:
        """Generate a new key pair for this algorithm.

        For symmetric providers, ``encryption_key`` and ``decryption_key`` in
        the returned ``KeyPair`` hold the same value.

        Returns:
            Newly generated key pair. Both fields are base64-encoded strings.
        """
        raise NotImplementedError

    @abstractmethod
    def encrypt(self, raw: str, encryption_key: str) -> str:
        """Encrypt plaintext using the given encryption key.

        Args:
            raw: Plaintext string to encrypt.
            encryption_key: Encryption key encoded as a base64 string.
                            For symmetric providers, this is the shared key.
                            For asymmetric providers, this is the public key.

        Returns:
            Encrypted payload as a base64 string. Format is provider-specific.

        Raises:
            CryptoUtilException: If encryption fails (e.g. invalid key format,
                                 plaintext exceeds size limit).
        """
        raise NotImplementedError

    @abstractmethod
    def decrypt(self, encrypted: str, decryption_key: str) -> str:
        """Decrypt a payload produced by ``encrypt``.

        Args:
            encrypted: Encrypted payload produced by ``encrypt``.
            decryption_key: Decryption key encoded as a base64 string.
                            For symmetric providers, this is the shared key.
                            For asymmetric providers, this is the private key.

        Returns:
            Decrypted plaintext as a UTF-8 string.

        Raises:
            CryptoUtilException: If decryption fails (e.g. invalid key format,
                                 authentication tag mismatch, corrupted ciphertext).
        """
        raise NotImplementedError
