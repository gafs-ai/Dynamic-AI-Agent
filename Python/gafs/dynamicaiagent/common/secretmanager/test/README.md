# secretmanager — Tests

Tests for `gafs.dynamicaiagent.common.secretmanager`.

## Test Files

| File | Description |
|---|---|
| `test_secret_manager.py` | Main test suite. Runs against the source Python package. |
| `test_build_secret_manager.py` | Build test. Runs the same suite against the Nuitka-compiled `.pyd` / `.so` module. |

## Running Tests

All commands must be run from the `Python/` directory.

### Source Tests

```bash
python -m pytest gafs/dynamicaiagent/common/secretmanager/test/test_secret_manager.py -v
```

### Build Tests

Build the compiled module first, then run:

```bash
# Build
python gafs/dynamicaiagent/common/secretmanager/build_nuitka.py

# Test compiled module
python -m pytest gafs/dynamicaiagent/common/secretmanager/test/test_build_secret_manager.py -v
```

## External Requirements

The test suite uses an **in-memory embedded SurrealDB** — no external database or
configuration files are required.

Cryptographic keys are auto-generated during test fixture setup and are isolated to a
temporary directory per test (via `tmp_path`).

## Test Structure

| Class | Tests | Description |
|---|---|---|
| `TestSecretKeyModel` | 11 | `SecretKey` construction, validation, serialization (`to_dict`, `to_json`, `from_dict`, `from_json`) |
| `TestSecretModel` | 14 | `Secret` construction, id normalization, datetime coercion, `to_dict` (excludes `raw_secret`), `from_dict` |
| `TestSecretSearchCriteria` | 13 | Criteria validation, datetime coercion, `to_query()` output for name/limit/unsupported-provider |
| `TestSecretManagerKeyManagement` | 8 | `add_key`, `get_key`, `generate_key`, `initialize()` key loading priority (A/B/C) |
| `TestSecretManagerCRUD` | 12 | Full CRUD lifecycle: `create_secret`, `get_secret` (decrypt/masked), `update_secret`, `search_secrets`, `delete_secret`, not-initialized guard |
