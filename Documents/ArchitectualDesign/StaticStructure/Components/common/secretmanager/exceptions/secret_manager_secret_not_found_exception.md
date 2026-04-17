---
class: SecretManagerSecretNotFoundException
kind: exception
module: gafs.dynamicaiagent.common.secretmanager.exceptions
inherits: [SecretManagerException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"SecretManagerSecretNotFoundException"` |
| `DEFAULT_MESSAGE()` | `str` | `"Secret not found."` |

## usage

- Raised when no matching `Secret` entry is found for the given id.
- Raised by `update_secret` and `delete_secret` when the target record does not exist.
