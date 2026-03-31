## Overview

`databasemanager` is the **database manager** component used within Dynamic AI Agent.  
It provides the `IDatabaseManager` interface and its concrete implementation `DatabaseManager`,  
which manages both **database provider instances** (`IDatabaseProvider`) and **connection
configuration entries** (`DatabaseConnection`) stored in the default database's `databases`
collection.

---

### Structure

```
databasemanager/
├── __init__.py                          – Public API re-exports
├── database_connection.py               – DatabaseConnection data class
├── i_database_manager.py               – IDatabaseManager interface
├── database_manager.py                 – DatabaseManager implementation
├── exceptions/
│   ├── __init__.py
│   ├── database_manager_exception.py   – Base exception
│   └── database_manager_exceptions.py  – Concrete exception types
└── test/
    ├── README.md
    ├── test_database_manager.py
    └── test_build_database_manager.py
```

---

### Initialisation Sequence

`DatabaseManager` and `SecretManager` have a mutual dependency.  
Use the following two-phase initialisation:

```python
# Phase 1 – minimal bootstrap (no secret manager needed)
await database_manager.initialize_default_connection(config)

# Phase 2 – initialise SecretManager (which depends on DatabaseManager)
secret_manager.initialize(database_manager, crypto_util, keys)

# Phase 3 – complete DatabaseManager setup
await database_manager.initialize(secret_manager)
```

---

## Public API

### Data Classes

#### `DatabaseConnection`

Represents one entry in the `databases` SurrealDB collection.

| Field                 | Type                    | Notes                                              |
|-----------------------|-------------------------|----------------------------------------------------|
| `id`                  | `str \| None`           | Record id (normalised from SurrealDB `RecordID`).  |
| `name`                | `str \| None`           | Unique human-readable name.                        |
| `description`         | `str \| None`           | Optional description.                              |
| `database_type`       | `DatabaseProviderType \| None` | e.g. `DatabaseProviderType.SURREALDB_REMOTE`. Accepts a string on construction (auto-converted). |
| `secret`              | `str \| None`           | ID of the associated `Secret` record.              |
| `raw_secret`          | `dict[str, Any] \| None`| **Transient.** Raw credentials for `add_connection`. Never stored. |
| `parameters` | `dict[str, Any] \| None` | Non-secret parameters (endpoint, namespace, etc.). |

Methods: `to_dict()`, `to_json()`, `from_dict()`, `from_json()`.


### Interfaces

#### `IDatabaseManager`

| Method | Async | Description |
|--------|-------|-------------|
| `DEFAULT_DATABASE_NAME() -> str` | – | Returns `"default"`. |
| `COLLECTION_NAME() -> str` | – | Returns `"databases"`. |
| `initialize_default_connection(config)` | ✓ | Phase-1 init: connect to default DB, create placeholder entry, define unique index. |
| `initialize(secret_manager)` | ✓ | Phase-3 init: register SecretManager. |
| `add_connection(connection_configurations)` | ✓ | Create a `DatabaseConnection` entry; handles raw_secret → Secret creation. |
| `update_connection(database_connection)` | ✓ | Merge-update a `DatabaseConnection`; replaces cached provider if needed. |
| `get_connection(id)` | ✓ | Fetch a `DatabaseConnection` by id (returns `None` if not found). |
| `get_connection_by_name(name)` | ✓ | Fetch a `DatabaseConnection` by name (returns `None` if not found). |
| `delete_connection(id)` | ✓ | Delete a `DatabaseConnection`; removes cached provider. |
| `get_provider(id)` | ✓ | Return or lazily create the `IDatabaseProvider` for a connection id. |
| `get_default_provider()` | – | Return the default `IDatabaseProvider` synchronously. |

---

### Implementation

#### `DatabaseManager`

- Maintains an internal `dict[str, IDatabaseProvider]` keyed by `DatabaseConnection.id`.
- The default provider is keyed under `"default"` (= `DEFAULT_DATABASE_NAME()`).
- Providers for non-default connections are created lazily on the first `get_provider(id)` call.
- On `add_connection` with `raw_secret`, the raw credentials are automatically encrypted and
  stored as a `Secret` via `ISecretManager` before the `DatabaseConnection` is persisted.
- `_add_provider` and `_remove_provider` are internal helpers; `add_provider` is **not** part
  of the public interface.

---

### Exceptions

| Exception | Raised When |
|-----------|-------------|
| `DatabaseManagerNotInitializedException` | `initialize()` (phase 3) has not been called and a method that requires `ISecretManager` is invoked. |
| `DatabaseManagerConnectionNotFoundException` | No `DatabaseConnection` record / provider found for the given id or name. |
| `DatabaseManagerSecretNotFoundException` | The `Secret` referenced by a `DatabaseConnection` does not exist. |
| `DatabaseManagerInvalidOperationException` | Attempt to update/delete the `default` connection; `raw_secret` in update; both `raw_secret` and `secret` in one request. |
| `DatabaseManagerConfigurationException` | Unsupported `database_type`. |
| `DatabaseManagerProviderInitializationException` | Provider creation or connection setup failed. |
| `DatabaseManagerProviderCloseException` | Closing an existing provider failed. |

---

## Dependencies & Libraries

| Dependency | Website | License |
|------------|---------|---------|
| `surrealdb` | https://github.com/surrealdb/surrealdb.py | Apache-2.0 |

Internal dependencies from within this project:

- `gafs.dynamicaiagent.utils.databaseprovider` — `IDatabaseProvider`, `DatabaseProviderOptions`, `DatabaseType`, `SurrealDbRemoteProvider`, `RemoteSurrealDbOptions`
- `gafs.dynamicaiagent.common.secretmanager` — `ISecretManager`, `Secret`

---

## Testing

```bash
# From the Python/ directory

# Source tests
pytest gafs/dynamicaiagent/common/databasemanager/test/test_database_manager.py -v

# Compiled (Nuitka) tests
python gafs/dynamicaiagent/common/databasemanager/build_nuitka.py
pytest gafs/dynamicaiagent/common/databasemanager/test/test_build_database_manager.py -v
```

Unit tests use `DummyProvider` and `DummySecretManager` test doubles so that no real
database connection is required. Integration tests (marked `skipif`) connect to a real
SurrealDB instance using `test/secret_test_config_default_database_configurations.json`.

See `Documents/CodingRules/NuitkaBuildRules.md` for compiled module test conventions.

