---
class: AiConnectionParameters
kind: data_class
roles: [value_object]
module: gafs.dynamicaiagent.modelcomponent.models
dependencies:
  - AiOperationType
  - AiDeploymentType
  - AiProviderType
  - CloudAiProviderType
---

## attributes

| name              | type                    | mutable | description                                                                                             |
| ----------------- | ----------------------- | ------- | ------------------------------------------------------------------------------------------------------- |
| `operation_type`  | `AiOperationType`       | no      | AI operation type. Read-only after construction.                                                        |
| `deployment_type` | `AiDeploymentType`      | no      | Deployment family. Read-only after construction.                                                        |
| `provider_type`   | `AiProviderType \| str` | no      | Specific provider. Read-only after construction. Must be `CloudAiProviderType` when `deployment_type == CLOUD`. |
| `parameters`      | `dict[str, Any]`        | yes     | Provider-specific parameters (endpoint, api_key, model, etc.). Supports dict merge assignment only.     |

## constructor

```python
def __init__(
    operation_type: AiOperationType | str,
    deployment_type: AiDeploymentType | str,
    provider_type: AiProviderType | str,
) -> None
```

- `operation_type` accepts both `AiOperationType` enum and string values.
- `deployment_type` accepts both `AiDeploymentType` enum and string values.
- When `deployment_type == CLOUD`: `provider_type` must be a `CloudAiProviderType` or a string resolvable to one. An unresolvable string is stored as-is (custom provider).
- `LOCAL` and `REMOTE` deployment types raise `NotImplementedError`.
- `parameters` is initialized as an empty `dict`.

## notes

- `operation_type`, `deployment_type`, and `provider_type` are read-only after construction (raise `AttributeError` on assignment).
- Assigning a `dict` to `parameters` **merges** the dict into the existing `parameters` (does not replace). This allows incremental parameter population:
  ```python
  conn = AiConnectionParameters(op_type, dep_type, prov_type)
  conn.parameters = {"endpoint": "...", "api_key": "..."}
  ```
- Setting an arbitrary attribute `conn.some_key = value` is equivalent to `conn.parameters["some_key"] = value`.
