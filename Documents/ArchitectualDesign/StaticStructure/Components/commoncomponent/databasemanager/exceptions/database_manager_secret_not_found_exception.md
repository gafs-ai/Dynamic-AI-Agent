---
class: DatabaseManagerSecretNotFoundException
kind: exception
module: gafs.dynamicaiagent.common.databasemanager.exceptions
inherits: [DatabaseManagerException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"DatabaseManagerSecretNotFoundException"` |
| `DEFAULT_MESSAGE()` | `str` | `"Secret referenced by DatabaseConnection not found."` |
