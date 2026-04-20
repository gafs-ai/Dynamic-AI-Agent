from __future__ import annotations

from enum import Enum


class CryptoType(Enum):
    """Supported cryptography algorithm types.

    Specifies the algorithm to use for key generation, encryption, and decryption
    in ``CryptoUtil``.
    """

    # Symmetric: AES-256 in Galois/Counter Mode (GCM).
    # encryption_key and decryption_key in KeyPair hold the same shared key value.
    AES_256_GCM = "aes-256-gcm"

    # Asymmetric: RSA-OAEP (SHA-256, MGF1-SHA256).
    # encryption_key is the public key; decryption_key is the private key.
    RSA_OAEP = "rsa-oaep"

    # Asymmetric: ECIES over P-256 (ECDH + HKDF-SHA256 + AES-256-GCM).
    # encryption_key is the public key; decryption_key is the private key.
    ECIES_P256 = "ecies-p256"
