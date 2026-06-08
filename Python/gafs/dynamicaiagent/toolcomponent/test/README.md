# ToolComponent — Integration Tests

All tests in this directory connect to a real SurrealDB instance and test against live data. There are no mocks.

---

## Test files

| File | What it tests |
|---|---|
| `test_tool_catalogue_service.py` | `ToolCatalogueService` — CRUD, search (status, keywords, tags), version entries, error cases |
| `test_sandbox_catalogue_service.py` | `SandboxCatalogueService` — CRUD for Host and Docker entries, search |
| `test_docker_sandbox_service.py` | `DockerSandboxService` — code execution with parameter I/O, file exchange, tmp directory, DB-stored code, file-stored code |
| `test_tool_component.py` | `ToolComponent` facade — initialization, configuration, delegation, invocation |

---

## Prerequisites

### SurrealDB connection

Create `Python/secret_test_db_config.json` (excluded from version control):

```json
{
    "endpoint": "wss://<your-surreal-cloud-endpoint>/rpc",
    "namespace": "dynamic-ai-agent",
    "database": "connection-test",
    "username": "<test-db-user>",
    "password": "<test-db-password>"
}
```

All test files skip automatically when this file is absent.

The `conftest.py` fixture also issues an `UPSERT component_configurations:tool_component MERGE {...}` to guarantee the configuration record is present before any test runs.

### Docker (optional)

`test_docker_sandbox_service.py` and the Docker invocation tests in `test_tool_component.py` require a reachable Docker daemon. Those tests are automatically skipped when Docker is not available.

---

## Running the tests

```sh
cd Python/

# All toolcomponent integration tests
pytest gafs/dynamicaiagent/toolcomponent/test/ -v

# Single test file
pytest gafs/dynamicaiagent/toolcomponent/test/test_tool_catalogue_service.py -v

# Single test
pytest gafs/dynamicaiagent/toolcomponent/test/test_tool_catalogue_service.py::TestToolCatalogueEntryCRUD::test_create_and_get -v -s
```

---

## Fixtures

All fixtures are defined in `conftest.py`.

### `integration_env_async` (function-scoped)

Returns an async factory callable. Each test calls it as:

```python
async def run() -> None:
    env = await integration_env_async()
    svc = env.catalogue_service
    ...
asyncio.run(run())
```

`IntegrationEnv` provides:

| Attribute | Type | Description |
|---|---|---|
| `logger` | `logging.Logger` | Shared test logger |
| `manager` | `DatabaseManager` | Initialized database manager |
| `provider` | `IDatabaseProvider` | Default SurrealDB provider |
| `catalogue_service` | `ToolCatalogueService` | Initialized catalogue service |
| `sandbox_service` | `SandboxCatalogueService` | Initialized sandbox catalogue service |
| `docker_service` | `DockerSandboxService` | Initialized Docker sandbox service |
| `component` | `ToolComponent` | Initialized top-level component |
| `app_data_folder` | `str` | `tmp_path`-based data folder (pytest-managed, cleaned per test) |

---

## Test markers

| Marker | Condition | Applied to |
|---|---|---|
| `requires_docker` | Docker daemon unreachable | All tests in `test_docker_sandbox_service.py`; Docker invocation tests in `test_tool_component.py` |

Skips are automatic — no manual intervention required.

---

## Helper utilities

`test_helpers.py` provides:

- `unique_suffix() -> str` — millisecond timestamp suffix used to avoid name collisions between parallel or repeated test runs
- `is_docker_available() -> bool` — probes the Docker daemon; used by the `requires_docker` skip marker

---

## Test data cleanup

Every test that creates DB records deletes them in a `finally` block to leave the database clean. The `conftest.py` fixture restores the `component_configurations:tool_component` record after tests that remove it (e.g. `test_initialize_fails_without_config`).
