# cryptoutil – Test Specification

## Overview

This document describes the test suite for the `gafs.dynamicaiagent.utils.cryptoutil` component.  
All tests are located in this `test/` directory and validate the public methods of `CryptoUtil`
against the specification defined in the design document.

---

## Test Files

| File | Description |
|------|-------------|
| `test_crypto_util.py` | Unit tests for all public methods of `CryptoUtil` (source code) |
| `test_build_crypto_util.py` | Nuitka-compiled module tests (reuses `test_crypto_util.py`) |

---

## Tested Methods

All public methods exposed from the `cryptoutil` component are tested:

| Class | Method | Normal Cases | Abnormal Cases |
|-------|--------|-------------|----------------|
| `CryptoUtil` | `generate_key_pair` | ✓ (AES / RSA / ECIES) | ✓ (unsupported type) |
| `CryptoUtil` | `encrypt` | ✓ (AES / RSA / ECIES) | ✓ (unsupported type, RSA oversized) |
| `CryptoUtil` | `decrypt` | ✓ (AES / RSA / ECIES) | ✓ (tampered data, wrong key, unsupported type) |
| `KeyPair` | `to_dict` | ✓ (excludes `decryption_key`) | — |
| `KeyPair` | `to_json` | ✓ (excludes `decryption_key`) | — |
| `KeyPair` | `from_dict` | ✓ (round-trip with `to_dict`) | — |

---

## Test Case Summary

### `TestGenerateKeyPairNormal`
- AES-256-GCM: returns a `KeyPair`; `encryption_key == decryption_key` (symmetric)
- RSA-OAEP: returns a `KeyPair`; `encryption_key != decryption_key` (asymmetric)
- ECIES-P256: returns a `KeyPair`; `encryption_key != decryption_key` (asymmetric)
- Randomness: two consecutive calls produce different keys

### `TestGenerateKeyPairAbnormal`
- Unsupported `CryptoType` raises `CryptoUtilException`

### `TestEncryptDecryptAesNormal`
- Round-trip encrypt→decrypt reproduces original plaintext
- Two encryptions of the same plaintext produce different ciphertexts (random nonce)
- Empty string and Unicode strings are handled correctly

### `TestEncryptDecryptRsaNormal`
- Round-trip encrypt→decrypt reproduces original plaintext
- Maximum-size plaintext (190 bytes) encrypts and decrypts successfully
- Two encryptions of the same plaintext produce different ciphertexts (OAEP randomization)

### `TestEncryptDecryptEciesNormal`
- Round-trip encrypt→decrypt reproduces original plaintext
- Large plaintext (10 KB) is handled correctly
- Two encryptions produce different ciphertexts (ephemeral key)
- Unicode strings are handled correctly

### `TestEncryptAbnormal`
- Unsupported `CryptoType` raises `CryptoUtilException`
- RSA-OAEP plaintext exceeding 190 bytes raises `CryptoUtilException`

### `TestDecryptAbnormal`
- Tampered ciphertext raises `CryptoUtilException` (for all three algorithms)
- Wrong decryption key raises `CryptoUtilException` (for all three algorithms)
- Unsupported `CryptoType` raises `CryptoUtilException`

### `TestKeyPairSerialization`
- `to_dict` includes `encryption_key` and excludes `decryption_key`
- `from_dict` restores `encryption_key` from a dict produced by `to_dict`
- `to_json` produces JSON that includes `encryption_key` and excludes `decryption_key`

---

## External Dependencies

- **External API connections**: None (pure cryptographic operations)
- **Mocks**: None
- **Third-party library**: PyCryptodome (`pycryptodome`)

---

## How to Run

Run from the `Python/` directory:

```bash
# Source code tests
python -m pytest gafs/dynamicaiagent/utils/cryptoutil/test/test_crypto_util.py -v

# Nuitka-compiled module tests (requires prior build)
python -m pytest gafs/dynamicaiagent/utils/cryptoutil/test/test_build_crypto_util.py -v
```

---

## Test Results

All 31 tests in `test_crypto_util.py` passed successfully.

Execution environment:
- OS: Windows x64
- Python: 3.12.10
- PyCryptodome: 3.23.0
- pytest: 9.0.2
