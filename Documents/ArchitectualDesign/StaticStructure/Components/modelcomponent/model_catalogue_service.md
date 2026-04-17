---
class: ModelCatalogueService
kind: class
module: gafs.dynamicaiagent.modelcomponent
implements: [IModelCatalogueService]
dependencies:
  - IDatabaseManager
  - IDatabaseProvider
  - ModelCatalogueEntry
  - ModelCatalogueSearchResultEntry
  - ModelDeployment
  - ModelComponentConfigurations
  - ModelCatalogueSearchCriteria
  - ModelDeploymentSearchCriteria
exceptions_used:
  - ModelComponentInitializationException
  - ModelComponentNotInitializedException
  - InvalidModelCatalogueEntryException
  - ConflictingModelCatalogueEntryException
  - ModelCatalogueEntryNotFoundException
  - ModelDeploymentNotFoundException
  - InvalidModelCatalogueSearchCriteriaException
  - InvalidModelDeploymentException
  - ConflictingModelDeploymentException
  - InvalidModelDeploymentSearchCriteriaException
  - ModelComponentOperationException
  - FullTextAnalyzerNotExistException
---

## fields

| name | type | description |
|------|------|-------------|
| `_logger` | `logging.Logger` | Logger instance |
| `_database_manager` | `IDatabaseManager \| None` | Set on `initialize` |
| `_database_provider` | `IDatabaseProvider \| None` | Default provider; set on `initialize` |
| `_configurations` | `ModelComponentConfigurations \| None` | Cached on `initialize` |

## private methods

---

### `_embed_description_text`

```python
async def _embed_description_text(description: str) -> list[float] | None
```

#### implementation notes

1. If `_configurations` is `None`, log a warning and return `None`.
2. If `_configurations.embedding_catalogue_id` is not configured, log a warning and return `None`.
3. Fetch the embedding catalogue via `get_catalogue_entry(embedding_catalogue_id)`. If not found, log a warning and return `None`.
4. Determine `deployment_id`:
   - Use `_configurations.embedding_deployment_id` if set.
   - Otherwise use the first entry in `embedding_catalogue.deployments`.
   - If no deployment is available, log a warning and return `None`.
5. Fetch the deployment via `get_deployment(deployment_id)`. If not found, log a warning and return `None`.
6. Build an `AiRequest` with `operation_type = EMBEDDING` and `EmbeddingPayload(input=description)`.
7. Invoke the embedding model via the provider's `invoke()` method. On failure, log the error and return `None`.
8. Extract the `embedding` field from the response output, cast all values to `float`, and return the list.

---

### `_normalize_catalogue_dict`

```python
def _normalize_catalogue_dict(data: dict) -> dict
```

#### implementation notes

1. For each item in `data["deployments"]` (if present), extract the bare record id (strip `table:` prefix) via `_doc_id_from_any`.
2. Replace the original list with the normalized `list[str]`.
3. Return the normalized dict.

---

### `_normalize_deployment_dict`

```python
def _normalize_deployment_dict(data: dict) -> dict
```

#### implementation notes

1. For each item in `data["secrets"]` (if present), extract the bare record id (strip `Secrets:` / `table:` prefix) via `_doc_id_from_any`.
2. Replace the original list with the normalized `list[str]`.
3. Return the normalized dict.

## methods

---

### initialize

```python
async def initialize(
    database_manager: IDatabaseManager,
    component_configurations: ModelComponentConfigurations
) -> bool
```

#### implementation notes

1. Store `database_manager` to `_database_manager`.
2. Store `component_configurations` to `_configurations`.
3. Call `ensure_indexes(component_configurations)`.
   - On failure (including `FullTextAnalyzerNotExistException`): raise `ModelComponentInitializationException`.
4. Return `True`.

---

### ensure_indexes

```python
async def ensure_indexes(
    component_configurations: ModelComponentConfigurations,
    overwrite: bool = False,
) -> bool
```

#### implementation notes

1. Obtain the default provider from `_database_manager`.
   - On failure: raise `ModelComponentOperationException`.
2. Verify that the analyzers referenced by `component_configurations.name_analyzer` and `component_configurations.description_analyzer` exist by calling a method in `IDatabaseManager`.
   - If either analyzer does not exist: raise `FullTextAnalyzerNotExistException`.
3. Create the indexes defined on `ModelCatalogueEntry` and `ModelDeployment`.
   - If `overwrite = True`: use `DEFINE INDEX OVERWRITE` with settings from `component_configurations`.
   - If `overwrite = False`: use `DEFINE INDEX IF NOT EXISTS` with the same settings.
   - On failure: raise `ModelComponentOperationException`.
4. Return `True`.

---

### create_catalogue_entry

```python
async def create_catalogue_entry(catalogue: ModelCatalogueEntry) -> ModelCatalogueEntry
```

#### implementation notes

1. Obtain the default provider from `_database_manager`.
   - On failure: raise `ModelComponentOperationException`.
2. If `catalogue.description_vector` is `None` and `catalogue.description` is non-empty, call `_embed_description_text(catalogue.description)` and set the result to `catalogue.description_vector`.
3. Execute a `BEGIN TRANSACTION` block:
   1. Build and execute the `CREATE` query:
      - If `catalogue.id` is `None` or empty: `CREATE ModelCatalogue CONTENT <json_without_id>`.
      - Otherwise: `CREATE type::thing('ModelCatalogue', '<id>') CONTENT <json>`.
   2. For each `deployment_id` in `catalogue.deployments` (if any), verify the deployment exists via `get_deployment(deployment_id)`. If not found: raise `ModelDeploymentNotFoundException` (rollback).
   3. For each `deployment_id` in `catalogue.deployments` (if any), execute: `RELATE type::thing('ModelCatalogue', '<created_id>') -> deployed_as -> type::thing('model_deployments', '<deployment_id>')`.
   4. `COMMIT TRANSACTION`.
   - On any failure: raise `ModelComponentOperationException` (transaction is rolled back).
4. Deserialize the created record as `ModelCatalogueEntry` and normalize via `_normalize_catalogue_dict`.
5. Return the created `ModelCatalogueEntry`.

---

### update_catalogue_entry

```python
async def update_catalogue_entry(catalogue: ModelCatalogueEntry) -> ModelCatalogueEntry
```

#### implementation notes

1. Obtain the default provider from `_database_manager`.
   - On failure: raise `ModelComponentOperationException`.
2. Validate that `catalogue.id` is non-empty.
   - On failure: raise `InvalidModelCatalogueEntryException`.
3. Fetch the current record by calling `get_catalogue_entry(catalogue.id)`.
   - If not found: raise `ModelCatalogueEntryNotFoundException`.
4. Handle `description_vector`:
   - If `description` changed: call `_embed_description_text` and set the returned vector to `catalogue.description_vector`.
   - If `description` is unchanged and `catalogue.description_vector` is `None`: copy `description_vector` from the previous record.
5. For each `deployment_id` in `catalogue.deployments` (if any), verify the deployment exists via `get_deployment(deployment_id)`. If not found: raise `ModelDeploymentNotFoundException`.
6. Execute a `BEGIN TRANSACTION` block:
   1. `UPDATE type::thing('ModelCatalogue', '<id>') MERGE <json>`.
   2. `DELETE deployed_as WHERE in = type::thing('ModelCatalogue', '<id>')`.
   3. For each `deployment_id` in `catalogue.deployments` (if any): `RELATE type::thing('ModelCatalogue', '<id>') -> deployed_as -> type::thing('model_deployments', '<deployment_id>')`.
   4. `COMMIT TRANSACTION`.
   - On any failure: raise `ModelComponentOperationException`.
7. Return the updated `ModelCatalogueEntry` (re-fetch via `get_catalogue_entry` or deserialize from UPDATE result).

---

### get_catalogue_entry

```python
async def get_catalogue_entry(id: str) -> ModelCatalogueEntry | None
```

#### implementation notes

1. Obtain the default provider from `_database_manager`.
   - On failure: raise `ModelComponentOperationException`.
2. Execute `SELECT *, ->deployed_as->model_deployments.id AS deployments FROM type::thing('ModelCatalogue', '<id>')`.
   - On failure: raise `ModelComponentOperationException`.
3. If no record is found, return `None`.
4. Normalize the result via `_normalize_catalogue_dict`.
5. Deserialize as `ModelCatalogueEntry` and return it.

---

### get_all_catalogue_entries

```python
async def get_all_catalogue_entries() -> list[ModelCatalogueEntry]
```

#### implementation notes

1. Obtain the default provider from `_database_manager`.
   - On failure: raise `ModelComponentOperationException`.
2. Execute `SELECT *, ->deployed_as->model_deployments.id AS deployments FROM ModelCatalogue`.
   - On failure: raise `ModelComponentOperationException`.
3. Normalize each result record via `_normalize_catalogue_dict`.
4. Deserialize each record as `ModelCatalogueEntry` and return the list. Return an empty list if no records are found.

---

### search_catalogue_entries

```python
async def search_catalogue_entries(catalogue_search_criteria: ModelCatalogueSearchCriteria) -> list[ModelCatalogueSearchResultEntry]
```

#### implementation notes

1. Obtain the default provider from `_database_manager`.
   - On failure: raise `ModelComponentOperationException`.
2. Build the SurrealQL query from `catalogue_search_criteria.to_query(provider, collection_name)`. The query must include `->deployed_as->model_deployments.id AS deployments` in the SELECT projection.
3. Execute the query.
   - On failure: raise `ModelComponentOperationException`.
4. Normalize each result record via `_normalize_catalogue_dict`.
5. Deserialize each record as `ModelCatalogueSearchResultEntry` and return the list. Return an empty list if no records are found.

---

### delete_catalogue_entry

```python
async def delete_catalogue_entry(id: str) -> None
```

#### implementation notes

1. Obtain the default provider from `_database_manager`.
   - On failure: raise `ModelComponentOperationException`.
2. Execute a `BEGIN TRANSACTION` block:
   1. `DELETE deployed_as WHERE in = type::thing('ModelCatalogue', '<id>')`.
   2. `DELETE type::thing('ModelCatalogue', '<id>') RETURN BEFORE`.
   3. `COMMIT TRANSACTION`.
   - On any failure: raise `ModelComponentOperationException`.
3. If the DELETE result is empty (no record was deleted): raise `ModelCatalogueEntryNotFoundException`.

---

### create_deployment

```python
async def create_deployment(deployment: ModelDeployment) -> ModelDeployment
```

#### implementation notes

1. Obtain the default provider from `_database_manager`.
   - On failure: raise `ModelComponentOperationException`.
2. Execute a `BEGIN TRANSACTION` block:
   1. Build and execute the `CREATE` query:
      - If `deployment.id` is `None` or empty: `CREATE model_deployments CONTENT <json_without_id>`.
      - Otherwise: `CREATE type::thing('model_deployments', '<key>') CONTENT <json>`.
   2. For each `secret_id` in `deployment.secrets` (if any): `RELATE type::thing('model_deployments', '<created_key>') -> references_secret -> type::thing('Secrets', '<secret_id>')`.
   3. `COMMIT TRANSACTION`.
   - On any failure: raise `ModelComponentOperationException`.
3. Deserialize the created record as `ModelDeployment` and normalize via `_normalize_deployment_dict`.
4. Return the created `ModelDeployment`.

---

### update_deployment

```python
async def update_deployment(deployment: ModelDeployment) -> ModelDeployment
```

#### implementation notes

1. Obtain the default provider from `_database_manager`.
   - On failure: raise `ModelComponentOperationException`.
2. Validate that `deployment.id` is non-empty.
   - On failure: raise `InvalidModelDeploymentException`.
3. Fetch the current record by calling `get_deployment(deployment.id)`.
   - If not found: raise `ModelDeploymentNotFoundException`.
4. Execute a `BEGIN TRANSACTION` block:
   1. `UPDATE type::thing('model_deployments', '<key>') MERGE <json>`.
   2. `DELETE references_secret WHERE in = type::thing('model_deployments', '<key>')`.
   3. For each `secret_id` in `deployment.secrets` (if any): `RELATE type::thing('model_deployments', '<key>') -> references_secret -> type::thing('Secrets', '<secret_id>')`.
   4. `COMMIT TRANSACTION`.
   - On any failure: raise `ModelComponentOperationException`.
5. Return the updated `ModelDeployment` (re-fetch via `get_deployment` or deserialize from UPDATE result).

---

### get_deployment

```python
async def get_deployment(id: str) -> ModelDeployment | None
```

#### implementation notes

1. Obtain the default provider from `_database_manager`.
   - On failure: raise `ModelComponentOperationException`.
2. Strip the table prefix from `id` to obtain the record key.
3. Execute `SELECT *, ->references_secret->Secrets.id AS secrets FROM type::thing('model_deployments', '<key>')`.
   - On failure: raise `ModelComponentOperationException`.
4. If no record is found, return `None`.
5. Normalize the result via `_normalize_deployment_dict`.
6. Deserialize and return the result as `ModelDeployment`.

---

### search_deployments

```python
async def search_deployments(search_criteria: ModelDeploymentSearchCriteria) -> list[ModelDeployment]
```

#### implementation notes

1. Obtain the default provider from `_database_manager`.
   - On failure: raise `ModelComponentOperationException`.
2. Build the SurrealQL query from `search_criteria.to_query(provider, collection_name)`. The query must include `->references_secret->Secrets.id AS secrets` in the SELECT projection.
3. Execute the query.
   - On failure: raise `ModelComponentOperationException`.
4. Normalize each result record via `_normalize_deployment_dict`.
5. Deserialize each record as `ModelDeployment` and return the list. Return an empty list if no records are found.

---

### delete_deployment

```python
async def delete_deployment(id: str) -> None
```

#### implementation notes

1. Obtain the default provider from `_database_manager`.
   - On failure: raise `ModelComponentOperationException`.
2. Strip the table prefix from `id` to obtain the record key.
3. Execute a `BEGIN TRANSACTION` block:
   1. `DELETE deployed_as WHERE out = type::thing('model_deployments', '<key>')`.
   2. `DELETE references_secret WHERE in = type::thing('model_deployments', '<key>')`.
   3. `DELETE type::thing('model_deployments', '<key>') RETURN BEFORE`.
   4. `COMMIT TRANSACTION`.
   - On any failure: raise `ModelComponentOperationException`.
4. If the DELETE result is empty (no record was deleted): raise `ModelDeploymentNotFoundException`.
