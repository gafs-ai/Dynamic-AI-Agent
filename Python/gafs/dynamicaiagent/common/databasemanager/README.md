## Overview

`databasemanager` is the **database manager** component used within Dynamic AI Agent.  
It provides the `IDatabaseManager` interface and its implementation `DatabaseManager`,  
which centrally manages multiple `IDatabaseProvider` implementations (for example, `SurrealDbRemoteProvider`).

### Structure

- `__init__.py`
  - Exposes the public API of the `databasemanager` component.
  - Re-exports `IDatabaseManager` / `DatabaseManager`.
- `i_database_manager.py`
  - Defines the `IDatabaseManager` interface.
    - `DEFAULT_DATABASE_NAME() -> str`
      - Returns the default database name (`"default"`).
    - `async add_provider(options: DatabaseProviderOptions, overwrite: bool = False) -> bool`
    - `get_provider(database_name: str) -> IDatabaseProvider | None`
    - `get_default_database_provider() -> IDatabaseProvider | None`
    - `async remove_provider(database_name: str) -> bool`
- `database_manager.py`
  - Provides the `DatabaseManager` implementation of `IDatabaseManager`.
  - Internally keeps a `dict[str, IDatabaseProvider]` and uses `database_name` as the key
    to register, fetch, and remove `IDatabaseProvider` instances.
  - Keeps the provider corresponding to the default database name
    (`IDatabaseManager.DEFAULT_DATABASE_NAME()`) as the **default provider**.
- `test/`
  - Provides `pytest`‑based unit tests (see `test/README.md` for details).
  - Does not connect to a real database; it uses `IDatabaseProvider` test doubles
    to verify the behavior of `DatabaseManager`.

## Public API (intended external use)

### Interfaces

- `IDatabaseManager`
  - **Role**: Interface for managing multiple `IDatabaseProvider` instances.
  - Main methods:
    - `DEFAULT_DATABASE_NAME() -> str`
      - Returns the default database name (`"default"`).
    - `async add_provider(options: DatabaseProviderOptions, overwrite: bool = False) -> bool`
      - Creates and initializes a provider based on `DatabaseProviderOptions`
        (or a subclass), and registers it under the specified `database_name`.
      - If a provider with the same name already exists, whether it is overwritten
        or not is controlled by the `overwrite` flag.
    - `get_provider(database_name: str) -> IDatabaseProvider | None`
      - Returns the provider corresponding to the specified `database_name`
        (or `None` if it does not exist).
    - `get_default_database_provider() -> IDatabaseProvider | None`
      - Returns the provider corresponding to the default database name
        (or `None` if it does not exist).
    - `async remove_provider(database_name: str) -> bool`
      - Closes the provider for the given `database_name` and removes it from the registry.

### Implementation

- `DatabaseManager`
  - **Role**: Implementation of `IDatabaseManager` that creates and keeps
    `IDatabaseProvider` instances according to `DatabaseType`.
  - At the moment, when `DatabaseType.SURREALDB_REMOTE` is specified,
    it creates `SurrealDbRemoteProvider` and initializes it with `RemoteSurrealDbOptions`.
  - Main behaviors:
    - `add_provider`
      - Handles new registration, overwrite, and unsupported types
        (raises `DatabaseProviderOptionsException` for unsupported options).
    - `get_provider`
      - Returns the corresponding provider from the internal dictionary.
    - `get_default_database_provider`
      - Returns the provider bound to the default database name.
    - `remove_provider`
      - Calls `close()` on the provider and then removes it from the registry.
      - If the removed provider is the default provider, it also clears
        the default reference.

## Dependencies & Libraries

- **gafs.dynamicaiagent.utils.databaseprovider**
  - `IDatabaseProvider`
  - `DatabaseProviderOptions`
  - `DatabaseType`
  - `SurrealDbRemoteProvider`
  - `RemoteSurrealDbOptions`
  - Exception types such as `DatabaseProviderOptionsException`
- **Python standard library**
  - `logging`
  - `typing`
  - `abc`

`databasemanager` itself does not contain any database connection logic.  
It is intentionally designed as a **thin layer that manages the lifecycle and routing of providers**.

## Testing

- Full test (source version):

  ```bash
  cd Python
  pytest gafs/dynamicaiagent/common/databasemanager/test/test_database_manager.py -v
  ```

  - Uses `IDatabaseProvider` test doubles (dummy providers) to verify the behavior of
    `add_provider`, `get_provider`, `get_default_database_provider`, and `remove_provider`.

- Tests for the module built with Nuitka:

  ```bash
  cd Python
  python gafs/dynamicaiagent/common/databasemanager/build_nuitka.py
  pytest gafs/dynamicaiagent/common/databasemanager/test/test_build_database_manager.py -v
  ```

  - Prioritizes loading the compiled module placed under
    `build/<arch>/gafs/dynamicaiagent/common/` and reuses the existing test cases
    to validate its behavior.
  - For details such as how `gafs.dynamicaiagent.common.__path__` is adjusted,
    see `Documents/CodingRules/NuitkaBuildRules.md`.
