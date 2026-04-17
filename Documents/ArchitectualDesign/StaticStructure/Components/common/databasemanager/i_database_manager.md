---
class: IDatabaseManager
kind: abstract_class
module: gafs.dynamicaiagent.common.databasemanager
inherits: [ABC]
dependencies:
  - DatabaseConnection
  - IDatabaseProvider
  - ISecretManager
  - FullTextAnalyzer
exceptions_used:
  - DatabaseManagerInitializationException
  - DatabaseManagerNotInitializedException
  - DatabaseManagerInvalidDatabaseConnectionEntryException
  - DatabaseManagerConflictingConnectionException
  - DatabaseManagerConnectionNotFoundException
  - DatabaseManagerSecretNotFoundException
  - DatabaseManagerOperationException
  - DatabaseManagerInvalidOperationException
  - DatabaseManagerConflictingAnalyzerException
  - DatabaseManagerInvalidAnalyzerException
  - DatabaseManagerAnalyzerNotFoundException
  - DatabaseManagerAnalyzerOperationException
---

## responsibilities

- Provider registry: create, cache, and dispose `IDatabaseProvider` instances
- Connection catalogue: persist and manage `DatabaseConnection` entries in the `DatabaseConnections` collection
- Analyzer catalogue: persist and manage `FullTextAnalyzer` entries in the `FullTextAnalyzers` collection

## initialization_sequence

| step | actor | method | phase |
|------|-------|--------|-------|
| 1 | DatabaseManager | `initialize_default_connection(config)` | 1 |
| 2 | SecretManager | `initialize(database_manager, ...)` | 2 |
| 3 | DatabaseManager | `initialize(secret_manager)` | 3 |

## constants

| name | type | value | description |
|------|------|-------|-------------|
| `DEFAULT_DATABASE_NAME()` | `str` | `"default"` | Key and record id used for the default database entry in `DatabaseConnections` |

## methods

---

### initialize_default_connection

```python
async def initialize_default_connection(config: DatabaseConnection) -> bool
```

| property | value |
|----------|-------|
| group | initialization |
| phase | 1 |
| description | Connect to the default database and ensure indexes on the `DatabaseConnections` collection. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `config` | `DatabaseConnection` | yes | Configuration for the default database connection |

#### returns

| type   | value  | description                            |
| ------ | ------ | -------------------------------------- |
| `bool` | `True` | Successfully connected and initialized |

#### raises

| exception                                | condition                                     |
| ---------------------------------------- | --------------------------------------------- |
| `DatabaseManagerInitializationException` | Connection establishment or index setup fails |

---

### initialize

```python
async def initialize(secret_manager: ISecretManager) -> bool
```

| property    | value                                                                                                                                      |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| group       | initialization                                                                                                                             |
| phase       | 3                                                                                                                                          |
| description | Register `ISecretManager` and complete full component setup. Must be called after Phase-1 and after `ISecretManager` is fully initialized. |

#### parameters

| name             | type             | required | description                                |
| ---------------- | ---------------- | -------- | ------------------------------------------ |
| `secret_manager` | `ISecretManager` | yes      | Already-initialized SecretManager instance |

#### returns

| type   | value  | description              |
| ------ | ------ | ------------------------ |
| `bool` | `True` | Successfully initialized |

#### raises

| exception                                | condition                    |
| ---------------------------------------- | ---------------------------- |
| `DatabaseManagerInitializationException` | Initialization process fails |

---

### create_connection

```python
async def create_connection(connection_configurations: DatabaseConnection) -> DatabaseConnection
```

| property       | value                                                                            |
| -------------- | -------------------------------------------------------------------------------- |
| group          | connection_catalogue                                                             |
| requires_phase | 3                                                                                |
| description    | Create a new `DatabaseConnection` entry in the `DatabaseConnections` collection. |

#### parameters

| name                        | type                 | required | description                                                                  |
| --------------------------- | -------------------- | -------- | ---------------------------------------------------------------------------- |
| `connection_configurations` | `DatabaseConnection` | yes      | Connection data to store. Set either `secret` or `raw_secret`, but not both. |

#### returns

| type                 | description                                                        |
| -------------------- | ------------------------------------------------------------------ |
| `DatabaseConnection` | Persisted entry. `raw_secret` is excluded from the returned value. |

#### raises

| exception                                                | condition                                                      |
| -------------------------------------------------------- | -------------------------------------------------------------- |
| `DatabaseManagerNotInitializedException`                 | DatabaseManager is not fully initialized                       |
| `DatabaseManagerInvalidDatabaseConnectionEntryException` | Entry is invalid (e.g. both `secret` and `raw_secret` are set) |
| `DatabaseManagerConflictingConnectionException`          | Specified `id` conflicts with an existing entry                |
| `DatabaseManagerSecretNotFoundException`                 | `secret` id does not reference an existing secret              |
| `DatabaseManagerOperationException`                      | Database query or connection failure                           |

---

### update_connection

```python
async def update_connection(database_connection: DatabaseConnection) -> DatabaseConnection
```

| property | value |
|----------|-------|
| group | connection_catalogue |
| requires_phase | 3 |
| description | Merge-update an existing `DatabaseConnection` entry. Only non-`None` fields are written. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `database_connection` | `DatabaseConnection` | yes | Updated connection data. `id` is required. `raw_secret` must not be set. |

#### returns

| type                 | description                               |
| -------------------- | ----------------------------------------- |
| `DatabaseConnection` | Updated entry as returned by the database |

#### raises

| exception                                                | condition                                                     |
| -------------------------------------------------------- | ------------------------------------------------------------- |
| `DatabaseManagerNotInitializedException`                 | DatabaseManager is not fully initialized                      |
| `DatabaseManagerInvalidDatabaseConnectionEntryException` | Entry is invalid (e.g. `raw_secret` is set, or `id` is empty) |
| `DatabaseManagerInvalidOperationException`               | Target is the `default` connection                            |
| `DatabaseManagerConnectionNotFoundException`             | No record exists for the given `id`                           |
| `DatabaseManagerSecretNotFoundException`                 | `secret` id does not reference an existing secret             |
| `DatabaseManagerOperationException`                      | Database query or connection failure                          |

#### rules

1. Updates to the `default` connection (by `id` or `name`) are rejected.
2. If a provider for the same `id` is already cached, it is closed and replaced with a newly created provider using the updated configuration.
3. If the provider is not in use (not cached), only the `DatabaseConnection` entry is updated.
4. Even if re-establishing the connection fails after update, the entry is still updated.
5. If the provider close operation fails during replacement, log at WARNING level and do not raise an exception.

---

### get_connection

```python
async def get_connection(id: str) -> DatabaseConnection | None
```

| property | value |
|----------|-------|
| group | connection_catalogue |
| requires_phase | 3 |
| description | Retrieve a `DatabaseConnection` entry by record id. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `id` | `str` | yes | Record id to look up |

#### returns

| type | condition | description |
|------|-----------|-------------|
| `DatabaseConnection` | found | Matching entry |
| `None` | not found | No matching record |

#### raises

| exception                                | condition                                |
| ---------------------------------------- | ---------------------------------------- |
| `DatabaseManagerNotInitializedException` | DatabaseManager is not fully initialized |
| `DatabaseManagerOperationException`      | Database query failure                   |

#### rules

1. This method simply returns the `DatabaseConnection` entry if exists, but does not create `IDatabaseProvider` instance from the entry.

---

### get_all_connections

```python
async def get_all_connections() -> list[DatabaseConnection]
```

| property       | value                                      |
| -------------- | ------------------------------------------ |
| group          | connection_catalogue                       |
| requires_phase | 3                                          |
| description    | Retrieve all `DatabaseConnection` entries. |

#### returns

| type                       | description                |
| -------------------------- | -------------------------- |
| `list[DatabaseConnection]` | All entries (can be empty) |

#### raises

| exception                                | condition                                |
| ---------------------------------------- | ---------------------------------------- |
| `DatabaseManagerNotInitializedException` | DatabaseManager is not fully initialized |
| `DatabaseManagerOperationException`      | Database query failure                   |

#### note

- Since the number of `DatabaseConnection` entries is expected to be limited, performance impact is not a concern at this stage. Paging can be added in a future release.

---

### get_connections_by_name

```python
async def get_connections_by_name(name: str, ambiguous: bool = False) -> list[DatabaseConnection]
```

| property       | value                                            |
| -------------- | ------------------------------------------------ |
| group          | connection_catalogue                             |
| requires_phase | 3                                                |
| description    | Retrieve `DatabaseConnection` entries by name. |

#### parameters

| name        | type   | required | description                                                                                                                                   |
| ----------- | ------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`      | `str`  | yes      | Connection name to search for                                                                                                                 |
| `ambiguous` | `bool` | no       | If `True`, search for entries that contain the given string. If `False`, search for an entry whose name exactly matches the given string. |

#### returns

| type                       | description                     |
| -------------------------- | ------------------------------- |
| `list[DatabaseConnection]` | Matching entries (can be empty) |


#### raises

| exception                                | condition                                |
| ---------------------------------------- | ---------------------------------------- |
| `DatabaseManagerNotInitializedException` | DatabaseManager is not fully initialized |
| `DatabaseManagerOperationException`      | Database query failure                   |

#### rules

- If `ambiguous = True`, search for entries whose name contains the given string.
- If `ambiguous = False`, search for entries whose name exactly matches the given string.
- Return an empty list if no entry is found.

---

### delete_connection

```python
async def delete_connection(id: str) -> None
```

| property | value |
|----------|-------|
| group | connection_catalogue |
| requires_phase | 3 |
| description | Delete a `DatabaseConnection` entry and close any cached provider for the same id. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `id` | `str` | yes | Record id of the connection to delete |

#### raises

| exception                                    | condition                                |
| -------------------------------------------- | ---------------------------------------- |
| `DatabaseManagerNotInitializedException`     | DatabaseManager is not fully initialized |
| `DatabaseManagerInvalidOperationException`   | `id` is `"default"`                      |
| `DatabaseManagerConnectionNotFoundException` | No record exists for the given `id`      |
| `DatabaseManagerOperationException`          | Database query failure                   |

#### rules

1. Deletion of the `default` connection is rejected.
2. If a provider for the specified `id` is cached, it is closed and removed before the record is deleted.
3. If the provider close operation fails, log at WARNING level and do not raise an exception.

---

### create_analyzer

```python
async def create_analyzer(analyzer: FullTextAnalyzer) -> FullTextAnalyzer
```

| property | value |
|----------|-------|
| group | full_text_analyzer |
| requires_phase | 1 |
| description | Create a new `FullTextAnalyzer` entry and define the analyzer on the default database. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `analyzer` | `FullTextAnalyzer` | yes | Analyzer definition to create |

#### returns

| type | description |
|------|-------------|
| `FullTextAnalyzer` | Created entry |

#### raises

| exception | condition |
|-----------|-----------|
| `DatabaseManagerNotInitializedException` | DatabaseManager is not fully initialized |
| `DatabaseManagerConflictingAnalyzerException` | `name` or `id` conflicts with an existing entry |
| `DatabaseManagerInvalidAnalyzerException` | Validation failure |
| `DatabaseManagerAnalyzerOperationException` | Creation or definition query fails |

#### rules

1. The `FullTextAnalyzer` collection entry and the actual database analyzer must remain consistent.

---

### update_analyzer

```python
async def update_analyzer(analyzer: FullTextAnalyzer) -> FullTextAnalyzer
```

| property | value |
|----------|-------|
| group | full_text_analyzer |
| requires_phase | 1 |
| description | Update an existing `FullTextAnalyzer` entry and alter the analyzer on the default database. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `analyzer` | `FullTextAnalyzer` | yes | Updated analyzer definition. `id` is required. |

#### returns

| type | description |
|------|-------------|
| `FullTextAnalyzer` | Updated entry |

#### raises

| exception | condition |
|-----------|-----------|
| `DatabaseManagerNotInitializedException` | DatabaseManager is not fully initialized |
| `DatabaseManagerAnalyzerNotFoundException` | Update target does not exist |
| `DatabaseManagerInvalidAnalyzerException` | Validation failure or `id` is empty |
| `DatabaseManagerAnalyzerOperationException` | Query failure |

#### rules

1. Use `ALTER ANALYZER` query to update the actual analyzer (do not use `DEFINE ANALYZER OVERWRITE`).
2. The `FullTextAnalyzer` collection entry and the actual database analyzer must remain consistent.
3. If the alteration affects analyzer functionality (tokenizers or filters changed), rebuild all indexes that reference the updated analyzer.
4. Editing only `comment` or `name` does not affect analyzer functionality and does not require an index rebuild.

---

### get_analyzer

```python
async def get_analyzer(id: str) -> FullTextAnalyzer | None
```

| property | value |
|----------|-------|
| group | full_text_analyzer |
| requires_phase | 1 |
| description | Retrieve a `FullTextAnalyzer` entry by record id. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `id` | `str` | yes | Record id to look up |

#### returns

| type | condition | description |
|------|-----------|-------------|
| `FullTextAnalyzer` | found | Matching entry |
| `None` | not found | No matching record |

#### raises

| exception | condition |
|-----------|-----------|
| `DatabaseManagerNotInitializedException` | DatabaseManager is not fully initialized |
| `DatabaseManagerAnalyzerOperationException` | Query failure |

---

### get_all_analyzers


```python
async def get_all_analyzers() -> list[FullTextAnalyzer]
```

| property       | value                                    |
| -------------- | ---------------------------------------- |
| group          | full_text_analyzer                       |
| requires_phase | 1                                        |
| description    | Retrieve all `FullTextAnalyzer` entries. |

#### returns

| type                     | description                    |
| ------------------------ | ------------------------------ |
| `list[FullTextAnalyzer]` | All `FullTextAnalyzer` entries |

#### raises

| exception                                   | condition                                |
| ------------------------------------------- | ---------------------------------------- |
| `DatabaseManagerNotInitializedException`    | DatabaseManager is not fully initialized |
| `DatabaseManagerAnalyzerOperationException` | Query failure                            |

#### note

- Since the number of `FullTextAnalyzer` entries is expected to be limited, performance impact is not a concern at this stage. Paging can be added in a future release.

---

### get_analyzers_by_name

```python
async def get_analyzers_by_name(name: str, ambiguous: bool = False) -> list[FullTextAnalyzer]
```

| property       | value                                        |
| -------------- | -------------------------------------------- |
| group          | full_text_analyzer                           |
| requires_phase | 1                                            |
| description    | Retrieve `FullTextAnalyzer` entries by name. |

#### parameters

| name        | type   | required | description                                                                                                                                |
| ----------- | ------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `name`      | `str`  | yes      | Analyzer name to search for                                                                                                                |
| `ambiguous` | `bool` | no       | If `True`, search for entries that contain the given string. If `False`, search for an entry whose name exactly matches the given string. |

#### returns

| type                     | description      |
| ------------------------ | ---------------- |
| `list[FullTextAnalyzer]` | Matching entries |


#### raises

| exception | condition |
|-----------|-----------|
| `DatabaseManagerNotInitializedException` | DatabaseManager is not fully initialized |
| `DatabaseManagerAnalyzerOperationException` | Query failure |

#### rules

- If `ambiguous = True`, search for entries whose name contains the given string.
- If `ambiguous = False`, search for entries whose name exactly matches the given string.
- Return an empty list if no entry is found.

---

### delete_analyzer

```python
async def delete_analyzer(id: str) -> None
```

| property | value |
|----------|-------|
| group | full_text_analyzer |
| requires_phase | 1 |
| description | Delete a `FullTextAnalyzer` entry and remove the analyzer from the default database. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `id` | `str` | yes | Record id of the analyzer to delete |

#### raises

| exception | condition |
|-----------|-----------|
| `DatabaseManagerNotInitializedException` | DatabaseManager is not fully initialized |
| `DatabaseManagerAnalyzerNotFoundException` | Target does not exist |
| `DatabaseManagerAnalyzerOperationException` | Query failure |

#### rules

1. The `FullTextAnalyzer` collection entry and the actual database analyzer must remain consistent.

---

### get_provider

```python
async def get_provider(id: str) -> IDatabaseProvider
```

| property | value |
|----------|-------|
| group | provider_getters |
| requires_phase | 1 (phase 3 for non-default providers) |
| description | Return the `IDatabaseProvider` for a connection id. If already cached, return immediately. |

#### parameters

| name | type  | required | description                           |
| ---- | ----- | -------- | ------------------------------------- |
| `id` | `str` | yes      | Record id of the `DatabaseConnection` |

#### returns

| type | description |
|------|-------------|
| `IDatabaseProvider` | Corresponding provider instance |

#### raises

| exception                                    | condition                                         |
| -------------------------------------------- | ------------------------------------------------- |
| `DatabaseManagerNotInitializedException`     | Phase-3 not completed (for non-default providers) |
| `DatabaseManagerConnectionNotFoundException` | No connection record for the given `id`           |
| `DatabaseManagerSecretNotFoundException`     | Required secret does not exist                    |
| `DatabaseManagerOperationException`          | Query failure                                     |

#### rules

1. Active providers are cached in the `DatabaseManager` instance.
2. If the requested provider is already cached, return it immediately without any database access.
3. If `id` is `"default"`, delegate to `get_default_provider()`.
4. For uncached non-default providers, create on demand using the following steps:
   1. Load `DatabaseConnection` from the `DatabaseConnections` collection.
   2. If `secret` is set, retrieve it via `ISecretManager`.
   3. Merge `parameters` with the secret dict (secret values take precedence on conflict).
   4. Construct a `DatabaseProviderOptions` subclass from the merged dict using `database_type`.
   5. Initialize new `IDatabaseProvider`, cache it, and return it.

---

### get_default_provider

```python
def get_default_provider() -> IDatabaseProvider
```

| property | value |
|----------|-------|
| group | provider_getters |
| async | false |
| requires_phase | 1 |
| description | Return the default `IDatabaseProvider` synchronously. |

#### returns

| type | description |
|------|-------------|
| `IDatabaseProvider` | Default provider instance |

#### raises

| exception | condition |
|-----------|-----------|
| `DatabaseManagerNotInitializedException` | Default provider is not registered (Phase-1 not completed) |
