---
class: IToolCatalogueService
kind: abstract_class
module: gafs.dynamicaiagent.toolcomponent
inherits: [ABC]
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

## responsibilities

- CRUD and search operations on `ToolCatalogueEntry` and `ToolVersionEntry` records in the database.
- Manage indexes on the `ToolCatalogue` and `ToolVersions` collections.
- Synchronise tool code to the filesystem under `{app_data_folder}/tools/codes/{tool_catalogue_id}_{tool_version_id}/` on version entry create/update.

## methods

---

### initialize

```python
async def initialize(
    database_manager: IDatabaseManager,
    component_configurations: ToolComponentConfigurations
) -> bool
```

| property    | value |
| ----------- | ----- |
| async       | true  |
| description | Initialize the catalogue service. Obtains a database provider from `database_manager` and ensures indexes both for `ToolCatalogueEntry` and `ToolVersionEntry`.<br>Indexes are defined in model class design documentations. |

#### returns

| type   | value  | description              |
| ------ | ------ | ------------------------ |
| `bool` | `True` | Successfully initialized |

#### raises

| exception                              | condition              |
| -------------------------------------- | ---------------------- |
| `ToolComponentInitializationException` | Initialization failure |

#### rules

- Some of the indexes reference Full Text Analyzers. The analyzers are managed by `IDatabaseManager` and the existence of the referenced analyzers must be confirmed before the creations of the indexes. (raise `FullTextAnalyzerNotExistException` on failure)
- This method is expected to internally call `ensure_indexes` method, but on failure, is expected to finally raise exception as `ToolComponentInitializationException`.

---

### ensure_indexes

```python
async def ensure_indexes(
    configurations: ToolComponentConfigurations,
    overwrite: bool = False
) -> bool
```

| property    | value |
| ----------- | ----- |
| async       | true  |
| description | Create or update indexes on `ToolCatalogue` and `ToolVersions` collections.<br>Indexes are defined in model class design documents. |

#### raises

| exception                              | condition                                                            |
| -------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException` | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `ToolComponentOperationException`      | Operation failures including index creation failures                 |
| `FullTextAnalyzerNotExistException`    | The referenced `FullTextAnalyzer` does not exist.                    |

#### rules

- If `overwrite = False`, send queries as `IF NOT EXISTS`, otherwise as `OVERWRITE`.
- Some of the indexes reference Full Text Analyzers. The analyzers are managed by `IDatabaseManager` and the existence of the referenced analyzers must be confirmed before the creations/updates of the indexes. (raise `FullTextAnalyzerNotExistException` on failure)

---

### create_tool_catalogue_entry

```python
async def create_tool_catalogue_entry(catalogue: ToolCatalogueEntry) -> ToolCatalogueEntry
```

| property    | value                           |
| ----------- | ------------------------------- |
| async       | true                            |
| description | Persist a new tool catalogue record. |

#### raises

| exception                                  | condition                                                            |
| ------------------------------------------ | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException`     | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidToolCatalogueEntryException`       | Validation failure                                                   |
| `ConflictingToolCatalogueEntryException`   | The entry conflicts with another entry.<br>(duplicated `name`)       |
| `ToolComponentOperationException`          | Database operation failures                                          |

---

### update_tool_catalogue_entry

```python
async def update_tool_catalogue_entry(catalogue: ToolCatalogueEntry) -> ToolCatalogueEntry
```

| property    | value                                                    |
| ----------- | -------------------------------------------------------- |
| async       | true                                                     |
| description | Update an existing tool catalogue record. `id` must be set. |

#### raises

| exception                              | condition                                                            |
| -------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException` | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidToolCatalogueEntryException`   | Invalid request entry including a case that the `id` is empty.      |
| `ToolCatalogueEntryNotFoundException`  | No record with the given `id` exists.                                |
| `ToolComponentOperationException`      | Database operation failures                                          |

---

### delete_tool_catalogue_entry

```python
async def delete_tool_catalogue_entry(catalogue_id: str) -> None
```

| property    | value                                        |
| ----------- | -------------------------------------------- |
| async       | true                                         |
| description | Delete a tool catalogue record by `catalogue_id`. |

#### raises

| exception                              | condition                                                            |
| -------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException` | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `ToolCatalogueEntryNotFoundException`  | No record with the given `catalogue_id` exists.                      |
| `ToolComponentOperationException`      | Database operation failures                                          |

#### rules

- All associated `ToolVersionEntry` records must be deleted in the same transaction.

---

### get_tool_catalogue_entry

```python
async def get_tool_catalogue_entry(catalogue_id: str) -> ToolCatalogueEntry
```

| property    | value                                                |
| ----------- | ---------------------------------------------------- |
| async       | true                                                 |
| description | Retrieve a single tool catalogue record by its `id`. |

#### raises

| exception                              | condition                                                            |
| -------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException` | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `ToolCatalogueEntryNotFoundException`  | No record with the given `catalogue_id` exists.                      |
| `ToolComponentOperationException`      | Database operation failures                                          |

---

### get_all_tool_catalogue_entries

```python
async def get_all_tool_catalogue_entries() -> list[ToolCatalogueEntry]
```

| property    | value                                   |
| ----------- | --------------------------------------- |
| async       | true                                    |
| description | Return all tool catalogue records. |

#### raises

| exception                              | condition                                                            |
| -------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException` | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `ToolComponentOperationException`      | Database operation failures                                          |

---

### search_tool_catalogue_entries

```python
async def search_tool_catalogue_entries(
    search_criteria: ToolCatalogueSearchCriteria
) -> list[ToolCatalogueSearchResultEntry]
```

| property    | value                                                                                      |
| ----------- | ------------------------------------------------------------------------------------------ |
| async       | true                                                                                       |
| description | Search tool catalogue records using `search_criteria`. Returns matched entries with their associated version records filtered by `version_status`. |

#### raises

| exception                                   | condition                                                                              |
| ------------------------------------------- | -------------------------------------------------------------------------------------- |
| `ToolComponentNotInitializedException`      | Tool component is not fully initialized.<br>(No `IDatabaseManager`)                   |
| `InvalidToolCatalogueSearchCriteriaException` | `search_criteria` is invalid.                                                        |
| `ToolCatalogueIndexNotAvailableException`   | The vector index is currently unavailable (e.g., being rebuilt) and vector search was requested. |
| `ToolComponentOperationException`           | Database operation failures                                                            |

---

### create_tool_version_entry

```python
async def create_tool_version_entry(version: ToolVersionEntry) -> ToolVersionEntry
```

| property    | value                               |
| ----------- | ----------------------------------- |
| async       | true                                |
| description | Persist a new tool version record. |

#### raises

| exception                              | condition                                                            |
| -------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException` | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidToolVersionEntryException`     | Validation failure                                                   |
| `ConflictingToolVersionEntryException` | The version entry conflicts with another entry.<br>(duplicated `id`) |
| `ToolCatalogueEntryNotFoundException`  | `tool_id` references a non-existent `ToolCatalogueEntry`.            |
| `ToolComponentOperationException`      | Database operation failures                                          |

#### rules

- `version.tool_id` must reference a valid `ToolCatalogueEntry`. (raise `ToolCatalogueEntryNotFoundException` on failure)
- Neither `version.code` nor `version.code_link` is required. When both are `None`, no filesystem sync is performed and the code is assumed to be externally managed and already present on disk at `{app_data_folder}/tools/codes/{version.tool_id}_{version.id}/main.py`.
- After the DB record is persisted and the version `id` is assigned, synchronise code to the filesystem if applicable:
  - If `version.code` is set: write its contents to `{app_data_folder}/tools/codes/{version.tool_id}_{version.id}/main.py` (create directory as needed).
  - If `version.code_link` is set: clone/download the repository to `{app_data_folder}/tools/codes/{version.tool_id}_{version.id}/`.
  - Filesystem failure must raise `ToolComponentOperationException` and roll back the DB record within the same transaction.

---

### update_tool_version_entry

```python
async def update_tool_version_entry(version: ToolVersionEntry) -> ToolVersionEntry
```

| property    | value                                                      |
| ----------- | ---------------------------------------------------------- |
| async       | true                                                       |
| description | Update an existing tool version record. `id` must be set. |

#### raises

| exception                              | condition                                                            |
| -------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException` | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidToolVersionEntryException`     | Invalid request entry including a case that the `id` is empty.      |
| `ToolVersionEntryNotFoundException`    | No record with the given `id` exists.                                |
| `ToolCatalogueEntryNotFoundException`  | `tool_id` references a non-existent `ToolCatalogueEntry`.            |
| `ToolComponentOperationException`      | Database operation failures                                          |

#### rules

- After the DB record is updated, re-synchronise code to the filesystem:
  - If `version.code` changed: overwrite `{app_data_folder}/tools/codes/{version.tool_id}_{version.id}/main.py`.
  - If `version.code_link` changed: re-clone/download to `{app_data_folder}/tools/codes/{version.tool_id}_{version.id}/`.
  - Filesystem failure must raise `ToolComponentOperationException` and roll back the DB update.

---

### delete_tool_version_entry

```python
async def delete_tool_version_entry(version_id: str) -> None
```

| property    | value                                        |
| ----------- | -------------------------------------------- |
| async       | true                                         |
| description | Delete a tool version record by `version_id`. |

#### raises

| exception                              | condition                                                            |
| -------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException` | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `ToolVersionEntryNotFoundException`    | No record with the given `version_id` exists.                        |
| `ToolComponentOperationException`      | Database operation failures                                          |

#### rules

- After the DB record is deleted, remove the code directory `{app_data_folder}/tools/codes/{version.tool_id}_{version_id}/` from the filesystem. Best-effort; filesystem errors are logged but do not cause the operation to fail.

---

### get_tool_version_entry

```python
async def get_tool_version_entry(version_id: str) -> ToolVersionEntry
```

| property    | value                                               |
| ----------- | --------------------------------------------------- |
| async       | true                                                |
| description | Retrieve a single tool version record by its `id`. |

#### raises

| exception                              | condition                                                            |
| -------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException` | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `ToolVersionEntryNotFoundException`    | No record with the given `version_id` exists.                        |
| `ToolComponentOperationException`      | Database operation failures                                          |

---

### get_all_tool_version_entries

```python
async def get_all_tool_version_entries(tool_id: str | None = None) -> list[ToolVersionEntry]
```

| property    | value                                                                              |
| ----------- | ---------------------------------------------------------------------------------- |
| async       | true                                                                               |
| description | Return all tool version records. If `tool_id` is given, return only versions belonging to that tool. |

#### raises

| exception                              | condition                                                            |
| -------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException` | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `ToolCatalogueEntryNotFoundException`  | `tool_id` references a non-existent `ToolCatalogueEntry`.            |
| `ToolComponentOperationException`      | Database operation failures                                          |

---

### search_tool_version_entries

```python
async def search_tool_version_entries(
    search_criteria: ToolVersionEntrySearchCriteria
) -> list[ToolVersionEntry]
```

| property    | value                                                                     |
| ----------- | ------------------------------------------------------------------------- |
| async       | true                                                                      |
| description | Search tool version records using `search_criteria`. |

#### raises

| exception                                  | condition                                                            |
| ------------------------------------------ | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException`     | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidToolVersionSearchCriteriaException` | `search_criteria` is invalid.                                       |
| `ToolComponentOperationException`          | Database operation failures                                          |
