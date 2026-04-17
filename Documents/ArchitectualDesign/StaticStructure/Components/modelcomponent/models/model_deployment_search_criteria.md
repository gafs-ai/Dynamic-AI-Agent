---
class: ModelDeploymentSearchCriteria
kind: data_class
roles: [value_object]
module: gafs.dynamicaiagent.modelcomponent.models
dependencies:
  - AiDeploymentType
  - AiProviderType
  - DeploymentStatus
  - TagsSearchCriteria
---

## attributes

| name | type | required | default | description |
|------|------|----------|---------|-------------|
| `name` | `str \| None` | no | `None` | Filter by exact name |
| `deployment_types` | `list[AiDeploymentType] \| None` | no | `None` | Filter by deployment type (OR) |
| `provider_types` | `list[AiProviderType] \| None` | no | `None` | Filter by provider type (OR) |
| `status` | `list[DeploymentStatus]` | no | `[ACTIVE]` | Filter by deployment status (OR) |
| `keywords` | `list[str] \| None` | no | `None` | Full-text search keywords |
| `min_priority` | `int` | no | `0` | Minimum priority threshold (inclusive) |
| `tags` | `TagsSearchCriteria \| None` | no | `None` | Tag filter |
| `min_confidence_level` | `int` | no | `0` | Minimum `max_confidence_level` required |
| `limit` | `int` | no | `100` | Maximum number of results |

## notes

- All filters are optional and combined with AND across fields.
- Multi-value filters (`deployment_types`, `provider_types`, `status`) are combined with OR within each field.
