## ModelComponent test README

This directory contains **integration tests only** for `gafs.dynamicaiagent.modelcomponent`.
Unit tests are intentionally not used because this component is highly integrated
with SurrealDB and external dependencies.

### Prerequisites

- **Python**: Use the `py` launcher on Windows (recommended).
- **Network access**: Tests require a reachable SurrealDB endpoint.
- **Credentials**: Integration tests require a SurrealDB connection. Place working credentials in local `secret_test_*.json` files. Those files are listed in `.gitignore` and will **not** be committed to the repository.

### Required local config files (not committed)

Tests will look for a DB config file in this directory and **skip** when missing.

- `secret_test_db_config.json` (preferred)
- `secret_test_config_0.json` (fallback)

Expected JSON keys:

- `endpoint` (e.g. `wss://.../rpc`)
- `namespace`
- `database`
- `username`
- `password`

### Running tests

Run from this folder:

```bash
py -m pytest -q
```

Run a single test file:

```bash
py -m pytest -q test_model_component.py
```

### Test scope (spec)

The test suite is organized by interface:

- `test_model_catalogue_service.py`
  - Covers all public methods defined on `IModelCatalogueService`
  - Happy-path and error-path scenarios
- `test_model_service.py`
  - Covers all public methods defined on `IModelService`
  - Happy-path and error-path scenarios
- `test_model_component.py`
  - Covers all public methods defined on `IModelComponent`
  - Happy-path and error-path scenarios
  - Acts as an end-to-end façade test over catalogue/service behaviors

### Test fixtures (`secret_test_*`)

JSON fixtures under this directory support integration / manual tests.

#### File roles

| File | Role |
|------|------|
| `secret_test_db_config.json` | SurrealDB connection (`endpoint`, `namespace`, `database`, `username`, `password`). |
| `secret_test_secret_*.json` | Secret documents (payload under `secret`). |
| `secret_test_deployment_*.json` | Deployment documents (`ModelDeployment` shape). |
| `secret_test_catalogue_*.json` | Catalogue documents (`ModelCatalogue` shape). |
| `secret_test_invoke_*.json` | Invoke requests (`AiRequest` shape). **All files matching this pattern are executed by the integration tests.** |

#### Loading a catalogue document (example)

```python
import json
from pathlib import Path

from gafs.dynamicaiagent.modelcomponent.models.model_catalogue import ModelCatalogue

path = Path(__file__).parent / "secret_test_catalogue_openai_tel3.json"
data = json.loads(path.read_text(encoding="utf-8"))
catalogue = ModelCatalogue.from_dict(data)
```

### Notes / troubleshooting

- **Hyphens in record IDs**: Avoid using `-` in ad-hoc ids in tests because some
  error messages can be parsed as SurrealQL subtraction. Prefer underscores
  (`does_not_exist`) for "missing id" scenarios.
- **SurrealDB index syntax variance**: Some SurrealDB deployments reject certain
  index DDL statements. The code uses best-effort index drop and then recreates
  indexes via `ensure_indexes(overwrite=True)` when needed.

#### Speech-to-text audio fixture note

`secret_test_invoke_stt_0.json` may omit large base64 `audio`. If you need STT
manual tests, copy `request.audio` from:

`gafs/dynamicaiagent/utils/databaseprovider/test/secret_test_config_azure_openai_speech_to_text.json`

into `invoke.payload.audio` at runtime, or load that file programmatically.

