---
class: DeploymentSelectionOptions
kind: data_class
roles: [value_object]
module: gafs.dynamicaiagent.modelcomponent.models
dependencies:
  - AiDeploymentType
---

## attributes

| name | type | required | default | description |
|------|------|----------|---------|-------------|
| `deployment_type` | `AiDeploymentType \| None` | no | `None` | Preferred deployment type. If set, only deployments of this type are considered. |
| `confidence` | `int \| None` | no | `None` | Caller's data confidence level. Only deployments with `max_confidence_level >= confidence` are eligible. |

## notes

- `deployment_type` accepts both `AiDeploymentType` enum instances and their string values.
- Both attributes default to `None` (no filter applied).
- Supports `from_dict` / `from_json` / `to_dict` / `to_json`.
