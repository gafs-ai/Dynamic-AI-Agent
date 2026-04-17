---
class: ModelDeployment
kind: data_class
roles: [stored_model]
module: gafs.dynamicaiagent.modelcomponent.models
collection: model_deployments
dependencies:
  - AiDeploymentType
  - AiProviderType
  - DeploymentStatus
  - Secret
  - DeploymentSecretEdge
---

## DeploymentStatus

```
kind: enum
module: gafs.dynamicaiagent.modelcomponent.models
```

| name | value |
|------|-------|
| `ACTIVE` | `"active"` |
| `INACTIVE` | `"inactive"` |
| `MAINTENANCE` | `"maintenance"` |
| `DEPRECATED` | `"deprecated"` |
| `RETIRED` | `"retired"` |

---

## ModelDeployment

### constants

| name                | return type | value                 | description                                    |
| ------------------- | ----------- | --------------------- | ---------------------------------------------- |
| `COLLECTION_NAME()` | `str`       | `"model_deployments"` | SurrealDB collection name for this record type |

### attributes

| name | type | required | description |
|------|------|----------|-------------|
| `id` | `str \| None` | no | Record ID. Normalized from SurrealDB `RecordID` (table prefix stripped). |
| `name` | `str` | yes | Unique name for this deployment |
| `description` | `str \| None` | no | Optional description |
| `tags` | `list[str] \| None` | no | Optional tags for filtering |
| `secrets` | `list[str] \| None` | no | IDs of linked `Secret` entries. Not stored as a field on the record; resolved from outbound `references_secret` edges. |
| `deployment_type` | `AiDeploymentType` | yes | Where the model runs (`CLOUD`, `LOCAL`, `REMOTE`) |
| `provider_type` | `AiProviderType` | yes | Specific AI provider (e.g. `CloudAiProviderType`) |
| `connection_parameters` | `dict[str, Any] \| None` | no | Non-secret connection parameters |
| `priority` | `int \| None` | no | Deployment priority; higher value = higher priority |
| `max_confidence_level` | `int \| None` | no | Maximum data confidence level this deployment accepts |
| `status` | `DeploymentStatus \| None` | no | Deployment lifecycle status |

### indexes

| field         | index_type | analyzer                                  | notes     |
| ------------- | ---------- | ----------------------------------------- | --------- |
| `id`          | auto       | —                                         | automatic |
| `name`        | standard   | —                                         | UNIQUE    |
| `name`        | FULL TEXT  | Defined in `ModelComponentConfigurations` | BM25      |
| `description` | FULL TEXT  | Defined in `ModelComponentConfigurations` | BM25      |
| `tags`        | standard   | —                                         |           |
| `status`      | standard   | —                                         |           |

### notes

- `deployment_type` and `provider_type` accept both enum instances and their string values.
- `LOCAL` and `REMOTE` deployment types are not yet implemented.
- `secrets` is NOT stored as a field on the record; it is resolved from outbound `references_secret` edges at read time.
- Supports `from_dict` / `from_json` / `to_dict(exclude_id=True)` / `to_json`.

---

## Edge

The `references_secret` relation edge between `ModelDeployment` and `Secret` is defined in [DeploymentSecretEdge](deployment_secret_edge.md).
