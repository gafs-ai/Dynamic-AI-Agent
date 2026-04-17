---
class: ModelComponentOperationException
kind: exception
module: gafs.dynamicaiagent.modelcomponent.exceptions
inherits: [ModelComponentException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"ModelComponentOperationException"` |
| `DEFAULT_MESSAGE()` | `str` | `"Model component operation failed."` |

## usage

- Base exception for operation failures in the ModelComponent, including database, service, and runtime errors.
