# ToolComponent

A component of the **Dynamic AI Agent** framework that manages tool definitions, sandboxed execution environments, and invocation of code-based tools via Docker or host-side execution.

---

## Overview

`ToolComponent` is the top-level facade that exposes all tool-related operations to the application. Internally it delegates to three sub-services:

| Sub-service | Responsibility |
|---|---|
| `ToolCatalogueService` | CRUD and full-text / vector search over `ToolCatalogueEntry` and `ToolVersionEntry` records |
| `SandboxCatalogueService` | CRUD and search over `SandboxCatalogueEntry` records (Host and Docker subtypes) |
| `DockerSandboxService` | Executes tool code inside Docker containers with parameter I/O, file exchange, and a per-run `tmp` directory |

All state is persisted in **SurrealDB**.

---

## Package structure

```
toolcomponent/
├── __init__.py                     # Public re-exports
├── build_nuitka.py                 # Nuitka compilation helper
├── i_tool_component.py             # IToolComponent interface
├── tool_component.py               # ToolComponent implementation
├── i_tool_catalogue_service.py     # IToolCatalogueService interface
├── tool_catalogue_service.py       # ToolCatalogueService implementation
├── i_sandbox_catalogue_service.py  # ISandboxCatalogueService interface
├── sandbox_catalogue_service.py    # SandboxCatalogueService implementation
├── i_docker_sandbox_service.py     # IDockerSandboxService interface
├── docker_sandbox_service.py       # DockerSandboxService implementation
├── exceptions/
│   ├── tool_component_exception.py   # Base ToolComponentException
│   └── tool_component_exceptions.py  # All concrete exceptions
└── models/
    ├── tool_catalogue.py                  # ToolCatalogueEntry, ToolVersionEntry, InputParameterDefinition
    ├── tool_catalogue_search_criteria.py  # ToolCatalogueSearchCriteria
    ├── tool_catalogue_search_result_entry.py  # ToolCatalogueSearchResultEntry
    ├── tool_version_entry_search_criteria.py  # ToolVersionEntrySearchCriteria
    ├── sandbox_catalogue.py               # SandboxCatalogueEntry, SandboxCatalogueHostEntry, SandboxCatalogueDockerEntry
    ├── sandbox_catalogue_search_criteria.py   # SandboxCatalogueSearchCriteria
    └── tool_component_configurations.py   # ToolComponentConfigurations
```

---

## Quick start

### 1. Pre-requisites

- SurrealDB with the `dynamic-ai-agent` namespace
- A `component_configurations:tool_component` record in the target database with at minimum `app_data_folder` set
- Docker (optional — only required for Docker-sandbox invocation)

### 2. Create the configuration record (SurrealQL)

```surql
UPSERT component_configurations:tool_component MERGE {
    app_data_folder: "/var/data/dynamic-ai-agent",
    name_analyzer: "default_ngram_analyzer",
    description_analyzer: "default_english_analyzer"
};
```

### 3. Initialize

```python
import logging
from gafs.dynamicaiagent.common.databasemanager import DatabaseManager
from gafs.dynamicaiagent.toolcomponent import (
    ToolComponent,
    ToolCatalogueService,
    SandboxCatalogueService,
    DockerSandboxService,
)

logger = logging.getLogger("myapp")

# Build the DatabaseManager (assumes initialize_default_connection already called)
manager = DatabaseManager(logger)

component = ToolComponent(
    logger=logger,
    tool_catalogue_service=ToolCatalogueService(logger),
    sandbox_catalogue_service=SandboxCatalogueService(logger),
    docker_sandbox_service=DockerSandboxService(logger),
)
await component.initialize(manager)
```

### 4. Register a tool

```python
from gafs.dynamicaiagent.toolcomponent.models import ToolCatalogueEntry, ToolVersionEntry
from gafs.dynamicaiagent.toolcomponent.models.tool_catalogue import ToolStatus, ToolVersionStatus, InputParameterDefinition
from gafs.dynamicaiagent.common.models import FieldAttributeType

# Create catalogue entry
entry = ToolCatalogueEntry()
entry.name = "echo_tool"
entry.status = ToolStatus.ACTIVE
entry.description = "Echoes the supplied value"
entry.tags = ["demo"]
created_entry = await component.create_tool_catalogue_entry(entry)

# Create a version with inline code
version = ToolVersionEntry()
version.tool_id = created_entry.id
version.status = ToolVersionStatus.LATEST
version.language = "Python"
version.sandbox_id = "<sandbox_id>"
version.code = (
    "import json, sys\n"
    "params = json.loads(open(sys.argv[1]).read())\n"
    "result = params['input_parameters'].get('value', '')\n"
    "print(json.dumps({'result': result}))\n"
)
param = InputParameterDefinition()
param.name = "value"
param.type = FieldAttributeType.STRING
param.required = True
version.input_parameters = [param]
created_version = await component.create_tool_version_entry(version)
```

### 5. Invoke a tool

```python
from gafs.dynamicaiagent.toolcomponent.models.tool_catalogue import ToolInvocationRequest

request = ToolInvocationRequest()
request.tool_id = created_entry.id
request.version_id = created_version.id
request.input_parameters = {"value": "hello"}

result = await component.invoke(
    tool_id=request.tool_id,
    version_id=request.version_id,
    input_parameters=request.input_parameters,
)
print(result.output_parameters)  # {"result": "hello"}
```

---

## Data model

### ToolCatalogueEntry

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Auto-assigned SurrealDB record ID |
| `name` | `str` | Unique tool name |
| `status` | `ToolStatus` | `active` / `deprecated` / `experimental` |
| `description` | `str` | Human-readable description |
| `description_vector` | `list[float]` | Embedding for vector search |
| `tags` | `list[str]` | Arbitrary labels for filtering |

### ToolVersionEntry

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Auto-assigned record ID |
| `tool_id` | `str` | ID of the parent `ToolCatalogueEntry` |
| `status` | `ToolVersionStatus` | `latest` / `stable` / `deprecated` |
| `language` | `str` | Implementation language (e.g. `"Python"`) |
| `sandbox_id` | `str` | ID of the `SandboxCatalogueEntry` to use |
| `code` | `str` \| `None` | Inline source code |
| `code_link` | `str` \| `None` | Git URL for the code repository |
| `input_parameters` | `list[InputParameterDefinition]` | Declared input schema |
| `output_parameters` | `list[OutputParameterDefinition]` | Declared output schema |

### SandboxCatalogueEntry (subtypes)

- **`SandboxCatalogueHostEntry`** — executes code directly on the host Python interpreter
- **`SandboxCatalogueDockerEntry`** — builds and runs a Docker container; requires `docker_file`

---

## File layout for tool execution

When `DockerSandboxService` runs a tool, it maps three host directories into the container:

```
{app_data_folder}/tools/files/{sandbox_id}_{run_counter}/
    input/      # Input files pre-written by the caller before invocation
    output/     # Output files written by the tool code and read back after
    tmp/        # Temporary scratch space; cleaned up after each run
```

Parameters are serialized to `input/params.json` and passed as `sys.argv[1]`. The tool writes its output as a JSON object to stdout; `DockerSandboxService` captures and parses it.

---

## Configuration

The `ToolComponentConfigurations` record at `component_configurations:tool_component` accepts:

| Field | Default | Description |
|---|---|---|
| `app_data_folder` | *(required)* | Root directory for all tool file I/O |
| `name_analyzer` | `default_ngram_analyzer` | SurrealDB FTS analyzer for `name` index |
| `description_analyzer` | `default_english_analyzer` | SurrealDB FTS analyzer for `description` index |
| `vector_dimensions` | `1536` | Embedding vector dimensionality |
| `vector_data_type` | `F32` | HNSW vector data type |
| `vector_search_method` | `COSINE` | HNSW distance metric |
| `vector_exploration_factor` | `150` | HNSW `EFC` parameter |
| `vector_max_connections` | `12` | HNSW `M` parameter |

---

## Building with Nuitka

```sh
cd Python/
python gafs/dynamicaiagent/toolcomponent/build_nuitka.py
```

Output is placed under `build/<arch>/gafs/dynamicaiagent/toolcomponent/`.

See [NuitkaBuildRules.md](../../../../../Documents/CodingRules/NuitkaBuildRules.md) for project-wide build conventions.

---

## Running the tests

```sh
cd Python/
pytest gafs/dynamicaiagent/toolcomponent/test/ -v
```

See [test/README.md](test/README.md) for full test documentation.
