# databasemanager

`gafs.dynamicaiagent.common.databasemanager` — Database management component.

Provides a unified interface for managing SurrealDB connections and full-text
analyzer definitions. Acts as a registry for `IDatabaseProvider` instances and a
catalogue for persisted `DatabaseConnection` and `FullTextAnalyzer` entries.

---

## Overview

`DatabaseManager` is responsible for:

- **Provider registry** — creating, caching, and disposing `IDatabaseProvider` instances.
- **Connection catalogue** — persisting and managing `DatabaseConnection` entries in the `DatabaseConnections` collection.
- **Analyzer catalogue** — persisting and managing `FullTextAnalyzer` entries in the `FullTextAnalyzers` collection.

---

## Initialization Sequence

`DatabaseManager` and `SecretManager` have a mutual dependency. Initialization must
follow this three-phase sequence:

```python
import logging
from gafs.dynamicaiagent.common.databasemanager import DatabaseManager, DatabaseConnection
from gafs.dynamicaiagent.utils.databaseprovider import DatabaseProviderType

# Phase 1 — database-only initialization (no SecretManager needed)
config = DatabaseConnection()
config.id = "default"
config.name = "default"
config.database_type = DatabaseProviderType.SURREALDB_LOCAL
config.parameters = {"namespace": "my-ns", "database": "my-db", "storage_type": "mem"}

logger = logging.getLogger(__name__)
db_manager = DatabaseManager(logger)
await db_manager.initialize_default_connection(config)

# Phase 2 — SecretManager initialization (uses DatabaseManager)
await secret_manager.initialize(db_manager, ...)

# Phase 3 — complete DatabaseManager setup (injects SecretManager)
await db_manager.initialize(secret_manager)
```

After phase 1, methods in the `full_text_analyzer` group are available.
After phase 3, all methods are available (including `connection_catalogue` and
`provider_registry` groups).

---

## Model Classes

### `DatabaseConnection`

Represents a database connection configuration stored in the `DatabaseConnections`
SurrealDB collection.

| Field | Type | Description |
|---|---|---|
| `id` | `str \| None` | Record id in the `DatabaseConnections` collection |
| `name` | `str \| None` | Human-readable connection name |
| `description` | `str \| None` | Optional description |
| `database_type` | `DatabaseProviderType \| None` | Provider type (`SURREALDB_LOCAL` or `SURREALDB_REMOTE`) |
| `secret` | `str \| None` | Id of the `Secret` entry that holds credentials |
| `raw_secret` | `dict \| None` | Raw credentials dict (never persisted; excluded from `to_dict()`) |
| `parameters` | `dict \| None` | Provider-specific options (namespace, database, endpoint, etc.) |

```python
conn = DatabaseConnection()
conn.name = "analytics"
conn.database_type = DatabaseProviderType.SURREALDB_REMOTE
conn.secret = "analytics_secret_id"
conn.parameters = {
    "endpoint": "wss://my-cluster.surrealdb.cloud/rpc",
    "namespace": "analytics",
    "database": "prod",
}
```

**Notes:**
- `id` and `secret` are automatically stripped of their SurrealDB table prefix
  (e.g. `"DatabaseConnections:abc"` → `"abc"`).
- `raw_secret` is never included in `to_dict()` or `to_json()`.
- Setting both `secret` and `raw_secret` is invalid.

### `FullTextAnalyzer`

Represents a SurrealDB full-text search analyzer definition stored in the
`FullTextAnalyzers` collection.

| Field | Type | Description |
|---|---|---|
| `id` | `str \| None` | Record id (also used as the SurrealDB analyzer name) |
| `name` | `str \| None` | SurrealDB analyzer name (must be alphanumeric + underscores) |
| `tokenizers` | `list[TokenizerDefinition] \| None` | Tokenizer pipeline |
| `filters` | `list[FilterDefinition] \| None` | Filter pipeline |
| `function` | `list[FunctionDefinition] \| None` | Custom SurrealDB functions |
| `comment` | `str \| None` | Optional description |

Two default analyzers are provided as factory methods:

```python
# ngram(3,5) analyzer — good for partial/fuzzy search
ngram = FullTextAnalyzer.DEFAULT_ANALYZER()

# Snowball English stemmer — good for natural language search
english = FullTextAnalyzer.DEFAULT_ENGLISH_ANALYZER()
```

Both are automatically defined during phase-1 initialization.

### `SurrealTokenizer`

Enum of supported SurrealDB tokenizer types:

| Value | SurrealQL |
|---|---|
| `BLANK` | `blank` |
| `CAMEL` | `camel` |
| `CLASS` | `class` |
| `PUNCT` | `punct` |

### `SurrealFilter`

Enum of supported SurrealDB filter types:

| Value | SurrealQL | Parameters |
|---|---|---|
| `ASCII` | `ascii` | — |
| `LOWERCASE` | `lowercase` | — |
| `UPPERCASE` | `uppercase` | — |
| `EDGENGRAM` | `edgengram(min,max)` | `min`, `max` |
| `NGRAM` | `ngram(min,max)` | `min`, `max` |
| `SNOWBALL` | `snowball(lang)` | `language` |

---

## Public API

### `IDatabaseManager`

Abstract base class defining the full interface.

#### Initialization

| Method | Phase | Description |
|---|---|---|
| `initialize_default_connection(config)` | 1 | Connect to default DB, define default analyzers, ensure indexes |
| `initialize(secret_manager)` | 3 | Register `ISecretManager`; enables connection catalogue methods |

#### Connection Catalogue (`requires_phase=3`)

| Method | Returns | Description |
|---|---|---|
| `create_connection(config)` | `DatabaseConnection` | Persist a new connection entry |
| `update_connection(connection)` | `DatabaseConnection` | Merge-update an existing entry; replaces cached provider if active |
| `get_connection(id)` | `DatabaseConnection \| None` | Retrieve entry by id |
| `get_all_connections()` | `list[DatabaseConnection]` | All entries |
| `get_connections_by_name(name, ambiguous)` | `list[DatabaseConnection]` | Entries matching name |
| `delete_connection(id)` | `None` | Delete entry and close cached provider |

**Rules:**
- The `default` connection cannot be updated or deleted.
- Both `secret` and `raw_secret` must not be set simultaneously.
- If a provider is cached for the updated/deleted connection, it is closed.
- Provider close failures are logged at WARNING level and do not raise.

#### Analyzer Catalogue (`requires_phase=1`)

| Method | Returns | Description |
|---|---|---|
| `create_analyzer(analyzer)` | `FullTextAnalyzer` | Define analyzer on DB and persist entry |
| `update_analyzer(analyzer)` | `FullTextAnalyzer` | Redefine analyzer on DB and update entry; rebuilds referencing indexes if tokenizers/filters changed |
| `get_analyzer(id)` | `FullTextAnalyzer \| None` | Retrieve entry by id |
| `get_all_analyzers()` | `list[FullTextAnalyzer]` | All entries |
| `get_analyzers_by_name(name, ambiguous)` | `list[FullTextAnalyzer]` | Entries matching name |
| `delete_analyzer(id)` | `None` | Remove analyzer from DB and delete entry |

**Notes:**
- `update_analyzer` uses `DEFINE ANALYZER OVERWRITE` (not `ALTER ANALYZER`, which is
  unsupported in surrealdb Python client v1.0.x embedded engine).
- Rebuilding indexes is triggered automatically when tokenizers or filters change.

#### Provider Registry

| Method | Returns | Description |
|---|---|---|
| `get_provider(id)` | `IDatabaseProvider` | Returns cached or creates a new provider for the given connection id |
| `get_default_provider()` | `IDatabaseProvider` | Returns the default provider (synchronous; raises if not initialized) |

---

## Exceptions

All exceptions inherit from `DatabaseManagerException` → `ApplicationException`.

| Exception | Trigger |
|---|---|
| `DatabaseManagerInitializationException` | Phase-1 or phase-3 initialization failure |
| `DatabaseManagerNotInitializedException` | Method called before required phase completes |
| `DatabaseManagerInvalidDatabaseConnectionEntryException` | Invalid `DatabaseConnection` (e.g. both `secret` and `raw_secret` set) |
| `DatabaseManagerConflictingConnectionException` | Duplicate `id` on create |
| `DatabaseManagerConnectionNotFoundException` | `id` not found for update/delete/get |
| `DatabaseManagerSecretNotFoundException` | Referenced `secret` id does not exist |
| `DatabaseManagerOperationException` | Generic database query/connection failure |
| `DatabaseManagerInvalidOperationException` | Operation rejected (e.g. modifying the default connection) |
| `DatabaseManagerConflictingAnalyzerException` | Duplicate `name` or `id` on create analyzer |
| `DatabaseManagerInvalidAnalyzerException` | Validation failure (invalid name, filter params, etc.) |
| `DatabaseManagerAnalyzerNotFoundException` | Analyzer id not found for update/delete/get |
| `DatabaseManagerAnalyzerOperationException` | Analyzer definition/removal query fails |

---

## Build

Compile to a Nuitka extension module (`.pyd` on Windows, `.so` on Linux):

```bash
# From the Python/ directory
python gafs/dynamicaiagent/common/databasemanager/build_nuitka.py
```

Output is placed at `build/<arch>/gafs/dynamicaiagent/common/databasemanager.<ext>`.

---

## Testing

```bash
# From the Python/ directory

# Source tests
python -m pytest gafs/dynamicaiagent/common/databasemanager/test/test_database_manager.py -v

# Compiled module tests (requires build step first)
python -m pytest gafs/dynamicaiagent/common/databasemanager/test/test_build_database_manager.py -v
```

Tests use an in-memory embedded SurrealDB instance (`storage_type: mem`) — no
external database is required for the local test suite.

One test (`test_initialize_remote_success`) is skipped unless a `remote_db_config.json`
file is present in the test directory with valid remote connection credentials.

---

## Package Structure

```
databasemanager/
├── __init__.py                    # Public exports
├── i_database_manager.py          # Abstract base class
├── database_manager.py            # Concrete implementation
├── build_nuitka.py                # Nuitka build script
├── README.md                      # This file
├── models/
│   ├── __init__.py
│   ├── database_connection.py     # DatabaseConnection data class
│   ├── full_text_analyzer.py      # FullTextAnalyzer + sub-definitions
│   ├── surreal_filter.py          # SurrealFilter enum
│   └── surreal_tokenizer.py       # SurrealTokenizer enum
├── exceptions/
│   ├── __init__.py
│   ├── database_manager_exception.py
│   ├── database_manager_initialization_exception.py
│   ├── database_manager_not_initialized_exception.py
│   ├── database_manager_invalid_database_connection_entry_exception.py
│   ├── database_manager_conflicting_connection_exception.py
│   ├── database_manager_connection_not_found_exception.py
│   ├── database_manager_secret_not_found_exception.py
│   ├── database_manager_operation_exception.py
│   ├── database_manager_invalid_operation_exception.py
│   ├── database_manager_conflicting_analyzer_exception.py
│   ├── database_manager_invalid_analyzer_exception.py
│   ├── database_manager_analyzer_not_found_exception.py
│   └── database_manager_analyzer_operation_exception.py
└── test/
    ├── test_database_manager.py   # Main test suite (78 tests)
    └── test_build_database_manager.py  # Nuitka build test
```
