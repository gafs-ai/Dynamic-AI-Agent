---
class: InvalidToolInvocationException
kind: exception
module: gafs.dynamicaiagent.toolcomponent.exceptions
inherits: [ToolComponentValidationException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"InvalidToolInvocationException"` |
| `DEFAULT_MESSAGE()` | `str` | `"Tool invocation request is invalid."` |

## usage

- Raised when `input_parameters` passed to `invoke` fail validation against the definitions in `ToolVersionEntry.input_parameters`.
