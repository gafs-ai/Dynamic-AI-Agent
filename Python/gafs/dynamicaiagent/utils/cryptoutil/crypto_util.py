from __future__ import annotations

from .aes_256_gcm_crypto_provider import Aes256GcmCryptoProvider
from .crypto_type import CryptoType
from .ecies_p256_crypto_provider import EciesP256CryptoProvider
from .exceptions.crypto_util_exception import CryptoUtilException
from .i_crypto_provider import ICryptoProvider
from .key_pair import KeyPair
from .rsa_oaep_crypto_provider import RsaOaepCryptoProvider


class CryptoUtil:
    """Unified facade for all cryptography operations.

    This class selects the appropriate ``ICryptoProvider`` implementation based
    on the given ``CryptoType`` and delegates all operations to it.

    This class is stateless: no internal state is held between calls.

    Supported algorithms:
        - ``CryptoType.AES_256_GCM``  → ``Aes256GcmCryptoProvider``
        - ``CryptoType.RSA_OAEP``     → ``RsaOaepCryptoProvider``
        - ``CryptoType.ECIES_P256``   → ``EciesP256CryptoProvider``
    """

    def _get_provider(self, crypto_type: CryptoType) -> ICryptoProvider:
        """Instantiate and return the provider for the given CryptoType.

        Args:
            crypto_type: Algorithm to dispatch to.

        Returns:
            A freshly created provider instance.

        Raises:
            CryptoUtilException: If ``crypto_type`` is not a supported algorithm.
        """
        # Select the concrete provider based on the requested algorithm.
        match crypto_type:
            case CryptoType.AES_256_GCM:
                return Aes256GcmCryptoProvider()
            case CryptoType.RSA_OAEP:
                return RsaOaepCryptoProvider()
            case CryptoType.ECIES_P256:
                return EciesP256CryptoProvider()
            case _:
                # Unsupported CryptoType value.
                raise CryptoUtilException(
                    f"Unsupported CryptoType: {crypto_type!r}."
                )

    def generate_key_pair(self, crypto_type: CryptoType) -> KeyPair:
        """Generate a new key pair for the specified algorithm.

        For symmetric types (e.g. ``AES_256_GCM``), ``encryption_key`` and
        ``decryption_key`` in the returned ``KeyPair`` hold the same value.

        Args:
            crypto_type: Algorithm for which to generate the key pair.

        Returns:
            Newly generated key pair. Both fields are base64-encoded strings.

        Raises:
            CryptoUtilException: If ``crypto_type`` is not a supported algorithm.
        """
        # Delegate to the appropriate provider.
        provider: ICryptoProvider = self._get_provider(crypto_type)
        return provider.generate_key_pair()

    def encrypt(
        self,
        crypto_type: CryptoType,
        raw: str,
        encryption_key: str,
    ) -> str:
        """Encrypt plaintext using the specified algorithm and encryption key.

        Args:
            crypto_type: Algorithm to use for encryption.
            raw: Plaintext string to encrypt.
            encryption_key: Encryption key encoded as a base64 string.

        Returns:
            Encrypted payload as a base64 string. Format is provider-specific.

        Raises:
            CryptoUtilException: If ``crypto_type`` is not supported, or the
                                 provider raises an exception (e.g. invalid key
                                 format, plaintext exceeds size limit).
        """
        # Delegate to the appropriate provider.
        provider: ICryptoProvider = self._get_provider(crypto_type)
        return provider.encrypt(raw, encryption_key)

    def decrypt(
        self,
        crypto_type: CryptoType,
        encrypted: str,
        decryption_key: str,
    ) -> str:
        """Decrypt a payload using the specified algorithm and decryption key.

        Args:
            crypto_type: Algorithm that was used for encryption.
            encrypted: Encrypted payload produced by ``encrypt``.
            decryption_key: Decryption key encoded as a base64 string.

        Returns:
            Decrypted plaintext as a UTF-8 string.

        Raises:
            CryptoUtilException: If ``crypto_type`` is not supported, or the
                                 provider raises an exception (e.g. authentication
                                 tag mismatch, wrong key, corrupted ciphertext).
        """
        # Delegate to the appropriate provider.
        provider: ICryptoProvider = self._get_provider(crypto_type)
        return provider.decrypt(encrypted, decryption_key)
