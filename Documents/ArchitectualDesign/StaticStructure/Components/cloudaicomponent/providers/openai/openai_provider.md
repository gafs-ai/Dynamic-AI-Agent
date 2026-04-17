---
class: OpenAiProvider
kind: class
module: gafs.dynamicaiagent.cloudaicomponent.providers.openai
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

- Implements `ICloudAiProvider` for the standard OpenAI API.
- Supports `CHAT_COMPLETION` and `EMBEDDING` operations.
- Converts `AiRequest` payloads to OpenAI API format via the `openai` SDK (`AsyncOpenAI`).
- Converts API responses to `AiResponse`.

## connection parameters

Parameters stored in `AiConnectionParameters.parameters` (`dict[str, Any]`):

| key               | required | default | description                        |
| ----------------- | -------- | ------- | ---------------------------------- |
| `api_key`         | yes      | —       | OpenAI API key                     |
| `model`           | yes      | —       | OpenAI model name (e.g. `gpt-4o`)  |
| `organization_id` | no       | `None`  | Organization ID                    |

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
2. Build `AsyncOpenAI` client via `_get_client(connection_parameters)`.
3. Extract `model` from `parameters`. If empty: raise `CloudAiConfigurationException`.
4. Convert `request.payload.messages` to OpenAI API format via `_messages_to_openai`.
5. Build kwargs: `model`, `stream` from `request.parameters` (default `False`). Optionally add `temperature`, `max_completion_tokens`, `reasoning_effort`.
6. Call `client.chat.completions.create(**kwargs)`.
   - On exception: raise `CloudAiRemoteApiException`.
7. If `stream = True`: accumulate content from chunks. If `stream = False`: extract content from `resp.choices[0].message` and populate `AiOperationStatus` from `resp.usage`.
8. Build `ChatCompletionOutput` with an `ASSISTANT` `Message`, wrap in `AiResponse`, and return.

---

### `_invoke_embedding`

```python
@classmethod
async def _invoke_embedding(cls, connection_parameters: AiConnectionParameters, request: AiRequest) -> AiResponse
```

#### implementation notes

1. If `request.payload` is `None`: raise `CloudAiRequestValidationException`.
2. Build `AsyncOpenAI` client via `_get_client(connection_parameters)`.
3. Extract `model` from `parameters`. If empty: raise `CloudAiConfigurationException`.
4. Build kwargs: `model`, `input = request.payload.input`. Optionally add `dimensions` from `request.parameters`.
5. Call `client.embeddings.create(**kwargs)`.
   - On exception: raise `CloudAiRemoteApiException`.
6. Extract `embedding` from the first result item.
7. Build `EmbeddingOutput`, populate `AiOperationStatus` from `resp.usage`, wrap in `AiResponse`, and return.

---

### `_get_client`

```python
@staticmethod
def _get_client(connection_parameters: AiConnectionParameters) -> AsyncOpenAI
```

#### implementation notes

1. Extract `api_key` from `connection_parameters.parameters`. If empty: raise `CloudAiConfigurationException`.
2. Optionally include `organization` from `parameters["organization_id"]`.
3. Construct and return `AsyncOpenAI`.

---

### `_messages_to_openai` / `_message_to_openai`

Same conversion logic as `AzureOpenAiProvider`. See [AzureOpenAiProvider](../azure_openai/azure_openai_provider.md) for details.
