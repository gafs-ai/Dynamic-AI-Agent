---
class: CloudAiConfigurationException
kind: exception
module: gafs.dynamicaiagent.cloudaicomponent.exceptions
inherits: [CloudAiException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME` | `str` | `"CloudAiConfigurationException"` |
| `DEFAULT_MESSAGE` | `str` | `"Invalid Cloud AI configuration or connection parameters."` |

## usage

- Raised when `deployment_type` is not `CLOUD`.
- Raised when required connection parameters (e.g. `endpoint`, `api_key`, `model`) are missing or empty.
- Raised when `provider_type` is unrecognized or of an unexpected type.
