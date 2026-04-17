---
class: Message
kind: data_class
module: gafs.dynamicaiagent.modelcomponent.models
dependencies:
  - Role
  - ContentType
  - MessagePart
---

## Role

```
kind: enum
module: gafs.dynamicaiagent.modelcomponent.models
```

| name | value |
|------|-------|
| `USER` | `"user"` |
| `ASSISTANT` | `"assistant"` |
| `SYSTEM` | `"system"` |

---

## ContentType

```
kind: enum
module: gafs.dynamicaiagent.modelcomponent.models
```

| name | value |
|------|-------|
| `TEXT` | `"text"` |
| `IMAGE_URL` | `"image_url"` |
| `AUDIO` | `"audio"` |
| `FILE` | `"file"` |
| `REFUSAL` | `"refusal"` |

---

## MessagePart

```
kind: abstract_class
module: gafs.dynamicaiagent.modelcomponent.models
```

Base class for message content parts. `from_dict` dispatches to the appropriate subclass based on `type`.

### attributes

| name   | type          | required | description                |
| ------ | ------------- | -------- | -------------------------- |
| `type` | `ContentType` | yes      | Content type discriminator |

### subclasses

| class                  | `type` value |
| ---------------------- | ------------ |
| `TextMessagePart`      | `TEXT`       |
| `ImageUrlMessagePart`  | `IMAGE_URL`  |
| `AudioDataMessagePart` | `AUDIO`      |
| `FileMessagePart`      | `FILE`       |
| `RefusalMessagePart`   | `REFUSAL`    |

### notes

- `type` accepts both `ContentType` enum instances and their string values.
- `from_dict` / `from_json` are factory methods that return the concrete subclass matching `type`.
- Supports `to_dict(recursive=False)` / `to_json`.

---

## TextMessagePart

```
kind: data_class
module: gafs.dynamicaiagent.modelcomponent.models
inherits: MessagePart
```

### attributes

| name   | type          | required | description               |
| ------ | ------------- | -------- | ------------------------- |
| `type` | `ContentType` | yes      | Always `ContentType.TEXT` |
| `text` | `str \| None` | no       | Text content              |

---

## ImageUrlMessagePart

```
kind: data_class
module: gafs.dynamicaiagent.modelcomponent.models
inherits: MessagePart
```

### attributes

| name     | type          | required | description                                                                                                  |
| -------- | ------------- | -------- | ------------------------------------------------------------------------------------------------------------ |
| `type`   | `ContentType` | yes      | Always `ContentType.IMAGE_URL`                                                                               |
| `url`    | `str \| None` | no       | URL of the image                                                                                             |
| `detail` | `str \| None` | no       | Resolution hint: `"auto"` (default), `"high"`, or `"low"`. Any other string value is normalized to `"auto"`. |

---

## AudioData

```
kind: data_class
module: gafs.dynamicaiagent.modelcomponent.models
```

Helper class that holds base64-encoded audio and its format.

### attributes

| name     | type          | required | description                                                                             |
| -------- | ------------- | -------- | --------------------------------------------------------------------------------------- |
| `data`   | `str \| None` | no       | Base64-encoded audio. Accepts `str` (stored as-is) or `bytes` (auto-encoded to base64). |
| `format` | `str \| None` | no       | Audio format (e.g. `"mp3"`, `"wav"`)                                                    |

---

## AudioDataMessagePart

```
kind: data_class
module: gafs.dynamicaiagent.modelcomponent.models
inherits: MessagePart
```

### attributes

| name          | type                | required | description                                                                                  |
| ------------- | ------------------- | -------- | -------------------------------------------------------------------------------------------- |
| `type`        | `ContentType`       | yes      | Always `ContentType.AUDIO`                                                                   |
| `input_audio` | `AudioData \| None` | no       | Audio payload. Accepts `AudioData`, `dict` (auto-converted), or JSON `str` (auto-converted). |

---

## FileData

```
kind: data_class
module: gafs.dynamicaiagent.modelcomponent.models
```

Helper class that holds base64-encoded file content and its metadata.

### attributes

| name       | type          | required | description                                                                                    |
| ---------- | ------------- | -------- | ---------------------------------------------------------------------------------------------- |
| `data`     | `str \| None` | no       | Base64-encoded file content. Accepts `str` (stored as-is) or `bytes` (auto-encoded to base64). |
| `file_id`  | `str \| None` | no       | Provider-assigned file identifier                                                              |
| `filename` | `str \| None` | no       | Original filename                                                                              |

---

## FileMessagePart

```
kind: data_class
module: gafs.dynamicaiagent.modelcomponent.models
inherits: MessagePart
```

### attributes

| name   | type               | required | description                                                                                |
| ------ | ------------------ | -------- | ------------------------------------------------------------------------------------------ |
| `type` | `ContentType`      | yes      | Always `ContentType.FILE`                                                                  |
| `file` | `FileData \| None` | no       | File payload. Accepts `FileData`, `dict` (auto-converted), or JSON `str` (auto-converted). |

---

## RefusalMessagePart

```
kind: data_class
module: gafs.dynamicaiagent.modelcomponent.models
inherits: MessagePart
```

### attributes

| name | type | required | description |
|------|------|----------|-------------|
| `type` | `ContentType` | yes | Always `ContentType.REFUSAL` |
| `refusal` | `str \| None` | no | Refusal text returned by the model |

---

## Message

### attributes

| name | type | required | description |
|------|------|----------|-------------|
| `role` | `Role` | yes | Sender role (`user`, `assistant`, `system`) |
| `name` | `str \| None` | no | Optional name of the sender |
| `content` | `str \| list[MessagePart] \| None` | no | Message body. A plain string or a list of typed `MessagePart` objects. |

### notes

- `role` accepts both `Role` enum instances and their string values.
- `content` accepts a `str`, a `list[MessagePart]`, a `list[dict]` (auto-converted via `MessagePart.from_dict`), or `None`.
