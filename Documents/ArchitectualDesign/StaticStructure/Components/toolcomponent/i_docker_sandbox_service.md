---
class: IDockerSandboxService
kind: abstract_class
module: gafs.dynamicaiagent.toolcomponent
inherits: [ABC]
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

## responsibilities

- Manage Docker image/container lifecycle for sandboxed tool execution.
- Pre-build images and pool standby containers for active `SandboxCatalogueDockerEntry` definitions to reduce per-invocation latency.
- Execute tool code inside a container, inject input parameters, and collect output parameters.

## naming conventions

| resource        | naming rule                                     | example                          |
| --------------- | ----------------------------------------------- | -------------------------------- |
| Docker image    | `{sandbox_catalogue_entry.id}`                  | `a1b2c3d4`                       |
| Docker container | `{sandbox_catalogue_entry.id}_{count}`         | `a1b2c3d4_0`, `a1b2c3d4_1`      |

## filesystem layout

```
{app_data_folder}/
  tools/
    codes/
      {tool_catalogue_id}_{tool_version_id}/   ← mounted in container as /app/codes/{tool_catalogue_id}_{tool_version_id}/ (read-only)
        main.py
        ...
    files/
      {container_name}/                        ← mounted in container as /app/data/ (read/write)
        input/
          _params.json                         ← written by system before execution
          ...                                  ← input files provided by caller
        output/
          ...                                  ← output files written by tool code
        tmp/
          ...                                  ← temporary files used by tool code
```

## container mount configuration

| host path                                              | container path | mode       |
| ------------------------------------------------------ | -------------- | ---------- |
| `{app_data_folder}/tools/codes`                        | `/app/codes`   | read-only  |
| `{app_data_folder}/tools/files/{container_name}`       | `/app/data`    | read/write |

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

| property    | value |
| ----------- | ----- |
| async       | true  |
| description | Initialize the Docker sandbox service. Obtains a database provider and pre-builds standby containers for active sandbox definitions up to the limits defined in `ToolComponentConfigurations`. |

#### returns

| type   | value  | description              |
| ------ | ------ | ------------------------ |
| `bool` | `True` | Successfully initialized |

#### raises

| exception                              | condition              |
| -------------------------------------- | ---------------------- |
| `ToolComponentInitializationException` | Initialization failure |

#### rules

- The number of standby containers per sandbox definition must not exceed `docker_default_image_max_stand_by` from `ToolComponentConfigurations`.
- The total number of standby containers across all definitions must not exceed `docker_total_default_image_max_stand_by` from `ToolComponentConfigurations`.

---

### execute_code

```python
async def execute_code(
    version_entry: ToolVersionEntry,
    sandbox_entry: SandboxCatalogueDockerEntry,
    input_parameters: dict[str, Any],
) -> dict[str, Any]
```

| property    | value |
| ----------- | ----- |
| async       | true  |
| description | Execute the code defined in `version_entry` inside a Docker container built from `sandbox_entry`. Injects `input_parameters` and returns the collected output parameters. |

#### parameters

| name               | type                           | required | description                                              |
| ------------------ | ------------------------------ | -------- | -------------------------------------------------------- |
| `version_entry`    | `ToolVersionEntry`             | yes      | Tool version record containing the code and parameter definitions |
| `sandbox_entry`    | `SandboxCatalogueDockerEntry`  | yes      | Docker sandbox definition (Dockerfile, run options)      |
| `input_parameters` | `dict[str, Any]`               | yes      | Actual values for the input parameters defined in `version_entry.input_parameters` |

#### returns

| type             | description                                                                       |
| ---------------- | --------------------------------------------------------------------------------- |
| `dict[str, Any]` | Collected output parameter values keyed by the names defined in `version_entry.output_parameters` |

#### raises

| exception                              | condition                                                            |
| -------------------------------------- | -------------------------------------------------------------------- |
| `ToolComponentNotInitializedException` | Service is not initialized.                                          |
| `SandboxCatalogueEntryNotFoundException` | `sandbox_entry` is not found or has been retired.                  |
| `ToolComponentOperationException`      | Container creation, execution, or output collection failure          |

#### rules

1. If a standby container for `sandbox_entry` is available, take it from the pool; otherwise call `_create_container` to provision a new one.
2. Construct the system parameters object and write to `{app_data_folder}/tools/files/{container_name}/input/_params.json`:
   ```json
   {
     "input_parameters": { ... },
     "input_dir":  "/app/data/input",
     "output_dir": "/app/data/output",
     "tmp_dir":    "/app/data/tmp"
   }
   ```
3. Execute the tool code inside the container:
   ```
   docker exec {container_name} python /app/codes/{tool_catalogue_id}_{tool_version_id}/main.py /app/data/input/_params.json
   ```
4. Capture stdout from the execution. Parse as JSON to obtain `output_parameters: dict[str, Any]`.
5. After execution (success or failure), destroy the container via `_destroy_container` and delete the data folder `{app_data_folder}/tools/files/{container_name}`.
6. Asynchronously replenish the standby pool in the background.
7. Input parameters are validated against the definitions in `version_entry.input_parameters` before injection.

## private methods

---

### `_create_image`

```python
async def _create_image(
    sandbox_entry: SandboxCatalogueDockerEntry
) -> str
```

| property    | value |
| ----------- | ----- |
| description | Build a Docker image from `sandbox_entry.docker_file`. The image is tagged with `sandbox_entry.id`. Returns the image name (= `sandbox_entry.id`). |

#### rules

- Image name (tag): `sandbox_entry.id`
- If an image with the same name already exists, reuse it without rebuilding.

#### raises

| exception                         | condition                  |
| --------------------------------- | -------------------------- |
| `ToolComponentOperationException` | Docker image build failure |

---

### `_create_container`

```python
async def _create_container(
    sandbox_entry: SandboxCatalogueDockerEntry,
    container_count: int,
) -> str
```

| property    | value |
| ----------- | ----- |
| description | Create and start a Docker container from the image `sandbox_entry.id`, applying `sandbox_entry.run_options`. Creates the host-side data folder and sets up both mounts. Returns the container name. |

#### rules

1. Container name: `{sandbox_entry.id}_{container_count}`
2. Create host directories before starting the container:
   - `{app_data_folder}/tools/files/{container_name}/input`
   - `{app_data_folder}/tools/files/{container_name}/output`
   - `{app_data_folder}/tools/files/{container_name}/tmp`
3. Start the container with the following volume mounts and keep it running:
   ```
   docker run -d \
     --name {container_name} \
     -v {app_data_folder}/tools/codes:/app/codes:ro \
     -v {app_data_folder}/tools/files/{container_name}:/app/data:rw \
     {sandbox_entry.run_options} \
     {sandbox_entry.id} \
     sleep infinity
   ```
4. Return the container name.

#### raises

| exception                         | condition                         |
| --------------------------------- | --------------------------------- |
| `ToolComponentOperationException` | Docker container creation failure |

---

### `_destroy_container`

```python
async def _destroy_container(container_name: str) -> None
```

| property    | value |
| ----------- | ----- |
| description | Stop and remove the Docker container identified by `container_name`, then delete the associated data folder `{app_data_folder}/tools/files/{container_name}`. Best-effort; errors are logged but not propagated. |

---

### `_remove_image`

```python
async def _remove_image(image_name: str) -> None
```

| property    | value |
| ----------- | ----- |
| description | Remove the Docker image identified by `image_name`. Best-effort; errors are logged but not propagated. |

---

### `_exit`

```python
async def _exit() -> None
```

| property    | value |
| ----------- | ----- |
| description | Gracefully shut down the service. Destroys all standby containers via `_destroy_container`. Docker images are retained for reuse on the next startup. |

---

## tool code conventions

All tool code deployed via `ToolVersionEntry` must follow the conventions below.

### entry point

- The entry point file must be named **`main.py`** and placed at the root of the version directory:
  `{app_data_folder}/tools/codes/{tool_catalogue_id}_{tool_version_id}/main.py`

### entry point function

The `main.py` file must contain an `if __name__ == "__main__":` block that:

1. Reads the system parameters file path from `sys.argv[1]`.
2. Loads the JSON file at that path into a dict.
3. Calls the main function passing the parameters.
4. Writes the returned `output_parameters` dict to **stdout** as a single-line JSON string.

The main function signature must be:

```python
def main(
    input_parameters: dict[str, Any],
    input_dir: str,
    output_dir: str,
    tmp_dir: str,
) -> dict[str, Any]:
    ...
```

| parameter          | provider  | description                                                  |
| ------------------ | --------- | ------------------------------------------------------------ |
| `input_parameters` | caller    | Values for the parameters defined in `ToolVersionEntry.input_parameters` |
| `input_dir`        | system    | Absolute path inside the container to the `input` folder     |
| `output_dir`       | system    | Absolute path inside the container to the `output` folder    |
| `tmp_dir`          | system    | Absolute path inside the container to the `tmp` folder       |

### system parameters file (`_params.json`)

Written by the system to `{input_dir}/_params.json` before execution. The `main.py` **must not** rely on the filename; it must read from the path given via `sys.argv[1]`.

```json
{
  "input_parameters": { "<name>": "<value>", "..." : "..." },
  "input_dir":  "/app/data/input",
  "output_dir": "/app/data/output",
  "tmp_dir":    "/app/data/tmp"
}
```

### minimal `main.py` template

```python
from __future__ import annotations
import json
import sys
from typing import Any


def main(
    input_parameters: dict[str, Any],
    input_dir: str,
    output_dir: str,
    tmp_dir: str,
) -> dict[str, Any]:
    # --- implement tool logic here ---
    return {}


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        params = json.load(f)
    result = main(
        input_parameters=params["input_parameters"],
        input_dir=params["input_dir"],
        output_dir=params["output_dir"],
        tmp_dir=params["tmp_dir"],
    )
    print(json.dumps(result))
```

