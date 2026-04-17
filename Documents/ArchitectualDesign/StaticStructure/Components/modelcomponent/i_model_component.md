---
class: IModelComponent
kind: abstract_class
module: gafs.dynamicaiagent.modelcomponent
inherits: [ABC]
dependencies:
  - IDatabaseManager
  - AiRequest
  - AiResponse
  - ModelCatalogueEntry
  - ModelCatalogueSearchResultEntry
  - ModelDeployment
  - ModelComponentConfigurations
  - ModelCatalogueSearchCriteria
  - ModelDeploymentSearchCriteria
  - DeploymentSelectionOptions
exceptions_used:
  - ModelComponentInitializationException
  - ModelComponentNotInitializedException
  - InvalidModelComponentConfigurationException
  - ModelComponentResourceNotFoundException
  - ModelComponentOperationException
  - ModelCatalogueIndexNotAvailableException
---

## responsibilities

- Top-level interface for all the Model Component operations exposed to the application.
- Delegates catalogue/deployment CRUD to `IModelCatalogueService` and inference to `IModelService`.

## methods

---

### initialize

```python
async def initialize(database_manager: IDatabaseManager) -> bool
```

| property | value |
|----------|-------|
| async | true |
| description | Initialize the model component using the given database manager. |

#### returns

| type | value | description |
|------|-------|-------------|
| `bool` | `True` | Successfully initialized |

#### raises

| exception                               | condition              |
| --------------------------------------- | ---------------------- |
| `ModelComponentInitializationException` | Initialization failure |

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

---

### create_catalogue_entry

```python
async def create_catalogue_entry(catalogue: ModelCatalogueEntry) -> ModelCatalogueEntry
```

*Delegates to `IModelCatalogueService.create_catalogue_entry`.*

---

### update_catalogue_entry

```python
async def update_catalogue_entry(catalogue: ModelCatalogueEntry) -> ModelCatalogueEntry
```

*Delegates to `IModelCatalogueService.update_catalogue_entry`.*

---

### delete_catalogue_entry

```python
async def delete_catalogue_entry(catalogue_id: str) -> None
```

*Delegates to `IModelCatalogueService.delete_catalogue_entry`.*

---

### get_catalogue_entry

```python
async def get_catalogue_entry(catalogue_id: str) -> ModelCatalogueEntry
```

*Delegates to `IModelCatalogueService.get_catalogue_entry`.*

---

### get_all_catalogue_entries

```python
async def get_all_catalogue_entries() -> list[ModelCatalogueEntry]
```

*Delegates to `IModelCatalogueService.get_all_catalogue_entries`.*

---

### search_catalogue_entries

```python
async def search_catalogue_entries(search_criteria: ModelCatalogueSearchCriteria) -> list[ModelCatalogueSearchResultEntry]
```

*Delegates to `IModelCatalogueService.search_catalogue_entries`.*

---

### create_deployment

```python
async def create_deployment(deployment: ModelDeployment) -> ModelDeployment
```

*Delegates to `IModelCatalogueService.create_deployment`.*

---

### update_deployment

```python
async def update_deployment(deployment: ModelDeployment) -> ModelDeployment
```

*Delegates to `IModelCatalogueService.update_deployment`.*

---

### delete_deployment

```python
async def delete_deployment(deployment_id: str) -> None
```

*Delegates to `IModelCatalogueService.delete_deployment`.*

---

### get_deployment

```python
async def get_deployment(deployment_id: str) -> ModelDeployment | None
```

*Delegates to `IModelCatalogueService.get_deployment`.*

---

### search_deployments

```python
async def search_deployments(search_criteria: ModelDeploymentSearchCriteria) -> list[ModelDeployment]
```

*Delegates to `IModelCatalogueService.search_deployments`.*

---

### get_configurations

```python
async def get_configurations() -> ModelComponentConfigurations
```

| property | value |
|----------|-------|
| async | true |
| description | Return the current `ModelComponentConfigurations`. |

#### raises

| exception                                     | condition                                                            |
| --------------------------------------------- | -------------------------------------------------------------------- |
| `ModelComponentNotInitializedException`       | Model component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidModelComponentConfigurationException` | `ModelComponentConfigurations` entry is invalid                      |
| `ModelComponentOperationException`            | Database operation failures                                          |


---

### update_configurations

```python
async def update_configurations(configurations: ModelComponentConfigurations) -> ModelComponentConfigurations
```

| property | value |
|----------|-------|
| async | true |
| description | Persist and return the updated `ModelComponentConfigurations`. |

#### raises

| exception                                     | condition                                                            |
| --------------------------------------------- | -------------------------------------------------------------------- |
| `ModelComponentNotInitializedException`       | Model component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidModelComponentConfigurationException` | `ModelComponentConfigurations` entry is invalid                      |
| `ModelComponentOperationException`            | Database operation failures or component operation failues           |

#### note

1. Update of configurations can affect the indexes of the `ModelCatalogue` or `ModelDeployments` collections. This methods need to evaluate whether the updates can affect the indexes, and, if it does, needs to update indexes and rebuild them together with updating the `ModelComponentConfigurations` entry itself.
   Do not internally call `IModelCatalogueService.ensure_idexes` method, as it defined operations on all the indexes of the `ModelCatalogue` or `ModelDeployments` collections. Evaluate if the update (overwrite) of each index is required, and then update it individually.