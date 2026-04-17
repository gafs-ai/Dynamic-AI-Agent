---
class: ApplicationException
kind: exception
module: gafs.dynamicaiagent.common.exceptions
inherits: [Exception]
---

## constants

| name | type | value |
|------|------|-------|
| `ERROR_NAME()` | `str` | `"ApplicationException"` |
| `DEFAULT_MESSAGE()` | `str` | `"Unexpected Exception in Application"` |
| `DEFAULT_COMPONENT_NAME()` | `str` | `"Unknown"` |

## attributes

| name | type | required | description |
|------|------|----------|-------------|
| `message` | `str` | yes | Error message |
| `details` | `dict[str, Any]` | yes | Structured details of the exception |
| `cause` | `BaseException \| None` | no | Original exception that caused this exception |

## details schema

| key | type | auto-set | description |
|-----|------|----------|-------------|
| `"datetime"` | `datetime` | yes | Datetime that the exception is detected |
| `"id"` | `str` | yes | Exception id in format `"{datetime_timestamp}-{6_random_characters}"` |
| `"component"` | `str` | yes | Name of the component that raised the exception |
| `"message"` | `str` | yes | Exception message. Included in details for further handling |
| `"causes"` | `list[str]` | yes (if cause is ApplicationException) | List of causal exception ids, propagated from the causing exception |

## usage

- `ApplicationException` is the base exception for this entire application. All exceptions in each component extend this base exception class.
- `details` may contain additional context-specific keys beyond the schema above, such as `"model_id"`, `"deployment_id"`, `"db_provider_id"`, `"db_query"`.
