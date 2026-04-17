---
class: SecretKey
kind: data_class
roles: [value_object]
module: gafs.dynamicaiagent.common.secretmanager
---

## attributes

| name | type | required | description |
|------|------|----------|-------------|
| `name` | `str` | yes | Crypto algorithm name. Must match `CryptoType.value` (e.g. `"aes-256-gcm"`). |
| `encryption_key` | `str` | yes | Key used for encryption. For symmetric algorithms, equal to `decryption_key`. |
| `decryption_key` | `str` | yes | Key used for decryption. For symmetric algorithms, equal to `encryption_key`. |

## notes

- Persisted in `secret_keys.json` under the application data folder when keys are auto-generated.
- Serialized format used in both the `secret_keys` config field and `secret_keys.json`:

```json
{
  "name": "aes-256-gcm",
  "encryption_key": "ABCD......",
  "decryption_key": "ABCD......"
}
```
