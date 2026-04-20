# databasemanager — Tests

Tests for `gafs.dynamicaiagent.common.databasemanager`.

## Test Files

| File | Description |
|---|---|
| `test_database_manager.py` | Main test suite. Runs against the source Python package. |
| `test_build_database_manager.py` | Build test. Runs the same suite against the Nuitka-compiled `.pyd` / `.so` module. |

## Running Tests

All commands must be run from the `Python/` directory.

### Source Tests

```bash
python -m pytest gafs/dynamicaiagent/common/databasemanager/test/test_database_manager.py -v
```

### Build Tests

Build the compiled module first, then run:

```bash
# Build
python gafs/dynamicaiagent/common/databasemanager/build_nuitka.py

# Test compiled module
python -m pytest gafs/dynamicaiagent/common/databasemanager/test/test_build_database_manager.py -v
```

## External Requirements

The local test suite uses an **in-memory embedded SurrealDB** — no external database
or configuration files are needed.

One test is conditionally skipped:

| Test | Skip Condition | Required File |
|---|---|---|
| `TestInitialization::test_initialize_remote_success` | Skipped if config file missing | `test/remote_db_config.json` |

### `remote_db_config.json` format

```json
{
  "endpoint": "wss://your-instance.surrealdb.cloud/rpc",
  "namespace": "test",
  "database": "test",
  "username": "root",
  "password": "root",
  "auth_level": "root"
}
```

## Test Structure

| Class | Tests | Description |
|---|---|---|
| `TestDatabaseConnectionModel` | 13 | `DatabaseConnection` serialization, normalization, `to_dict`, `from_dict` |
| `TestFullTextAnalyzerModel` | 14 | `FullTextAnalyzer` factory methods, SurrealQL statement generation, validation |
| `TestSurrealEnums` | 3 | `SurrealTokenizer` and `SurrealFilter` enum values |
| `TestInitialization` | 7 (1 skipped) | Phase-1 and phase-3 initialization, error cases |
| `TestAnalyzerCatalogue` | 12 | Full CRUD on `FullTextAnalyzer` entries |
| `TestConnectionCatalogue` | 15 | Full CRUD on `DatabaseConnection` entries |
| `TestProviderGetters` | 4 | `get_provider`, `get_default_provider` |
