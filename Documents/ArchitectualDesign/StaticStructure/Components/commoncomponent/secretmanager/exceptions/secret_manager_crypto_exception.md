---
class: SecretManagerCryptoException
kind: exception
module: gafs.dynamicaiagent.common.secretmanager.exceptions
inherits: [SecretManagerException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"SecretManagerCryptoException"` |
| `DEFAULT_MESSAGE()` | `str` | `"A cryptographic operation in Secret Manager failed."` |

## usage

- Raised when encryption or decryption of a secret value fails.
