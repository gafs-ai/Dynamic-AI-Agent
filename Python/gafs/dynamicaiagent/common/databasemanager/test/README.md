## 1. Target classes, methods, and test items

### `IDatabaseManager` / `DatabaseManager`

`DatabaseManager` is the concrete implementation of `IDatabaseManager`. It manages a
registry of `IDatabaseProvider` instances keyed by `DatabaseConnection.id` and persists
`DatabaseConnection` configuration entries in the `databases` collection of the default
database.

#### `initialize_default_connection(config: DatabaseConnection) -> None`

- Builds `DatabaseProviderOptions` from `config.parameters` merged with `config.raw_secret`.
- Creates and registers the default `IDatabaseProvider`.
- Upserts a placeholder record (`id: "default"`, `name: "default"`) in the `databases`
  collection (idempotent).
- Defines a unique index on the `name` field of the `databases` collection.

#### `initialize(secret_manager: ISecretManager) -> None`

- Registers an `ISecretManager` to complete phase-3 initialisation.
- All methods that depend on secrets raise `DatabaseManagerNotInitializedException` until
  this method is called.

#### `add_connection(connection_configurations: DatabaseConnection) -> DatabaseConnection`

- Creates a new `DatabaseConnection` entry in the `databases` collection.
- If `raw_secret` is set, creates a `Secret` via `ISecretManager` and links it by id.
- If both `raw_secret` and `secret` are set simultaneously, raises
  `DatabaseManagerInvalidOperationException`.
- If `secret` is provided but does not exist, raises `DatabaseManagerSecretNotFoundException`.

#### `update_connection(database_connection: DatabaseConnection) -> DatabaseConnection`

- Merge-updates an existing `DatabaseConnection` record.
- Raises `DatabaseManagerInvalidOperationException` when:
  - The target id or name is `"default"`.
  - `raw_secret` is set (rotate credentials via `SecretManager` directly).
  - `id` is `None`.
- Raises `DatabaseManagerConnectionNotFoundException` if the record does not exist.
- If a cached provider exists for the id, closes and recreates it with updated options.

#### `get_connection(id: str) -> DatabaseConnection | None`

- Returns the `DatabaseConnection` for the given id, or `None`.

#### `get_connection_by_name(name: str) -> DatabaseConnection | None`

- Returns the `DatabaseConnection` for the given name, or `None`.

#### `delete_connection(id: str) -> None`

- Raises `DatabaseManagerInvalidOperationException` if id is `"default"`.
- Raises `DatabaseManagerConnectionNotFoundException` if the record does not exist.
- Removes the cached provider (if any) and deletes the record from the database.

#### `get_provider(id: str) -> IDatabaseProvider`

- Returns the cached provider immediately if already registered.
- Lazily creates and caches the provider from the `databases` collection if not cached.
- Raises `DatabaseManagerNotInitializedException` for non-default ids when phase-3 init
  has not been completed.
- Raises `DatabaseManagerConnectionNotFoundException` if no record exists for the id.
- Raises `DatabaseManagerSecretNotFoundException` if the required secret does not exist.

#### `get_default_provider() -> IDatabaseProvider`

- Returns the default `IDatabaseProvider` synchronously (no `await`).
- Raises `DatabaseManagerConnectionNotFoundException` if phase-1 init has not been done.

#### `_add_provider(options, provider_id, overwrite=False) -> IDatabaseProvider` *(internal)*

- Creates and registers a new provider under `provider_id`.
- When `overwrite=True`, closes the existing provider before replacing it.
- Raises `DatabaseManagerConfigurationException` for unsupported `database_type`.

#### `_remove_provider(provider_id) -> bool` *(internal)*

- Closes and deregisters the provider for `provider_id`.
- Returns `True` if removed, `False` if the key was not registered.

---

## 2. Test workflows

All tests are in `test_database_manager.py` using `pytest` and `pytest-asyncio`.

For unit tests, `IDatabaseProvider` is replaced with `DummyProvider` and `ISecretManager`
with `DummySecretManager`, so no real database connection is required.

Integration tests (marked with `@pytest.mark.skipif`) connect to a real SurrealDB instance.
Connection details are loaded from `secret_test_config_default_database_configurations.json`.
The tests are automatically skipped when that file is absent.

### Test categories

| Category | Tests |
|----------|-------|
| `_add_provider` (internal) | register, overwrite closes old, unsupported type raises |
| `get_default_provider` | raises when not registered, returns registered provider |
| `initialize` / `_check_initialized` | registers secret manager, raises before initialize |
| `get_provider` | returns default, returns cached, raises before phase-3 init |
| `update_connection` validation | rejects default id/name, rejects raw_secret, rejects missing id |
| `delete_connection` validation | rejects default, raises for missing record |
| `add_connection` validation | rejects both raw_secret + secret simultaneously |
| `DatabaseConnection` model | raw_secret excluded from serialization, from_dict roundtrip, to_dict enum handling, to_json exclude_id |
| Integration | real connect smoke test, default entry exists in `databases` collection after init |

---

## 3. Running the tests

```bash
# From the Python/ directory

# Source tests
pytest gafs/dynamicaiagent/common/databasemanager/test/test_database_manager.py -v

# Compiled (Nuitka) tests
python gafs/dynamicaiagent/common/databasemanager/build_nuitka.py
pytest gafs/dynamicaiagent/common/databasemanager/test/test_build_database_manager.py -v
```

For details on how `gafs.dynamicaiagent.common.__path__` is adjusted when running compiled
tests, see `Documents/CodingRules/NuitkaBuildRules.md`.

Concrete providers (e.g. `SurrealDbRemoteProvider`) are monkeypatched with a simple dummy provider
to avoid external dependencies.

### 2.1 `add_provider`

- **Workflow: add new provider**
  1. Create a `DatabaseManager` with a test logger.
  2. Create `DatabaseProviderOptions` (or a concrete subclass) with a unique `database_name`
     and supported `database_type` (e.g. `DatabaseType.SURREALDB_REMOTE`).
  3. Monkeypatch the provider factory (`SurrealDbRemoteProvider`) with a dummy provider that records
     calls to `initialize()` and `close()`.
  4. Call `add_provider(options)`.
  5. Assert that:
     - The call returns `True`.
     - A provider is stored under `options.database_name`.
     - When `database_name` equals the default name, `get_default_database_provider()` returns
       the same provider.

- **Workflow: duplicate without overwrite**
  1. Register a provider with `database_name="dup-db"`.
  2. Call `add_provider(options, overwrite=False)` again with the same options.
  3. Assert that:
     - The second call returns `False`.
     - The original provider instance remains stored (not replaced).
     - `close()` on the original provider is **not** called.

- **Workflow: duplicate with overwrite**
  1. Register a provider with `database_name="overwrite-db"`.
  2. Call `add_provider(options, overwrite=True)` with the same `database_name`.
  3. Assert that:
     - The second call returns `True`.
     - The original provider’s `close()` is called.
     - The stored provider is replaced with a new instance.

- **Workflow: unsupported type**
  1. Create options with an unsupported `database_type` (e.g. `DatabaseType.SURREALDB_SUBPROCESS`).
  2. Call `add_provider(options)`.
  3. Assert that `DatabaseProviderOptionsException` is raised.

### 2.2 `get_provider`

- **Workflow: existing provider**
  1. Register a provider with `database_name="existing-db"`.
  2. Call `get_provider("existing-db")`.
  3. Assert that the returned object is the stored provider.

- **Workflow: non-existing provider**
  1. Create a `DatabaseManager` without registering any providers.
  2. Call `get_provider("non-existing-db")`.
  3. Assert that the result is `None`.

### 2.3 `get_default_database_provider`

- **Workflow: default exists**
  1. Register a provider with `database_name=IDatabaseManager.DEFAULT_DATABASE_NAME()`.
  2. Call `get_default_database_provider()`.
  3. Assert that the returned provider is the one registered for the default name.

- **Workflow: default does not exist**
  1. Create a `DatabaseManager` and register only non-default names.
  2. Call `get_default_database_provider()`.
  3. Assert that the result is `None`.

### 2.4 `remove_provider`

- **Workflow: remove existing provider**
  1. Register a provider with `database_name="removable-db"` (and optionally as default).
  2. Call `remove_provider("removable-db")`.
  3. Assert that:
     - The call returns `True`.
     - The provider is removed from the manager.
     - The provider’s `close()` is called once.
     - If it was the default, `get_default_database_provider()` returns `None` afterwards.

- **Workflow: remove non-existing provider**
  1. Create a `DatabaseManager` and (optionally) register some providers under other names.
  2. Call `remove_provider("non-existing-db")`.
  3. Assert that the call returns `False` and the manager state is unchanged.

---

## 3. Prerequisites and test commands

### 3.1 Prerequisites

- Python 3.12 (same as project environment).
- `pytest` and `pytest-asyncio` (already required by the project; see `Python/requirements`).
- No external database or configuration files are required; database providers are replaced by
  in-memory dummy providers in tests.

### 3.2 Test command

From the `Python/` directory:

```bash
cd Python
pytest gafs/dynamicaiagent/common/databasemanager/test/test_database_manager.py -v
```
