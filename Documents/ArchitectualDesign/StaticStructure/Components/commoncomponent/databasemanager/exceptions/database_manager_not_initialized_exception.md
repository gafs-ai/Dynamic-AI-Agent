---
class: DatabaseManagerNotInitializedException
kind: exception
module: gafs.dynamicaiagent.common.databasemanager.exceptions
inherits: [DatabaseManagerException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"DatabaseManagerNotInitializedException"` |
| `DEFAULT_MESSAGE()` | `str` | `"DatabaseManager is not fully initialized. Call initialize() with a SecretManager first."` |
