---
class: DeploymentSecretEdge
kind: edge_class
module: gafs.dynamicaiagent.modelcomponent.models
collection: references_secret
dependencies:
  - ModelDeployment
  - Secret
---

## DeploymentSecretEdge

Represents a `references_secret` relation edge in SurrealDB that links a `ModelDeployment` to a `Secret`.

```
model_deployments:<id>  ->  references_secret  ->  Secrets:<id>
```

### constants

| name | type | value | description |
|------|------|-------|-------------|
| `EDGE_TYPE()` | `str` | `"references_secret"` | SurrealDB edge collection name |

### attributes

| name | type | required | description |
|------|------|----------|-------------|
| `id` | `str \| None` | no | Edge record ID. Auto-assigned by SurrealDB on `RELATE`. |
| `source` | `str` | yes | Record ID of the source `ModelDeployment` (without table prefix). |
| `target` | `str` | yes | Record ID of the target `Secret` (without table prefix). |

### notes

- `source` and `target` are the Python-side attribute names. On the database they are stored as `in` and `out` (SurrealDB edge standard fields).
- The object is instantiated in Python first and then persisted to the database via `RELATE`.
- Supports `from_dict` / `to_dict` / `to_json`.

## persistence

### create edge

```surql
RELATE type::thing('model_deployments', '<in_id>') -> references_secret -> type::thing('Secrets', '<out_id>');
```

### delete edge

```surql
DELETE references_secret WHERE in = type::thing('model_deployments', '<in_id>') AND out = type::thing('Secrets', '<out_id>');
```

### resolve secrets from deployment

```surql
SELECT out FROM references_secret WHERE in = type::thing('model_deployments', '<in_id>');
```

## caller view

- Not directly exposed to callers.
- `ModelDeployment.secrets: list[str] | None` contains `Secret` record IDs resolved from outbound `references_secret` edges at read time. The field is **not** stored as a field on the `model_deployments` record itself.

## transactional constraints

- Edge create / delete operations must be committed in the same transaction as the corresponding `ModelDeployment` write operation.
- On `ModelDeployment` deletion, all outbound `references_secret` edges from that deployment must be deleted in the same transaction as the `ModelDeployment` record itself.
