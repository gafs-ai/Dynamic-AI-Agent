---
class: ModelService
kind: class
module: gafs.dynamicaiagent.modelcomponent
implements: [IModelService]
---

## fields

| name | type | description |
|------|------|-------------|
| `_logger` | `logging.Logger` | Logger instance |
| `_database_manager` | `IDatabaseManager` | Set on `initialize` |
| `_model_catalogue_service` | `IModelCatalogueService` | Set on `initialize` |
| `_cloud_ai_component` | `ICloudAiComponent` | Set on `initialize` |

## private methods

---

### `_validate_and_merge_request_parameters`

```python
def _validate_and_merge_request_parameters(
    catalogue: ModelCatalogueEntry,
    request: AiRequest,
) -> None
```

#### implementation notes

1. Build a lookup `dict[key, AttributeDefinition]` from `catalogue.available_inference_parameters`.
2. For each key–value pair in `request.parameters`:
   - If the key is not in the lookup, discard it (ignore unknown parameters).
   - Otherwise call `_validate_parameter_value(parameter_def, value)` and collect the result.
3. Merge `catalogue.default_inference_parameters` into the validated set (caller-supplied values take precedence).
4. Assign the merged dict back to `request.parameters`.

---

### `_validate_parameter_value`

```python
@staticmethod
def _validate_parameter_value(parameter_def: AttributeDefinition, value: Any) -> Any
```

#### implementation notes

1. Check type against `parameter_def.type` (`STR`, `INT`, `FLOAT`, `BOOL`).
   - For `FLOAT`: coerce `int` to `float`.
   - On type mismatch: raise `InvalidAiRequestException`.
2. If `parameter_def.allowed_values` is set and `value` is not in it: raise `InvalidAiRequestException`.
3. If `parameter_def.min` is set and `value < min`: raise `InvalidAiRequestException`.
4. If `parameter_def.max` is set and `value > max`: raise `InvalidAiRequestException`.
5. Return the (possibly coerced) value.

---

### `_select_deployments`

```python
async def _select_deployments(
    catalogue: ModelCatalogueEntry,
    deployment_selection_options: DeploymentSelectionOptions | None,
) -> list[ModelDeployment]
```

#### implementation notes

1. If `catalogue.deployments` is `None` or empty, return an empty list.
2. For each `deployment_id` in `catalogue.deployments`, call `_model_catalogue_service.get_deployment(deployment_id)` and collect non-`None` results.
3. If `deployment_selection_options` is provided:
   - Filter by `deployment_type` if set.
   - Filter by `confidence`: retain only deployments where `max_confidence_level >= deployment_selection_options.confidence`.
4. Sort the remaining deployments by `priority` descending (`None` priority treated as `0`).
5. Return the sorted list.

---

### `_invoke_with_deployment`

```python
async def _invoke_with_deployment(
    deployment: ModelDeployment,
    request: AiRequest,
) -> AiResponse
```

#### implementation notes

1. Collect `base_connection_parameters` from `deployment.connection_parameters` (default `{}`).
2. Collect secret IDs from `deployment.secrets` (may be `None` or empty).
3. If no secrets:
   1. Call `_invoke_model_operation(deployment, request, base_connection_parameters)` and return the result.
4. If secrets exist, iterate over each:
   1. Call `_get_secret_values(secret_id)` to retrieve the secret key–value pairs.
   2. Merge with `base_connection_parameters` (secret values take precedence on duplicate keys).
   3. Call `_invoke_model_operation(deployment, request, merged_parameters)`.
   4. On success: return the result. On failure: log the error, record `last_error`, and continue.
5. If all secrets fail, re-raise `last_error`.

---

### `_invoke_model_operation`

```python
async def _invoke_model_operation(
    deployment: ModelDeployment,
    request: AiRequest,
    connection_parameters: dict[str, Any],
) -> AiResponse
```

#### implementation notes

1. Match on `deployment.deployment_type`:
   - `CLOUD`: Build `AiConnectionParameters` from `request.operation_type`, `deployment.deployment_type`, and `deployment.provider_type`; set `parameters = connection_parameters`; call `_cloud_ai_component.invoke(connection, request)` and return the result.
   - `LOCAL`: raise `NotImplementedError`.
   - `REMOTE`: raise `NotImplementedError`.
   - Other: raise `ModelComponentOperationException`.

---

### `_get_secret_links`

```python
@staticmethod
def _get_secret_links(deployment: ModelDeployment) -> list[str]
```

#### implementation notes

1. Return `deployment.secrets or []`.

---

### `_get_secret_values`

```python
async def _get_secret_values(secret_id: str) -> dict[str, Any]
```

#### implementation notes

1. Strip the `Secrets:` table prefix from `secret_id` to obtain the bare ID.
2. Execute `SELECT * FROM type::thing('Secrets', '<id>')`.
3. If no record is found or `secret.raw_secret` is `None`: raise `ModelDeploymentNotFoundException`.
4. Cast `secret.raw_secret` to `dict`. If not a dict: raise `ModelComponentOperationException`.
5. Return the `raw_secret` dict as-is.

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

#### implementation notes

1. Validate that both `model_catalogue_service` and `cloud_ai_component` are provided.
   - If either is `None`: raise `ModelComponentInitializationException`.
2. Store all three arguments to the corresponding internal fields.
3. Return `True`.

---

### invoke

```python
async def invoke(
    catalogue_id: str,
    request: AiRequest,
    deployment_selection_options: DeploymentSelectionOptions | None = None,
) -> AiResponse
```

#### implementation notes

1. Fetch the catalogue via `_model_catalogue_service.get_catalogue_entry(catalogue_id)`.
   - If the result is `None`: raise `ModelCatalogueEntryNotFoundException`.
2. Call `_validate_and_merge_request_parameters(catalogue, request)` to validate and merge inference parameters.
   - On validation failure: raise `InvalidAiRequestException`.
3. Call `_select_deployments(catalogue, deployment_selection_options)` to obtain an ordered list of eligible deployments.
   - If the list is empty: raise `ModelDeploymentNotFoundException`.
4. Iterate over deployments in order and call `_invoke_with_deployment(deployment, request)` for each.
   - On success: return the `AiResponse` immediately.
   - On failure: log the error, record `last_error`, and continue to the next deployment.
5. If all deployments fail, raise `ModelComponentOperationException`.
