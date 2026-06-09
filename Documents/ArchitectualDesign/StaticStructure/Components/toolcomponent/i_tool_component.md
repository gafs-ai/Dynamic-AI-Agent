---
class: IToolComponent
kind: abstract_class
module: gafs.dynamicaiagent.toolcomponent
inherits: [ABC]
dependencies:
  - IDatabaseManager
  - ToolCatalogueEntry
  - ToolCatalogueSearchResultEntry
  - ToolVersionEntry
  - SandboxCatalogueEntry
  - ToolComponentConfigurations
  - ToolCatalogueSearchCriteria
  - ToolVersionEntrySearchCriteria
  - SandboxCatalogueSearchCriteria
exceptions_used:
  - ToolComponentInitializationException
  - ToolComponentNotInitializedException
  - InvalidToolComponentConfigurationException
  - InvalidToolInvocationException
  - ToolComponentResourceNotFoundException
  - ToolComponentOperationException
  - ToolCatalogueIndexNotAvailableException
---

## responsibilities

- Top-level interface for all the Tool Component operations exposed to the application.
- Defines the following operations
	- Initialization operation
	- Tool invocation operation
	- Tool Catalogue & Tool Version operations
	- Sandbox Catalogue operations
	- Tool component  configuration operations

---
## methods

### initialize

``` python
async def initialize(database_manager: IDatabaseManager) -> bool
```

| property | value |
|----------|-------|
| async | true |
| description | Initialize the tool component using the given database manager. |

#### returns

| type | value | description |
|------|-------|-------------|
| `bool` | `True` | Successfully initialized |

#### raises

| exception                              | condition              |
| -------------------------------------- | ---------------------- |
| `ToolComponentInitializationException` | Initialization failure |

---

### invoke

``` python
async def invoke(tool_id: str, version_id: str, input_parameters: dict[str, Any]) -> dict[str, Any]
```

| property | value |
|----------|-------|
| async | true |
| description | Execute the tool identified by `tool_id` and `version_id` with the given `input_parameters`. Returns the output parameters produced by the tool. |

#### parameters

| name               | type             | required | description                                  |
| ------------------ | ---------------- | -------- | -------------------------------------------- |
| `tool_id`          | `str`            | yes      | ID of the `ToolCatalogueEntry` record         |
| `version_id`       | `str`            | yes      | ID of the `ToolVersionEntry` record           |
| `input_parameters` | `dict[str, Any]` | yes      | Actual values for the tool's input parameters |

#### returns

| type             | description                              |
| ---------------- | ---------------------------------------- |
| `dict[str, Any]` | Output parameter values produced by the tool |

#### raises

| exception                              | condition                                                            |
| -------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException` | Tool component is not fully initialized.                             |
| `ToolCatalogueEntryNotFoundException`  | No `ToolCatalogueEntry` found for `tool_id`.                         |
| `ToolVersionEntryNotFoundException`    | No `ToolVersionEntry` found for `version_id`.                        |
| `InvalidToolInvocationException`         | `input_parameters` fail validation against `ToolVersionEntry.input_parameters`. |
| `SandboxCatalogueEntryNotFoundException` | No suitable sandbox found for the version.                         |
| `ToolComponentOperationException`      | Tool execution failure                                               |

---

### create_tool_catalogue_entry

``` python
async def create_tool_catalogue_entry(catalogue: ToolCatalogueEntry) -> ToolCatalogueEntry
```

*Delegates to `IToolCatalogueService.create_tool_catalogue_entry`.*

---

### update_tool_catalogue_entry

``` python
async def update_tool_catalogue_entry(catalogue: ToolCatalogueEntry) -> ToolCatalogueEntry
```

*Delegates to `IToolCatalogueService.update_tool_catalogue_entry`.*

---
### delete_tool_catalogue_entry

```python
async def delete_tool_catalogue_entry(catalogue_id: str) -> None
```

*Delegates to `IToolCatalogueService.delete_tool_catalogue_entry`.*

---

### get_tool_catalogue_entry

```python
async def get_tool_catalogue_entry(catalogue_id: str) -> ToolCatalogueEntry
```

*Delegates to `IToolCatalogueService.get_tool_catalogue_entry`.*

---

### get_all_tool_catalogue_entries

```python
async def get_all_tool_catalogue_entries() -> list[ToolCatalogueEntry]
```

*Delegates to `IToolCatalogueService.get_all_tool_catalogue_entries`.*

---
### search_tool_catalogue_entries

```python
async def search_tool_catalogue_entries(search_criteria: ToolCatalogueSearchCriteria) -> list[ToolCatalogueSearchResultEntry]
```

*Delegates to `IToolCatalogueService.search_tool_catalogue_entries`.*

---

### create_tool_version_entry

```python
async def create_tool_version_entry(version: ToolVersionEntry) -> ToolVersionEntry
```

*Delegates to `IToolCatalogueService.create_tool_version_entry`.*

---

### update_tool_version_entry

```python
async def update_tool_version_entry(version: ToolVersionEntry) -> ToolVersionEntry
```

*Delegates to `IToolCatalogueService.update_tool_version_entry`.*

---

### delete_tool_version_entry

```python
async def delete_tool_version_entry(version_id: str) -> None
```

*Delegates to `IToolCatalogueService.delete_tool_version_entry`.*

---

### get_tool_version_entry

```python
async def get_tool_version_entry(version_id: str) -> ToolVersionEntry
```

*Delegates to `IToolCatalogueService.get_tool_version_entry`.*

---

### get_all_tool_version_entries

```python
async def get_all_tool_version_entries(tool_id: str | None = None) -> list[ToolVersionEntry]
```

*Delegates to `IToolCatalogueService.get_all_tool_version_entries`.*

---

### search_tool_version_entries

```python
async def search_tool_version_entries(search_criteria: ToolVersionEntrySearchCriteria) -> list[ToolVersionEntry]
```

*Delegates to `IToolCatalogueService.search_tool_version_entries`.*

---

### create_sandbox_catalogue_entry

```python
async def create_sandbox_catalogue_entry(catalogue: SandboxCatalogueEntry) -> SandboxCatalogueEntry
```

*Delegates to `ISandboxCatalogueService.create_catalogue_entry`.*

---

### update_sandbox_catalogue_entry

```python
async def update_sandbox_catalogue_entry(catalogue: SandboxCatalogueEntry) -> SandboxCatalogueEntry
```

*Delegates to `ISandboxCatalogueService.update_catalogue_entry`.*

---

### delete_sandbox_catalogue_entry

```python
async def delete_sandbox_catalogue_entry(catalogue_id: str) -> None
```

*Delegates to `ISandboxCatalogueService.delete_catalogue_entry`.*

---

### get_sandbox_catalogue_entry

```python
async def get_sandbox_catalogue_entry(catalogue_id: str) -> SandboxCatalogueEntry
```

*Delegates to `ISandboxCatalogueService.get_catalogue_entry`.*

---

### get_all_sandbox_catalogue_entries

```python
async def get_all_sandbox_catalogue_entries() -> list[SandboxCatalogueEntry]
```

*Delegates to `ISandboxCatalogueService.get_all_catalogue_entries`.*

---

### search_sandbox_catalogue_entries

```python
async def search_sandbox_catalogue_entries(search_criteria: SandboxCatalogueSearchCriteria) -> list[SandboxCatalogueEntry]
```

*Delegates to `ISandboxCatalogueService.search_catalogue_entries`.*

---

### get_configurations

```python
async def get_configurations() -> ToolComponentConfigurations
```

| property | value |
|----------|-------|
| async | true |
| description | Return the current `ToolComponentConfigurations`. |

#### raises

| exception                                    | condition                                                            |
| -------------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException`       | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidToolComponentConfigurationException` | `ToolComponentConfigurations` entry is invalid.                      |

---

### update_configurations

```python
async def update_configurations(configurations: ToolComponentConfigurations) -> ToolComponentConfigurations
```

| property | value |
|----------|-------|
| async | true |
| description | Persist updated `ToolComponentConfigurations` and return the saved record. |

#### raises

| exception                                    | condition                                                            |
| -------------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException`       | Tool component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidToolComponentConfigurationException` | `configurations` entry is invalid.                                   |
| `ToolComponentOperationException`            | Database operation failures                                          |
