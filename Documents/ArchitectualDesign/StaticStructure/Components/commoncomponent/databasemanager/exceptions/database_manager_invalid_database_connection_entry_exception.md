---
class: DatabaseManagerInvalidDatabaseConnectionEntryException
kind: exception
module: gafs.dynamicaiagent.common.databasemanager.exceptions
inherits: [DatabaseManagerException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"DatabaseManagerInvalidDatabaseConnectionEntryException"` |
| `DEFAULT_MESSAGE()` | `str` | `"Invalid DatabaseConnection entry."` |

## usage

- Raised when the caller attempts to create or update a `DatabaseConnection` entry with invalid data (e.g. malformed fields, or both `secret` and `raw_secret` set simultaneously).