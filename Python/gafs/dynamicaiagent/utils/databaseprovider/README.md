## Overview

This package provides the database provider abstraction and concrete implementations used by the Dynamic AI Agent.  
It defines the common provider interface, error model, and the SurrealDB remote provider implementation.

### Structure

- `__init__.py`
  - Exposes the public API of the `databaseprovider` component.
  - Re-exports the main interfaces, implementations, and exception classes.
- `i_database_provider.py`
  - Defines the `IDatabaseProvider` interface and shared enums / option types:
    - `IDatabaseProvider`
    - `DatabaseProviderStatus`
    - `DatabaseProviderOptions`
    - `DatabaseType`
- `surrealdb_remote_provider.py`
  - Implements the `IDatabaseProvider` interface for SurrealDB Cloud / remote instances:
    - `SurrealDbRemoteProvider`
    - `RemoteSurrealDbOptions`
- `exceptions/`
  - `database_provider_exception.py`
    - `DatabaseProviderException` – base exception for this component.
  - `database_provider_initialization_exception.py`
    - `DatabaseProviderInitializationException`
    - `DatabaseProviderOptionsException`
    - `DatabaseProviderUnconnectableException`
    - `DatabaseProviderAuthenticationException`
  - `database_operation_exception.py`
    - `DatabaseOperationException`
    - `UnpermittedDatabaseOperationException`
    - `UnsupportedDatabaseOperationException`
    - `MalformedDatabaseQueryException`
    - `DatabaseQueryErrorException`
    - `DatabaseQueryTimeoutException`
    - `DatabaseDisconnectedException`
    - `DatabaseConnectionLimitExceededException`
    - `DatabaseRecordNotFoundException`
    - `DatabaseRecordAlreadyExistsException`
    - `DatabaseConstraintViolationException`
    - `DatabaseTransactionException`
    - `DatabaseDeadlockException`
  - `embedded_database_exception.py`
    - `EmbeddedDatabaseException` – placeholder for embedded database support.
- `test/`
  - Pytest-based tests for `SurrealDbRemoteProvider` (see `test/README.md`):
    - Options serialization and validation, initialization and connection, query and query_raw, close and reconnect.
    - Failure cases for unreachable endpoints and invalid credentials.
- `requirements.txt`
  - Lists the Python dependencies required by this component.

## Public API (intended external use)

- **Interfaces and enums**
  - `IDatabaseProvider`
  - `DatabaseProviderStatus`
  - `DatabaseProviderOptions`
  - `DatabaseType`

- **SurrealDB provider**
  - `SurrealDbRemoteProvider`
    - `async initialize(options: RemoteSurrealDbOptions) -> bool`
    - `async query(query: str, model: type[T] | None = None, many: bool = False) -> T | list[T] | None`
      - Executes the given SurrealQL query and, when `model` is provided, parses the result using the model’s `from_dict` class method (per Data Class Coding Rules).
    - `async query_raw(query: str) -> Any`
      - Executes the query and returns the raw result from the driver without parsing.
    - `async close() -> None`
  - `RemoteSurrealDbOptions`
    - Options class for remote SurrealDB connection (custom serialization per Data Class Coding Rules).

- **Exceptions** (re-exported from package root; more subclasses in `.exceptions`)
  - `DatabaseProviderException`
  - `DatabaseProviderInitializationException`
  - `DatabaseProviderUnconnectableException`
  - `DatabaseProviderAuthenticationException`
  - `DatabaseOperationException`
  - `DatabaseDisconnectedException`
  - `DatabaseQueryErrorException`
  - `EmbeddedDatabaseException`

All symbols above are re-exported from `gafs.dynamicaiagent.utils.databaseprovider` via `__init__.py`.

## Dependencies & Libraries

- **surrealdb (Python SDK)**
  - **Purpose**: Asynchronous client to connect to SurrealDB instances and execute SurrealQL queries.
  - **Website**: <https://surrealdb.com/docs/sdk/python>
  - **License**: Business Source License 1.1 (BSL-1.1)
  - **License URL**: <https://github.com/surrealdb/surrealdb.py/blob/main/LICENSE>

- **Python standard library**
  - `asyncio`, `logging`, `enum`, `typing`, `json`
  - Used for asynchronous I/O, logging, type hints, and serialization (options and models use custom `from_dict` / `to_dict` per Data Class Coding Rules).

## Nuitka build (extension module / DLL)

- **Build**:
  - `cd Python && python gafs/dynamicaiagent/utils/databaseprovider/build_nuitka.py`
- **Test compiled output (reuses existing tests)**:
  - `cd Python && pytest gafs/dynamicaiagent/utils/databaseprovider/test/test_build_surrealdb_remote_provider.py -v`
