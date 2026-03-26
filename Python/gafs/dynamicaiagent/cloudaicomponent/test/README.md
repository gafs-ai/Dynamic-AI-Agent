# Cloud AI Component Test Documentation

## Overview

This directory contains integration tests for:

- `AzureOpenAiProvider`
- `OpenAiProvider`
- `CloudAiComponent` (provider routing path)

Tests use secret JSON config files. If a config file is missing, the matching
integration test is skipped.

## Config Format

All integration tests load:

```json
{
  "provider": "openai or azure-openai",
  "options": {
    "...": "provider connection parameters"
  },
  "request": {
    "...": "request payload and request.parameters values"
  }
}
```

Notes:

- Request runtime options must be provided via `AiRequest.parameters`
  (for example: `stream`, `temperature`, `max_tokens`, `dimensions`).
- Providers do not read `payload.custom_params`.

## Main Test Modules

| File | Scope |
|---|---|
| `test_openai_provider_integration.py` | OpenAI provider behavior |
| `test_azure_openai_provider_integration.py` | Azure OpenAI provider behavior |
| `test_cloud_ai_component_integration.py` | CloudAiComponent provider dispatch and errors |
| `test_build_cloudaicomponent.py` | Re-runs integration tests against Nuitka-compiled module |

## Run Tests

From `Python/`:

```bash
python -m pytest gafs/dynamicaiagent/cloudaicomponent/test -v
```

Run only compiled-module tests:

```bash
python -m pytest gafs/dynamicaiagent/cloudaicomponent/test/test_build_cloudaicomponent.py -v
```

## Logging

`conftest.py` writes test logs to:

`gafs/dynamicaiagent/cloudaicomponent/test/test_run.log`
