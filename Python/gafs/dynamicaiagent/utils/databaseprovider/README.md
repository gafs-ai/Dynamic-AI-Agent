# DatabaseProvider

Database provider abstraction with SurrealDB implementations (embedded and remote).
Part of `gafs.dynamicaiagent.utils`.

## Overview

`databaseprovider` provides a unified interface (`IDatabaseProvider`) for executing
database queries with automatic retry and connection-error handling.

Two concrete providers are included:

| Provider | Class | Transport |
|---|---|---|
| SurrealDB embedded | `SurrealDbLocalProvider` | In-process via SurrealDB SDK |
| SurrealDB remote | `SurrealDbRemoteProvider` | WebSocket (`wss://` / `ws://`) |

## Installation

```bash
pip install surrealdb
```

## Quick Start

### Embedded (in-memory) SurrealDB

```python
import logging
from gafs.dynamicaiagent.utils.databaseprovider import (
    SurrealDbLocalProvider,
    LocalSurrealDbOptions,
    LocalSurrealDbStorageType,
)

options = LocalSurrealDbOptions(
    namespace="my-ns",
    database="my-db",
    storage_type=LocalSurrealDbStorageType.MEM,
)

logger = logging.getLogger(__name__)

async with SurrealDbLocalProvider(logger) as provider:
    await provider.initialize(options)
    records = await provider.query("SELECT * FROM user", model=MyModel)
```

### Remote SurrealDB

```python
from gafs.dynamicaiagent.utils.databaseprovider import (
    SurrealDbRemoteProvider,
    RemoteSurrealDbOptions,
)

options = RemoteSurrealDbOptions(
    endpoint="wss://my-instance.surreal.cloud/rpc",
    namespace="my-ns",
    database="my-db",
    username="admin",
    password="secret",
    auth_level="namespace",
)

async with SurrealDbRemoteProvider(logger) as provider:
    await provider.initialize(options)
    raw = await provider.query_raw("SELECT * FROM user WHERE active = true")
```

## Public API

### `IDatabaseProvider`

Abstract base class. All providers implement this interface.

| Method | Signature | Description |
|---|---|---|
| `initialize` | `(options, retry_options?)` → `None` | Connect and authenticate. |
| `query` | `(query, model?, retry_options?)` → `list[T] \| None` | Execute a query and deserialize results into `model`. Returns `None` when `model` is `None`. |
| `query_raw` | `(query, retry_options?)` → `list[dict]` | Execute a query and return raw dicts (last statement result). |
| `close` | `()` → `None` | Disconnect and release resources. |
| `status` | property | Current `DatabaseProviderStatus`. |

All methods are `async`.

### `RetryOptions`

Controls retry behaviour for `initialize`, `query`, and `query_raw`.

| Field | Default | Description |
|---|---|---|
| `timeout` | `60` (s) | Per-attempt timeout. |
| `max_retry` | `2` | Maximum number of retries after initial failure. |
| `retry_interval` | `10` (s) | Base interval; retry `n` waits `n × retry_interval` seconds. |

`RetryOptions` is a value object (immutable after construction, equality by value).

Per-request retry options passed to `query` / `query_raw` override provider-level
options, which in turn override the defaults above.

### `LocalSurrealDbOptions`

| Field | Type | Description |
|---|---|---|
| `namespace` | `str` | SurrealDB namespace. |
| `database` | `str` | SurrealDB database name. |
| `storage_type` | `LocalSurrealDbStorageType` | Storage backend (see below). |
| `path` | `str \| None` | File path for `FILE`, `SURREALKV`, and `ROCKSDB` backends. |
| `retry_options` | `RetryOptions \| None` | Provider-level retry options. |

#### `LocalSurrealDbStorageType`

| Value | Backend |
|---|---|
| `MEM` | In-memory (no persistence) |
| `SURREALKV` | SurrealKV (default persistent backend) |
| `ROCKSDB` | RocksDB |
| `FILE` | Single file |

### `RemoteSurrealDbOptions`

| Field | Type | Description |
|---|---|---|
| `endpoint` | `str` | WebSocket endpoint (`wss://…/rpc`). |
| `namespace` | `str` | SurrealDB namespace. |
| `database` | `str` | SurrealDB database name. |
| `username` | `str` | Credential username. |
| `password` | `str` | Credential password. |
| `auth_level` | `str` | `"root"`, `"namespace"`, or `"database"`. Default: `"database"`. |
| `retry_options` | `RetryOptions \| None` | Provider-level retry options. |

### `DatabaseProviderStatus`

| Value | Meaning |
|---|---|
| `UNINITIALIZED` | Provider created, `initialize()` not yet called. |
| `INITIALIZING` | `initialize()` in progress. |
| `AVAILABLE` | Ready to accept queries. |
| `TEMPORARILY_UNAVAILABLE` | Retrying after a transient error. |
| `ERROR` | Fatal error; provider cannot be used. |
| `TERMINATING` | `close()` in progress. |
| `TERMINATED` | Closed successfully. |

## Exception Hierarchy

```
DatabaseProviderException
├── DatabaseProviderInitializationException
│   ├── DatabaseProviderOptionsException      # invalid options passed to initialize()
│   ├── DatabaseProviderUnconnectableException # could not reach the database server
│   ├── DatabaseProviderAuthenticationException # authentication failed
│   └── EmbeddedDatabaseInitializationException # embedded engine failed to start
└── DatabaseOperationException
    ├── UnpermittedDatabaseOperationException  # operation not allowed for current user
    ├── UnsupportedDatabaseOperationException  # operation not supported by provider
    ├── DatabaseQueryErrorException            # query syntax / semantic error
    ├── DatabaseConnectionException            # connection lost during query
    ├── DatabaseRecordNotFoundException        # expected record does not exist
    └── DatabaseConflictingEntryException      # unique constraint violation
```

All exceptions expose `message: str`, `details: str | None`, and `cause: Exception | None`.

## Build

Compile to a native extension module (requires Nuitka):

```bash
cd Python/
python gafs/dynamicaiagent/utils/databaseprovider/build_nuitka.py
```

Output: `Python/build/win_x64/gafs/dynamicaiagent/utils/databaseprovider.cp312-win_amd64.pyd`

After building, run the build tests to verify the compiled module:

```bash
pytest gafs/dynamicaiagent/utils/databaseprovider/test/test_build_databaseprovider.py -v
pytest gafs/dynamicaiagent/utils/databaseprovider/test/test_build_remote_provider.py -v
```

## Testing

See [test/README.md](test/README.md) for full test documentation and configuration details.
