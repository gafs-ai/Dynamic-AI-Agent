---
class: DatabaseManagerConnectionNotFoundException
kind: exception
module: gafs.dynamicaiagent.common.databasemanager.exceptions
inherits: [DatabaseManagerException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"DatabaseManagerConnectionNotFoundException"` |
| `DEFAULT_MESSAGE()` | `str` | `"DatabaseConnection not found."` |

## usage

- Raised when no matching `DatabaseConnection` entry is found when looking up by id.