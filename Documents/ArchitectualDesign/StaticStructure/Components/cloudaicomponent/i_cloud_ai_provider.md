---
class: ICloudAiProvider
kind: abstract_class
module: gafs.dynamicaiagent.cloudaicomponent
inherits: [ABC]
dependencies:
  - AiConnectionParameters
  - AiRequest
  - AiResponse
exceptions_used:
  - CloudAiConfigurationException
  - CloudAiRequestValidationException
  - CloudAiUnsupportedOperationException
  - CloudAiRemoteApiException
---

## responsibilities

- Abstracts a single Cloud AI backend (e.g. Azure OpenAI, OpenAI) behind a uniform interface.
- Converts `AiRequest` payloads to the provider API format, calls the API, and converts the response to `AiResponse`.
- Implemented as a stateless class (`@classmethod`); no instance state is required.

## methods

---

### invoke

```python
@classmethod
async def invoke(
    cls,
    connection_parameters: AiConnectionParameters,
    request: AiRequest,
) -> AiResponse
```

| property    | value                                                                             |
| ----------- | --------------------------------------------------------------------------------- |
| async       | true                                                                              |
| class method | true                                                                             |
| description | Execute the AI operation specified by `request` against the provider's API.       |

#### parameters

| name                    | type                     | required | description                                                       |
| ----------------------- | ------------------------ | -------- | ----------------------------------------------------------------- |
| `connection_parameters` | `AiConnectionParameters` | yes      | Provider-specific connection parameters (endpoint, api_key, etc.) |
| `request`               | `AiRequest`              | yes      | AI operation type, payload, and inference parameters.             |

#### returns

| type         | description                            |
| ------------ | -------------------------------------- |
| `AiResponse` | The model output and operation status. |

#### raises

| exception                              | condition                                                                               |
| -------------------------------------- | --------------------------------------------------------------------------------------- |
| `CloudAiConfigurationException`        | Connection parameters are invalid including cases that required parameters are missing. |
| `CloudAiRequestValidationException`    | Request payload or message content is invalid.                                          |
| `CloudAiUnsupportedOperationException` | The operation type is not supported by this provider.                                   |
| `CloudAiRemoteApiException`            | The upstream API call failed.                                                           |

## known implementations

| class                 | module                                                              | provider       |
| --------------------- | ------------------------------------------------------------------- | -------------- |
| `AzureOpenAiProvider` | `gafs.dynamicaiagent.cloudaicomponent.providers.azure_openai`       | Azure OpenAI   |
| `OpenAiProvider`      | `gafs.dynamicaiagent.cloudaicomponent.providers.openai`             | OpenAI         |
