---
class: ISandboxCatalogueService
kind: abstract_class
module: gafs.dynamicaiagent.toolcomponent
inherits: [ABC]
dependencies:
  - IDatabaseManager
  - IDatabaseProvider
  - SandboxCatalogueEntry
  - SandboxCatalogueHostEntry
  - SandboxCatalogueDockerEntry
  - ToolComponentConfigurations
  - SandboxCatalogueSearchCriteria
exceptions_used:
  - ToolComponentInitializationException
  - ToolComponentNotInitializedException
  - InvalidSandboxCatalogueEntryException
  - ConflictingSandboxCatalogueEntryException
  - SandboxCatalogueEntryNotFoundException
  - InvalidSandboxCatalogueSearchCriteriaException
  - ToolComponentOperationException
  - FullTextAnalyzerNotExistException
---

## responsibilities

- CRUD and search operations on `SandboxCatalogueEntry` records in the database.
- Manage indexes on the `SandboxCatalogue` collection.

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
| description | Initialize the sandbox catalogue service. Obtains a database provider from `database_manager` and ensures indexes for `SandboxCatalogueEntry`.<br>Indexes are defined in model class design documentations. |

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
| description | Create or update indexes on the `SandboxCatalogue` collection.<br>Indexes are defined in model class design documents. |

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

### create_catalogue_entry

```python
async def create_catalogue_entry(catalogue: SandboxCatalogueEntry) -> SandboxCatalogueEntry
```

| property    | value                              |
| ----------- | ---------------------------------- |
| async       | true                               |
| description | Persist a new sandbox catalogue record. |

#### raises

| exception                                | condition                                                            |
| ---------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException`   | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidSandboxCatalogueEntryException`  | Validation failure                                                   |
| `ConflictingSandboxCatalogueEntryException` | The entry conflicts with another entry.<br>(duplicated `name`)    |
| `ToolComponentOperationException`        | Database operation failures                                          |

---

### update_catalogue_entry

```python
async def update_catalogue_entry(catalogue: SandboxCatalogueEntry) -> SandboxCatalogueEntry
```

| property    | value                                                       |
| ----------- | ----------------------------------------------------------- |
| async       | true                                                        |
| description | Update an existing sandbox catalogue record. `id` must be set. |

#### raises

| exception                               | condition                                                            |
| --------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException`  | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidSandboxCatalogueEntryException` | Invalid request entry including a case that the `id` is empty.      |
| `SandboxCatalogueEntryNotFoundException` | No record with the given `id` exists.                               |
| `ToolComponentOperationException`       | Database operation failures                                          |

---

### delete_catalogue_entry

```python
async def delete_catalogue_entry(catalogue_id: str) -> None
```

| property    | value                                              |
| ----------- | -------------------------------------------------- |
| async       | true                                               |
| description | Delete a sandbox catalogue record by `catalogue_id`. |

#### raises

| exception                               | condition                                                            |
| --------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException`  | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `SandboxCatalogueEntryNotFoundException` | No record with the given `catalogue_id` exists.                     |
| `ToolComponentOperationException`       | Database operation failures                                          |

---

### get_catalogue_entry

```python
async def get_catalogue_entry(catalogue_id: str) -> SandboxCatalogueEntry
```

| property    | value                                                   |
| ----------- | ------------------------------------------------------- |
| async       | true                                                    |
| description | Retrieve a single sandbox catalogue record by its `id`. |

#### raises

| exception                               | condition                                                            |
| --------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException`  | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `SandboxCatalogueEntryNotFoundException` | No record with the given `catalogue_id` exists.                     |
| `ToolComponentOperationException`       | Database operation failures                                          |

---

### get_all_catalogue_entries

```python
async def get_all_catalogue_entries() -> list[SandboxCatalogueEntry]
```

| property    | value                                      |
| ----------- | ------------------------------------------ |
| async       | true                                       |
| description | Return all sandbox catalogue records. |

#### raises

| exception                              | condition                                                            |
| -------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException` | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `ToolComponentOperationException`      | Database operation failures                                          |

---

### search_catalogue_entries

```python
async def search_catalogue_entries(
    search_criteria: SandboxCatalogueSearchCriteria
) -> list[SandboxCatalogueEntry]
```

| property    | value                                                                   |
| ----------- | ----------------------------------------------------------------------- |
| async       | true                                                                    |
| description | Search sandbox catalogue records using `search_criteria`. |

#### raises

| exception                                     | condition                                                            |
| --------------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException`        | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidSandboxCatalogueSearchCriteriaException` | `search_criteria` is invalid.                                     |
| `ToolComponentOperationException`             | Database operation failures                                          |
