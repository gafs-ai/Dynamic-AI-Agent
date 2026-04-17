---
class: CloudAiRequestValidationException
kind: exception
module: gafs.dynamicaiagent.cloudaicomponent.exceptions
inherits: [CloudAiException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME` | `str` | `"CloudAiRequestValidationException"` |
| `DEFAULT_MESSAGE` | `str` | `"Invalid request for Cloud AI operation."` |

## usage

- Raised when `AiRequest.payload` is `None` for an operation that requires it.
- Raised when a `Message` has an invalid `role` value not accepted by the provider API.
