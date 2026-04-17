---
class: AiPayload
kind: abstract_class
module: gafs.dynamicaiagent.modelcomponent.models
dependencies:
  - Message
---

## usage

- Abstract base for all model request payloads.
- `AiRequest` selects the appropriate concrete subclass based on `operation_type`.

## subclasses

| class | operation_type | key attribute |
|-------|---------------|---------------|
| `TextCompletionPayload` | `TEXT_COMPLETION` | `text: str` |
| `ChatCompletionPayload` | `CHAT_COMPLETION` | `messages: list[Message]` |
| `EmbeddingPayload` | `EMBEDDING` | `text: str` |

## notes

- All subclasses support `from_dict` / `from_json` / `to_dict` / `to_json`.
- `ChatCompletionPayload.messages` accepts `list[Message]` or `list[dict]` (auto-converted via `Message.from_dict`).
