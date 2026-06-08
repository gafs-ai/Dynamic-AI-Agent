---
class: FullTextAnalyzerNotExistException
kind: exception
module: gafs.dynamicaiagent.toolcomponent.exceptions
inherits: [ToolComponentOperationException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"FullTextAnalyzerNotExistException"` |
| `DEFAULT_MESSAGE()` | `str` | `"The referenced full-text analyzer does not exist."` |

## usage

- Raised during `ensure_indexes` when a full-text analyzer referenced in `ToolComponentConfigurations` is not registered in `IDatabaseManager`.
