---
class: ModelCatalogueEntry
kind: data_class
roles: [stored_model]
module: gafs.dynamicaiagent.modelcomponent.models
collection: ModelCatalogue
dependencies:
  - AiOperationType
  - ModelStatus
  - AttributeDefinition
  - ModelDeployment
  - ModelDeploymentEdge
---

## ModelStatus

```
kind: enum
module: gafs.dynamicaiagent.modelcomponent.models
```

| name | value | description |
|------|-------|-------------|
| `RECOMMENDED` | `"recommended"` | Preferred model for new usage |
| `ACTIVE` | `"active"` | Available for use |
| `MAINTENANCE` | `"maintenance"` | Temporarily limited availability |
| `DEPRECATED` | `"deprecated"` | Scheduled for retirement; avoid new usage |
| `RETIRED` | `"retired"` | No longer available |

---

## ModelCatalogueEntry

### constants (class methods)

| name                             | return type | value                        | description                                         |
| -------------------------------- | ----------- | ---------------------------- | --------------------------------------------------- |
| `CollectionName()`               | `str`       | `"ModelCatalogue"`           | SurrealDB collection name for this record type      |


### attributes

| name                             | type                                | required | description                                                                                                               |
| -------------------------------- | ----------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------- |
| `id`                             | `str \| None`                       | no       | Record ID. Normalized from SurrealDB `RecordID` (table prefix stripped).                                                  |
| `name`                           | `str`                               | yes      | Unique model name                                                                                                         |
| `type`                           | `AiOperationType`                   | yes      | Type of operation this model supports                                                                                     |
| `status`                         | `ModelStatus \| None`               | no       | Lifecycle status                                                                                                          |
| `description`                    | `str \| None`                       | no       | Optional text description                                                                                                 |
| `description_vector`             | `list[float] \| None`               | no       | Embedding vector for similarity search                                                                                    |
| `priority`                       | `int \| None`                       | no       | Model priority; higher value = higher priority                                                                            |
| `tags`                           | `list[str] \| None`                 | no       | Optional tags for filtering                                                                                               |
| `deployments`                    | `list[str] \| None`                 | no       | IDs of linked `ModelDeployment` entries. Not stored as a field on the record; resolved from outbound `deployed_as` edges. |
| `default_inference_parameters`   | `dict[str, Any] \| None`            | no       | Default provider-specific inference parameters                                                                            |
| `available_inference_parameters` | `list[AttributeDefinition] \| None` | no       | Schema of supported inference parameters                                                                                  |

### notes

- `type` and `status` accept both enum instances and their string values and are persisted as string values.
- `available_inference_parameters` accepts `list[AttributeDefinition]` or `list[dict]` (auto-converted) and is persisted as `list[dict]`.
- Supports `from_dict` / `from_json` / `to_dict(recursive: bool = False ,exclude_id: bool = False)` / `to_json(exclude_id: bool = False)`.

---
### indexes

| field                | index_type | analyzer                                  | notes                                                       |
| -------------------- | ---------- | ----------------------------------------- | ----------------------------------------------------------- |
| `id`                 | auto       | —                                         | automatic                                                   |
| `name`               | standard   | —                                         | UNIQUE                                                      |
| `name`               | FULL TEXT  | Defined in `ModelComponentConfigurations` | BM25                                                        |
| `type`               | standard   | —                                         |                                                             |
| `status`             | standard   | —                                         |                                                             |
| `description`        | FULL TEXT  | Defined in `ModelComponentConfigurations` | BM25                                                        |
| `tags`               | standard   | —                                         |                                                             |
| `description_vector` | HNSW       | —                                         | dimensions and settings from `ModelComponentConfigurations` |

---

## Edge

The `deployed_as` relation edge between `ModelCatalogueEntry` and `ModelDeployment` is defined in [ModelDeploymentEdge](model_deployment_edge.md).
