---
class: ToolCatalogueSearchCriteria
kind: data_class
roles: [value_object]
module: gafs.dynamicaiagent.toolcomponent.models
dependencies:
  - ToolStatus
  - ToolVersionStatus
  - TagsSearchCriteria
---

## attributes

| name                   | type                              | required | default            | description                                                                 |
| ---------------------- | --------------------------------- | -------- | ------------------ | --------------------------------------------------------------------------- |
| `name`                 | `str \| None`                     | no       | `None`             | Filter by exact tool name                                                   |
| `status`               | `list[ToolStatus]`                | no       | `[ACTIVE]`         | Filter by tool status (OR)                                                  |
| `description_keywords` | `list[str] \| None`               | no       | `None`             | Full-text search keywords for `description`                                 |
| `description_vector`   | `list[float] \| None`             | no       | `None`             | Query vector for vector similarity search on `description_vector`           |
| `tags`                 | `TagsSearchCriteria \| None`      | no       | `None`             | Tag filter supporting AND/OR matching                                       |
| `version_status`       | `list[ToolVersionStatus] \| None` | no       | `[LATEST, ACTIVE]` | Filter versions by status (OR) and include matched versions in the response |
| `limit`                | `int`                             | no       | `100`              | Maximum number of tool records returned                                     |

## notes

- All filters are optional and combined with AND across fields.
- Multi-value filters (`status`, `version_status`) are combined with OR within each field.
- If `version_status` is provided, each result must include only `ToolVersionEntry` records whose status matches `version_status`.
- Search results must return both matched `ToolCatalogueEntry` and corresponding matched version information.
- `tags` supports both AND and OR semantics through `TagsSearchCriteria`.
