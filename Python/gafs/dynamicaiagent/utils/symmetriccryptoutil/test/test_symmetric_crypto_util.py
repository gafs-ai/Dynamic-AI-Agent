from __future__ import annotations

# Use relative import to match the package structure
from .. import SymmetricCryptoUtil, SymmetricCryptoType


def test_encrypt_decrypt_normal() -> None:
    """Normal: verify that data can be encrypted and decrypted with a generated key."""
    util = SymmetricCryptoUtil()
    key = util.generate_key(SymmetricCryptoType.AES_256_GCM)

    raw = "hello symmetric crypto"

    print("[TEST] test_encrypt_decrypt_normal")
    print("  Method: generate_key -> encrypt -> decrypt")
    print(f"  Input (plain text): {raw!r}")
    print(f"  Input (crypto type): {SymmetricCryptoType.AES_256_GCM!r}")

    encrypted = util.encrypt(SymmetricCryptoType.AES_256_GCM, raw, key)
    print(f"  Output (encrypted): {encrypted!r}")

    decrypted = util.decrypt(SymmetricCryptoType.AES_256_GCM, encrypted, key)
    print(f"  Output (decrypted): {decrypted!r}")

    assert decrypted == raw
    print("  Result: SUCCESS (decrypted text matches original)")


def test_encrypt_unsupported_type() -> None:
    """Abnormal: verify that encrypt raises ValueError for unsupported crypto type."""

    class DummyType:
        AES_256_GCM = "dummy"

    util = SymmetricCryptoUtil()
    key = util.generate_key(SymmetricCryptoType.AES_256_GCM)

    print("[TEST] test_encrypt_unsupported_type")
    print("  Method: encrypt")
    print(f"  Input (crypto type): {DummyType.AES_256_GCM!r} (unsupported type)")
    print("  Input (plain text): 'data'")

    try:
        util.encrypt(DummyType.AES_256_GCM, "data", key)  # type: ignore[arg-type]
        print("  Output: NO ERROR (unexpected)")
        assert False, "encrypt must not succeed with an unsupported crypto type"
    except ValueError as e:
        print(f"  Error: ValueError as expected: {e!r}")
        print("  Result: SUCCESS (raised ValueError for unsupported type)")


def test_decrypt_tampered_data() -> None:
    """Abnormal: verify that decrypt fails when ciphertext has been tampered."""
    util = SymmetricCryptoUtil()
    key = util.generate_key(SymmetricCryptoType.AES_256_GCM)

    raw = "hello symmetric crypto"

    print("[TEST] test_decrypt_tampered_data")
    print("  Method: encrypt -> decrypt")
    print(f"  Input (plain text): {raw!r}")

    encrypted = util.encrypt(SymmetricCryptoType.AES_256_GCM, raw, key)
    print(f"  Original encrypted text: {encrypted!r}")

    # Intentionally tamper with the ciphertext (flip last few bytes)
    tampered_bytes = bytearray(encrypted.encode("utf-8"))
    if len(tampered_bytes) > 4:
        for i in range(1, 5):
            tampered_bytes[-i] ^= 0xFF
    tampered = tampered_bytes.decode("utf-8", errors="ignore")

    print(f"  Tampered encrypted text: {tampered!r}")

    try:
        util.decrypt(SymmetricCryptoType.AES_256_GCM, tampered, key)
        print("  Output: NO ERROR (unexpected)")
        assert False, "decrypt must not succeed with tampered ciphertext"
    except Exception as e:  # noqa: BLE001
        print(f"  Error: exception raised as expected: {e!r}")
        print("  Result: SUCCESS (decrypt failed for tampered ciphertext)")


if __name__ == "__main__":
    # Simple manual runner
    print("=== symmetric_crypto_util manual tests start ===")
    test_encrypt_decrypt_normal()
    print()
    test_encrypt_unsupported_type()
    print()
    test_decrypt_tampered_data()
    print("=== symmetric_crypto_util manual tests completed ===")

