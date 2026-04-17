---
class: FullTextAnalyzerNotExistException
kind: exception
module: gafs.dynamicaiagent.modelcomponent.exceptions
inherits: [ModelComponentOperationException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"FullTextAnalyzerNotExistException"` |
| `DEFAULT_MESSAGE()` | `str` | `"The required full-text analyzer does not exist."` |

## usage

- Raised when an index operation references a full-text analyzer that has not been registered in the database.
- The analyzer must be created by `IDatabaseManager` before any index depending on it can be created or updated.
