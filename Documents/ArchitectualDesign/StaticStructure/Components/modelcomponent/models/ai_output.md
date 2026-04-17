---
class: AiOutput
kind: abstract_class
module: gafs.dynamicaiagent.modelcomponent.models
dependencies:
  - Message
---

## usage

- Abstract base for all model response outputs.
- Held by `AiResponse.output`.

## subclasses

| class | operation_type | key attribute |
|-------|---------------|---------------|
| `TextCompletionOutput` | `TEXT_COMPLETION` | `text: str` |
| `ChatCompletionOutput` | `CHAT_COMPLETION` | `messages: list[Message]` |
| `EmbeddingOutput` | `EMBEDDING` | `vector: list[float]` |

## notes

- All subclasses are immutable (`__setattr__` raises `ValueError` for unknown fields after construction).
- All subclasses support `from_dict` / `from_json` / `to_dict` / `to_json`.
