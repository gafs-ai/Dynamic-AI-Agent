---
class: SecretManagerKeyNotFoundException
kind: exception
module: gafs.dynamicaiagent.common.secretmanager.exceptions
inherits: [SecretManagerException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"SecretManagerKeyNotFoundException"` |
| `DEFAULT_MESSAGE()` | `str` | `"Key not found for the specified crypto type."` |

## usage

- Raised when a key for the requested `CryptoType` is not registered.
