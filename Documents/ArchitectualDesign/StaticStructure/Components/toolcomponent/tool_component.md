---
class: ToolComponent
kind: class
module: gafs.dynamicaiagent.toolcomponent
implements: [IToolComponent]
dependencies:
  - IDatabaseManager
  - IDatabaseProvider
  - IToolCatalogueService
  - ISandboxCatalogueService
  - IDockerSandboxService
  - IModelComponent
  - ToolCatalogueEntry
  - ToolVersionEntry
  - SandboxCatalogueEntry
  - SandboxCatalogueDockerEntry
  - ToolCatalogueSearchResultEntry
  - ToolComponentConfigurations
  - ToolCatalogueSearchCriteria
  - ToolVersionEntrySearchCriteria
  - SandboxCatalogueSearchCriteria
  - AiRequest
  - DeploymentSelectionOptions
exceptions_used:
  - ToolComponentInitializationException
  - ToolComponentNotInitializedException
  - InvalidToolComponentConfigurationException
  - InvalidToolInvocationException
  - ToolCatalogueEntryNotFoundException
  - ToolVersionEntryNotFoundException
  - SandboxCatalogueEntryNotFoundException
  - ToolComponentOperationException
  - ToolCatalogueIndexNotAvailableException
---

## fields

| name | type | description |
|------|------|-------------|
| `_logger` | `logging.Logger` | Logger instance |
| `_tool_catalogue_service` | `IToolCatalogueService` | Injected on construction |
| `_sandbox_catalogue_service` | `ISandboxCatalogueService` | Injected on construction |
| `_docker_sandbox_service` | `IDockerSandboxService` | Injected on construction |
| `_model_component` | `IModelComponent \| None` | Injected on construction; used for description vector embedding. `None` if vector search is not needed. |
| `_database_manager` | `IDatabaseManager \| None` | Set on `initialize` |
| `_configurations` | `ToolComponentConfigurations \| None` | Cached after `initialize`; refreshed by `get_configurations` / `update_configurations` |
| `_is_rebuilding_vector_index` | `bool` | Flag set to `True` while the HNSW vector index is being rebuilt; blocks vector search during this period |

## private methods

---

### `_provider`

```python
async def _provider() -> IDatabaseProvider
```

#### implementation notes

1. If `_database_manager` is `None`: raise `ToolComponentNotInitializedException`.
2. Obtain the default provider from `_database_manager`.
   - If `None`: raise `ToolComponentNotInitializedException`.
3. Return the provider.

---

### `_load_configurations`

```python
async def _load_configurations() -> ToolComponentConfigurations
```

#### implementation notes

1. Obtain the default provider via `_provider()`.
2. Execute `SELECT * FROM component_configurations:tool_component`.
3. If a record is found, deserialize and return it as `ToolComponentConfigurations`.
4. If no record exists: raise `InvalidToolComponentConfigurationException` with a message indicating that `ToolComponentConfigurations` must be created before initialization (a default cannot be generated because `app_data_folder` has no default value).

---

### `_save_configurations`

```python
async def _save_configurations(configurations: ToolComponentConfigurations) -> ToolComponentConfigurations
```

#### implementation notes

1. Validate that `configurations.app_data_folder` is non-empty.
   - On failure: raise `InvalidToolComponentConfigurationException`.
2. Obtain the default provider via `_provider()`.
3. Execute `UPDATE component_configurations:tool_component MERGE <json>`.
   - If the result is `None`: raise `ToolComponentOperationException`.
4. Return the updated record deserialized as `ToolComponentConfigurations`.

---

### `_select_sandbox`

```python
async def _select_sandbox(version_entry: ToolVersionEntry) -> SandboxCatalogueDockerEntry
```

#### implementation notes

1. If `version_entry.sandbox_id` is set:
   1. Call `_sandbox_catalogue_service.get_catalogue_entry(version_entry.sandbox_id)`.
   2. If not found: raise `SandboxCatalogueEntryNotFoundException`.
   3. Cast the result to `SandboxCatalogueDockerEntry`. If the type is not Docker: raise `ToolComponentOperationException` with a message that the designated sandbox is not a Docker sandbox.
   4. Return the entry.
2. If `version_entry.sandbox_selection_tags` is set and non-empty:
   1. Build a `SandboxCatalogueSearchCriteria` with `status=[SandboxStatus.ACTIVE]` and `tags=TagsSearchCriteria(all=version_entry.sandbox_selection_tags)`.
   2. Call `_sandbox_catalogue_service.search_catalogue_entries(criteria)`.
   3. Filter the results to `SandboxCatalogueDockerEntry` instances only.
   4. If the filtered list is empty: raise `SandboxCatalogueEntryNotFoundException`.
   5. Return the first entry.
3. If neither is set: raise `ToolComponentOperationException` indicating no sandbox is configured for the version.

---

### `_validate_input_parameters`

```python
def _validate_input_parameters(
    version_entry: ToolVersionEntry,
    input_parameters: dict[str, Any],
) -> None
```

#### implementation notes

1. If `version_entry.input_parameters` is `None` or empty, return immediately.
2. Build a lookup `dict[str, InputParameterDefinition]` from `version_entry.input_parameters` keyed by `name`.
3. For each definition where `required = True`:
   - If the key is absent in `input_parameters` and `definition.default` is also `None`: raise `InvalidToolInvocationException` with the missing parameter name.
4. For each key in `input_parameters`:
   - If the key is not in the lookup: log a warning and continue (unknown parameters are tolerated).
   - Otherwise validate the value against `definition.allowed_values`, `definition.min_value`, and `definition.max_value`. On failure: raise `InvalidToolInvocationException` with the parameter name and reason.

---

### `_embed_text`

```python
async def _embed_text(text: str) -> list[float]
```

#### implementation notes

1. If `_model_component` is `None`: raise `InvalidToolComponentConfigurationException` indicating no model component is available for embedding.
2. Load configurations via `get_configurations()`.
3. If `_configurations.embedding_catalogue_id` is `None`: raise `InvalidToolComponentConfigurationException`.
4. Build an `AiRequest` with `operation_type = EMBEDDING`, `EmbeddingPayload(input=text)`, and `DeploymentSelectionOptions(deployment_type=CLOUD)`.
5. Call `_model_component.invoke(_configurations.embedding_catalogue_id, request, selection)`.
6. Extract and return the `embedding` list from the response output, casting all values to `float`.
   - If the output is missing or the type is incorrect: raise `ToolComponentOperationException`.

---

### `_drop_vector_index_safely`

```python
async def _drop_vector_index_safely() -> None
```

#### implementation notes

1. Obtain the default provider via `_provider()`.
2. Attempt `ALTER INDEX idx_tool_catalogue_description_vector ON ToolCatalogue PREPARE REMOVE` (best-effort; ignore any error).
3. Attempt `SELECT * FROM ToolCatalogue LIMIT 1 EXPLAIN` (best-effort; ignore any error).
4. Attempt `REMOVE INDEX idx_tool_catalogue_description_vector ON ToolCatalogue` (best-effort; ignore any error).

---

### `_clear_all_description_vectors`

```python
async def _clear_all_description_vectors() -> None
```

#### implementation notes

1. Obtain the default provider via `_provider()`.
2. Execute in a single transaction: `BEGIN TRANSACTION; UPDATE ToolCatalogue SET description_vector = NONE; COMMIT TRANSACTION`.

---

### `_reembed_all_catalogues`

```python
async def _reembed_all_catalogues() -> None
```

#### implementation notes

1. Call `_tool_catalogue_service.get_all_tool_catalogue_entries()` to fetch all entries.
2. For each entry that has a non-empty `description`:
   1. Call `_embed_text(entry.description)` to generate a new vector.
   2. Set `entry.description_vector` to the returned vector.
   3. Call `_tool_catalogue_service.update_tool_catalogue_entry(entry)`.

## methods

---

### initialize

```python
async def initialize(database_manager: IDatabaseManager) -> bool
```

#### implementation notes

1. Store `database_manager` to `_database_manager`.
2. Obtain the default provider from `database_manager`.
   - On failure: raise `ToolComponentInitializationException`.
3. Load `ToolComponentConfigurations` via `_load_configurations()` and cache in `_configurations`.
   - On failure: wrap and raise as `ToolComponentInitializationException`.
4. Call `_tool_catalogue_service.initialize(database_manager, _configurations)`.
   - On failure: raise `ToolComponentInitializationException`.
5. Call `_sandbox_catalogue_service.initialize(database_manager, _configurations)`.
   - On failure: raise `ToolComponentInitializationException`.
6. Call `_docker_sandbox_service.initialize(database_manager, _sandbox_catalogue_service, _configurations)`.
   - On failure: raise `ToolComponentInitializationException`.
7. Return `True`.

---

### invoke

```python
async def invoke(tool_id: str, version_id: str, input_parameters: dict[str, Any]) -> dict[str, Any]
```

#### implementation notes

1. If `_database_manager` is `None`: raise `ToolComponentNotInitializedException`.
2. Call `_tool_catalogue_service.get_tool_catalogue_entry(tool_id)`.
   - If not found (`ToolCatalogueEntryNotFoundException`): re-raise as-is.
3. Call `_tool_catalogue_service.get_tool_version_entry(version_id)`.
   - If not found (`ToolVersionEntryNotFoundException`): re-raise as-is.
4. Call `_validate_input_parameters(version_entry, input_parameters)`.
   - On failure: raise `InvalidToolInvocationException`.
5. Call `_select_sandbox(version_entry)` to obtain a `SandboxCatalogueDockerEntry`.
   - On failure: re-raise as-is.
6. Call `_docker_sandbox_service.execute_code(version_entry, sandbox_entry, input_parameters)`.
   - On failure: wrap and re-raise as `ToolComponentOperationException` (unless already a `ToolComponentException`).
7. Return the output parameter dict.

---

### create_tool_catalogue_entry

```python
async def create_tool_catalogue_entry(catalogue: ToolCatalogueEntry) -> ToolCatalogueEntry
```

*Delegates to `IToolCatalogueService.create_tool_catalogue_entry`.*

#### implementation notes

1. If `catalogue.description` is non-empty and `catalogue.description_vector` is `None`, call `_embed_text(catalogue.description)` and set the result to `catalogue.description_vector`. Log a warning and continue if embedding fails.
2. Call `_tool_catalogue_service.create_tool_catalogue_entry(catalogue)` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### update_tool_catalogue_entry

```python
async def update_tool_catalogue_entry(catalogue: ToolCatalogueEntry) -> ToolCatalogueEntry
```

*Delegates to `IToolCatalogueService.update_tool_catalogue_entry`.*

#### implementation notes

1. If `catalogue.description` is non-empty and `catalogue.description_vector` is `None`, call `_embed_text(catalogue.description)` and set the result to `catalogue.description_vector`. Log a warning and continue if embedding fails.
2. Call `_tool_catalogue_service.update_tool_catalogue_entry(catalogue)` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### delete_tool_catalogue_entry

```python
async def delete_tool_catalogue_entry(catalogue_id: str) -> None
```

*Delegates to `IToolCatalogueService.delete_tool_catalogue_entry`.*

#### implementation notes

1. Call `_tool_catalogue_service.delete_tool_catalogue_entry(catalogue_id)`.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### get_tool_catalogue_entry

```python
async def get_tool_catalogue_entry(catalogue_id: str) -> ToolCatalogueEntry
```

*Delegates to `IToolCatalogueService.get_tool_catalogue_entry`.*

#### implementation notes

1. Call `_tool_catalogue_service.get_tool_catalogue_entry(catalogue_id)` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### get_all_tool_catalogue_entries

```python
async def get_all_tool_catalogue_entries() -> list[ToolCatalogueEntry]
```

*Delegates to `IToolCatalogueService.get_all_tool_catalogue_entries`.*

#### implementation notes

1. Call `_tool_catalogue_service.get_all_tool_catalogue_entries()` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### search_tool_catalogue_entries

```python
async def search_tool_catalogue_entries(search_criteria: ToolCatalogueSearchCriteria) -> list[ToolCatalogueSearchResultEntry]
```

*Delegates to `IToolCatalogueService.search_tool_catalogue_entries`.*

#### implementation notes

1. If `_is_rebuilding_vector_index` is `True` and `search_criteria.description_vector` is not `None`: raise `ToolCatalogueIndexNotAvailableException`.
2. Call `_tool_catalogue_service.search_tool_catalogue_entries(search_criteria)` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### create_tool_version_entry

```python
async def create_tool_version_entry(version: ToolVersionEntry) -> ToolVersionEntry
```

*Delegates to `IToolCatalogueService.create_tool_version_entry`.*

#### implementation notes

1. Call `_tool_catalogue_service.create_tool_version_entry(version)` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### update_tool_version_entry

```python
async def update_tool_version_entry(version: ToolVersionEntry) -> ToolVersionEntry
```

*Delegates to `IToolCatalogueService.update_tool_version_entry`.*

#### implementation notes

1. Call `_tool_catalogue_service.update_tool_version_entry(version)` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### delete_tool_version_entry

```python
async def delete_tool_version_entry(version_id: str) -> None
```

*Delegates to `IToolCatalogueService.delete_tool_version_entry`.*

#### implementation notes

1. Call `_tool_catalogue_service.delete_tool_version_entry(version_id)`.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### get_tool_version_entry

```python
async def get_tool_version_entry(version_id: str) -> ToolVersionEntry
```

*Delegates to `IToolCatalogueService.get_tool_version_entry`.*

#### implementation notes

1. Call `_tool_catalogue_service.get_tool_version_entry(version_id)` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### get_all_tool_version_entries

```python
async def get_all_tool_version_entries(tool_id: str | None = None) -> list[ToolVersionEntry]
```

*Delegates to `IToolCatalogueService.get_all_tool_version_entries`.*

#### implementation notes

1. Call `_tool_catalogue_service.get_all_tool_version_entries(tool_id)` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### search_tool_version_entries

```python
async def search_tool_version_entries(search_criteria: ToolVersionEntrySearchCriteria) -> list[ToolVersionEntry]
```

*Delegates to `IToolCatalogueService.search_tool_version_entries`.*

#### implementation notes

1. Call `_tool_catalogue_service.search_tool_version_entries(search_criteria)` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### create_sandbox_catalogue_entry

```python
async def create_sandbox_catalogue_entry(catalogue: SandboxCatalogueEntry) -> SandboxCatalogueEntry
```

*Delegates to `ISandboxCatalogueService.create_catalogue_entry`.*

#### implementation notes

1. Call `_sandbox_catalogue_service.create_catalogue_entry(catalogue)` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### update_sandbox_catalogue_entry

```python
async def update_sandbox_catalogue_entry(catalogue: SandboxCatalogueEntry) -> SandboxCatalogueEntry
```

*Delegates to `ISandboxCatalogueService.update_catalogue_entry`.*

#### implementation notes

1. Call `_sandbox_catalogue_service.update_catalogue_entry(catalogue)` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### delete_sandbox_catalogue_entry

```python
async def delete_sandbox_catalogue_entry(catalogue_id: str) -> None
```

*Delegates to `ISandboxCatalogueService.delete_catalogue_entry`.*

#### implementation notes

1. Call `_sandbox_catalogue_service.delete_catalogue_entry(catalogue_id)`.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### get_sandbox_catalogue_entry

```python
async def get_sandbox_catalogue_entry(catalogue_id: str) -> SandboxCatalogueEntry
```

*Delegates to `ISandboxCatalogueService.get_catalogue_entry`.*

#### implementation notes

1. Call `_sandbox_catalogue_service.get_catalogue_entry(catalogue_id)` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### get_all_sandbox_catalogue_entries

```python
async def get_all_sandbox_catalogue_entries() -> list[SandboxCatalogueEntry]
```

*Delegates to `ISandboxCatalogueService.get_all_catalogue_entries`.*

#### implementation notes

1. Call `_sandbox_catalogue_service.get_all_catalogue_entries()` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### search_sandbox_catalogue_entries

```python
async def search_sandbox_catalogue_entries(search_criteria: SandboxCatalogueSearchCriteria) -> list[SandboxCatalogueEntry]
```

*Delegates to `ISandboxCatalogueService.search_catalogue_entries`.*

#### implementation notes

1. Call `_sandbox_catalogue_service.search_catalogue_entries(search_criteria)` and return the result.
   - On any exception that is not already a `ToolComponentException`: wrap and re-raise as `ToolComponentOperationException`.

---

### get_configurations

```python
async def get_configurations() -> ToolComponentConfigurations
```

#### implementation notes

1. If `_configurations` is `None`, call `_load_configurations()` and cache the result in `_configurations`.
2. Return `_configurations`.
   - On any exception: wrap and re-raise as `ToolComponentOperationException`.

---

### update_configurations

```python
async def update_configurations(configurations: ToolComponentConfigurations) -> ToolComponentConfigurations
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
   4. Persist the new configurations via `_save_configurations(configurations)` and cache in `_configurations`.
   5. Call `_tool_catalogue_service.ensure_indexes(_configurations, overwrite=True)` to recreate the HNSW index with the new settings.
   6. If `requires_reembed`: call `_reembed_all_catalogues()` to regenerate all description vectors using the new embedding model.
   7. Set `_is_rebuilding_vector_index = False` in a `finally` block to ensure it is always reset.
5. Return `_configurations`.
   - On any exception: wrap and re-raise as `ToolComponentOperationException`.
