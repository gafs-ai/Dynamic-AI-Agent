---
class: FieldMutability
kind: enum
module: gafs.dynamicaiagent.common.models
---

## values

| name | value | description |
|------|-------|-------------|
| `IMMUTABLE` | `"immutable"` | After the creation of the entry, the value is not allowed to be changed |
| `MUTABLE` | `"mutable"` | The value of the field can be updated by users or the system |
| `SYSTEM` | `"system"` | Only the system can update the value |
| `SET_ONLY` | `"set_only"` | The value can be set only when it is null or empty |
