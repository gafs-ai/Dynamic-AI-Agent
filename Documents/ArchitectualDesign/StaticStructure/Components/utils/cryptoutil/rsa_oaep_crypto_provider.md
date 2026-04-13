---
class: RsaOaepCryptoProvider
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
| `name` | `str` | `"rsa-oaep"` | Identifier string for this provider |

## encryption scheme

| parameter | value |
|-----------|-------|
| Algorithm | RSA-OAEP |
| Key size | 2048 bits |
| Hash (OAEP) | SHA-256 |
| Mask generation function | MGF1-SHA256 |

## key format

All keys are exported in DER format and encoded as base64 strings.

| field | format | encoding |
|-------|--------|----------|
| `encryption_key` | DER SubjectPublicKeyInfo (RSA public key) | base64 |
| `decryption_key` | DER PKCS#8 (RSA private key) | base64 |

## encrypted payload format

RSA-OAEP randomization is built into the padding scheme; no separate nonce or authentication tag is embedded. The payload is the raw RSA ciphertext encoded as a base64 string.

| content | length |
|---------|--------|
| RSA-OAEP ciphertext | 256 bytes (= key size / 8) for 2048-bit keys |

## plaintext size limit

The maximum plaintext size for RSA-OAEP with SHA-256 and a 2048-bit key is:

$$\text{max} = \frac{\text{key\_size}}{8} - 2 \times \text{hash\_size} - 2 = 256 - 64 - 2 = 190 \text{ bytes}$$

Callers must ensure the UTF-8-encoded plaintext does not exceed 190 bytes.

## methods

---

### generate_key_pair

```python
def generate_key_pair() -> KeyPair
```

| property | value |
|----------|-------|
| description | Generate a new random 2048-bit RSA key pair. |

#### returns

| type | description |
|------|-------------|
| `KeyPair` | `encryption_key` = DER SubjectPublicKeyInfo base64-encoded; `decryption_key` = DER PKCS#8 base64-encoded |

#### implementation notes

1. Generate a 2048-bit RSA key pair using `Crypto.PublicKey.RSA.generate(2048)`.
2. Export the public key as DER (`export_key(format="DER")` on `key.publickey()`).
3. Export the private key as DER (`export_key(format="DER", pkcs=8)`).
4. Base64-encode both and return as `KeyPair(encryption_key=public, decryption_key=private)`.

---

### encrypt

```python
def encrypt(raw: str, encryption_key: str) -> str
```

| property | value |
|----------|-------|
| description | Encrypt a UTF-8 string using RSA-OAEP with the given encryption key. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `raw` | `str` | yes | Plaintext string to encrypt (max 190 bytes when UTF-8 encoded) |
| `encryption_key` | `str` | yes | RSA public key in DER SubjectPublicKeyInfo format, base64-encoded |

#### returns

| type | description |
|------|-------------|
| `str` | RSA-OAEP ciphertext encoded as a base64 string |

#### raises

| exception | condition |
|-----------|-----------|
| `CryptoUtilException` | Plaintext exceeds the maximum size for the given key size |

#### implementation notes

1. Decode `encryption_key` from base64 and import as an RSA public key (`RSA.import_key`).
2. Encode `raw` as UTF-8 bytes.
3. Create an OAEP cipher: `PKCS1_OAEP.new(key, hashAlgo=SHA256, mgfunc=lambda x, y: MGF1(x, y, SHA256))`.
4. Encrypt the plaintext bytes.
5. Return the ciphertext base64-encoded.

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
| `encrypted` | `str` | yes | Base64-encoded RSA-OAEP ciphertext produced by `encrypt` |
| `decryption_key` | `str` | yes | RSA private key in DER PKCS#8 format, base64-encoded |

#### returns

| type | description |
|------|-------------|
| `str` | Decrypted plaintext as a UTF-8 string |

#### raises

| exception | condition |
|-----------|-----------|
| `CryptoUtilException` | Decryption fails (wrong key or corrupted ciphertext) |

#### implementation notes

1. Decode `decryption_key` from base64 and import as an RSA private key (`RSA.import_key`).
2. Decode `encrypted` from base64.
3. Create an OAEP cipher: `PKCS1_OAEP.new(key, hashAlgo=SHA256, mgfunc=lambda x, y: MGF1(x, y, SHA256))`.
4. Decrypt the ciphertext.
   - On failure: raises `CryptoUtilException`.
5. Decode the resulting bytes as UTF-8 and return.
