---
class: CloudAiComponent
kind: class
module: gafs.dynamicaiagent.cloudaicomponent
implements: [ICloudAiComponent]
dependencies:
  - ICloudAiProvider
  - AiConnectionParameters
  - AiRequest
  - AiResponse
  - AiDeploymentType
  - CloudAiProviderType
  - AzureOpenAiProvider
  - OpenAiProvider
exceptions_used:
  - CloudAiException
  - CloudAiConfigurationException
  - CloudAiUnsupportedOperationException
---

## responsibilities

- Validates that `connection_parameters.deployment_type` is `CLOUD`.
- Routes the invocation to the appropriate `ICloudAiProvider` based on `connection_parameters.provider_type`.
- Wraps any unexpected exceptions as `CloudAiException`.

## methods

---

### invoke

```python
async def invoke(
    connection_parameters: AiConnectionParameters,
    request: AiRequest,
) -> AiResponse
```

#### implementation notes

1. If `connection_parameters.deployment_type` is not `AiDeploymentType.CLOUD`: raise `CloudAiConfigurationException`.
2. Match on `connection_parameters.provider_type`:
   - `CloudAiProviderType.AZURE_OPENAI`: call `AzureOpenAiProvider.invoke(connection_parameters, request)` and return the result.
   - `CloudAiProviderType.OPENAI`: call `OpenAiProvider.invoke(connection_parameters, request)` and return the result.
   - Any other `CloudAiProviderType` value: raise `CloudAiConfigurationException`.
   - `str` (custom provider type): raise `CloudAiUnsupportedOperationException`.
   - Other types: raise `CloudAiConfigurationException`.
3. Re-raise any `CloudAiException` as-is.
4. Wrap any other unexpected exception as `CloudAiException`.
