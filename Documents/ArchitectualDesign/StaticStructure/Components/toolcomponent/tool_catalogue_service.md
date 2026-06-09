---
class: ToolCatalogueService
kind: class
module: gafs.dynamicaiagent.toolcomponent
implements: [IToolCatalogueService]
dependencies:
  - IDatabaseManager
  - IDatabaseProvider
  - ToolCatalogueEntry
  - ToolCatalogueSearchResultEntry
  - ToolVersionEntry
  - ToolComponentConfigurations
  - ToolCatalogueSearchCriteria
  - ToolVersionEntrySearchCriteria
exceptions_used:
  - ToolComponentInitializationException
  - ToolComponentNotInitializedException
  - InvalidToolCatalogueEntryException
  - ConflictingToolCatalogueEntryException
  - ToolCatalogueEntryNotFoundException
  - InvalidToolCatalogueSearchCriteriaException
  - InvalidToolVersionEntryException
  - ConflictingToolVersionEntryException
  - ToolVersionEntryNotFoundException
  - InvalidToolVersionSearchCriteriaException
  - ToolComponentOperationException
  - ToolCatalogueIndexNotAvailableException
  - FullTextAnalyzerNotExistException
---

## fields

| name | type | description |
|------|------|-------------|
| `_logger` | `logging.Logger` | Logger instance |
| `_database_manager` | `IDatabaseManager \| None` | Set on `initialize` |
| `_database_provider` | `IDatabaseProvider \| None` | Default provider; set on `initialize` |
| `_configurations` | `ToolComponentConfigurations \| None` | Cached on `initialize` |

## private methods

---

### `_sync_code_to_filesystem`

```python
async def _sync_code_to_filesystem(version: ToolVersionEntry) -> None
```

#### implementation notes

1. Construct the code directory path: `{_configurations.app_data_folder}/tools/codes/{version.tool_id}_{version.id}/`.
2. Create the directory (and any required parent directories) if it does not already exist.
3. If `version.code` is set:
   - Write its contents to `{code_dir}/main.py`, overwriting any existing file.
4. If `version.code_link` is set:
   - If the code directory already contains files, remove them first.
   - Clone or download the repository at `version.code_link` into the code directory.
   - On failure: raise `ToolComponentOperationException`.
5. On any filesystem error: raise `ToolComponentOperationException`.

---

### `_delete_code_from_filesystem`

```python
def _delete_code_from_filesystem(tool_id: str, version_id: str) -> None
```

#### implementation notes

1. Construct the code directory path: `{_configurations.app_data_folder}/tools/codes/{tool_id}_{version_id}/`.
2. If the directory exists, remove it and all its contents.
3. Errors are logged but not propagated (best-effort).

## methods

---

### initialize

```python
async def initialize(
    database_manager: IDatabaseManager,
    component_configurations: ToolComponentConfigurations
) -> bool
```

#### implementation notes

1. Store `database_manager` to `_database_manager`.
2. Store `component_configurations` to `_configurations`.
3. Obtain the default provider from `database_manager` and store to `_database_provider`.
   - On failure: raise `ToolComponentInitializationException`.
4. Call `ensure_indexes(component_configurations)`.
   - On failure (including `FullTextAnalyzerNotExistException`): wrap and raise as `ToolComponentInitializationException`.
5. Return `True`.

---

### ensure_indexes

```python
async def ensure_indexes(
    configurations: ToolComponentConfigurations,
    overwrite: bool = False
) -> bool
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Verify that the analyzers referenced by `configurations.name_analyzer` and `configurations.description_analyzer` exist by calling the appropriate method on `_database_manager`.
   - If either does not exist: raise `FullTextAnalyzerNotExistException`.
3. Create the indexes defined on `ToolCatalogueEntry` and `ToolVersionEntry` (see model class design documents for index definitions):
   - If `overwrite = True`: use `DEFINE INDEX OVERWRITE` with settings derived from `configurations`.
   - If `overwrite = False`: use `DEFINE INDEX IF NOT EXISTS` with the same settings.
   - Vector index (`idx_tool_catalogue_description_vector`) uses `TYPE HNSW` with `DIST {vector_search_method}`, `DIMENSION {vector_dimensions}`, `TYPE {vector_data_type}`, `EFC {vector_exploration_factor}`, `M {vector_max_connections}`.
   - Full-text indexes use `SEARCH ANALYZER {name_analyzer|description_analyzer} BM25`.
   - On failure: raise `ToolComponentOperationException`.
4. Return `True`.

---

### create_tool_catalogue_entry

```python
async def create_tool_catalogue_entry(catalogue: ToolCatalogueEntry) -> ToolCatalogueEntry
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Validate `catalogue` (non-empty `name`, valid `status`). On failure: raise `InvalidToolCatalogueEntryException`.
3. Check for a duplicate `name` by querying `SELECT id FROM ToolCatalogue WHERE name = $name`. If a record is found: raise `ConflictingToolCatalogueEntryException`.
4. Build and execute:
   - If `catalogue.id` is `None` or empty: `CREATE ToolCatalogue CONTENT <json_without_id>`.
   - Otherwise: `CREATE type::thing('ToolCatalogue', '<id>') CONTENT <json>`.
   - On failure: raise `ToolComponentOperationException`.
5. Deserialize the created record as `ToolCatalogueEntry` and return it.

---

### update_tool_catalogue_entry

```python
async def update_tool_catalogue_entry(catalogue: ToolCatalogueEntry) -> ToolCatalogueEntry
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Validate that `catalogue.id` is non-empty. On failure: raise `InvalidToolCatalogueEntryException`.
3. Fetch the existing record via `get_tool_catalogue_entry(catalogue.id)`.
   - If not found: raise `ToolCatalogueEntryNotFoundException`.
4. If `catalogue.description_vector` is `None` and the existing record has a `description_vector`, copy it from the existing record (preserve existing vector unless explicitly replaced).
5. Execute `UPDATE type::thing('ToolCatalogue', '<id>') MERGE <json>`.
   - On failure: raise `ToolComponentOperationException`.
6. Return the updated `ToolCatalogueEntry` (re-fetch via `get_tool_catalogue_entry` or deserialize from the UPDATE result).

---

### delete_tool_catalogue_entry

```python
async def delete_tool_catalogue_entry(catalogue_id: str) -> None
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Fetch all associated version entries: `SELECT id, tool_id FROM ToolVersions WHERE tool_id = $catalogue_id`.
3. Execute a `BEGIN TRANSACTION` block:
   1. `DELETE ToolVersions WHERE tool_id = $catalogue_id`.
   2. `DELETE type::thing('ToolCatalogue', '<catalogue_id>') RETURN BEFORE`.
   3. `COMMIT TRANSACTION`.
   - If the DELETE result for the catalogue record is empty (no record deleted): raise `ToolCatalogueEntryNotFoundException` (rollback).
   - On any other failure: raise `ToolComponentOperationException` (rollback).
4. For each version entry fetched in step 2: call `_delete_code_from_filesystem(version.tool_id, version.id)` to clean up code directories (best-effort; errors are logged but do not fail the operation).

---

### get_tool_catalogue_entry

```python
async def get_tool_catalogue_entry(catalogue_id: str) -> ToolCatalogueEntry
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Execute `SELECT * FROM type::thing('ToolCatalogue', '<catalogue_id>')`.
   - On failure: raise `ToolComponentOperationException`.
3. If no record is found: raise `ToolCatalogueEntryNotFoundException`.
4. Deserialize and return the result as `ToolCatalogueEntry`.

---

### get_all_tool_catalogue_entries

```python
async def get_all_tool_catalogue_entries() -> list[ToolCatalogueEntry]
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Execute `SELECT * FROM ToolCatalogue`.
   - On failure: raise `ToolComponentOperationException`.
3. Deserialize each record as `ToolCatalogueEntry` and return the list. Return an empty list if no records are found.

---

### search_tool_catalogue_entries

```python
async def search_tool_catalogue_entries(
    search_criteria: ToolCatalogueSearchCriteria
) -> list[ToolCatalogueSearchResultEntry]
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Validate `search_criteria`. On failure: raise `InvalidToolCatalogueSearchCriteriaException`.
3. Build the SurrealQL query dynamically from `search_criteria`:
   - Base projection: `SELECT * FROM ToolCatalogue`.
   - `WHERE` clauses (all combined with `AND`):
     - `name = $name` if `search_criteria.name` is set.
     - `status IN $status` if `search_criteria.status` is set.
     - `description @@ $keywords` (BM25 full-text search) if `search_criteria.description_keywords` is set.
     - `description_vector <|{limit}|> $vector` (HNSW ANN search) if `search_criteria.description_vector` is set.
     - Tag filter from `search_criteria.tags` (AND: all tags must be present; OR: any tag must be present).
   - Append `LIMIT $limit`.
4. Execute the query.
   - On failure: raise `ToolComponentOperationException`.
5. For each matched `ToolCatalogueEntry`, fetch associated `ToolVersionEntry` records filtered by `search_criteria.version_status`:
   - Execute `SELECT * FROM ToolVersions WHERE tool_id = $tool_id AND status IN $version_status`.
   - If `search_criteria.version_status` is `None`, skip version filtering (return empty version list).
6. Construct a `ToolCatalogueSearchResultEntry` for each catalogue record, attaching the filtered version list.
7. Return the list of `ToolCatalogueSearchResultEntry`. Return an empty list if no records match.

---

### create_tool_version_entry

```python
async def create_tool_version_entry(version: ToolVersionEntry) -> ToolVersionEntry
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Validate `version` (non-empty `tool_id`). On failure: raise `InvalidToolVersionEntryException`.
   - Note: neither `code` nor `code_link` is required. If both are `None`, no filesystem sync is performed (code is assumed to be externally managed and already present on disk).
3. Verify that `version.tool_id` references a valid `ToolCatalogueEntry` via `get_tool_catalogue_entry(version.tool_id)`.
   - If not found: raise `ToolCatalogueEntryNotFoundException`.
4. Build and execute:
   - If `version.id` is `None` or empty: `CREATE ToolVersions CONTENT <json_without_id>`.
   - Otherwise: `CREATE type::thing('ToolVersions', '<id>') CONTENT <json>`.
   - On failure: raise `ToolComponentOperationException`.
5. Deserialize the created record as `ToolVersionEntry`.
6. Synchronise the code to the filesystem via `_sync_code_to_filesystem(created_version)`.
   - On failure: delete the newly created DB record in a rollback query (`DELETE type::thing('ToolVersions', '<id>')`), then raise `ToolComponentOperationException`.
7. Return the created `ToolVersionEntry`.

---

### update_tool_version_entry

```python
async def update_tool_version_entry(version: ToolVersionEntry) -> ToolVersionEntry
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Validate that `version.id` is non-empty. On failure: raise `InvalidToolVersionEntryException`.
3. Fetch the existing record via `get_tool_version_entry(version.id)`.
   - If not found: raise `ToolVersionEntryNotFoundException`.
4. Verify that `version.tool_id` references a valid `ToolCatalogueEntry`.
   - If not found: raise `ToolCatalogueEntryNotFoundException`.
5. Execute `UPDATE type::thing('ToolVersions', '<id>') MERGE <json>`.
   - On failure: raise `ToolComponentOperationException`.
6. If `version.code` or `version.code_link` changed from the existing record, re-synchronise via `_sync_code_to_filesystem(version)`.
   - On failure: rollback the UPDATE (`UPDATE type::thing('ToolVersions', '<id>') MERGE <previous_json>`), then raise `ToolComponentOperationException`.
7. Return the updated `ToolVersionEntry` (re-fetch or deserialize from UPDATE result).

---

### delete_tool_version_entry

```python
async def delete_tool_version_entry(version_id: str) -> None
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Fetch the existing record via `get_tool_version_entry(version_id)` to obtain `tool_id` for filesystem cleanup.
   - If not found: raise `ToolVersionEntryNotFoundException`.
3. Execute `DELETE type::thing('ToolVersions', '<version_id>') RETURN BEFORE`.
   - If the result is empty (no record deleted): raise `ToolVersionEntryNotFoundException`.
   - On other failure: raise `ToolComponentOperationException`.
4. Call `_delete_code_from_filesystem(version.tool_id, version_id)` to remove the code directory. Best-effort; errors are logged but not propagated.

---

### get_tool_version_entry

```python
async def get_tool_version_entry(version_id: str) -> ToolVersionEntry
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Execute `SELECT * FROM type::thing('ToolVersions', '<version_id>')`.
   - On failure: raise `ToolComponentOperationException`.
3. If no record is found: raise `ToolVersionEntryNotFoundException`.
4. Deserialize and return the result as `ToolVersionEntry`.

---

### get_all_tool_version_entries

```python
async def get_all_tool_version_entries(tool_id: str | None = None) -> list[ToolVersionEntry]
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. If `tool_id` is provided, verify the catalogue entry exists via `get_tool_catalogue_entry(tool_id)`.
   - If not found: raise `ToolCatalogueEntryNotFoundException`.
3. Build and execute:
   - If `tool_id` is `None`: `SELECT * FROM ToolVersions`.
   - Otherwise: `SELECT * FROM ToolVersions WHERE tool_id = $tool_id`.
   - On failure: raise `ToolComponentOperationException`.
4. Deserialize each record as `ToolVersionEntry` and return the list. Return an empty list if no records are found.

---

### search_tool_version_entries

```python
async def search_tool_version_entries(
    search_criteria: ToolVersionEntrySearchCriteria
) -> list[ToolVersionEntry]
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Validate `search_criteria`. On failure: raise `InvalidToolVersionSearchCriteriaException`.
3. Build the SurrealQL query dynamically:
   - Base: `SELECT * FROM ToolVersions`.
   - `WHERE` clauses (combined with `AND`):
     - `tool_id = $tool_id` if `search_criteria.tool_id` is set.
     - `status IN $status` if `search_criteria.status` is set.
   - Append `LIMIT $limit`.
4. Execute the query. On failure: raise `ToolComponentOperationException`.
5. Deserialize each record as `ToolVersionEntry` and return the list. Return an empty list if no records match.
