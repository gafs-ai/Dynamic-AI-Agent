---
class: CloudAiRemoteApiException
kind: exception
module: gafs.dynamicaiagent.cloudaicomponent.exceptions
inherits: [CloudAiException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME` | `str` | `"CloudAiRemoteApiException"` |
| `DEFAULT_MESSAGE` | `str` | `"Cloud AI remote API call failed."` |

## usage

- Raised when the upstream provider SDK call raises an exception (e.g. network error, HTTP 4xx/5xx from the API).
- The original SDK exception is stored in `cause`.
