---
class: SandboxCatalogueService
kind: class
module: gafs.dynamicaiagent.toolcomponent
implements: [ISandboxCatalogueService]
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

## fields

| name | type | description |
|------|------|-------------|
| `_logger` | `logging.Logger` | Logger instance |
| `_database_manager` | `IDatabaseManager \| None` | Set on `initialize` |
| `_database_provider` | `IDatabaseProvider \| None` | Default provider; set on `initialize` |
| `_configurations` | `ToolComponentConfigurations \| None` | Cached on `initialize` |

## notes on polymorphic deserialization

`SandboxCatalogueEntry` is an abstract base class with two concrete subtypes: `SandboxCatalogueHostEntry` and `SandboxCatalogueDockerEntry`. Records stored in the `SandboxCatalogue` collection include a discriminator field `sandbox_type` (value: `SandboxType` enum string). When deserializing, inspect this field and instantiate the appropriate subtype:

| `sandbox_type` value | Concrete class |
|---|---|
| `"host"` | `SandboxCatalogueHostEntry` |
| `"docker"` | `SandboxCatalogueDockerEntry` |

When serializing, always include the `sandbox_type` field derived from the concrete class type.

## private methods

---

### `_deserialize_entry`

```python
def _deserialize_entry(data: dict) -> SandboxCatalogueEntry
```

#### implementation notes

1. Read the `sandbox_type` field from `data`.
2. If `sandbox_type == "docker"`: deserialize as `SandboxCatalogueDockerEntry`.
3. If `sandbox_type == "host"`: deserialize as `SandboxCatalogueHostEntry`.
4. If `sandbox_type` is missing or unrecognised: raise `ToolComponentOperationException`.

---

### `_serialize_entry`

```python
def _serialize_entry(entry: SandboxCatalogueEntry) -> dict
```

#### implementation notes

1. Serialize `entry` to a dict.
2. Set `sandbox_type` to the appropriate `SandboxType` enum value (`"docker"` or `"host"`) based on the runtime type.
3. Return the dict.

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
2. Verify that the analyzer referenced by `configurations.name_analyzer` exists by calling the appropriate method on `_database_manager`.
   - If it does not exist: raise `FullTextAnalyzerNotExistException`.
3. Create the indexes defined on `SandboxCatalogueEntry` (see model class design documents for index definitions):
   - If `overwrite = True`: use `DEFINE INDEX OVERWRITE`.
   - If `overwrite = False`: use `DEFINE INDEX IF NOT EXISTS`.
   - Full-text index on `name` uses `SEARCH ANALYZER {name_analyzer} BM25`.
   - On failure: raise `ToolComponentOperationException`.
4. Return `True`.

---

### create_catalogue_entry

```python
async def create_catalogue_entry(catalogue: SandboxCatalogueEntry) -> SandboxCatalogueEntry
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Validate `catalogue` (non-empty `name`, valid `status`). On failure: raise `InvalidSandboxCatalogueEntryException`.
3. Check for a duplicate `name`: `SELECT id FROM SandboxCatalogue WHERE name = $name`. If found: raise `ConflictingSandboxCatalogueEntryException`.
4. Serialize `catalogue` via `_serialize_entry`.
5. Build and execute:
   - If `catalogue.id` is `None` or empty: `CREATE SandboxCatalogue CONTENT <json_without_id>`.
   - Otherwise: `CREATE type::thing('SandboxCatalogue', '<id>') CONTENT <json>`.
   - On failure: raise `ToolComponentOperationException`.
6. Deserialize the created record via `_deserialize_entry` and return it.

---

### update_catalogue_entry

```python
async def update_catalogue_entry(catalogue: SandboxCatalogueEntry) -> SandboxCatalogueEntry
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Validate that `catalogue.id` is non-empty. On failure: raise `InvalidSandboxCatalogueEntryException`.
3. Verify the existing record exists via `get_catalogue_entry(catalogue.id)`.
   - If not found: raise `SandboxCatalogueEntryNotFoundException`.
4. Serialize `catalogue` via `_serialize_entry`.
5. Execute `UPDATE type::thing('SandboxCatalogue', '<id>') MERGE <json>`.
   - On failure: raise `ToolComponentOperationException`.
6. Return the updated entry (re-fetch via `get_catalogue_entry` or deserialize from UPDATE result).

---

### delete_catalogue_entry

```python
async def delete_catalogue_entry(catalogue_id: str) -> None
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Execute `DELETE type::thing('SandboxCatalogue', '<catalogue_id>') RETURN BEFORE`.
   - If the result is empty (no record deleted): raise `SandboxCatalogueEntryNotFoundException`.
   - On other failure: raise `ToolComponentOperationException`.

---

### get_catalogue_entry

```python
async def get_catalogue_entry(catalogue_id: str) -> SandboxCatalogueEntry
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Execute `SELECT * FROM type::thing('SandboxCatalogue', '<catalogue_id>')`.
   - On failure: raise `ToolComponentOperationException`.
3. If no record is found: raise `SandboxCatalogueEntryNotFoundException`.
4. Deserialize via `_deserialize_entry` and return the result.

---

### get_all_catalogue_entries

```python
async def get_all_catalogue_entries() -> list[SandboxCatalogueEntry]
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Execute `SELECT * FROM SandboxCatalogue`.
   - On failure: raise `ToolComponentOperationException`.
3. Deserialize each record via `_deserialize_entry` and return the list. Return an empty list if no records are found.

---

### search_catalogue_entries

```python
async def search_catalogue_entries(
    search_criteria: SandboxCatalogueSearchCriteria
) -> list[SandboxCatalogueEntry]
```

#### implementation notes

1. If `_database_provider` is `None`: raise `ToolComponentNotInitializedException`.
2. Validate `search_criteria`. On failure: raise `InvalidSandboxCatalogueSearchCriteriaException`.
3. Build the SurrealQL query dynamically:
   - Base: `SELECT * FROM SandboxCatalogue`.
   - `WHERE` clauses (combined with `AND`):
     - `name = $name` if `search_criteria.name` is set.
     - `status IN $status` if `search_criteria.status` is set.
     - Tag filter from `search_criteria.tags` (AND: all tags must be present; OR: any tag must be present).
   - Append `LIMIT $limit`.
4. Execute the query. On failure: raise `ToolComponentOperationException`.
5. Deserialize each record via `_deserialize_entry` and return the list. Return an empty list if no records match.
