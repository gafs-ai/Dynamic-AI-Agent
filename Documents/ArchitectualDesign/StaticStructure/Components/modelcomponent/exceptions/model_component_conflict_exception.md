---
class: ModelComponentConflictException
kind: exception
module: gafs.dynamicaiagent.modelcomponent.exceptions
inherits: [ModelComponentException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"ModelComponentConflictException"` |
| `DEFAULT_MESSAGE()` | `str` | `"Model component resource conflict."` |

## usage

- Base exception for resource conflict failures in the ModelComponent (e.g. duplicate entries).
