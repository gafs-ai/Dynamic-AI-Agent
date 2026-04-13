---
class: EciesP256CryptoProvider
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
| `name` | `str` | `"ecies-p256"` | Identifier string for this provider |

## encryption scheme

This provider implements ECIES (Elliptic Curve Integrated Encryption Scheme) using the following construction:

| step | algorithm | purpose |
|------|-----------|---------|
| Key agreement | P-256 (secp256r1) ECDH | Derive a shared secret from an ephemeral private key and the encryption key |
| Key derivation | HKDF-SHA256 | Derive a 256-bit symmetric key from the shared secret |
| Symmetric encryption | AES-256-GCM | Encrypt the plaintext with the derived symmetric key |

## key format

All keys are exported in DER format and encoded as base64 strings.

| field | format | encoding |
|-------|--------|----------|
| `encryption_key` | DER SubjectPublicKeyInfo (P-256 uncompressed point) | base64 |
| `decryption_key` | DER PKCS#8 (P-256 private key) | base64 |

## encrypted payload format

`encrypt` produces and `decrypt` consumes the following binary layout, encoded as a single base64 string:

| offset | length | content |
|--------|--------|---------|
| 0 | 65 bytes | Ephemeral P-256 public key (uncompressed: `0x04 \|\| X \|\| Y`) |
| 65 | 16 bytes | AES-GCM nonce |
| 81 | 16 bytes | AES-GCM authentication tag |
| 97 | variable | Ciphertext |

## methods

---

### generate_key_pair

```python
def generate_key_pair() -> KeyPair
```

| property | value |
|----------|-------|
| description | Generate a new random P-256 key pair. |

#### returns

| type | description |
|------|-------------|
| `KeyPair` | `encryption_key` = DER SubjectPublicKeyInfo base64-encoded; `decryption_key` = DER PKCS#8 base64-encoded |

#### implementation notes

1. Generate a P-256 key pair using `ECC.generate(curve="P-256")`.
2. Export the public key as DER SubjectPublicKeyInfo (`export_key(format="DER")`).
3. Export the private key as DER PKCS#8 (`export_key(format="DER", use_pkcs8=True)`).
4. Base64-encode both and return as `KeyPair(encryption_key=public, decryption_key=private)`.

---

### encrypt

```python
def encrypt(raw: str, encryption_key: str) -> str
```

| property | value |
|----------|-------|
| description | Encrypt a UTF-8 string using ECIES with the given encryption key. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `raw` | `str` | yes | Plaintext string to encrypt |
| `encryption_key` | `str` | yes | P-256 public key in DER SubjectPublicKeyInfo format, base64-encoded |

#### returns

| type | description |
|------|-------------|
| `str` | `ephemeral_public_key (65) \|\| nonce (16) \|\| tag (16) \|\| ciphertext` encoded as a base64 string (see encrypted payload format) |

#### implementation notes

1. Decode `encryption_key` from base64 and import as a P-256 ECC key (`ECC.import_key`).
2. Generate an ephemeral P-256 key pair (`ECC.generate(curve="P-256")`).
3. Perform ECDH: multiply the encryption key point by the ephemeral private key scalar. Use the x-coordinate (32 bytes) as `shared_secret`.
4. Derive a 256-bit symmetric key: `sym_key = HKDF(shared_secret, 32, b"", SHA256)`.
5. Generate a random 16-byte AES-GCM nonce.
6. Encrypt `raw` (UTF-8 encoded) with AES-256-GCM using `sym_key` and the nonce, producing `ciphertext` and `tag`.
7. Export the ephemeral public key as an uncompressed point (65 bytes).
8. Concatenate `ephemeral_public_key (65) + nonce (16) + tag (16) + ciphertext` and return as a base64 string.

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
| `encrypted` | `str` | yes | Base64-encoded payload produced by `encrypt` |
| `decryption_key` | `str` | yes | P-256 private key in DER PKCS#8 format, base64-encoded |

#### returns

| type | description |
|------|-------------|
| `str` | Decrypted plaintext as a UTF-8 string |

#### raises

| exception | condition |
|-----------|-----------|
| `CryptoUtilException` | Authentication tag verification fails (data tampered or wrong key) |

#### implementation notes

1. Decode `decryption_key` from base64 and import as a P-256 ECC key (`ECC.import_key`).
2. Decode `encrypted` from base64 and parse the binary payload (see encrypted payload format):
   - `ephemeral_public_key` = bytes `[0:65]`
   - `nonce` = bytes `[65:81]`
   - `tag` = bytes `[81:97]`
   - `ciphertext` = bytes `[97:]`
3. Import the ephemeral public key from the 65-byte uncompressed point.
4. Perform ECDH: multiply the ephemeral public key point by the decryption key scalar. Use the x-coordinate (32 bytes) as `shared_secret`.
5. Derive the symmetric key: `sym_key = HKDF(shared_secret, 32, b"", SHA256)`.
6. Decrypt using AES-256-GCM with `sym_key` and the parsed `nonce`, verifying `tag`.
   - On tag mismatch: raises `CryptoUtilException`.
7. Decode the resulting bytes as UTF-8 and return.
