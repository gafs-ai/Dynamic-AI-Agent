---
class: CryptoUtil
kind: class
module: gafs.dynamicaiagent.utils.cryptoutil
dependencies:
  - CryptoType
  - KeyPair
exceptions_used:
  - CryptoUtilException
---

## responsibilities

- Unified facade for all cryptography operations, both symmetric and asymmetric.
- Selects the appropriate `ICryptoProvider` implementation based on the given `CryptoType` and delegates all operations to it.
- Stateless: no internal state is held between calls.

## provider dispatch

| `CryptoType` | provider |
|--------------|----------|
| `AES_256_GCM` | `Aes256GcmCryptoProvider` |
| `RSA_OAEP` | `RsaOaepCryptoProvider` |
| `ECIES_P256` | `EciesP256CryptoProvider` |

## methods

---

### generate_key_pair

```python
def generate_key_pair(crypto_type: CryptoType) -> KeyPair
```

| property | value |
|----------|-------|
| description | Generate a new key pair for the specified algorithm. For symmetric types, `encryption_key` and `decryption_key` in the returned `KeyPair` hold the same value. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `crypto_type` | `CryptoType` | yes | Algorithm for which to generate the key pair |

#### returns

| type | description |
|------|-------------|
| `KeyPair` | Newly generated key pair. Both fields are base64-encoded strings. |

#### raises

| exception | condition |
|-----------|-----------|
| `CryptoUtilException` | `crypto_type` is not a supported algorithm |

#### implementation notes

1. Instantiate the provider for `crypto_type` (see provider dispatch table).
   - If `crypto_type` is not listed: raise `CryptoUtilException`.
2. Return the result of `provider.generate_key_pair()`.

---

### encrypt

```python
def encrypt(crypto_type: CryptoType, raw: str, encryption_key: str) -> str
```

| property | value |
|----------|-------|
| description | Encrypt plaintext using the specified algorithm and encryption key. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `crypto_type` | `CryptoType` | yes | Algorithm to use for encryption |
| `raw` | `str` | yes | Plaintext string to encrypt |
| `encryption_key` | `str` | yes | Encryption key encoded as a base64 string |

#### returns

| type | description |
|------|-------------|
| `str` | Encrypted payload as a base64 string. Format is provider-specific. |

#### raises

| exception | condition |
|-----------|-----------|
| `CryptoUtilException` | `crypto_type` is not a supported algorithm, or the provider raises an exception (e.g. key format invalid, plaintext exceeds size limit) |

#### implementation notes

1. Instantiate the provider for `crypto_type` (see provider dispatch table).
   - If `crypto_type` is not listed: raise `CryptoUtilException`.
2. Return the result of `provider.encrypt(raw, encryption_key)`.

---

### decrypt

```python
def decrypt(crypto_type: CryptoType, encrypted: str, decryption_key: str) -> str
```

| property | value |
|----------|-------|
| description | Decrypt a payload using the specified algorithm and decryption key. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `crypto_type` | `CryptoType` | yes | Algorithm that was used for encryption |
| `encrypted` | `str` | yes | Encrypted payload produced by `encrypt` |
| `decryption_key` | `str` | yes | Decryption key encoded as a base64 string |

#### returns

| type | description |
|------|-------------|
| `str` | Decrypted plaintext as a UTF-8 string |

#### raises

| exception | condition |
|-----------|-----------|
| `CryptoUtilException` | `crypto_type` is not a supported algorithm, or the provider raises an exception (e.g. authentication tag mismatch, wrong key, corrupted ciphertext) |

#### implementation notes

1. Instantiate the provider for `crypto_type` (see provider dispatch table).
   - If `crypto_type` is not listed: raise `CryptoUtilException`.
2. Return the result of `provider.decrypt(encrypted, decryption_key)`.
