# CloudAiComponent

A Cloud AI invocation component for the Dynamic AI Agent framework.
Wraps the OpenAI and Azure OpenAI Python SDKs behind a provider-neutral interface,
routes requests based on `AiConnectionParameters.provider_type`, and returns
typed `AiResponse` objects.

---

## Package layout

```
cloudaicomponent/
├── __init__.py                        # Public exports
├── cloud_ai_component.py              # CloudAiComponent (main entry point)
├── i_cloud_ai_component.py            # ICloudAiComponent interface
├── i_cloud_ai_provider.py             # ICloudAiProvider interface
├── build_nuitka.py                    # Nuitka compilation script
├── requirements.txt                   # Runtime dependencies
├── exceptions/
│   ├── cloud_ai_exception.py          # Base exception
│   └── cloud_ai_exceptions.py         # Configuration / validation / API exceptions
├── models/
│   └── cloud_ai_provider_type.py      # CloudAiProviderType enum
├── providers/
│   ├── azure_openai/
│   │   └── azure_openai_provider.py   # AzureOpenAiProvider
│   └── openai/
│       └── openai_provider.py         # OpenAiProvider
└── test/
    ├── conftest.py                    # pytest logging plugin
    ├── secret_test_config_*.json      # Real-credential test configs (git-ignored)
    ├── test_azure_openai_provider_integration.py
    ├── test_openai_provider_integration.py
    ├── test_cloud_ai_component_integration.py
    └── test_build_cloudaicomponent.py
```

---

## Supported operations

| Provider        | CHAT_COMPLETION | EMBEDDING | Others |
|-----------------|:---------------:|:---------:|:------:|
| Azure OpenAI    | ✓               | ✓         | ✗      |
| OpenAI          | ✓               | ✓         | ✗      |

---

## Usage

### 1. Build connection parameters

```python
from gafs.dynamicaiagent.modelcomponent.models.ai_connection_parameters import AiConnectionParameters
from gafs.dynamicaiagent.modelcomponent.models.ai_deployment_type import AiDeploymentType
from gafs.dynamicaiagent.modelcomponent.models.ai_operation_type import AiOperationType
from gafs.dynamicaiagent.cloudaicomponent.models.cloud_ai_provider_type import CloudAiProviderType

# Azure OpenAI — chat
conn = AiConnectionParameters(
    operation_type=AiOperationType.CHAT_COMPLETION,
    deployment_type=AiDeploymentType.CLOUD,
    provider_type=CloudAiProviderType.AZURE_OPENAI,
)
conn.parameters = {
    "deployment": "gpt-5",
    "endpoint": "https://<resource>.openai.azure.com/",
    "api_key": "<your-api-key>",
    "api_version": "2024-12-01-preview",   # optional, defaults to 2025-06-01
}

# OpenAI — embedding
conn_emb = AiConnectionParameters(
    operation_type=AiOperationType.EMBEDDING,
    deployment_type=AiDeploymentType.CLOUD,
    provider_type=CloudAiProviderType.OPENAI,
)
conn_emb.parameters = {
    "model": "text-embedding-3-large",
    "api_key": "<your-api-key>",
    "organization_id": "<org-id>",          # optional
}
```

### 2. Build a request

```python
from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.ai_payload import ChatCompletionPayload, EmbeddingPayload
from gafs.dynamicaiagent.modelcomponent.models.message import Message

# Chat
payload = ChatCompletionPayload()
msg = Message()
msg.role = "user"
msg.content = "Hello!"
payload.messages = [msg]
request = AiRequest(AiOperationType.CHAT_COMPLETION, payload=payload)

# Embedding
emb_payload = EmbeddingPayload()
emb_payload.text = "text to embed"
emb_request = AiRequest(AiOperationType.EMBEDDING, payload=emb_payload)
```

### 3. Invoke

```python
import asyncio
from gafs.dynamicaiagent.cloudaicomponent import CloudAiComponent

component = CloudAiComponent()

async def main():
    response = await component.invoke(conn, request)
    print(response.output.messages[0].content)

    emb_response = await component.invoke(conn_emb, emb_request)
    print(len(emb_response.output.vector))

asyncio.run(main())
```

### 4. Streaming chat

```python
request.parameters["stream"] = True
response = await component.invoke(conn, request)
# Content is accumulated server-side; response.output.messages[0].content
# contains the full concatenated text after the stream completes.
```

---

## Connection parameter reference

### Azure OpenAI (`CloudAiProviderType.AZURE_OPENAI`)

| Key | Required | Description |
|-----|:--------:|-------------|
| `endpoint` | ✓ | Azure OpenAI resource endpoint URL |
| `api_key` | ✓ | Azure API key |
| `deployment` | ✓ (chat/embedding) | Deployment name |
| `api_version` | — | API version string (default: `2025-06-01`) |
| `organization` | — | OpenAI organization header |
| `project` | — | OpenAI project header |

### OpenAI (`CloudAiProviderType.OPENAI`)

| Key | Required | Description |
|-----|:--------:|-------------|
| `api_key` | ✓ | OpenAI API key |
| `model` | ✓ (chat/embedding) | Model name (e.g. `gpt-4o`) |
| `organization_id` | — | OpenAI organization ID |
| `base_url` | — | Override the API base URL |

---

## Inference parameters (`AiRequest.parameters`)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `stream` | `bool` | `False` | Enable streaming (content is accumulated) |
| `temperature` | `float` | — | Sampling temperature |
| `max_tokens` | `int` | — | Maximum output tokens |
| `reasoning_effort` | `str` | — | o-series reasoning effort (`low`/`medium`/`high`) |
| `dimensions` | `int` | — | Embedding vector dimension |

---

## Exceptions

| Exception | When raised |
|-----------|-------------|
| `CloudAiConfigurationException` | `deployment_type != CLOUD`, missing endpoint/api_key/model |
| `CloudAiRequestValidationException` | `None` payload, invalid message role |
| `CloudAiUnsupportedOperationException` | Unsupported operation type, custom string provider |
| `CloudAiRemoteApiException` | Upstream SDK / API error |
| `CloudAiException` | Base class for all of the above |

---

## Running tests

Tests make real API calls. Credentials are stored in `secret_test_config_*.json`
files that are git-ignored.

```bash
# From Python/ directory

# Source tests
pytest gafs/dynamicaiagent/cloudaicomponent/test/test_azure_openai_provider_integration.py -v
pytest gafs/dynamicaiagent/cloudaicomponent/test/test_openai_provider_integration.py -v
pytest gafs/dynamicaiagent/cloudaicomponent/test/test_cloud_ai_component_integration.py -v

# Build tests (requires compiled .pyd first)
python gafs/dynamicaiagent/cloudaicomponent/build_nuitka.py
pytest gafs/dynamicaiagent/cloudaicomponent/test/test_build_cloudaicomponent.py -v
```

---

## Building with Nuitka

```bash
# From Python/ directory
python gafs/dynamicaiagent/cloudaicomponent/build_nuitka.py
```

The compiled extension is placed at:

```
build/win_x64/gafs/dynamicaiagent/cloudaicomponent/cloudaicomponent.cp312-win_amd64.pyd
```

---

## Dependencies

```
openai>=1.0.0
```
