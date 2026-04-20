from __future__ import annotations

from base64 import b64decode, b64encode

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import HKDF
from Crypto.PublicKey import ECC
from Crypto.Random import get_random_bytes

from .exceptions.crypto_util_exception import CryptoUtilException
from .i_crypto_provider import ICryptoProvider
from .key_pair import KeyPair


class EciesP256CryptoProvider(ICryptoProvider):
    """ECIES (Elliptic Curve Integrated Encryption Scheme) over P-256.

    Encryption pipeline:
        1. ECDH (P-256)   – derive a shared secret from ephemeral private key
                            and the recipient's public key.
        2. HKDF-SHA256    – derive a 256-bit symmetric key from the shared secret.
        3. AES-256-GCM    – encrypt the plaintext with the derived key.

    Key format (all base64-encoded DER):
        - encryption_key: DER SubjectPublicKeyInfo (P-256 public key)
        - decryption_key: DER PKCS#8 (P-256 private key)

    Encrypted payload layout (all concatenated, then base64-encoded):
        | offset | length | content                                           |
        |--------|--------|---------------------------------------------------|
        |      0 |     65 | Ephemeral P-256 public key (uncompressed 0x04||X||Y) |
        |     65 |     16 | AES-GCM nonce                                     |
        |     81 |     16 | AES-GCM authentication tag                        |
        |     97 |    var | Ciphertext                                        |
    """

    # Byte lengths for each section of the binary payload.
    _EPH_PUB_LEN: int = 65   # 0x04 || X (32) || Y (32)
    _NONCE_LEN: int = 16
    _TAG_LEN: int = 16

    @property
    def name(self) -> str:
        """Identifier string for this provider.

        Returns:
            ``"ecies-p256"``
        """
        return "ecies-p256"

    def generate_key_pair(self) -> KeyPair:
        """Generate a new random P-256 key pair.

        Returns:
            KeyPair with DER-encoded, base64-encoded keys:
            ``encryption_key`` = SubjectPublicKeyInfo; ``decryption_key`` = PKCS#8.
        """
        # Generate a new P-256 key pair.
        ecc_key = ECC.generate(curve="P-256")

        # Export the public key in DER SubjectPublicKeyInfo format.
        public_der: bytes = ecc_key.public_key().export_key(format="DER")

        # Export the private key in DER PKCS#8 format.
        private_der: bytes = ecc_key.export_key(format="DER", use_pkcs8=True)

        # Base64-encode both keys.
        pair = KeyPair()
        pair.encryption_key = b64encode(public_der).decode("utf-8")
        pair.decryption_key = b64encode(private_der).decode("utf-8")
        return pair

    def _ecdh_shared_secret(
        self,
        private_scalar: int,
        public_point: ECC.EccPoint,
    ) -> bytes:
        """Perform ECDH scalar multiplication and return the x-coordinate as 32 bytes.

        Args:
            private_scalar: Private key scalar (integer).
            public_point: Peer's public key point on P-256.

        Returns:
            32-byte big-endian x-coordinate of the shared point.
        """
        # Scalar multiplication: shared_point = d * Q
        shared_point: ECC.EccPoint = private_scalar * public_point

        # Use only the x-coordinate as the shared secret (standard ECDH practice).
        shared_x: int = int(shared_point.x)
        return shared_x.to_bytes(32, byteorder="big")

    def _derive_sym_key(self, shared_secret: bytes) -> bytes:
        """Derive a 256-bit symmetric key from the ECDH shared secret using HKDF-SHA256.

        Args:
            shared_secret: 32-byte ECDH shared secret (x-coordinate).

        Returns:
            32-byte symmetric key.
        """
        # HKDF with SHA-256, no salt, no info string, output length = 32 bytes.
        return HKDF(shared_secret, 32, b"", SHA256)

    def _export_uncompressed(self, ecc_key: ECC.EccKey) -> bytes:
        """Export a P-256 public key as a 65-byte uncompressed point.

        Uncompressed format: ``0x04 || X (32 bytes) || Y (32 bytes)``

        Args:
            ecc_key: ECC key whose public portion is to be exported.

        Returns:
            65-byte uncompressed point bytes.
        """
        # Extract X and Y coordinates as big-endian 32-byte values.
        x_bytes: bytes = int(ecc_key.pointQ.x).to_bytes(32, byteorder="big")
        y_bytes: bytes = int(ecc_key.pointQ.y).to_bytes(32, byteorder="big")

        # Prepend the uncompressed-point marker 0x04.
        return b"\x04" + x_bytes + y_bytes

    def _import_uncompressed(self, point_bytes: bytes) -> ECC.EccKey:
        """Import a 65-byte uncompressed P-256 point as a public ECC key.

        Args:
            point_bytes: 65 bytes: ``0x04 || X (32) || Y (32)``.

        Returns:
            Public ECC key on P-256.

        Raises:
            CryptoUtilException: If the point bytes are not a valid uncompressed P-256 point.
        """
        if len(point_bytes) != self._EPH_PUB_LEN or point_bytes[0] != 0x04:
            raise CryptoUtilException("Invalid ephemeral public key format in payload.")

        # Parse X and Y coordinates from the uncompressed point bytes.
        x: int = int.from_bytes(point_bytes[1:33], byteorder="big")
        y: int = int.from_bytes(point_bytes[33:65], byteorder="big")

        # Reconstruct the public key object on the P-256 curve.
        return ECC.construct(curve="P-256", point_x=x, point_y=y)

    def encrypt(self, raw: str, encryption_key: str) -> str:
        """Encrypt a UTF-8 string using ECIES (P-256 ECDH + HKDF-SHA256 + AES-256-GCM).

        Args:
            raw: Plaintext string to encrypt.
            encryption_key: P-256 public key in DER SubjectPublicKeyInfo format,
                            base64-encoded.

        Returns:
            ``ephemeral_pub (65) || nonce (16) || tag (16) || ciphertext``
            encoded as a base64 string.

        Raises:
            CryptoUtilException: If encryption fails.
        """
        try:
            # --- Step 1: Import the recipient's public key ---
            pub_der: bytes = b64decode(encryption_key)
            recipient_pub: ECC.EccKey = ECC.import_key(pub_der)

            # --- Step 2: Generate a fresh ephemeral P-256 key pair ---
            eph_key: ECC.EccKey = ECC.generate(curve="P-256")

            # --- Step 3: ECDH – derive the shared secret ---
            # eph_key.d is the ephemeral private scalar (Integer object).
            shared_secret: bytes = self._ecdh_shared_secret(
                int(eph_key.d), recipient_pub.pointQ
            )

            # --- Step 4: HKDF – derive a 256-bit symmetric key ---
            sym_key: bytes = self._derive_sym_key(shared_secret)

            # --- Step 5: AES-256-GCM encryption ---
            nonce: bytes = get_random_bytes(self._NONCE_LEN)
            cipher: AES = AES.new(sym_key, AES.MODE_GCM, nonce=nonce)
            ciphertext, tag = cipher.encrypt_and_digest(raw.encode("utf-8"))

            # --- Step 6: Export the ephemeral public key as uncompressed point (65 bytes) ---
            eph_pub_bytes: bytes = self._export_uncompressed(eph_key)

            # --- Assemble the payload and base64-encode it ---
            payload: bytes = eph_pub_bytes + nonce + tag + ciphertext
            return b64encode(payload).decode("utf-8")

        except CryptoUtilException:
            raise
        except Exception as e:
            raise CryptoUtilException(f"ECIES-P256 encryption failed: {e}") from e

    def decrypt(self, encrypted: str, decryption_key: str) -> str:
        """Decrypt a payload produced by ``encrypt``.

        Args:
            encrypted: Base64-encoded payload produced by ``encrypt``.
            decryption_key: P-256 private key in DER PKCS#8 format, base64-encoded.

        Returns:
            Decrypted plaintext as a UTF-8 string.

        Raises:
            CryptoUtilException: If authentication tag verification fails
                                 (data tampered or wrong key), or any other
                                 decryption error occurs.
        """
        try:
            # --- Step 1: Import the recipient's private key ---
            priv_der: bytes = b64decode(decryption_key)
            recipient_priv: ECC.EccKey = ECC.import_key(priv_der)

            # --- Step 2: Decode and parse the binary payload ---
            payload: bytes = b64decode(encrypted)

            # Slice out each field using the defined offsets.
            eph_pub_bytes: bytes = payload[:self._EPH_PUB_LEN]                         # [0:65]
            nonce: bytes = payload[self._EPH_PUB_LEN: self._EPH_PUB_LEN + self._NONCE_LEN]  # [65:81]
            tag: bytes = payload[
                self._EPH_PUB_LEN + self._NONCE_LEN:
                self._EPH_PUB_LEN + self._NONCE_LEN + self._TAG_LEN
            ]                                                                            # [81:97]
            ciphertext: bytes = payload[self._EPH_PUB_LEN + self._NONCE_LEN + self._TAG_LEN:]  # [97:]

            # --- Step 3: Import the ephemeral public key from the 65-byte uncompressed point ---
            eph_pub: ECC.EccKey = self._import_uncompressed(eph_pub_bytes)

            # --- Step 4: ECDH – derive the shared secret ---
            # recipient_priv.d is the recipient's private scalar (Integer object).
            shared_secret: bytes = self._ecdh_shared_secret(
                int(recipient_priv.d), eph_pub.pointQ
            )

            # --- Step 5: HKDF – re-derive the same symmetric key ---
            sym_key: bytes = self._derive_sym_key(shared_secret)

            # --- Step 6: AES-256-GCM decryption with tag verification ---
            cipher: AES = AES.new(sym_key, AES.MODE_GCM, nonce=nonce)
            # decrypt_and_verify raises ValueError if the tag does not match.
            plaintext_bytes: bytes = cipher.decrypt_and_verify(ciphertext, tag)

            # Decode the resulting bytes as UTF-8 and return.
            return plaintext_bytes.decode("utf-8")

        except CryptoUtilException:
            raise
        except Exception as e:
            raise CryptoUtilException(
                f"ECIES-P256 decryption failed (tag mismatch or wrong key): {e}"
            ) from e
