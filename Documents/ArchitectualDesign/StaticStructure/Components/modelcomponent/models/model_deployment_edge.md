---
class: ModelDeploymentEdge
kind: edge_class
module: gafs.dynamicaiagent.modelcomponent.models
collection: deployed_as
dependencies:
  - ModelCatalogueEntry
  - ModelDeployment
---

## ModelDeploymentEdge

Represents a `deployed_as` relation edge in SurrealDB that links a `ModelCatalogueEntry` to a `ModelDeployment`.

```
ModelCatalogue:<id>  ->  deployed_as  ->  model_deployments:<id>
```

### constants

| name | type | value | description |
|------|------|-------|-------------|
| `EDGE_TYPE()` | `str` | `"deployed_as"` | SurrealDB edge collection name |

### attributes

| name | type | required | description |
|------|------|----------|-------------|
| `id` | `str \| None` | no | Edge record ID. Auto-assigned by SurrealDB on `RELATE`. |
| `source` | `str` | yes | Record ID of the source `ModelCatalogueEntry` (without table prefix). |
| `target` | `str` | yes | Record ID of the target `ModelDeployment` (without table prefix). |

### notes

- `source` and `target` are the Python-side attribute names. On the database they are stored as `in` and `out` (SurrealDB edge standard fields).
- The object is instantiated in Python first and then persisted to the database via `RELATE`.
- Supports `from_dict` / `to_dict` / `to_json`.

## persistence

### create edge

```surql
RELATE type::thing('ModelCatalogue', '<in_id>') -> deployed_as -> type::thing('model_deployments', '<out_id>');
```

### delete edge

```surql
DELETE deployed_as WHERE in = type::thing('ModelCatalogue', '<in_id>') AND out = type::thing('model_deployments', '<out_id>');
```

### resolve deployments from catalogue

```surql
SELECT out FROM deployed_as WHERE in = type::thing('ModelCatalogue', '<in_id>');
```

## caller view

- Not directly exposed to callers.
- `ModelCatalogueEntry.deployments: list[str] | None` contains `ModelDeployment` record IDs resolved from outbound `deployed_as` edges at read time. The field is **not** stored as a field on the `ModelCatalogue` record itself.

## transactional constraints

- Edge create / delete operations must be committed in the same transaction as the corresponding `ModelCatalogueEntry` write operation.
- On `ModelDeployment` deletion, all inbound `deployed_as` edges to that deployment must be deleted in the same transaction as the `ModelDeployment` record itself.
