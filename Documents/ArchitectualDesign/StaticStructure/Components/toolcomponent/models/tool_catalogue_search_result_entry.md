---
class: ToolCatalogueSearchResultEntry
kind: data_class
roles: [value_object]
module: gafs.dynamicaiagent.toolcomponent.models
dependencies:
  - ToolCatalogueEntry
  - ToolVersionEntry
---

## description

Represents a single result record returned by `IToolCatalogueService.search_tool_catalogue_entries`.
Each result contains a matched `ToolCatalogueEntry` together with the subset of its `ToolVersionEntry` records that satisfied the `version_status` filter in `ToolCatalogueSearchCriteria`.

## attributes

| name       | type                    | required | description                                                                                                               |
| ---------- | ----------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------- |
| `catalogue` | `ToolCatalogueEntry`   | yes      | The matched tool catalogue entry.                                                                                         |
| `versions`  | `list[ToolVersionEntry]` | yes      | Version entries belonging to `catalogue` whose status matched `ToolCatalogueSearchCriteria.version_status`.<br>Empty list when no versions matched or `version_status` was `None`. |
