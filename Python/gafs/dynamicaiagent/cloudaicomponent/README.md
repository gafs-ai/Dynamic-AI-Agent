# gafs.dynamicaiagent.cloudaicomponent

Cloud AI component for Azure OpenAI and OpenAI providers.

This component delegates model execution to provider implementations and uses
Model Component models for requests/responses.

## Current Public API

- `CloudAiComponent`
- `ICloudAiComponent`
- `ICloudAiProvider`
- `AzureOpenAiProvider`
- `OpenAiProvider`
- `CloudAiException`
- `AiRequest` / `AiResponse` (re-exported from modelcomponent)

## Connection Parameters

Connection settings are passed via
`gafs.dynamicaiagent.modelcomponent.models.AiConnectionParameters`.

Required `parameters` keys:

- OpenAI chat/embedding: `model`, `api_key` (optional: `organization_id`)
- Azure OpenAI chat/embedding: `deployment`, `endpoint`, `api_key`
  (optional: `api_version`, `organization`, `project`)

Provider routing is done by:

- `deployment_type = AiDeploymentType.CLOUD`
- `provider_type = CloudAiProviderType.OPENAI | CloudAiProviderType.AZURE_OPENAI`

## AiRequest Usage

`AiRequest` carries:

- `operation_type`
- `payload`
- `parameters` (provider call options such as `stream`, `temperature`, `max_tokens`)

`payload.custom_params` is not used by providers.

## Supported Operations

| Operation | Status |
|---|---|
| Chat completion | Supported |
| Embedding | Supported |
| Speech-to-text | Not implemented |
| Text-to-speech | Not implemented |
| Image generation | Not implemented |

## Exception Contract

`CloudAiComponent` always raises `CloudAiException` or one of its subclasses.

- Configuration and routing errors -> `CloudAiConfigurationException`
- Request payload validation errors -> `CloudAiRequestValidationException`
- Unsupported operations/features -> `CloudAiUnsupportedOperationException`
- Provider SDK/API failures -> `CloudAiRemoteApiException`
- Any unexpected internal error is wrapped as `CloudAiException`

## Tests

From the `Python/` directory:

```bash
python -m pytest gafs/dynamicaiagent/cloudaicomponent/test -v
```

## Nuitka Build

Build extension module:

```bash
python gafs/dynamicaiagent/cloudaicomponent/build_nuitka.py
```

Run compiled-module tests:

```bash
python -m pytest gafs/dynamicaiagent/cloudaicomponent/test/test_build_cloudaicomponent.py -v
```

