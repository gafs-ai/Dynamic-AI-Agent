---
class: CloudAiException
kind: exception
module: gafs.dynamicaiagent.cloudaicomponent.exceptions
inherits: [ApplicationException]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME` | `str` | `"CloudAiException"` |
| `DEFAULT_MESSAGE` | `str` | `"Unexpected Error in Cloud AI component."` |

## attributes

| name | type | description |
|------|------|-------------|
| `message` | `str` | Human-readable error description. Defaults to `DEFAULT_MESSAGE`. |
| `details` | `dict[str, Any]` | Structured details. Always includes `"component": "CloudAiComponent"` and `"ai_provider"` (provider value or `"unknown"`). |
| `cause` | `BaseException \| None` | Underlying exception, if any. |

## constructor

```python
def __init__(
    message: str | None = DEFAULT_MESSAGE,
    details: dict[str, Any] | None = None,
    cause: BaseException | None = None,
    provider: CloudAiProviderType | str | None = None,
)
```

- `details["component"]` is automatically set to `"CloudAiComponent"`.
- `details["ai_provider"]` is set to `provider.value` (for `CloudAiProviderType`) or the raw string; `"unknown"` if `provider` is `None`.

## hierarchy

```
CloudAiException
├── CloudAiConfigurationException
├── CloudAiRequestValidationException
├── CloudAiUnsupportedOperationException
└── CloudAiRemoteApiException
```
