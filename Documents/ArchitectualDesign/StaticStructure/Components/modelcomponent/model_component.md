---
class: ModelComponent
kind: class
module: gafs.dynamicaiagent.modelcomponent
implements: [IModelComponent]
---

## fields

| name | type | description |
|------|------|-------------|
| `_logger` | `logging.Logger` | Logger instance |
| `_model_catalogue_service` | `IModelCatalogueService` | Injected on construction |
| `_model_service` | `IModelService` | Injected on construction |
| `_cloud_ai_component` | `Any \| None` | Injected on construction; forwarded to `IModelService.initialize` |
| `_database_manager` | `IDatabaseManager \| None` | Set on `initialize` |
| `_configurations` | `ModelComponentConfigurations \| None` | Cached after `initialize`; refreshed by `get_configurations` / `update_configurations` |
| `_is_rebuilding_vector_index` | `bool` | Flag set to `True` while the vector index is being rebuilt; blocks vector search |

## private methods

---

### _provider

```python
async def _provider() -> IDatabaseProvider
```

#### implementation notes

1. If `_database_manager` is `None`: raise `ModelComponentNotInitializedException`.
2. Obtain the default provider from `_database_manager`.
   - If `None`: raise `ModelComponentNotInitializedException`.
3. Return the provider.

---

### _load_or_create_configurations

```python
async def _load_or_create_configurations() -> ModelComponentConfigurations
```

#### implementation notes

1. Obtain the default provider via `_provider()`.
2. Execute `SELECT * FROM ModelComponentConfigurations:<default_id>`.
3. If a record is found, deserialize and return it as `ModelComponentConfigurations`.
4. If no record exists, create a default `ModelComponentConfigurations()` and execute `CREATE ModelComponentConfigurations:<default_id> CONTENT <json>`. Return the created record.
   - On failure: raise `ModelComponentOperationException`.

---

### _save_configurations

```python
async def _save_configurations(configurations: ModelComponentConfigurations) -> ModelComponentConfigurations
```

#### implementation notes

1. Obtain the default provider via `_provider()`.
2. Execute `UPDATE ModelComponentConfigurations:<default_id> MERGE <json>`.
   - If the result is `None`: raise `ModelComponentOperationException`.
3. Return the updated record.

---

### _drop_vector_index_safely

```python
async def _drop_vector_index_safely() -> None
```

#### implementation notes

1. Obtain the default provider via `_provider()`.
2. Attempt `ALTER INDEX idx_model_catalogues_description_vector ON ModelCatalogue PREPARE REMOVE` (best-effort; ignore any error).
3. Attempt `SELECT * FROM ModelCatalogue LIMIT 1 EXPLAIN` (best-effort; ignore any error).
4. Attempt `REMOVE INDEX idx_model_catalogues_description_vector ON ModelCatalogue` (best-effort; ignore any error).

---

### _clear_all_description_vectors

```python
async def _clear_all_description_vectors() -> None
```

#### implementation notes

1. Obtain the default provider via `_provider()`.
2. Execute in a single transaction: `BEGIN TRANSACTION; UPDATE ModelCatalogue SET description_vector = NONE; COMMIT TRANSACTION`.

---

### _reembed_all_catalogues

```python
async def _reembed_all_catalogues() -> None
```

#### implementation notes

1. Obtain the default provider via `_provider()`.
2. Fetch all `ModelCatalogueEntry` records: `SELECT * FROM ModelCatalogue`.
3. For each record that has a non-empty `description`:
   1. Call `_embed_text(description)` to generate a new embedding vector.
   2. Set `catalogue.description_vector` to the returned vector.
   3. Call `_model_catalogue_service.update_catalogue_entry(catalogue)`.

---

### _embed_text

```python
async def _embed_text(text: str) -> list[float]
```

#### implementation notes

1. Load configurations via `get_configurations()`.
2. If `embedding_catalogue_id` is `None`: raise `InvalidModelComponentConfigurationException`.
3. Build `AiRequest` with `operation_type = EMBEDDING`, `EmbeddingPayload(input=text)`, and `DeploymentSelectionOptions(deployment_type=CLOUD)`.
4. Call `_model_service.invoke(embedding_catalogue_id, request, selection)`.
5. Extract and return the `embedding` list from the response output, casting all values to `float`.
   - If output is missing or invalid: raise `ModelComponentOperationException`.

## methods

---

### initialize

```python
async def initialize(database_manager: IDatabaseManager) -> bool
```

#### implementation notes

1. Store `database_manager` to `_database_manager`.
2. Obtain the default provider from `database_manager`.
   - On failure: raise `ModelComponentInitializationException`.
3. Load or create `ModelComponentConfigurations` via `_load_or_create_configurations()` and cache it in `_configurations`.
4. Call `_model_catalogue_service.initialize(database_manager, _configurations)`.
5. Call `_model_service.initialize(database_manager, _model_catalogue_service, _cloud_ai_component)`.
6. Return `True`.

---

### invoke

```python
async def invoke(
    catalogue_id: str,
    request: AiRequest,
    deployment_selection_options: DeploymentSelectionOptions | None = None,
) -> AiResponse
```

*Delegates to `IModelService.invoke`.*

#### implementation notes

1. Call `_model_service.invoke(catalogue_id, request, deployment_selection_options)` and return the result.
   - On any exception: wrap and re-raise as `ModelComponentOperationException` (unless it is already a `ModelComponentException`).

---

### create_catalogue_entry

```python
async def create_catalogue_entry(catalogue: ModelCatalogueEntry) -> ModelCatalogueEntry
```

*Delegates to `IModelCatalogueService.create_catalogue_entry`.*

#### implementation notes

1. Call `_model_catalogue_service.create_catalogue_entry(catalogue)` and return the result.
   - On any exception: wrap and re-raise as `ModelComponentOperationException`.

---

### update_catalogue_entry

```python
async def update_catalogue_entry(catalogue: ModelCatalogueEntry) -> ModelCatalogueEntry
```

*Delegates to `IModelCatalogueService.update_catalogue_entry`.*

#### implementation notes

1. Call `_model_catalogue_service.update_catalogue_entry(catalogue)` and return the result.
   - On any exception: wrap and re-raise as `ModelComponentOperationException`.

---

### delete_catalogue_entry

```python
async def delete_catalogue_entry(catalogue_id: str) -> None
```

*Delegates to `IModelCatalogueService.delete_catalogue_entry`.*

#### implementation notes

1. Call `_model_catalogue_service.delete_catalogue_entry(catalogue_id)`.
   - On any exception: wrap and re-raise as `ModelComponentOperationException` (unless it is already a `ModelComponentException`).

---

### get_catalogue_entry

```python
async def get_catalogue_entry(catalogue_id: str) -> ModelCatalogueEntry
```

*Delegates to `IModelCatalogueService.get_catalogue_entry`.*

#### implementation notes

1. Call `_model_catalogue_service.get_catalogue_entry(catalogue_id)`.
2. If the result is `None`: raise `ModelCatalogueEntryNotFoundException`.
3. Return the result.
   - On any other exception: wrap and re-raise as `ModelComponentOperationException`.

---

### get_all_catalogue_entries

```python
async def get_all_catalogue_entries() -> list[ModelCatalogueEntry]
```

*Delegates to `IModelCatalogueService.get_all_catalogue_entries`.*

#### implementation notes

1. Call `_model_catalogue_service.get_all_catalogue_entries()` and return the result.
   - On any exception: wrap and re-raise as `ModelComponentOperationException`.

---

### search_catalogue_entries

```python
async def search_catalogue_entries(search_criteria: ModelCatalogueSearchCriteria) -> list[ModelCatalogueSearchResultEntry]
```

*Delegates to `IModelCatalogueService.search_catalogue_entries`.*

#### implementation notes

1. If `_is_rebuilding_vector_index` is `True` and `search_criteria.vector` is not `None`: raise `ModelCatalogueIndexNotAvailableException`.
2. Call `_model_catalogue_service.search_catalogue_entries(search_criteria)` and return the result.
   - On any exception: wrap and re-raise as `ModelComponentOperationException`.

---

### create_deployment

```python
async def create_deployment(deployment: ModelDeployment) -> ModelDeployment
```

*Delegates to `IModelCatalogueService.create_deployment`.*

#### implementation notes

1. Call `_model_catalogue_service.create_deployment(deployment)` and return the result.
   - On any exception: wrap and re-raise as `ModelComponentOperationException`.

---

### update_deployment

```python
async def update_deployment(deployment: ModelDeployment) -> ModelDeployment
```

*Delegates to `IModelCatalogueService.update_deployment`.*

#### implementation notes

1. Call `_model_catalogue_service.update_deployment(deployment)` and return the result.
   - On any exception: wrap and re-raise as `ModelComponentOperationException`.

---

### delete_deployment

```python
async def delete_deployment(deployment_id: str) -> None
```

*Delegates to `IModelCatalogueService.delete_deployment`.*

#### implementation notes

1. Call `_model_catalogue_service.delete_deployment(deployment_id)`.
   - On any exception: wrap and re-raise as `ModelComponentOperationException` (unless it is already a `ModelComponentException`).

---

### get_deployment

```python
async def get_deployment(deployment_id: str) -> ModelDeployment | None
```

*Delegates to `IModelCatalogueService.get_deployment`.*

#### implementation notes

1. Call `_model_catalogue_service.get_deployment(deployment_id)` and return the result.
   - On any exception: wrap and re-raise as `ModelComponentOperationException`.

---

### search_deployments

```python
async def search_deployments(search_criteria: ModelDeploymentSearchCriteria) -> list[ModelDeployment]
```

*Delegates to `IModelCatalogueService.search_deployments`.*

#### implementation notes

1. Call `_model_catalogue_service.search_deployments(search_criteria)` and return the result.
   - On any exception: wrap and re-raise as `ModelComponentOperationException`.

---

### get_configurations

```python
async def get_configurations() -> ModelComponentConfigurations
```

#### implementation notes

1. If `_configurations` is `None`, call `_load_or_create_configurations()` and cache the result.
2. Return `_configurations`.
   - On any exception: wrap and re-raise as `ModelComponentOperationException`.

---

### update_configurations

```python
async def update_configurations(configurations: ModelComponentConfigurations) -> ModelComponentConfigurations
```

#### implementation notes

1. Fetch the current configurations via `get_configurations()`.
2. Determine whether the vector index requires changes:
   - `requires_reembed`: `True` if `embedding_catalogue_id`, `vector_data_type`, or `vector_dimensions` changed.
   - `requires_rebuild_only`: `True` if `vector_search_method`, `vector_exploration_factor`, or `vector_max_connections` changed.
   - `needs_vector_rebuild = requires_reembed OR requires_rebuild_only`.
3. If `needs_vector_rebuild` is `False`:
   1. Persist configurations via `_save_configurations(configurations)` and cache in `_configurations`.
   2. Return `_configurations`.
4. If `needs_vector_rebuild` is `True`:
   1. Set `_is_rebuilding_vector_index = True`.
   2. Call `_drop_vector_index_safely()` to remove the HNSW index.
   3. If `requires_reembed`: call `_clear_all_description_vectors()` to null all vectors.
   4. Persist new configurations via `_save_configurations(configurations)` and cache in `_configurations`.
   5. Call `_model_catalogue_service.ensure_indexes(_configurations, overwrite=True)` to recreate the HNSW index with new settings.
   6. If `requires_reembed`: call `_reembed_all_catalogues()` to regenerate all description vectors using the new embedding model.
   7. Set `_is_rebuilding_vector_index = False` (in a `finally` block to ensure it is always reset).
5. Return `_configurations`.
   - On any exception: wrap and re-raise as `ModelComponentOperationException`.
