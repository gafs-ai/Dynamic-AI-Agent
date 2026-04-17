---
class: IModelService
kind: abstract_class
module: gafs.dynamicaiagent.modelcomponent
inherits: [ABC]
dependencies:
  - IDatabaseManager
  - IModelCatalogueService
  - ICloudAiComponent
  - AiRequest
  - AiResponse
  - DeploymentSelectionOptions
exceptions_used:
  - ModelComponentInitializationException
  - ModelComponentNotInitializedException
  - InvalidAiRequestException
  - ModelCatalogueEntryNotFoundException
  - ModelDeploymentNotFoundException
  - ModelComponentOperationException
---

## responsibilities

- Select an appropriate `ModelDeployment` for a given catalogue and request.
- Delegate the actual inference call to the corresponding AI provider component (e.g. `CloudAIComponent`).

## methods

---

### initialize

```python
async def initialize(
    database_manager: IDatabaseManager,
    model_catalogue_service: IModelCatalogueService | None = None,
    cloud_ai_component: ICloudAiComponent | None = None,
) -> bool
```

| property | value |
|----------|-------|
| async | true |
| description | Initialize the model service. Sets up the catalogue service and AI component adapters. |

#### returns

| type | value | description |
|------|-------|-------------|
| `bool` | `True` | Successfully initialized |

#### raises

| exception                                | condition              |
| ---------------------------------------- | ---------------------- |
| `ModelComponentInitializationException`  | Initialization failure |

---

### invoke

```python
async def invoke(
    catalogue_id: str,
    request: AiRequest,
    deployment_selection_options: DeploymentSelectionOptions | None = None,
) -> AiResponse
```

| property | value |
|----------|-------|
| async | true |
| description | Invoke an AI model. Selects a deployment matching `catalogue_id` and `deployment_selection_options`, then delegates the request to the appropriate provider. |

#### parameters

| name                           | type                                 | required | description                                                        |
| ------------------------------ | ------------------------------------ | -------- | ------------------------------------------------------------------ |
| `catalogue_id`                 | `str`                                | yes      | ID of the `ModelCatalogueEntry` record                             |
| `request`                      | `AiRequest`                          | yes      | Operation type, payload, and inference parameters                  |
| `deployment_selection_options` | `DeploymentSelectionOptions \| None` | no       | Optional filters for deployment selection (type, confidence level) |


#### returns

| type | description |
|------|-------------|
| `AiResponse` | The model output and operation status |

#### raises

| exception                               | condition                                                                                           |
| --------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `ModelComponentNotInitializedException` | Model component is not fully initialized.<br>(No `IDatabaseManager` or no `IModelCatalogueService`) |
| `InvalidAiRequestException`             | `AiRequest` or `DeploymentSelectionOptions` entry is invalid                                        |
| `ModelCatalogueEntryNotFoundException`  | No catalogue found for `catalogue_id`                                                               |
| `ModelDeploymentNotFoundException`      | No eligible `ModelDeployment` is found                                                              |
| `ModelComponentOperationException`      | Database operation or inference call failures                                                       |
