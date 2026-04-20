# cryptoutil

`gafs.dynamicaiagent.utils.cryptoutil` — Cryptography utility component.

This component provides a unified facade for symmetric and asymmetric encryption
operations. It supports three algorithms (AES-256-GCM, RSA-OAEP, ECIES-P256)
through a single, consistent API exposed by `CryptoUtil`.

---

## Quick Start

```python
from gafs.dynamicaiagent.utils.cryptoutil import CryptoUtil, CryptoType

util = CryptoUtil()

# Generate a key pair
pair = util.generate_key_pair(CryptoType.AES_256_GCM)

# Encrypt
encrypted = util.encrypt(CryptoType.AES_256_GCM, "Hello, World!", pair.encryption_key)

# Decrypt
plaintext = util.decrypt(CryptoType.AES_256_GCM, encrypted, pair.decryption_key)
```

---

## Public Classes

### `CryptoType` (Enum)

Identifies the cryptographic algorithm to use.

| Member | Value | Kind | Description |
|--------|-------|------|-------------|
| `AES_256_GCM` | `"aes-256-gcm"` | Symmetric | AES-256-GCM authenticated encryption. `encryption_key` and `decryption_key` in `KeyPair` hold the **same** shared key. |
| `RSA_OAEP` | `"rsa-oaep"` | Asymmetric | RSA-OAEP (SHA-256, MGF1-SHA256). `encryption_key` = public key; `decryption_key` = private key. Plaintext limit: **190 bytes** (UTF-8). |
| `ECIES_P256` | `"ecies-p256"` | Asymmetric | ECIES over P-256: ECDH + HKDF-SHA256 + AES-256-GCM. `encryption_key` = public key; `decryption_key` = private key. No plaintext size limit. |

---

### `KeyPair`

A value object that holds a pair of cryptographic keys. Both keys are
base64-encoded strings.

| Attribute | Type | Description |
|-----------|------|-------------|
| `encryption_key` | `str` | Key used for encryption. For symmetric types, this is the shared key. For asymmetric types, this is the public key. |
| `decryption_key` | `str` | Key used for decryption. For symmetric types, this is the same value as `encryption_key`. For asymmetric types, this is the private key. |

**Security constraint**: `decryption_key` must never be logged, serialized to
external systems, or stored in plaintext. `to_dict()` and `to_json()` intentionally
exclude `decryption_key`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `to_dict` | `to_dict() -> dict` | Returns a dict containing only `encryption_key`. |
| `to_json` | `to_json() -> str` | Returns a JSON string containing only `encryption_key`. |
| `from_dict` | `@classmethod from_dict(data: dict) -> KeyPair` | Creates a `KeyPair` from a dict. |
| `from_json` | `@classmethod from_json(json_str: str) -> KeyPair` | Creates a `KeyPair` from a JSON string. |

---

### `CryptoUtil`

Stateless facade for all cryptography operations. Selects the appropriate provider
based on the given `CryptoType` and delegates to it.

#### `generate_key_pair`

```python
def generate_key_pair(crypto_type: CryptoType) -> KeyPair
```

Generate a new key pair for the specified algorithm.

| Parameter | Type | Description |
|-----------|------|-------------|
| `crypto_type` | `CryptoType` | Algorithm for which to generate the key pair. |

**Returns**: `KeyPair` — both fields are base64-encoded strings.  
For symmetric types, `encryption_key == decryption_key`.

**Raises**: `CryptoUtilException` — if `crypto_type` is not a supported algorithm.

---

#### `encrypt`

```python
def encrypt(crypto_type: CryptoType, raw: str, encryption_key: str) -> str
```

Encrypt plaintext using the specified algorithm and encryption key.

| Parameter | Type | Description |
|-----------|------|-------------|
| `crypto_type` | `CryptoType` | Algorithm to use. |
| `raw` | `str` | Plaintext string to encrypt. |
| `encryption_key` | `str` | Base64-encoded encryption key (shared key for AES; public key for RSA/ECIES). |

**Returns**: `str` — encrypted payload as a base64 string. Format is algorithm-specific.

**Raises**: `CryptoUtilException` — if `crypto_type` is not supported, the key is
invalid, or the plaintext exceeds the algorithm's size limit (RSA-OAEP: 190 bytes).

---

#### `decrypt`

```python
def decrypt(crypto_type: CryptoType, encrypted: str, decryption_key: str) -> str
```

Decrypt a payload using the specified algorithm and decryption key.

| Parameter | Type | Description |
|-----------|------|-------------|
| `crypto_type` | `CryptoType` | Algorithm that was used for encryption. |
| `encrypted` | `str` | Encrypted payload produced by `encrypt`. |
| `decryption_key` | `str` | Base64-encoded decryption key (shared key for AES; private key for RSA/ECIES). |

**Returns**: `str` — decrypted plaintext as a UTF-8 string.

**Raises**: `CryptoUtilException` — if `crypto_type` is not supported, the key is wrong,
the ciphertext is corrupted, or authentication tag verification fails.

---

### `CryptoUtilException`

Base exception class for all errors raised by this component. Inherits from
`Exception`.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | `"Unexpected Error in Crypto Util."` | Human-readable error description. |

---

## Algorithm Details

### AES-256-GCM

- **Type**: Symmetric
- **Key size**: 256 bits (32 bytes)
- **Nonce**: 16 bytes, randomly generated per encryption
- **Authentication tag**: 16 bytes
- **Payload format**: `nonce (16) || tag (16) || ciphertext` (base64-encoded)
- **Plaintext limit**: None

### RSA-OAEP

- **Type**: Asymmetric
- **Key size**: 2048 bits
- **Hash**: SHA-256
- **Mask generation function**: MGF1-SHA256
- **Key format**: DER SubjectPublicKeyInfo (public) / DER PKCS#8 (private), both base64-encoded
- **Payload format**: Raw RSA ciphertext (256 bytes), base64-encoded
- **Plaintext limit**: **190 bytes** (UTF-8 encoded)

### ECIES-P256

- **Type**: Asymmetric
- **Key agreement**: P-256 (secp256r1) ECDH
- **Key derivation**: HKDF-SHA256
- **Symmetric cipher**: AES-256-GCM
- **Key format**: DER SubjectPublicKeyInfo (public) / DER PKCS#8 (private), both base64-encoded
- **Payload format**: `ephemeral_pub (65) || nonce (16) || tag (16) || ciphertext` (base64-encoded)
- **Plaintext limit**: None

---

## Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| `pycryptodome` | ≥ 3.0 | BSD 2-Clause | AES-GCM, RSA-OAEP, ECC, HKDF |

Install:
```bash
pip install pycryptodome
```

---

## File Structure

```
cryptoutil/
├── __init__.py                       – Public exports
├── crypto_type.py                    – CryptoType enum
├── key_pair.py                       – KeyPair data class
├── i_crypto_provider.py              – ICryptoProvider abstract interface
├── aes_256_gcm_crypto_provider.py    – AES-256-GCM implementation
├── rsa_oaep_crypto_provider.py       – RSA-OAEP implementation
├── ecies_p256_crypto_provider.py     – ECIES-P256 implementation
├── crypto_util.py                    – CryptoUtil facade
├── build_nuitka.py                   – Nuitka build script
├── exceptions/
│   ├── __init__.py
│   └── crypto_util_exception.py      – CryptoUtilException
└── test/
    ├── README.md                     – Test specification
    ├── test_crypto_util.py           – pytest tests (source)
    └── test_build_crypto_util.py     – pytest tests (Nuitka compiled)
```
