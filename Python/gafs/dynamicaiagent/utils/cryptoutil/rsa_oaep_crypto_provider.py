from __future__ import annotations

from base64 import b64decode, b64encode

from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pss as _pss  # noqa: F401 – imported for MGF1 reference
from Crypto.Cipher.PKCS1_OAEP import PKCS1OAEP_Cipher
from Crypto.Hash.SHA256 import SHA256Hash

from .exceptions.crypto_util_exception import CryptoUtilException
from .i_crypto_provider import ICryptoProvider
from .key_pair import KeyPair


def _mgf1_sha256(x: bytes, y: int) -> bytes:
    """MGF1 mask-generation function using SHA-256."""
    from Crypto.Signature.pss import MGF1
    return MGF1(x, y, SHA256)


class RsaOaepCryptoProvider(ICryptoProvider):
    """RSA-OAEP implementation of ICryptoProvider.

    Encryption scheme:
        - Algorithm: RSA-OAEP
        - Key size: 2048 bits
        - Hash (OAEP): SHA-256
        - Mask generation function: MGF1-SHA256

    Key format (all base64-encoded DER):
        - encryption_key: DER SubjectPublicKeyInfo (RSA public key)
        - decryption_key: DER PKCS#8 (RSA private key)

    Plaintext size limit:
        key_size/8 - 2 * hash_size - 2 = 256 - 64 - 2 = 190 bytes (UTF-8 encoded)
    """

    # Maximum UTF-8-encoded plaintext size in bytes.
    _MAX_PLAINTEXT_BYTES: int = 190

    @property
    def name(self) -> str:
        """Identifier string for this provider.

        Returns:
            ``"rsa-oaep"``
        """
        return "rsa-oaep"

    def generate_key_pair(self) -> KeyPair:
        """Generate a new random 2048-bit RSA key pair.

        Returns:
            KeyPair with DER-encoded, base64-encoded keys:
            ``encryption_key`` = SubjectPublicKeyInfo; ``decryption_key`` = PKCS#8.
        """
        # Generate a 2048-bit RSA key pair.
        rsa_key = RSA.generate(2048)

        # Export the public key in DER SubjectPublicKeyInfo format.
        public_der: bytes = rsa_key.publickey().export_key(format="DER")

        # Export the private key in DER PKCS#8 format.
        private_der: bytes = rsa_key.export_key(format="DER", pkcs=8)

        # Base64-encode both keys.
        pair = KeyPair()
        pair.encryption_key = b64encode(public_der).decode("utf-8")
        pair.decryption_key = b64encode(private_der).decode("utf-8")
        return pair

    def _build_cipher(self, key: RSA.RsaKey) -> PKCS1OAEP_Cipher:
        """Create an RSA-OAEP cipher with SHA-256 and MGF1-SHA256.

        Args:
            key: RSA key object (public for encryption, private for decryption).

        Returns:
            Configured PKCS1_OAEP cipher instance.
        """
        return PKCS1_OAEP.new(
            key,
            hashAlgo=SHA256,
            mgfunc=_mgf1_sha256,
        )

    def encrypt(self, raw: str, encryption_key: str) -> str:
        """Encrypt a UTF-8 string using RSA-OAEP.

        Args:
            raw: Plaintext string to encrypt (max 190 bytes when UTF-8 encoded).
            encryption_key: RSA public key in DER SubjectPublicKeyInfo format,
                            base64-encoded.

        Returns:
            RSA-OAEP ciphertext encoded as a base64 string.

        Raises:
            CryptoUtilException: If the plaintext exceeds 190 bytes or encryption fails.
        """
        try:
            # Encode the plaintext to UTF-8 bytes and validate the size limit.
            raw_bytes: bytes = raw.encode("utf-8")
            if len(raw_bytes) > self._MAX_PLAINTEXT_BYTES:
                raise CryptoUtilException(
                    f"Plaintext exceeds RSA-OAEP size limit "
                    f"({len(raw_bytes)} > {self._MAX_PLAINTEXT_BYTES} bytes)."
                )

            # Decode the base64 public key and import it as an RSA key object.
            public_der: bytes = b64decode(encryption_key)
            rsa_key = RSA.import_key(public_der)

            # Build the RSA-OAEP cipher and encrypt.
            cipher = self._build_cipher(rsa_key)
            ciphertext: bytes = cipher.encrypt(raw_bytes)

            # Return the ciphertext base64-encoded.
            return b64encode(ciphertext).decode("utf-8")

        except CryptoUtilException:
            raise
        except Exception as e:
            raise CryptoUtilException(f"RSA-OAEP encryption failed: {e}") from e

    def decrypt(self, encrypted: str, decryption_key: str) -> str:
        """Decrypt a payload produced by ``encrypt``.

        Args:
            encrypted: Base64-encoded RSA-OAEP ciphertext produced by ``encrypt``.
            decryption_key: RSA private key in DER PKCS#8 format, base64-encoded.

        Returns:
            Decrypted plaintext as a UTF-8 string.

        Raises:
            CryptoUtilException: If decryption fails (wrong key or corrupted ciphertext).
        """
        try:
            # Decode the base64 private key and import it as an RSA key object.
            private_der: bytes = b64decode(decryption_key)
            rsa_key = RSA.import_key(private_der)

            # Decode the base64 ciphertext to raw bytes.
            ciphertext: bytes = b64decode(encrypted)

            # Build the RSA-OAEP cipher and decrypt.
            cipher = self._build_cipher(rsa_key)
            plaintext_bytes: bytes = cipher.decrypt(ciphertext)

            # Decode the resulting bytes as UTF-8 and return.
            return plaintext_bytes.decode("utf-8")

        except CryptoUtilException:
            raise
        except Exception as e:
            raise CryptoUtilException(
                f"RSA-OAEP decryption failed (wrong key or corrupted ciphertext): {e}"
            ) from e
