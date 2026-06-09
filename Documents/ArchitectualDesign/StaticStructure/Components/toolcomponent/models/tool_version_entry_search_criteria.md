---
class: ToolVersionEntrySearchCriteria
kind: data_class
roles: [value_object]
module: gafs.dynamicaiagent.toolcomponent.models
dependencies:
  - ToolVersionStatus
---

## attributes

| name | type | required | default | description |
|------|------|----------|---------|-------------|
| `tool_id` | `str \| None` | no | `None` | Filter by tool id |
| `status` | `list[ToolVersionStatus]` | no | `[LATEST, ACTIVE]` | Filter by tool version status (OR) |
| `limit` | `int` | no | `100` | Maximum number of version records returned |

## notes

- All filters are optional and combined with AND across fields.
- Multi-value filter (`status`) is combined with OR within the field.
