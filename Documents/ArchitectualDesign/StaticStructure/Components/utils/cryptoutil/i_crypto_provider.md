---
class: ICryptoProvider
kind: abstract_class
module: gafs.dynamicaiagent.utils.cryptoutil
inherits: [ABC]
dependencies:
  - KeyPair
exceptions_used:
  - CryptoUtilException
---

## responsibilities

- Define the unified contract for all cryptography providers, symmetric and asymmetric alike.
- Each provider encapsulates a single algorithm and exposes a consistent three-method interface: `generate_key_pair`, `encrypt`, and `decrypt`.

## methods

---

### name

```python
@property
def name(self) -> str
```

| property | value |
|----------|-------|
| description | Identifier string for this provider (e.g. `"aes-256-gcm"`, `"rsa-oaep"`, `"ecies-p256"`). |

#### returns

| type | description |
|------|-------------|
| `str` | Provider identifier string |

---

### generate_key_pair

```python
def generate_key_pair() -> KeyPair
```

| property | value |
|----------|-------|
| description | Generate a new key pair for this algorithm. For symmetric providers, `encryption_key` and `decryption_key` in the returned `KeyPair` hold the same value. |

#### returns

| type | description |
|------|-------------|
| `KeyPair` | Newly generated key pair. Both fields are base64-encoded strings. |

---

### encrypt

```python
def encrypt(raw: str, encryption_key: str) -> str
```

| property | value |
|----------|-------|
| description | Encrypt plaintext using the given encryption key. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `raw` | `str` | yes | Plaintext string to encrypt |
| `encryption_key` | `str` | yes | Encryption key encoded as a base64 string (shared key for symmetric; public key for asymmetric) |

#### returns

| type | description |
|------|-------------|
| `str` | Encrypted payload. Format is provider-specific. |
#### raises

| exception | condition |
|-----------|-----------|
| `CryptoUtilException` | Encryption fails (e.g. key format invalid, plaintext exceeds size limit) |
---

### decrypt

```python
def decrypt(encrypted: str, decryption_key: str) -> str
```

| property | value |
|----------|-------|
| description | Decrypt a payload produced by `encrypt` using the given decryption key. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `encrypted` | `str` | yes | Encrypted payload produced by `encrypt` |
| `decryption_key` | `str` | yes | Decryption key encoded as a base64 string (shared key for symmetric; private key for asymmetric) |

#### returns

| type | description |
|------|-------------|
| `str` | Decrypted plaintext as a UTF-8 string |
#### raises

| exception | condition |
|-----------|-----------|
| `CryptoUtilException` | Decryption fails (e.g. key format invalid, authentication tag mismatch, corrupted ciphertext) |