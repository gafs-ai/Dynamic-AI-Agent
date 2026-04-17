---
class: AiOperationStatus
kind: data_class
roles: [value_object]
module: gafs.dynamicaiagent.modelcomponent.models
---

## AiOperationStatusEnum

```
kind: enum
module: gafs.dynamicaiagent.modelcomponent.models
```

_(Values defined in the implementation; represents completion states such as `success`, `error`, etc.)_

---

## AiOperationStatus

### attributes

| name | type | required | description |
|------|------|----------|-------------|
| `status` | `AiOperationStatusEnum \| None` | no | Completion status of the operation |
| `operation_id` | `str \| None` | no | Provider-assigned operation identifier |
| `input_tokens` | `int \| None` | no | Number of input tokens consumed |
| `output_tokens` | `int \| None` | no | Number of output tokens produced |

### notes

- All attributes default to `None`.
- `status` accepts both `AiOperationStatusEnum` instances and their string values.
- Supports `from_dict` / `from_json` / `to_dict` / `to_json`.
