"""Tests for gafs.dynamicaiagent.utils.cryptoutil.

This module tests all public methods of ``CryptoUtil`` against the specification
defined in the design document. Both normal and abnormal cases are covered for
each supported algorithm (AES-256-GCM, RSA-OAEP, ECIES-P256).

External API connections: None (pure cryptography operations).
Mocks: None.
"""
from __future__ import annotations

import pytest

from gafs.dynamicaiagent.utils.cryptoutil import (
    CryptoType,
    CryptoUtil,
    CryptoUtilException,
    KeyPair,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _UnsupportedType:
    """A dummy type that is not a valid CryptoType, used for abnormal-case tests."""
    pass


_UTIL = CryptoUtil()


# ---------------------------------------------------------------------------
# CryptoUtil.generate_key_pair – normal cases
# ---------------------------------------------------------------------------

class TestGenerateKeyPairNormal:
    """Normal cases for CryptoUtil.generate_key_pair."""

    def test_aes_256_gcm_returns_key_pair(self) -> None:
        """AES-256-GCM: generate_key_pair returns a KeyPair with non-empty keys."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)

        print("[TEST] generate_key_pair / AES-256-GCM")
        print(f"  encryption_key: {pair.encryption_key!r}")

        assert isinstance(pair, KeyPair)
        assert pair.encryption_key is not None and len(pair.encryption_key) > 0
        assert pair.decryption_key is not None and len(pair.decryption_key) > 0

    def test_aes_256_gcm_symmetric_keys_are_equal(self) -> None:
        """AES-256-GCM: encryption_key and decryption_key must be the same value."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)

        print("[TEST] generate_key_pair / AES-256-GCM symmetric")
        print(f"  encryption_key == decryption_key: {pair.encryption_key == pair.decryption_key}")

        assert pair.encryption_key == pair.decryption_key

    def test_rsa_oaep_returns_key_pair(self) -> None:
        """RSA-OAEP: generate_key_pair returns a KeyPair with non-empty keys."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.RSA_OAEP)

        print("[TEST] generate_key_pair / RSA-OAEP")
        print(f"  encryption_key length: {len(pair.encryption_key)}")

        assert isinstance(pair, KeyPair)
        assert pair.encryption_key is not None and len(pair.encryption_key) > 0
        assert pair.decryption_key is not None and len(pair.decryption_key) > 0

    def test_rsa_oaep_keys_are_different(self) -> None:
        """RSA-OAEP: encryption_key (public) and decryption_key (private) must differ."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.RSA_OAEP)

        print("[TEST] generate_key_pair / RSA-OAEP asymmetric")
        print(f"  encryption_key != decryption_key: {pair.encryption_key != pair.decryption_key}")

        assert pair.encryption_key != pair.decryption_key

    def test_ecies_p256_returns_key_pair(self) -> None:
        """ECIES-P256: generate_key_pair returns a KeyPair with non-empty keys."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.ECIES_P256)

        print("[TEST] generate_key_pair / ECIES-P256")
        print(f"  encryption_key length: {len(pair.encryption_key)}")

        assert isinstance(pair, KeyPair)
        assert pair.encryption_key is not None and len(pair.encryption_key) > 0
        assert pair.decryption_key is not None and len(pair.decryption_key) > 0

    def test_ecies_p256_keys_are_different(self) -> None:
        """ECIES-P256: encryption_key (public) and decryption_key (private) must differ."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.ECIES_P256)

        print("[TEST] generate_key_pair / ECIES-P256 asymmetric")
        print(f"  encryption_key != decryption_key: {pair.encryption_key != pair.decryption_key}")

        assert pair.encryption_key != pair.decryption_key

    def test_generate_two_aes_key_pairs_different(self) -> None:
        """AES-256-GCM: two consecutive generate_key_pair calls must produce different keys."""
        pair1: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)
        pair2: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)

        print("[TEST] generate_key_pair / randomness check")
        print(f"  pair1.encryption_key != pair2.encryption_key: {pair1.encryption_key != pair2.encryption_key}")

        assert pair1.encryption_key != pair2.encryption_key


# ---------------------------------------------------------------------------
# CryptoUtil.generate_key_pair – abnormal cases
# ---------------------------------------------------------------------------

class TestGenerateKeyPairAbnormal:
    """Abnormal cases for CryptoUtil.generate_key_pair."""

    def test_unsupported_type_raises_exception(self) -> None:
        """generate_key_pair with an unsupported type must raise CryptoUtilException."""
        dummy = _UnsupportedType()

        print("[TEST] generate_key_pair / unsupported type")

        with pytest.raises(CryptoUtilException):
            _UTIL.generate_key_pair(dummy)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# CryptoUtil.encrypt / decrypt – normal cases
# ---------------------------------------------------------------------------

class TestEncryptDecryptAesNormal:
    """Normal encrypt/decrypt round-trip tests for AES-256-GCM."""

    def test_round_trip(self) -> None:
        """AES-256-GCM: encrypt then decrypt must reproduce the original plaintext."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)
        raw: str = "Hello, AES-256-GCM!"

        print("[TEST] AES-256-GCM round-trip")
        print(f"  plaintext: {raw!r}")

        encrypted: str = _UTIL.encrypt(CryptoType.AES_256_GCM, raw, pair.encryption_key)
        print(f"  encrypted: {encrypted!r}")

        decrypted: str = _UTIL.decrypt(CryptoType.AES_256_GCM, encrypted, pair.decryption_key)
        print(f"  decrypted: {decrypted!r}")

        assert decrypted == raw

    def test_encrypt_same_plaintext_produces_different_ciphertext(self) -> None:
        """AES-256-GCM: encrypting the same plaintext twice must produce different ciphertexts (random nonce)."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)
        raw: str = "same message"

        encrypted1: str = _UTIL.encrypt(CryptoType.AES_256_GCM, raw, pair.encryption_key)
        encrypted2: str = _UTIL.encrypt(CryptoType.AES_256_GCM, raw, pair.encryption_key)

        print("[TEST] AES-256-GCM random nonce check")
        print(f"  encrypted1 != encrypted2: {encrypted1 != encrypted2}")

        assert encrypted1 != encrypted2

    def test_empty_string(self) -> None:
        """AES-256-GCM: round-trip with an empty plaintext must succeed."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)
        raw: str = ""

        encrypted: str = _UTIL.encrypt(CryptoType.AES_256_GCM, raw, pair.encryption_key)
        decrypted: str = _UTIL.decrypt(CryptoType.AES_256_GCM, encrypted, pair.decryption_key)

        print("[TEST] AES-256-GCM empty string round-trip")

        assert decrypted == raw

    def test_unicode_string(self) -> None:
        """AES-256-GCM: round-trip with a Unicode plaintext must succeed."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)
        raw: str = "日本語テスト 🔐"

        encrypted: str = _UTIL.encrypt(CryptoType.AES_256_GCM, raw, pair.encryption_key)
        decrypted: str = _UTIL.decrypt(CryptoType.AES_256_GCM, encrypted, pair.decryption_key)

        print("[TEST] AES-256-GCM Unicode round-trip")

        assert decrypted == raw


class TestEncryptDecryptRsaNormal:
    """Normal encrypt/decrypt round-trip tests for RSA-OAEP."""

    def test_round_trip(self) -> None:
        """RSA-OAEP: encrypt then decrypt must reproduce the original plaintext."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.RSA_OAEP)
        raw: str = "Hello, RSA-OAEP!"

        print("[TEST] RSA-OAEP round-trip")
        print(f"  plaintext: {raw!r}")

        encrypted: str = _UTIL.encrypt(CryptoType.RSA_OAEP, raw, pair.encryption_key)
        print(f"  encrypted length: {len(encrypted)}")

        decrypted: str = _UTIL.decrypt(CryptoType.RSA_OAEP, encrypted, pair.decryption_key)
        print(f"  decrypted: {decrypted!r}")

        assert decrypted == raw

    def test_max_size_plaintext(self) -> None:
        """RSA-OAEP: a 190-byte ASCII plaintext must encrypt and decrypt successfully."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.RSA_OAEP)
        # 190 ASCII characters = 190 UTF-8 bytes (the maximum).
        raw: str = "A" * 190

        print("[TEST] RSA-OAEP max-size plaintext")

        encrypted: str = _UTIL.encrypt(CryptoType.RSA_OAEP, raw, pair.encryption_key)
        decrypted: str = _UTIL.decrypt(CryptoType.RSA_OAEP, encrypted, pair.decryption_key)

        assert decrypted == raw

    def test_encrypt_same_plaintext_produces_different_ciphertext(self) -> None:
        """RSA-OAEP: encrypting the same plaintext twice must produce different ciphertexts (OAEP randomization)."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.RSA_OAEP)
        raw: str = "same message"

        encrypted1: str = _UTIL.encrypt(CryptoType.RSA_OAEP, raw, pair.encryption_key)
        encrypted2: str = _UTIL.encrypt(CryptoType.RSA_OAEP, raw, pair.encryption_key)

        print("[TEST] RSA-OAEP randomization check")
        print(f"  encrypted1 != encrypted2: {encrypted1 != encrypted2}")

        assert encrypted1 != encrypted2


class TestEncryptDecryptEciesNormal:
    """Normal encrypt/decrypt round-trip tests for ECIES-P256."""

    def test_round_trip(self) -> None:
        """ECIES-P256: encrypt then decrypt must reproduce the original plaintext."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.ECIES_P256)
        raw: str = "Hello, ECIES-P256!"

        print("[TEST] ECIES-P256 round-trip")
        print(f"  plaintext: {raw!r}")

        encrypted: str = _UTIL.encrypt(CryptoType.ECIES_P256, raw, pair.encryption_key)
        print(f"  encrypted length: {len(encrypted)}")

        decrypted: str = _UTIL.decrypt(CryptoType.ECIES_P256, encrypted, pair.decryption_key)
        print(f"  decrypted: {decrypted!r}")

        assert decrypted == raw

    def test_large_plaintext(self) -> None:
        """ECIES-P256: a large plaintext (10 KB) must encrypt and decrypt successfully."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.ECIES_P256)
        raw: str = "X" * 10240

        print("[TEST] ECIES-P256 large plaintext (10 KB)")

        encrypted: str = _UTIL.encrypt(CryptoType.ECIES_P256, raw, pair.encryption_key)
        decrypted: str = _UTIL.decrypt(CryptoType.ECIES_P256, encrypted, pair.decryption_key)

        assert decrypted == raw

    def test_encrypt_same_plaintext_produces_different_ciphertext(self) -> None:
        """ECIES-P256: encrypting the same plaintext twice must produce different ciphertexts (ephemeral key)."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.ECIES_P256)
        raw: str = "same message"

        encrypted1: str = _UTIL.encrypt(CryptoType.ECIES_P256, raw, pair.encryption_key)
        encrypted2: str = _UTIL.encrypt(CryptoType.ECIES_P256, raw, pair.encryption_key)

        print("[TEST] ECIES-P256 ephemeral key randomness check")
        print(f"  encrypted1 != encrypted2: {encrypted1 != encrypted2}")

        assert encrypted1 != encrypted2

    def test_unicode_string(self) -> None:
        """ECIES-P256: round-trip with a Unicode plaintext must succeed."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.ECIES_P256)
        raw: str = "暗号化テスト 🛡️ ECIES-P256"

        encrypted: str = _UTIL.encrypt(CryptoType.ECIES_P256, raw, pair.encryption_key)
        decrypted: str = _UTIL.decrypt(CryptoType.ECIES_P256, encrypted, pair.decryption_key)

        print("[TEST] ECIES-P256 Unicode round-trip")

        assert decrypted == raw


# ---------------------------------------------------------------------------
# CryptoUtil.encrypt / decrypt – abnormal cases
# ---------------------------------------------------------------------------

class TestEncryptAbnormal:
    """Abnormal cases for CryptoUtil.encrypt."""

    def test_aes_unsupported_type_raises_exception(self) -> None:
        """encrypt with an unsupported type must raise CryptoUtilException."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)

        print("[TEST] encrypt / unsupported type")

        with pytest.raises(CryptoUtilException):
            _UTIL.encrypt(_UnsupportedType(), "data", pair.encryption_key)  # type: ignore[arg-type]

    def test_rsa_plaintext_too_large_raises_exception(self) -> None:
        """RSA-OAEP: a plaintext exceeding 190 bytes must raise CryptoUtilException."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.RSA_OAEP)
        # 191 ASCII characters = 191 UTF-8 bytes, which exceeds the 190-byte limit.
        oversized: str = "A" * 191

        print("[TEST] RSA-OAEP oversized plaintext")

        with pytest.raises(CryptoUtilException):
            _UTIL.encrypt(CryptoType.RSA_OAEP, oversized, pair.encryption_key)


class TestDecryptAbnormal:
    """Abnormal cases for CryptoUtil.decrypt."""

    def test_aes_tampered_data_raises_exception(self) -> None:
        """AES-256-GCM: decrypting tampered ciphertext must raise CryptoUtilException."""
        import base64

        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)
        encrypted: str = _UTIL.encrypt(CryptoType.AES_256_GCM, "secret", pair.encryption_key)

        # Flip the last byte of the base64-decoded payload to simulate tampering.
        raw_bytes = bytearray(base64.b64decode(encrypted))
        raw_bytes[-1] ^= 0xFF
        tampered: str = base64.b64encode(bytes(raw_bytes)).decode("utf-8")

        print("[TEST] AES-256-GCM tampered ciphertext")

        with pytest.raises(CryptoUtilException):
            _UTIL.decrypt(CryptoType.AES_256_GCM, tampered, pair.decryption_key)

    def test_aes_wrong_key_raises_exception(self) -> None:
        """AES-256-GCM: decrypting with a different key must raise CryptoUtilException."""
        pair1: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)
        pair2: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)
        encrypted: str = _UTIL.encrypt(CryptoType.AES_256_GCM, "secret", pair1.encryption_key)

        print("[TEST] AES-256-GCM wrong key")

        with pytest.raises(CryptoUtilException):
            _UTIL.decrypt(CryptoType.AES_256_GCM, encrypted, pair2.decryption_key)

    def test_rsa_tampered_data_raises_exception(self) -> None:
        """RSA-OAEP: decrypting tampered ciphertext must raise CryptoUtilException."""
        import base64

        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.RSA_OAEP)
        encrypted: str = _UTIL.encrypt(CryptoType.RSA_OAEP, "secret", pair.encryption_key)

        # Flip the last byte of the base64-decoded payload.
        raw_bytes = bytearray(base64.b64decode(encrypted))
        raw_bytes[-1] ^= 0xFF
        tampered: str = base64.b64encode(bytes(raw_bytes)).decode("utf-8")

        print("[TEST] RSA-OAEP tampered ciphertext")

        with pytest.raises(CryptoUtilException):
            _UTIL.decrypt(CryptoType.RSA_OAEP, tampered, pair.decryption_key)

    def test_rsa_wrong_key_raises_exception(self) -> None:
        """RSA-OAEP: decrypting with a different key must raise CryptoUtilException."""
        pair1: KeyPair = _UTIL.generate_key_pair(CryptoType.RSA_OAEP)
        pair2: KeyPair = _UTIL.generate_key_pair(CryptoType.RSA_OAEP)
        encrypted: str = _UTIL.encrypt(CryptoType.RSA_OAEP, "secret", pair1.encryption_key)

        print("[TEST] RSA-OAEP wrong key")

        with pytest.raises(CryptoUtilException):
            _UTIL.decrypt(CryptoType.RSA_OAEP, encrypted, pair2.decryption_key)

    def test_ecies_tampered_data_raises_exception(self) -> None:
        """ECIES-P256: decrypting tampered ciphertext must raise CryptoUtilException."""
        import base64

        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.ECIES_P256)
        encrypted: str = _UTIL.encrypt(CryptoType.ECIES_P256, "secret", pair.encryption_key)

        # Flip the last byte of the ciphertext section to simulate tampering.
        raw_bytes = bytearray(base64.b64decode(encrypted))
        raw_bytes[-1] ^= 0xFF
        tampered: str = base64.b64encode(bytes(raw_bytes)).decode("utf-8")

        print("[TEST] ECIES-P256 tampered ciphertext")

        with pytest.raises(CryptoUtilException):
            _UTIL.decrypt(CryptoType.ECIES_P256, tampered, pair.decryption_key)

    def test_ecies_wrong_key_raises_exception(self) -> None:
        """ECIES-P256: decrypting with a different key must raise CryptoUtilException."""
        pair1: KeyPair = _UTIL.generate_key_pair(CryptoType.ECIES_P256)
        pair2: KeyPair = _UTIL.generate_key_pair(CryptoType.ECIES_P256)
        encrypted: str = _UTIL.encrypt(CryptoType.ECIES_P256, "secret", pair1.encryption_key)

        print("[TEST] ECIES-P256 wrong key")

        with pytest.raises(CryptoUtilException):
            _UTIL.decrypt(CryptoType.ECIES_P256, encrypted, pair2.decryption_key)

    def test_unsupported_type_raises_exception(self) -> None:
        """decrypt with an unsupported type must raise CryptoUtilException."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)
        encrypted: str = _UTIL.encrypt(CryptoType.AES_256_GCM, "data", pair.encryption_key)

        print("[TEST] decrypt / unsupported type")

        with pytest.raises(CryptoUtilException):
            _UTIL.decrypt(_UnsupportedType(), encrypted, pair.decryption_key)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# KeyPair – serialization tests
# ---------------------------------------------------------------------------

class TestKeyPairSerialization:
    """Tests for KeyPair.to_dict, to_json, from_dict, from_json."""

    def test_to_dict_excludes_decryption_key(self) -> None:
        """to_dict must include encryption_key but not decryption_key."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)
        d = pair.to_dict()

        print("[TEST] KeyPair.to_dict excludes decryption_key")
        print(f"  keys in dict: {list(d.keys())}")

        assert "encryption_key" in d
        assert "decryption_key" not in d

    def test_from_dict_round_trip(self) -> None:
        """from_dict must restore encryption_key from a dict produced by to_dict."""
        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)
        d = pair.to_dict()
        restored: KeyPair = KeyPair.from_dict(d)

        print("[TEST] KeyPair.from_dict round-trip")

        assert restored.encryption_key == pair.encryption_key

    def test_to_json_excludes_decryption_key(self) -> None:
        """to_json must produce JSON that does not contain decryption_key."""
        import json

        pair: KeyPair = _UTIL.generate_key_pair(CryptoType.AES_256_GCM)
        json_str: str = pair.to_json()
        parsed = json.loads(json_str)

        print("[TEST] KeyPair.to_json excludes decryption_key")

        assert "encryption_key" in parsed
        assert "decryption_key" not in parsed
