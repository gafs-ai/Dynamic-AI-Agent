---
class: SandboxCatalogueSearchCriteria
kind: data_class
roles: [value_object]
module: gafs.dynamicaiagent.toolcomponent.models
dependencies:
  - SandboxStatus
  - TagsSearchCriteria
---

## attributes

| name | type | required | default | description |
|------|------|----------|---------|-------------|
| `name` | `str \| None` | no | `None` | Filter by exact sandbox name |
| `status` | `list[SandboxStatus]` | no | `[ACTIVE]` | Filter by sandbox status (OR) |
| `tags` | `TagsSearchCriteria \| None` | no | `None` | Tag filter supporting AND/OR matching |
| `limit` | `int` | no | `100` | Maximum number of sandbox records returned |

## notes

- All filters are optional and combined with AND across fields.
- Multi-value filter (`status`) is combined with OR within the field.
- `tags` supports both AND and OR semantics through `TagsSearchCriteria`.
