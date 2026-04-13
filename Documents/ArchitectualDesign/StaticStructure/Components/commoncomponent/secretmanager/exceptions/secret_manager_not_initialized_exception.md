---
class: SecretManagerNotInitializedException
kind: exception
module: gafs.dynamicaiagent.common.secretmanager.exceptions
inherits: [SecretManagerException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"SecretManagerNotInitializedException"` |
| `DEFAULT_MESSAGE()` | `str` | `"SecretManager is not initialized. Ensure initialize() has been called."` |
