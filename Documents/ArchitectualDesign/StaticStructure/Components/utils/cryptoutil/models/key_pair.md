---
class: KeyPair
kind: data_class
roles: [value_object]
module: gafs.dynamicaiagent.utils.cryptoutil
---

## attributes

| name | type | required | description |
|------|------|----------|-------------|
| `encryption_key` | `str` | yes | Key used for encryption, encoded as a base64 string. For symmetric types, this is the shared key. For asymmetric types, this is the public key. |
| `decryption_key` | `str` | yes | Key used for decryption, encoded as a base64 string. For symmetric types, this holds the same value as `encryption_key`. For asymmetric types, this is the private key. |

## constraints

- `KeyPair` is a value object: it carries no identity and is not persisted.
- `decryption_key` must never be logged, serialized to external systems, or stored in plaintext.
- For symmetric `CryptoType` values (e.g. `AES_256_GCM`), `encryption_key` and `decryption_key` always hold the same value.
