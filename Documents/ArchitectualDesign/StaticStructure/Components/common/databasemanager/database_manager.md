---
class: DatabaseManager
kind: class
module: gafs.dynamicaiagent.common.databasemanager
implements: [IDatabaseManager]
status: work_in_progress
---

## methods

---

### initialize_default_connection

```python
async def initialize_default_connection(config: DatabaseConnection) -> bool
```

| property | value          |
| -------- | -------------- |
| group    | initialization |
| phase    | 1              |

#### implementation notes

1. Validate and normalize the given `config`.
   - On failure: raise `DatabaseManagerInitializationException`
2. Create a default `IDatabaseProvider` instance from `config`.
   - On failure: raise `DatabaseManagerInitializationException`
3. Read the `"default"` entry from the `DatabaseConnections` collection using the created provider. If no entry exists (first run), create it. If an entry exists but differs from `config`, overwrite it.
   - On failure: raise `DatabaseManagerInitializationException`.
   - The persisted `default` entry must contain **only** the following fields (drop all others before saving):
     - `id`  (must be `"default"`)
     - `name` (must be `"default"`)
     - `description`
     - `database_type`
   - Secrets and connection parameters must **never** be saved (useless data with security risk).
4. Ensure indexes on the `DatabaseConnections` collection using `DEFINE INDEX IF NOT EXISTS` statements.
   - On failure: raise `DatabaseManagerInitializationException`.
5. Return `True`.

---

### initialize

```python
async def initialize(secret_manager: ISecretManager) -> bool
```

| property | value          |
| -------- | -------------- |
| group    | initialization |
| phase    | 3              |

#### implementation notes

1. Register the given `ISecretManager` instance to the internal field.
2. Return `True`.

---

### create_connection

```python
async def create_connection(connection_configurations: DatabaseConnection) -> DatabaseConnection
```

| property       | value                |
| -------------- | -------------------- |
| group          | connection_catalogue |
| requires_phase | 3                    |

#### implementation notes

1. Validate and normalize `connection_configurations`.
   - On failure: raise `DatabaseManagerInvalidDatabaseConnectionEntryException`
2. Get default database provider by calling `get_default_provider()`.
   - On failure: raise `DatabaseManagerNotInitializedException`
3. If `connection_configurations` contains `id`, check if the `id` is already in use by calling `get_connection()`. (Otherwise, let the database assign the id automatically.)
   - If a conflicting entry exists: raise `DatabaseManagerConflictingConnectionException`
   - On other failures: raise `DatabaseManagerOperationException`
4. If `connection_configurations` contains a `secret` id, check if the secret exists by calling the `SecretManager` method.
   - If the secret does not exist: raise `DatabaseManagerSecretNotFoundException`
5. Else if `connection_configurations` contains `raw_secret`:
   1. Create a `Secret` object with `raw_secret` set to `connection_configurations.raw_secret`.
   2. Call `create_secret(secret)` on `ISecretManager` and get the returned `Secret` entry.
      - On failure: raise `DatabaseManagerOperationException`.
   3. Set `connection_configurations.secret` to the returned `Secret.id` and clear `connection_configurations.raw_secret`.
6. Save `connection_configurations` entry to the collection.
7. Return the created `DatabaseConnection` entry.

---

### update_connection

```python
async def update_connection(database_connection: DatabaseConnection) -> DatabaseConnection
```

| property       | value                |
| -------------- | -------------------- |
| group          | connection_catalogue |
| requires_phase | 3                    |

#### implementation notes

1. Validate and normalize the given `database_connection`.
   - `database_connection` must have a non-empty `id` value.
   - `id` and `name` in `database_connection` must not be `"default"`.
   - `database_connection` must not have a non-empty `raw_secret` value (updating the secret together with the `DatabaseConnection` entry is not allowed).
   - On failure:
     - If `id` or `name` is `"default"`: raise `DatabaseManagerInvalidOperationException`
     - On other validation failures: raise `DatabaseManagerInvalidDatabaseConnectionEntryException`
2. Get default database provider.
   - On failure: raise `DatabaseManagerNotInitializedException`
3. Get the original entry.
   - If the entry is not found: raise `DatabaseManagerConnectionNotFoundException`
   - On other database operation failures: raise `DatabaseManagerOperationException`
4. If the caller is updating `secret` (reference):
   1. Check if the `secret` with the new id exists.
      - If the secret is not found: raise `DatabaseManagerSecretNotFoundException`
5. Update the `DatabaseConnection` entry.
   - On failure: raise `DatabaseManagerOperationException`
6. If an `IDatabaseProvider` with the same `id` as the updated `DatabaseConnection` is cached:
   1. Try to create a new `IDatabaseProvider` with the updated configuration.
      - On failure: log at `WARNING` level, deregister the old provider from the cache, and do not raise an exception.
   2. Replace the cached `IDatabaseProvider` with the newly created one.
   3. Call `close()` on the old `IDatabaseProvider`.
      - On failure: log at `WARNING` level and do not raise an exception.
7. Return the updated `DatabaseConnection` entry.


---

### get_connection

```python
async def get_connection(id: str) -> DatabaseConnection | None
```

| property       | value                |
| -------------- | -------------------- |
| group          | connection_catalogue |
| requires_phase | 3                    |

#### implementation notes

1.  Get default database provider
	- On failure: raise `DatabaseManagerNotInitializedException`
2. Try to get the `DatabaseConnection` entry from the default database.
	- On failure: raise `DatabaseManagerOperationException` (Do not raise exception even if an entry with the given `id` was not found)
3. Return the found `DatabaseConnection` entry if an entry with the given `id` exists. Otherwise return `None`.

---

### get_all_connections

```python
async def get_all_connections() -> list[DatabaseConnection]
```

| property       | value                |
| -------------- | -------------------- |
| group          | connection_catalogue |
| requires_phase | 3                    |

#### implementation notes

1.  Get default database provider
	- On failure: raise `DatabaseManagerNotInitializedException`
2. Get all `DatabaseConnection` entries from the default database.
	- On failure: raise `DatabaseManagerOperationException` (Do not raise exception even if no entry is found)
3. Return the found `DatabaseConnection` entries as a list. (If no entry is found, return an empty list.)

---

### get_connections_by_name

```python
async def get_connections_by_name(name: str, ambiguous: bool = False) -> list[DatabaseConnection]
```

| property       | value                |
| -------------- | -------------------- |
| group          | connection_catalogue |
| requires_phase | 3                    |

#### implementation notes

1.  Get default database provider
	- On failure: raise `DatabaseManagerNotInitializedException`
2. Query `DatabaseConnection` entries from the default database by name.
	- If `ambiguous = True`: use a partial (contains) match.
	- If `ambiguous = False`: use an exact name match.
	- On failure: raise `DatabaseManagerOperationException` (Do not raise an exception if no entry is found.)
3. Return the found `DatabaseConnection` entries as a list. (Return an empty list if no entry is found.)


---

### delete_connection

```python
async def delete_connection(id: str) -> None
```

| property | value |
|----------|-------|
| group | connection_catalogue |
| requires_phase | 3 |

#### implementation notes

1. If `id == "default"`, raise `DatabaseManagerInvalidOperationException`.
2. Get default database provider.
	- On failure: raise `DatabaseManagerNotInitializedException`
3. If an `IDatabaseProvider` with the same `id` is active (cached) deregister it from the cache, and then close it.
	- If the `close` operation fails, log at `WARNING` level and do not raise an exception.
4. Try to delete the `DatabaseConnection` entry from the default database. (`DELETE` query with `RETURN BEFORE`)
	- If the return was empty (no entry was deleted): raise `DatabaseManagerConnectionNotFoundException`
	- On other kinds of failures: raise `DatabaseManagerOperationException`

---

### create_analyzer

```python
async def create_analyzer(analyzer: FullTextAnalyzer) -> FullTextAnalyzer
```

| property | value |
|----------|-------|
| group | full_text_analyzer |
| requires_phase | 1 |

#### implementation notes

1. Validate and normalize `FullTextAnalyzer` entry.
	- On failure: raise `DatabaseManagerInvalidAnalyzerException`
2. Get default database provider
	- On failure: raise `DatabaseManagerNotInitializedException`
3. Try to get the `FullTextAnalyzer` entry from the default database by `id` (`get_analyzer`) and by name `get_analyzers_by_name`
	- If a `FullTextAnalyzer` instance with the same `id` or `name` exists, raise `DatabaseManagerConflictingAnalyzerException`.
	- On other kinds of failures: raise `DatabaseManagerAnalyzerOperationException`
4. Create an analyzer with `DEFINE ANALYZER` statement (use `OVERWRITE`)
	- On failure: raise `DatabaseManagerAnalyzerOperationException`
5. Create `FullTextAnalyzer` entry on the default database
	- On failure:
		1. Try to delete the created analyzer with `REMOVE ANALYZER` statement
			- On failure: raise `DatabaseManagerAnalyzerOperationException`
		2. raise `DatabaseManagerAnalyzerOperationException`
6. Return the created `FullTextAnalyzer` entry

---

### update_analyzer

```python
async def update_analyzer(analyzer: FullTextAnalyzer) -> FullTextAnalyzer
```

| property       | value                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------- |
| group          | full_text_analyzer                                                                          |
| requires_phase | 1                                                                                           |

#### implementation notes

1.  Validate and normalize `FullTextAnalyzer` entry.
	- `id` must not be None or empty.
	- On failure: raise `DatabaseManagerInvalidAnalyzerException`
2. Get default database provider
	- On failure: raise `DatabaseManagerNotInitializedException`
3. Try to get the `FullTextAnalyzer` entry from the default database by `id` (`get_analyzer`) 
	- If the entry is not found, raise `DatabaseManagerAnalyzerNotFoundException`
	- On other kinds of failures: raise `DatabaseManagerAnalyzerOperationException`
4. Update `FullTextAnalyzer` entry.
	- On failure: raise `DatabaseManagerAnalyzerOperationException`
5. Update analyzer with `ALTER ANALYZER` statement.
	- On failure:
		1. Rollback `FullTextAnalyzer` entry.
		2. Raise `DatabaseManagerAnalyzerOperationException`.
6. Return updated `FullTextAnalyzer` entry.


---

### get_analyzer

```python
async def get_analyzer(id: str) -> FullTextAnalyzer | None
```

| property       | value                                             |
| -------------- | ------------------------------------------------- |
| group          | full_text_analyzer                                |
| requires_phase | 1                                                 |

#### implementation notes

1.  Get default database provider
	- On failure: raise `DatabaseManagerNotInitializedException`
2. Get the `FullTextAnalyzer` entry.
	- On failure: raise `DatabaseManagerAnalyzerOperationException` (Do not raise exception even if an entry with the given `id` was not found)
3. Return the found `FullTextAnalyzer` entry if an entry with the given `id` exists. Otherwise return `None`.

---

### get_all_analyzers


```python
async def get_all_analyzers() -> list[FullTextAnalyzer]
```

| property       | value              |
| -------------- | ------------------ |
| group          | full_text_analyzer |
| requires_phase | 1                  |

#### implementation notes

1.  Get default database provider
	- On failure: raise `DatabaseManagerNotInitializedException`
2. Try to get the `FullTextAnalyzer` entry from the default database.
	- On failure: raise `DatabaseManagerAnalyzerOperationException` (Do not raise exception even if the result is empty)
3. Return the found `FullTextAnalyzer` entries.

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

#### implementation notes

1. Get default database provider.
	- On failure: raise `DatabaseManagerNotInitializedException`
2. Query `FullTextAnalyzer` entries from the default database by name.
	- If `ambiguous = True`: use a partial (contains) match.
	- If `ambiguous = False`: use an exact name match.
	- On failure: raise `DatabaseManagerAnalyzerOperationException` (Do not raise an exception if no entry is found.)
3. Return the found `FullTextAnalyzer` entries as a list.

---

### delete_analyzer

```python
async def delete_analyzer(id: str) -> None
```

| property       | value                                                                                |
| -------------- | ------------------------------------------------------------------------------------ |
| group          | full_text_analyzer                                                                   |
| requires_phase | 1                                                                                    |

#### implementation notes

1. Get default database provider.
	- On failure: raise `DatabaseManagerNotInitializedException`
2. Try to delete the `FullTextAnalyzer` by `id` (`DELETE` statement with `RETURN BEFORE`).
	- If nothing was deleted (no entry with the given `id`): raise `DatabaseManagerAnalyzerNotFoundException`
	- On other failures: raise `DatabaseManagerAnalyzerOperationException`
3. Remove the analyzer with a `REMOVE ANALYZER` statement.
	- On failure:
		1. Rollback (re-create) the `FullTextAnalyzer` entry.
		2. Raise `DatabaseManagerAnalyzerOperationException`.

---

### get_provider

```python
async def get_provider(id: str) -> IDatabaseProvider
```

| property | value |
|----------|-------|
| group | provider_getters |
| requires_phase | 1 (phase 3 for non-default providers) |

#### implementation notes

1. If `id` is `"default"`, delegate to `get_default_provider()` and return its result.
2. If the provider is already active (cached), return the cached instance immediately.
3. Get default database provider.
	- On failure: raise `DatabaseManagerNotInitializedException`
4. Get `DatabaseConnection` entry by `id`.
	- If the entry is not found: raise `DatabaseManagerConnectionNotFoundException`
	- On other kinds of failures: raise `DatabaseManagerOperationException`
5. Get the referenced secret by calling `get_secret` in `ISecretManager`.
	- If the secret is not found: raise `DatabaseManagerSecretNotFoundException`
6. Merge `parameters` from `DatabaseConnection` with the values in `secret.raw_secret`. Values from `raw_secret` take precedence on duplicate keys.
7. Create an `IDatabaseProvider` instance from the merged parameters.
8. Cache the created `IDatabaseProvider` instance.
9. Return the `IDatabaseProvider` instance.

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

#### implementation notes

1. Return the cached default database provider.
	- If it is not cached: raise `DatabaseManagerNotInitializedException`

---

## Planned Improvements & Limitations

- Switch `DatabaseProvider` management to a subscription-based model:
	- Start a subscription on the designated `DatabaseConnection` record.
	- Update `DatabaseProvider` on change or deletion events.
	- Dispose of the subscription when the `DatabaseProvider` instance is disposed.
- Implement LRU (Least Recently Used) or LFU (Least Frequently Used) style `DatabaseProvider` management.
- Current implementation assumes single-user database access. If multiple users connect to the same database, or a user directly edits an entry in the database, undesired behavior may occur.
- If a `FullTextAnalyzer` entry is modified, all indexes that use the analyzer must be rebuilt, but this functionality is not yet implemented.
- `FullTextAnalyzer` entries need to be protected (block deletion) if they are in use, but this functionality is not yet implemented.
