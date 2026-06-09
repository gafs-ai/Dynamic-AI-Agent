---
class: DockerSandboxService
kind: class
module: gafs.dynamicaiagent.toolcomponent
implements: [IDockerSandboxService]
dependencies:
  - IDatabaseManager
  - ISandboxCatalogueService
  - SandboxCatalogueDockerEntry
  - ToolVersionEntry
  - ToolComponentConfigurations
exceptions_used:
  - ToolComponentInitializationException
  - ToolComponentNotInitializedException
  - SandboxCatalogueEntryNotFoundException
  - ToolComponentOperationException
---

## fields

| name | type | description |
|------|------|-------------|
| `_logger` | `logging.Logger` | Logger instance |
| `_database_manager` | `IDatabaseManager \| None` | Set on `initialize` |
| `_sandbox_catalogue_service` | `ISandboxCatalogueService \| None` | Set on `initialize` |
| `_configurations` | `ToolComponentConfigurations \| None` | Set on `initialize` |
| `_standby_containers` | `dict[str, list[str]]` | Maps `sandbox_entry.id` to a list of standby container names. Populated on `initialize`; maintained after each `execute_code` call. |
| `_container_counts` | `dict[str, int]` | Maps `sandbox_entry.id` to the next container sequence number used for naming. Incremented each time a container is created for that sandbox. |

## notes on Docker operations

All Docker operations are performed via the Docker SDK for Python (`docker` package). Long-running operations (image build, container start/stop) must be executed in a thread executor (`asyncio.get_event_loop().run_in_executor`) to avoid blocking the event loop.

## private methods

---

### `_create_image`

```python
async def _create_image(
    sandbox_entry: SandboxCatalogueDockerEntry
) -> str
```

#### implementation notes

1. Check whether a Docker image named `sandbox_entry.id` already exists (e.g., `docker images -q {sandbox_entry.id}`).
2. If the image exists: log a debug message and return `sandbox_entry.id` immediately (reuse without rebuilding).
3. If the image does not exist: build a new image from `sandbox_entry.docker_file` and tag it with `sandbox_entry.id`.
   - On failure: raise `ToolComponentOperationException`.
4. Return the image name (`sandbox_entry.id`).

---

### `_create_container`

```python
async def _create_container(
    sandbox_entry: SandboxCatalogueDockerEntry,
    container_count: int,
) -> str
```

#### implementation notes

1. Derive the container name: `{sandbox_entry.id}_{container_count}`.
2. Derive the host data directory: `{_configurations.app_data_folder}/tools/files/{container_name}/`.
3. Create the following host directories:
   - `{host_data_dir}/input`
   - `{host_data_dir}/output`
   - `{host_data_dir}/tmp`
4. Run the container with:
   - `--name {container_name}`
   - `-v {app_data_folder}/tools/codes:/app/codes:ro`
   - `-v {host_data_dir}:/app/data:rw`
   - Label: `gafs.toolcomponent=true` (used for orphan container cleanup on next `initialize`)
   - Any additional options from `sandbox_entry.run_options`
   - Image: `sandbox_entry.id`
   - Command: `sleep infinity`
   - Detached mode (`-d`)
   - On failure:
     - If the error is a name-conflict (HTTP 409 / container name already in use): check whether the container already exists.
       - If the container is running: log a debug message and return the existing container name (reuse).
       - If the container is stopped: start it and return its name.
     - Otherwise: raise `ToolComponentOperationException`.
5. Return the container name.

---

### `_destroy_container`

```python
async def _destroy_container(container_name: str) -> None
```

#### implementation notes

1. Stop the Docker container identified by `container_name` (best-effort; log errors but do not propagate).
2. Remove the Docker container (best-effort; log errors but do not propagate).
3. Delete the associated host data directory `{app_data_folder}/tools/files/{container_name}/` and all its contents (best-effort; log errors but do not propagate).

---

### `_remove_image`

```python
async def _remove_image(image_name: str) -> None
```

#### implementation notes

1. Remove the Docker image identified by `image_name` (best-effort; log errors but do not propagate).

---

### `_exit`

```python
async def _exit() -> None
```

#### implementation notes

1. For each sandbox_id in `_standby_containers`:
   1. For each container name in `_standby_containers[sandbox_id]`: call `_destroy_container(container_name)`.
2. Clear `_standby_containers`.

---

### `_replenish_standby_pool`

```python
async def _replenish_standby_pool(sandbox_entry: SandboxCatalogueDockerEntry) -> None
```

#### implementation notes

1. Determine the current standby count for `sandbox_entry.id`: `len(_standby_containers.get(sandbox_entry.id, []))`.
2. Determine how many containers to add:
   - `per_sandbox_limit = _configurations.docker_default_image_max_stand_by`
   - `total_limit = _configurations.docker_total_default_image_max_stand_by`
   - `total_current = sum(len(v) for v in _standby_containers.values())`
   - `slots_available = min(per_sandbox_limit - current_count, total_limit - total_current)`
3. If `slots_available <= 0`: return immediately.
4. For each slot:
   1. Obtain the next container count from `_container_counts[sandbox_entry.id]` and increment it.
   2. Call `_create_container(sandbox_entry, count)`.
   3. On success: append the container name to `_standby_containers[sandbox_entry.id]`.
   4. On failure: log the error and stop adding further containers (best-effort).

## methods

---

### initialize

```python
async def initialize(
    database_manager: IDatabaseManager,
    sandbox_catalogue_service: ISandboxCatalogueService,
    configurations: ToolComponentConfigurations,
) -> bool
```

#### implementation notes

1. Store `database_manager` to `_database_manager`.
2. Store `sandbox_catalogue_service` to `_sandbox_catalogue_service`.
3. Store `configurations` to `_configurations`.
4. Initialise `_standby_containers` and `_container_counts` as empty dicts.
5. Fetch all active `SandboxCatalogueDockerEntry` records:
   - Build a `SandboxCatalogueSearchCriteria` with `status=[SandboxStatus.ACTIVE]`.
   - Call `_sandbox_catalogue_service.search_catalogue_entries(criteria)`.
   - Filter results to `SandboxCatalogueDockerEntry` instances only.
   - On failure: raise `ToolComponentInitializationException`.
6. Cleanup orphaned standby containers from previous runs (best-effort; errors are logged and do not abort initialization):
   - Build the set of active sandbox IDs from the results of step 5.
   - List all running Docker containers that have the label `gafs.toolcomponent=true`.
   - For each such container whose name follows the pattern `{sandbox_id}_{n}` and whose `sandbox_id` is **not** in the active sandbox ID set: stop and remove the container.
7. For each `SandboxCatalogueDockerEntry`:
   1. Call `_create_image(sandbox_entry)` to build or verify the Docker image.
      - On failure: log the error and skip this entry (best-effort; do not abort initialization).
   2. Initialise `_standby_containers[sandbox_entry.id] = []` and `_container_counts[sandbox_entry.id] = 0`.
   3. Call `_replenish_standby_pool(sandbox_entry)` to create the initial standby containers.
      - Errors are logged and do not abort initialization.
8. Return `True`.

---

### execute_code

```python
async def execute_code(
    version_entry: ToolVersionEntry,
    sandbox_entry: SandboxCatalogueDockerEntry,
    input_parameters: dict[str, Any],
) -> dict[str, Any]
```

#### implementation notes

1. If `_configurations` is `None`: raise `ToolComponentNotInitializedException`.
2. Verify that `sandbox_entry.id` is present in `_standby_containers` (i.e., the sandbox was registered at initialization). If not: raise `SandboxCatalogueEntryNotFoundException`.
3. Obtain a container to use:
   - If `_standby_containers[sandbox_entry.id]` is non-empty: pop the first container name from the list.
   - Otherwise: obtain the next count from `_container_counts[sandbox_entry.id]`, increment it, and call `_create_container(sandbox_entry, count)` to provision a new container on demand.
   - On container creation failure: raise `ToolComponentOperationException`.
4. Validate required input parameters against `version_entry.input_parameters` before injection:
   - For each definition with `required = True`: confirm the key is present in `input_parameters`. If missing and `default` is `None`: raise `ToolComponentOperationException`.
5. Apply defaults for any missing optional parameters that have a `default` value defined.
6. Construct the system parameters object:
   ```json
   {
     "input_parameters": { ... },
     "input_dir":  "/app/data/input",
     "output_dir": "/app/data/output",
     "tmp_dir":    "/app/data/tmp"
   }
   ```
7. Write the JSON to `{app_data_folder}/tools/files/{container_name}/input/_params.json`.
   - On failure: call `_destroy_container(container_name)` and raise `ToolComponentOperationException`.
8. Execute the tool code inside the container:
   ```
   docker exec {container_name} python /app/codes/{version_entry.tool_id}_{version_entry.id}/main.py /app/data/input/_params.json
   ```
   Capture stdout. On non-zero exit code: call `_destroy_container(container_name)` and raise `ToolComponentOperationException` with the stderr output.
9. Parse stdout as JSON to obtain `output_parameters: dict[str, Any]`.
   - On parse failure: call `_destroy_container(container_name)` and raise `ToolComponentOperationException`.
10. Call `_destroy_container(container_name)` to clean up the container and its data directory.
11. Trigger `_replenish_standby_pool(sandbox_entry)` asynchronously in the background (fire-and-forget; do not await).
12. Return `output_parameters`.
