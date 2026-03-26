## 1. Target classes, methods, and test items

### 1.1 `IDatabaseManager` / `DatabaseManager`

`DatabaseManager` is the concrete implementation of `IDatabaseManager`. It manages multiple
database providers keyed by `database_name` and tracks a single default provider.

#### `add_provider(options: DatabaseProviderOptions, overwrite: bool = False) -> bool`

- **Normal**:
  - Adds a new provider when `database_name` does not exist.
  - When `database_name` equals `IDatabaseManager.DEFAULT_DATABASE_NAME()`, the provider is
    also set as the default.
- **Duplicate (overwrite = False)**:
  - When a provider with the same `database_name` already exists and `overwrite=False`,
    the method returns `False` and does **not** replace the existing provider.
- **Duplicate (overwrite = True)**:
  - When a provider with the same `database_name` already exists and `overwrite=True`,
    the existing provider is closed and replaced by a new one, and the method returns `True`.
- **Unsupported type**:
  - When `options.database_type` is not supported, `DatabaseProviderOptionsException` is raised.

#### `get_provider(database_name: str) -> IDatabaseProvider | None`

- Returns the provider instance when `database_name` exists.
- Returns `None` when `database_name` does not exist.

#### `get_default_database_provider() -> IDatabaseProvider | None`

- Returns the provider whose `database_name` equals `IDatabaseManager.DEFAULT_DATABASE_NAME()`
  when it exists.
- Returns `None` when no provider is registered under the default name.

#### `remove_provider(database_name: str) -> bool`

- **Existing provider**:
  - Closes and removes the provider when `database_name` exists, and returns `True`.
  - If the removed provider was the default, the default reference is cleared.
- **Non-existing provider**:
  - Returns `False` when `database_name` is not found and leaves the manager state unchanged.

Implementation details (e.g. how providers are created for each `DatabaseType`) are tested
indirectly via the above behaviors. For unit tests, concrete providers are **replaced with
test doubles** so that database connections are not required.

---

## 2. Test workflows

All tests are implemented in `test_database_manager.py` as pytest tests (`pytest-asyncio` for async).
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
