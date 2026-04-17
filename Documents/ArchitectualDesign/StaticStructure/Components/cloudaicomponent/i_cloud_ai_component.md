---
class: ICloudAiComponent
kind: abstract_class
module: gafs.dynamicaiagent.cloudaicomponent
inherits: [ABC]
dependencies:
  - AiConnectionParameters
  - AiRequest
  - AiResponse
exceptions_used:
  - CloudAiException
  - CloudAiConfigurationException
  - CloudAiRequestValidationException
  - CloudAiUnsupportedOperationException
  - CloudAiRemoteApiException
---

## responsibilities

- Single entry point for invoking Cloud AI operations from the ModelComponent.
- Routes the request to the appropriate `ICloudAiProvider` based on `connection_parameters.provider_type`.

## methods

---

### invoke

```python
async def invoke(
    connection_parameters: AiConnectionParameters,
    request: AiRequest,
) -> AiResponse
```

| property    | value                                                                                             |
| ----------- | ------------------------------------------------------------------------------------------------- |
| async       | true                                                                                              |
| description | Invoke a Cloud AI operation using the given connection parameters and request. |

#### parameters

| name                   | type                   | required | description                                                             |
| ---------------------- | ---------------------- | -------- | ----------------------------------------------------------------------- |
| `connection_parameters` | `AiConnectionParameters` | yes    | Contains `deployment_type`, `provider_type`, and provider-specific `parameters` (e.g. endpoint, api_key). |
| `request`              | `AiRequest`            | yes      | AI operation type, payload, and inference parameters.                   |

#### returns

| type         | description                              |
| ------------ | ---------------------------------------- |
| `AiResponse` | The model output and operation status.   |

#### raises

| exception                              | condition                                                                 |
| -------------------------------------- | ------------------------------------------------------------------------- |
| `CloudAiConfigurationException`        | `deployment_type` is not `CLOUD`, or connection parameters are invalid.   |
| `CloudAiRequestValidationException`    | Request payload or message content is invalid.                            |
| `CloudAiUnsupportedOperationException` | The requested operation is not supported by the selected provider.        |
| `CloudAiRemoteApiException`            | The upstream Cloud AI API call failed.                                    |
| `CloudAiException`                     | Unexpected errors not covered by the above categories.                    |
