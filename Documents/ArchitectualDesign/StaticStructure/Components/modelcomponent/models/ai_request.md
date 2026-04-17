---
class: AiRequest
kind: data_class
roles: [value_object]
module: gafs.dynamicaiagent.modelcomponent.models
dependencies:
  - AiOperationType
  - AiPayload
---

## attributes

| name | type | required | description |
|------|------|----------|-------------|
| `operation_type` | `AiOperationType` | yes | Type of AI operation. Read-only after construction. |
| `payload` | `AiPayload` | yes | Input payload. Automatically converted to the matching subclass based on `operation_type`. |
| `parameters` | `dict[str, Any]` | no | Optional provider-specific inference parameters (e.g. `temperature`, `max_tokens`). Defaults to `{}`. |

## notes

- `operation_type` accepts both `AiOperationType` enum instances and their string values.
- `payload` accepts an `AiPayload` instance, a `dict`, or a JSON string. The appropriate subclass (`ChatCompletionPayload`, `TextCompletionPayload`, `EmbeddingPayload`) is selected automatically based on `operation_type`.
- `operation_type` is read-only after construction.
- `IMAGE_GENERATION`, `SPEECH_TO_TEXT`, `TEXT_TO_SPEECH` payload construction is not yet implemented (`NotImplementedError`).
