---
class: CloudAiUnsupportedOperationException
kind: exception
module: gafs.dynamicaiagent.cloudaicomponent.exceptions
inherits: [CloudAiException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME` | `str` | `"CloudAiUnsupportedOperationException"` |
| `DEFAULT_MESSAGE` | `str` | `"The requested operation is not supported by Cloud AI."` |

## usage

- Raised when an `AiOperationType` is not implemented by the selected provider (e.g. `SPEECH_TO_TEXT`, `TEXT_TO_SPEECH`, `IMAGE_GENERATION`).
- Raised when `provider_type` is a custom string (not a known `CloudAiProviderType`).
