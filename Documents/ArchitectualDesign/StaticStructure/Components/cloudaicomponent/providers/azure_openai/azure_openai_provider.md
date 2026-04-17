---
class: AzureOpenAiProvider
kind: class
module: gafs.dynamicaiagent.cloudaicomponent.providers.azure_openai
implements: [ICloudAiProvider]
dependencies:
  - AiConnectionParameters
  - AiRequest
  - AiResponse
  - AiOperationType
  - AiOperationStatus
  - ChatCompletionOutput
  - EmbeddingOutput
  - Message
  - CloudAiProviderType
exceptions_used:
  - CloudAiConfigurationException
  - CloudAiRequestValidationException
  - CloudAiUnsupportedOperationException
  - CloudAiRemoteApiException
---

## responsibilities

- Implements `ICloudAiProvider` for the Azure OpenAI service.
- Supports `CHAT_COMPLETION` and `EMBEDDING` operations.
- Converts `AiRequest` payloads to Azure OpenAI API format via the `openai` SDK (`AsyncAzureOpenAI`).
- Converts API responses to `AiResponse`.

## connection parameters

Parameters stored in `AiConnectionParameters.parameters` (`dict[str, Any]`):

| key            | required | default            | description                                                        |
| -------------- | -------- | ------------------ | ------------------------------------------------------------------ |
| `endpoint`     | yes      | —                  | Azure OpenAI endpoint URL (trailing `/` is stripped)               |
| `api_key`      | yes      | —                  | Azure OpenAI API key                                               |
| `deployment`   | no       | `""`               | Azure deployment name (used as model identifier)                   |
| `api_version`  | no       | `"2025-06-01"`     | Azure OpenAI REST API version                                      |
| `organization` | no       | `None`             | Organization ID                                                    |
| `project`      | no       | `None`             | Project ID                                                         |

## supported operations

| `AiOperationType`    | supported | notes                                              |
| -------------------- | --------- | -------------------------------------------------- |
| `CHAT_COMPLETION`    | yes       | Streaming (`stream=True`) is supported             |
| `EMBEDDING`          | yes       |                                                    |
| `SPEECH_TO_TEXT`     | no        | Raises `CloudAiUnsupportedOperationException`      |
| `TEXT_TO_SPEECH`     | no        | Raises `CloudAiUnsupportedOperationException`      |
| `IMAGE_GENERATION`   | no        | Raises `CloudAiUnsupportedOperationException`      |

## inference parameters (`AiRequest.parameters`)

| key                | type    | default | description                                             |
| ------------------ | ------- | ------- | ------------------------------------------------------- |
| `temperature`      | `float` | —       | Sampling temperature                                    |
| `max_tokens`       | `int`   | —       | Maximum output tokens (mapped to `max_completion_tokens`) |
| `reasoning_effort` | `str`   | —       | Reasoning effort level (passed through as-is)           |
| `stream`           | `bool`  | `False` | Enable streaming; response content is accumulated       |
| `dimensions`       | `int`   | —       | Embedding dimensions (for `EMBEDDING` only)             |

## methods

---

### invoke

```python
@classmethod
async def invoke(cls, connection_parameters: AiConnectionParameters, request: AiRequest) -> AiResponse
```

#### implementation notes

1. Match on `request.operation_type`:
   - `CHAT_COMPLETION`: call `_invoke_chat(connection_parameters, request)` and return the result.
   - `EMBEDDING`: call `_invoke_embedding(connection_parameters, request)` and return the result.
   - `SPEECH_TO_TEXT`, `TEXT_TO_SPEECH`, `IMAGE_GENERATION`: raise `CloudAiUnsupportedOperationException`.
   - Other: raise `CloudAiUnsupportedOperationException`.

---

### `_invoke_chat`

```python
@classmethod
async def _invoke_chat(cls, connection_parameters: AiConnectionParameters, request: AiRequest) -> AiResponse
```

#### implementation notes

1. If `request.payload` is `None`: raise `CloudAiRequestValidationException`.
2. Build `AsyncAzureOpenAI` client via `_get_client(connection_parameters)`.
3. Convert `request.payload.messages` to OpenAI API format via `_messages_to_openai`.
4. Build kwargs: `model = parameters["deployment"]`, `stream` from `request.parameters` (default `False`). Optionally add `temperature`, `max_completion_tokens`, `reasoning_effort`.
5. Call `client.chat.completions.create(**kwargs)`.
   - On exception: raise `CloudAiRemoteApiException`.
6. If `stream = True`: accumulate content from chunks. If `stream = False`: extract content from `resp.choices[0].message` and populate `AiOperationStatus` from `resp.usage`.
7. Build `ChatCompletionOutput` with an `ASSISTANT` `Message`, wrap in `AiResponse`, and return.

---

### `_invoke_embedding`

```python
@classmethod
async def _invoke_embedding(cls, connection_parameters: AiConnectionParameters, request: AiRequest) -> AiResponse
```

#### implementation notes

1. If `request.payload` is `None`: raise `CloudAiRequestValidationException`.
2. Build `AsyncAzureOpenAI` client via `_get_client(connection_parameters)`.
3. Build kwargs: `model = parameters["deployment"]`, `input = request.payload.input`. Optionally add `dimensions` from `request.parameters`.
4. Call `client.embeddings.create(**kwargs)`.
   - On exception: raise `CloudAiRemoteApiException`.
5. Extract `embedding` from the first result item.
6. Build `EmbeddingOutput`, populate `AiOperationStatus` from `resp.usage`, wrap in `AiResponse`, and return.

---

### `_get_client`

```python
@classmethod
def _get_client(cls, connection_parameters: AiConnectionParameters) -> AsyncAzureOpenAI
```

#### implementation notes

1. Extract `endpoint` and `api_key` from `connection_parameters.parameters`.
2. If `endpoint` is empty: raise `CloudAiConfigurationException`.
3. If `api_key` is empty: raise `CloudAiConfigurationException`.
4. Construct and return `AsyncAzureOpenAI` with `azure_endpoint`, `azure_deployment`, `api_version`, `api_key`, `organization`, `project`.

---

### `_messages_to_openai`

```python
@classmethod
def _messages_to_openai(cls, messages: list[Message]) -> list[dict[str, Any]]
```

#### implementation notes

1. For each `Message`, call `_message_to_openai(m)` and collect results.

---

### `_message_to_openai`

```python
@classmethod
def _message_to_openai(cls, m: Message) -> dict[str, Any]
```

#### implementation notes

1. Extract `role` as string. If not in `{"system", "assistant", "user", "function", "tool", "developer"}`: raise `CloudAiRequestValidationException`.
2. If `m.content` is a list of `MessagePart`, convert each part:
   - `TextMessagePart` → `{"type": "text", "text": ...}`
   - `ImageUrlMessagePart` → `{"type": "image_url", "image_url": {"url": ..., "detail": ...}}`
   - Other → `{"type": "text", "text": ...}` (best effort)
   - If there is only one text item, unwrap to a plain string.
3. Build and return `{"role": role, "content": content}`. Include `"name"` if `m.name` is set.
