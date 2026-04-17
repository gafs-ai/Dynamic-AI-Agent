---
class: ModelComponentResourceNotFoundException
kind: exception
module: gafs.dynamicaiagent.modelcomponent.exceptions
inherits: [ModelComponentException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"ModelComponentResourceNotFoundException"` |
| `DEFAULT_MESSAGE()` | `str` | `"Requested model resource was not found."` |

## usage

- Base exception for resource not found failures in the ModelComponent.
