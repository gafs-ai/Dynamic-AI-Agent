---
class: AiResponse
kind: data_class
roles: [value_object]
module: gafs.dynamicaiagent.modelcomponent.models
dependencies:
  - AiOutput
  - AiOperationStatus
---

## attributes

| name | type | required | description |
|------|------|----------|-------------|
| `output` | `AiOutput \| None` | no | The model's output (e.g. `TextCompletionOutput`, `ChatCompletionOutput`, `EmbeddingOutput`) |
| `status` | `AiOperationStatus \| None` | no | Metadata about the operation (token usage, operation ID, etc.) |

## notes

- Both attributes default to `None`.
- Supports `from_dict` / `from_json` / `to_dict` / `to_json`.
- Unknown attributes are silently ignored.
