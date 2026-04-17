---
class: IModelCatalogueService
kind: abstract_class
module: gafs.dynamicaiagent.modelcomponent
inherits: [ABC]
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
  - ModelCatalogueIndexNotAvailableException
  - FullTextAnalyzerNotExistException
---

## responsibilities

- CRUD and search operations on `ModelCatalogueEntry` and `ModelDeployment` records in the database.
- Manage indexes on the `ModelCatalogue` and `ModelDeployments` collections.

## methods

---

### initialize

```python
async def initialize(
    database_manager: IDatabaseManager,
    component_configurations: ModelComponentConfigurations
) -> bool
```

| property    | value                                                                                                                                                                                                                                                                         |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| async       | true                                                                                                                                                                                                                                                                          |
| description | Initialize the catalogue service. Obtains a database provider from `database_manager` (or uses the given `database_provider` directly) and ensures indexes both for `ModelCatalogueEntry` and `ModelDeployment`.<br>Indexes are defined in model class design documentations. |


#### returns

| type   | value  | description              |
| ------ | ------ | ------------------------ |
| `bool` | `True` | Successfully initialized |

#### raises

| exception                               | condition              |
| --------------------------------------- | ---------------------- |
| `ModelComponentInitializationException` | Initialization failure |

#### rules

- Some of the indexes reference Full Text Analyzers. The analyzers are managed by `IDatabaseManager` and the existence of the referenced analyzers must be confirmed before the creations of the indexes. (raise `FullTextAnalyzerNotExistException` on failure)
- This method is expected to internally call `ensure_indexes` method, but on failure, is expected to finally raise exception as `ModelComponentInitializationException`.

---

### ensure_indexes

```python
async def ensure_indexes(
    configurations: ModelComponentConfigurations,
    overwrite: bool = False
) -> bool
```

| property    | value                                                                                                                                   |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| async       | true                                                                                                                                    |
| description | Create or update indexes on `ModelCatalogue` and `ModelDeployments` collection.<br>Indexes are defined in model class design documents. |

#### raises

| exception                               | condition                                                            |
| --------------------------------------- | -------------------------------------------------------------------- |
| `ModelComponentNotInitializedException` | Model component is not fully initialized.<br>(No `IDatabaseManager`) |
| `ModelComponentOperationException`      | Operation failures including index creation failures                 |
| `FullTextAnalyzerNotExistException`     | The referenced `FullTextAnalyzer` does not exist.                    |

#### rules

- If `overwrite = False`, send queries as `IF NOT EXISTS`, otherwise as `OVERWRITE`.
- Some of the indexes reference Full Text Analyzers. The analyzers are managed by `IDatabaseManager` and the existence of the referenced analyzers must be confirmed before the creations/updates of the indexes. (raise `FullTextAnalyzerNotExistException` on failure)

---

### create_catalogue_entry

```python
async def create_catalogue_entry(catalogue: ModelCatalogueEntry) -> ModelCatalogueEntry
```

| property    | value                           |
| ----------- | ------------------------------- |
| async       | true                            |
| description | Persist a new catalogue record. |

#### raises

| exception                                 | condition                                                                   |
| ----------------------------------------- | --------------------------------------------------------------------------- |
| `ModelComponentNotInitializedException`   | Model component is not fully initialized.<br>(No `IDatabaseManager`)        |
| `InvalidModelCatalogueEntryException`     | Validation failure                                                          |
| `ConflictingModelCatalogueEntryException` | The entry conflicts with another entry.<br>(duplicated `id`)                |
| `ModelDeploymentNotFoundException`        | `ModelDeployment` entry specified in the `ModelCatalogueEntry` is not found. |
| `ModelComponentOperationException`        | Database provider operation failures                                         |

#### note

1. References to `ModelDeployment` entries are saved and managed as `deployed_as` edges (`ModelCatalogue -> deployed_as -> model_deployments`). Operations on `ModelCatalogue` and edges must be committed in a single transaction.

---

### update_catalogue_entry

```python
async def update_catalogue_entry(catalogue: ModelCatalogueEntry) -> ModelCatalogueEntry
```

| property    | value                                                  |
| ----------- | ------------------------------------------------------ |
| async       | true                                                   |
| description | Update an existing catalogue record. `id` must be set. |

#### raises

| exception                               | condition                                                                   |
| --------------------------------------- | --------------------------------------------------------------------------- |
| `ModelComponentNotInitializedException` | Model component is not fully initialized.<br>(No `IDatabaseManager`)        |
| `InvalidModelCatalogueEntryException`   | Invalid request entry including a case that the `id` is empty.              |
| `ModelCatalogueEntryNotFoundException`  | No record with the given `id` exists                                        |
| `ModelDeploymentNotFoundException`      | `ModelDeployment` entry specified in the `ModelCatalogueEntry` is not found. |
| `ModelComponentOperationException`      | Database operation failures                                                  |

#### note

1. References to `ModelDeployment` entries are saved and managed as `deployed_as` edges (`ModelCatalogue -> deployed_as -> model_deployments`). Operations on `ModelCatalogue` and edges must be committed in a single transaction.

---

### get_catalogue_entry

```python
async def get_catalogue_entry(id: str) -> ModelCatalogueEntry | None
```

| property    | value                                                                    |
| ----------- | ------------------------------------------------------------------------ |
| async       | true                                                                     |
| description | Return the catalogue record with the given `id`, or `None` if not found. |

#### raises

| exception                               | condition                                                            |
| --------------------------------------- | -------------------------------------------------------------------- |
| `ModelComponentNotInitializedException` | Model component is not fully initialized.<br>(No `IDatabaseManager`) |
| `ModelComponentOperationException`      | Database operation failures                                          |

#### note

1. References to `ModelDeployment` entries are saved and managed as `deployed_as` edges (`ModelCatalogue -> deployed_as -> model_deployments`). This method needs to resolve the outbound edges from the `ModelCatalogue` entry to `ModelDeployment` entries. However, only the `id` of each referenced `ModelDeployment` entry needs to be contained in the response, not the `ModelDeployment` entries themselves.

---

### get_all_catalogue_entries

```python
async def get_all_catalogue_entries() -> list[ModelCatalogueEntry]
```

| property    | value                               |
| ----------- | ----------------------------------- |
| async       | true                                |
| description | Return all model catalogue entries. |

#### raises

| exception                               | condition                                                            |
| --------------------------------------- | -------------------------------------------------------------------- |
| `ModelComponentNotInitializedException` | Model component is not fully initialized.<br>(No `IDatabaseManager`) |
| `ModelComponentOperationException`      | Database operation failures                                          |

#### note

1. References to `ModelDeployment` entries are saved and managed as `deployed_as` edges (`ModelCatalogue -> deployed_as -> model_deployments`). This method needs to resolve the outbound edges from the `ModelCatalogue` entry to `ModelDeployment` entries. However, only the `id` of each referenced `ModelDeployment` entry needs to be contained in the response, not the `ModelDeployment` entries themselves.

---

### search_catalogue_entries

```python
async def search_catalogue_entries(catalogue_search_criteria: ModelCatalogueSearchCriteria) -> list[ModelCatalogueSearchResultEntry]
```

| property | value |
|----------|-------|
| async | true |
| description | Search catalogue records using the given criteria. Returns an empty list if no matches. |

#### raises

| exception                                      | condition                                                            |
| ---------------------------------------------- | -------------------------------------------------------------------- |
| `ModelComponentNotInitializedException`        | Model component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidModelCatalogueSearchCriteriaException` | Search criteria is invalid                                           |
| `ModelComponentOperationException`             | Database operation failures                                          |

#### note

1. References to `ModelDeployment` entries are saved and managed as `deployed_as` edges (`ModelCatalogue -> deployed_as -> model_deployments`). This method needs to resolve the outbound edges from the `ModelCatalogue` entry to `ModelDeployment` entries. However, only the `id` of each referenced `ModelDeployment` entry needs to be contained in the response, not the `ModelDeployment` entries themselves.

---

### delete_catalogue_entry

```python
async def delete_catalogue_entry(id: str) -> None
```

| property | value |
|----------|-------|
| async | true |
| description | Delete the catalogue record with the given `id`. Raises an exception if not found. |

#### raises

| exception                               | condition                                                            |
| --------------------------------------- | -------------------------------------------------------------------- |
| `ModelComponentNotInitializedException` | Model component is not fully initialized.<br>(No `IDatabaseManager`) |
| `ModelCatalogueEntryNotFoundException`  | No record with the given `id` exists                                 |
| `ModelComponentOperationException`      | Database operation failure                                           |

#### note

1. References to `ModelDeployment` entries are saved and managed as `deployed_as` edges (`ModelCatalogue -> deployed_as -> model_deployments`). All outbound `deployed_as` edges from the `ModelCatalogueEntry` must be deleted in the same transaction as the deletion of the entry itself.

---

### create_deployment

```python
async def create_deployment(deployment: ModelDeployment) -> ModelDeployment
```

| property | value |
|----------|-------|
| async | true |
| description | Persist a new deployment record. |

#### raises

| exception                               | condition                                                            |
| --------------------------------------- | -------------------------------------------------------------------- |
| `ModelComponentNotInitializedException` | Model component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidModelDeploymentException`       | Validation failure                                                   |
| `ConflictingModelDeploymentException`   | The entry conflicts with another entry.<br>(duplicated `id`)         |
| `ModelComponentOperationException`      | Database provider operation failures                                 |

#### note

1. References to `Secret` entries are saved and managed as `references_secret` edges (`model_deployments -> references_secret -> Secrets`). Operations on `model_deployments` and edges must be committed in a single transaction.

---

### update_deployment

```python
async def update_deployment(deployment: ModelDeployment) -> ModelDeployment
```

| property | value |
|----------|-------|
| async | true |
| description | Update an existing deployment record. `id` must be set. |

#### raises

| exception                               | condition                                                            |
| --------------------------------------- | -------------------------------------------------------------------- |
| `ModelComponentNotInitializedException` | Model component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidModelDeploymentException`       | Validation failure including a case that `id` is empty.              |
| `ModelDeploymentNotFoundException`      | No record with the given `id` exists                                 |
| `ModelComponentOperationException`      | Database provider operation failures                                 |

#### note

1. References to `Secret` entries are saved and managed as `references_secret` edges. All existing outbound `references_secret` edges must be deleted and new edges created for the updated `secrets` list in the same transaction as the record update.

---

### get_deployment

```python
async def get_deployment(id: str) -> ModelDeployment | None
```

| property | value |
|----------|-------|
| async | true |
| description | Return the deployment record with the given `id`, or `None` if not found. |

#### raises

| exception                               | condition                                                            |
| --------------------------------------- | -------------------------------------------------------------------- |
| `ModelComponentNotInitializedException` | Model component is not fully initialized.<br>(No `IDatabaseManager`) |
| `ModelComponentOperationException`      | Database operation failures                                          |

#### note

1. References to `Secret` entries are saved and managed as `references_secret` edges. This method must resolve the outbound `references_secret` edges and include only the `id` of each linked `Secret` in `deployment.secrets`.

---

### search_deployments

```python
async def search_deployments(search_criteria: ModelDeploymentSearchCriteria) -> list[ModelDeployment]
```

| property | value |
|----------|-------|
| async | true |
| description | Search deployment records using the given criteria. Returns an empty list if no matches. |

#### raises

| exception                                       | condition                                                            |
| ----------------------------------------------- | -------------------------------------------------------------------- |
| `ModelComponentNotInitializedException`         | Model component is not fully initialized.<br>(No `IDatabaseManager`) |
| `InvalidModelDeploymentSearchCriteriaException` | Search criteria is invalid                                           |
| `ModelComponentOperationException`              | Database operation failures                                          |

#### note

1. References to `Secret` entries are saved and managed as `references_secret` edges. This method must resolve the outbound `references_secret` edges for each result and include only the `id` of each linked `Secret` in `deployment.secrets`.

---

### delete_deployment

```python
async def delete_deployment(id: str) -> None
```

| property | value |
|----------|-------|
| async | true |
| description | Delete the deployment record with the given `id`. Raises an exception if not found. |

#### raises

| exception                               | condition                                                            |
| --------------------------------------- | -------------------------------------------------------------------- |
| `ModelComponentNotInitializedException` | Model component is not fully initialized.<br>(No `IDatabaseManager`) |
| `ModelDeploymentNotFoundException`      | No record with the given `id` exists                                 |
| `ModelComponentOperationException`      | Database operation failure                                           |

#### note

1. All outbound `references_secret` edges from the `ModelDeployment` must be deleted in the same transaction as the deletion of the record itself.
2. All inbound `deployed_as` edges pointing to this `ModelDeployment` must be deleted in the same transaction. Do not delete the linked `ModelCatalogueEntry` entries.
