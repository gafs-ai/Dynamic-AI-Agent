---
class: Aes256GcmCryptoProvider
kind: class
module: gafs.dynamicaiagent.utils.cryptoutil
implements: [ICryptoProvider]
dependencies:
  - KeyPair
exceptions_used:
  - CryptoUtilException
---

## properties

| name | type | value | description |
|------|------|-------|-------------|
| `name` | `str` | `"aes-256-gcm"` | Identifier string for this provider |

## key semantics

This is a symmetric provider. Both `encryption_key` and `decryption_key` in the returned `KeyPair` hold the **same** shared key value.

## encrypted payload format

`encrypt` produces and `decrypt` consumes the following binary layout, encoded as a single base64 string:

| offset | length | content |
|--------|--------|---------|
| 0 | 16 bytes | Nonce (randomly generated per-encryption) |
| 16 | 16 bytes | GCM authentication tag |
| 32 | variable | Ciphertext |

## methods

---

### generate_key_pair

```python
def generate_key_pair() -> KeyPair
```

| property | value |
|----------|-------|
| description | Generate a new random 256-bit AES key and return it as a symmetric `KeyPair`. |

#### returns

| type | description |
|------|-------------|
| `KeyPair` | `encryption_key` and `decryption_key` both set to the same 32 random bytes encoded as a base64 string |

#### implementation notes

1. Generate 32 random bytes using `Crypto.Random.get_random_bytes(32)`.
2. Base64-encode the bytes to produce `key`.
3. Return `KeyPair(encryption_key=key, decryption_key=key)`.

---

### encrypt

```python
def encrypt(raw: str, encryption_key: str) -> str
```

| property | value |
|----------|-------|
| description | Encrypt a UTF-8 string using AES-256-GCM. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `raw` | `str` | yes | Plaintext string to encrypt |
| `encryption_key` | `str` | yes | 256-bit AES key encoded as a base64 string |

#### returns

| type | description |
|------|-------------|
| `str` | `nonce \|\| tag \|\| ciphertext` encoded as a base64 string (see encrypted payload format) |

#### implementation notes

1. Decode `encryption_key` from base64 to bytes.
2. Encode `raw` as UTF-8 bytes.
3. Create a new AES-GCM cipher with a randomly generated nonce.
4. Encrypt the plaintext and obtain the ciphertext and 16-byte authentication tag.
5. Concatenate `nonce (16) + tag (16) + ciphertext` and return as a base64 string.

---

### decrypt

```python
def decrypt(encrypted: str, decryption_key: str) -> str
```

| property | value |
|----------|-------|
| description | Decrypt a payload produced by `encrypt`. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `encrypted` | `str` | yes | Base64-encoded payload produced by `encrypt` |
| `decryption_key` | `str` | yes | 256-bit AES key encoded as a base64 string |

#### returns

| type | description |
|------|-------------|
| `str` | Decrypted plaintext as a UTF-8 string |

#### raises

| exception | condition |
|-----------|-----------|
| `CryptoUtilException` | Authentication tag verification fails (data tampered or wrong key) |

#### implementation notes

1. Decode `decryption_key` and `encrypted` from base64 to bytes.
2. Parse the binary payload:
   - `nonce` = bytes `[0:16]`
   - `tag` = bytes `[16:32]`
   - `ciphertext` = bytes `[32:]`
3. Create a new AES-GCM cipher with the parsed nonce.
4. Decrypt the ciphertext and verify the authentication tag (`decrypt_and_verify`).
   - On tag mismatch: raises `CryptoUtilException`.
5. Decode the resulting bytes as UTF-8 and return.
