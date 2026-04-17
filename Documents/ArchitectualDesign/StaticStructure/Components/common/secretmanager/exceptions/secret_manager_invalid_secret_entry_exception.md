---
class: SecretManagerInvalidSecretEntryException
kind: exception
module: gafs.dynamicaiagent.common.secretmanager.exceptions
inherits: [SecretManagerException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"SecretManagerInvalidSecretEntryException"` |
| `DEFAULT_MESSAGE()` | `str` | `"Invalid Secret entry."` |

## usage

- Raised when the caller attempts to create or update a `Secret` entry with invalid data.
- Also raised when a key registration is attempted for a crypto type that already has a registered key.
