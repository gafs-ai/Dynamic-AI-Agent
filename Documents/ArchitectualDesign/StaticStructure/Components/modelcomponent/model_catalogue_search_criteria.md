---
class: ModelCatalogueSearchCriteria
kind: data_class
roles: [value_object]
module: gafs.dynamicaiagent.modelcomponent.models
dependencies:
  - AiOperationType
  - AiDeploymentType
  - ModelStatus
  - VectorSearchCriteria
  - TagsSearchCriteria
  - LogicalOperator
---

## LogicalOperator

```
kind: enum
module: gafs.dynamicaiagent.modelcomponent.models
```

| name  | value   |
| ----- | ------- |
| `AND` | `"AND"` |
| `OR`  | `"OR"`  |

---

## TagsSearchCriteria

```
kind: data_class
module: gafs.dynamicaiagent.modelcomponent.models
```

| name | type | default | description |
|------|------|---------|-------------|
| `tags` | `list[str] \| None` | `None` | Tags to match |
| `operator` | `LogicalOperator` | `OR` | How to combine multiple tags |

---

## VectorSearchCriteria

```
kind: data_class
module: gafs.dynamicaiagent.modelcomponent.models
```

| name | type | default | description |
|------|------|---------|-------------|
| `vector` | `list[float] \| None` | `None` | Query vector for similarity search |
| `vector_limit` | `int` | `10` | Maximum number of nearest neighbours to return |
| `options` | `dict[str, int]` | `{}` | Optional HNSW parameters (e.g. `effort`) |

---

## ModelCatalogueSearchCriteria

### attributes

| name | type | required | default | description |
|------|------|----------|---------|-------------|
| `name` | `str \| None` | no | `None` | Filter by exact name |
| `type` | `AiOperationType \| None` | no | `None` | Filter by operation type |
| `status` | `list[ModelStatus]` | no | `[ACTIVE]` | Filter by lifecycle status (OR) |
| `keywords` | `list[str] \| None` | no | `None` | Full-text search keywords |
| `deployment_types` | `list[AiDeploymentType] \| None` | no | `None` | Filter by deployment type (OR) |
| `vector_search` | `VectorSearchCriteria \| None` | no | `None` | Vector similarity search parameters |
| `tags` | `TagsSearchCriteria \| None` | no | `None` | Tag filter |
| `limit` | `int` | no | `100` | Maximum number of results |

### notes

- All filters are optional and combined with AND across fields.
- Multi-value filters (`status`, `deployment_types`) are combined with OR within each field.
