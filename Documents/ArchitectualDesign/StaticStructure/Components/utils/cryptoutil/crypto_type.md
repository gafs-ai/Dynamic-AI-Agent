---
class: CryptoType
kind: enum
module: gafs.dynamicaiagent.utils.cryptoutil
---

## values

| name | value | kind | description |
|------|-------|------|-------------|
| `AES_256_GCM` | `"aes-256-gcm"` | symmetric | AES-256-GCM authenticated encryption. `encryption_key` and `decryption_key` in `KeyPair` hold the same shared key value. |
| `RSA_OAEP` | `"rsa-oaep"` | asymmetric | RSA-OAEP encryption (SHA-256, MGF1-SHA256). `encryption_key` is the public key; `decryption_key` is the private key. |
| `ECIES_P256` | `"ecies-p256"` | asymmetric | ECIES over P-256: ECDH key agreement + HKDF-SHA256 + AES-256-GCM. `encryption_key` is the public key; `decryption_key` is the private key. |
