---
class: SurrealDbLocalProvider
kind: class
module: gafs.dynamicaiagent.utils.databaseprovider.surrealdblocal
implements:
  - IDatabaseProvider
dependencies:
  - LocalSurrealDbOptions
  - DatabaseProviderStatus
  - RetryOptions
exceptions_used:
  - DatabaseProviderInitializationException
  - DatabaseProviderOptionsException
  - DatabaseProviderUnconnectableException
  - DatabaseOperationException
  - DatabaseQueryErrorException
  - EmbeddedDatabaseInitializationException
  - DatabaseConnectionException
---

## responsibilities

- Run SurrealDB as an embedded database within the application process.
- Support in-memory (`mem://`), `surrealkv` (`surrealkv://`), `rocksdb` (`rocksdb://`), and `file` (`file://`) storage backends.
- Execute queries via the SurrealDB async Python client (`AsyncSurreal`).

## constants

| name | type | value | description |
|------|------|-------|-------------|
| `PROVIDER_NAME` | `str` | `"SurrealDBLocalProvider"` | Identifier string for this provider |

## methods

---

### initialize

```python
async def initialize(options: LocalSurrealDbOptions) -> bool
```

| property | value |
|----------|-------|
| async | true |
| description | Start the embedded SurrealDB instance with the given options. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `options` | `LocalSurrealDbOptions` | yes | Storage and configuration options |

#### returns

| type | value | description |
|------|-------|-------------|
| `bool` | `True` | Successfully started and connected |

#### raises

| exception                                 | condition                                  |
| ----------------------------------------- | ------------------------------------------ |
| `DatabaseProviderOptionsException`        | Given `options` are invalid                |
| `EmbeddedDatabaseInitializationException` | Embedded database-specific startup failure |
| `DatabaseProviderUnconnectableException`  | Fails to connect to the database           |
| `DatabaseProviderInitializationException` | General initialization failure             |



#### implementation notes

1. Validate and store `options` internally.
	- If the `options` are invalid, raise `DatabaseProviderOptionsException`
2. Build an `AsyncSurreal` instance for embedded database.
	- On failure: raise `EmbeddedDatabaseInitializationException`
3. Connect to the database (give `namespace` and 'database').
	- If not connectable, raise `DatabaseProviderUnconnectableException`
	- On other kinds of failures: raise `DatabaseProviderInitializationException`

---

### query

```python
async def query(query: str, model: type[T] | None = None, many: bool = False, retry_options: RetryOptions | None = None) -> T | list[T] | None
```

| property | value |
|----------|-----------|
| async | true |
| description | Execute a SurrealQL query and optionally deserialize results. Retries on connection errors according to the effective `RetryOptions`. |

#### raises

| exception                     | condition                                                                 |
| ----------------------------- | ------------------------------------------------------------------------- |
| `DatabaseConnectionException` | Provider is not connected and all retry attempts are exhausted            |
| `DatabaseQueryErrorException` | Server returns an error for the query                                     |
| `DatabaseOperationException`  | On failures that other types of exceptions cannot represent the exception |



#### implementation notes

1. Send query to the SurrealDB by calling `query_raw` method
2. Extract the collection entries from the result
3. Convert the list to a list of model class instance or a model class instance.

---

### query_raw

```python
async def query_raw(query: str, retry_options: RetryOptions | None = None) -> Any
```

| property | value |
|----------|-----------|
| async | true |
| description | Execute a SurrealQL query and return the raw `AsyncSurreal.query()` result without deserialization. Retries on connection errors according to the effective `RetryOptions`. |

#### raises

| exception                     | condition                                                                 |
| ----------------------------- | ------------------------------------------------------------------------- |
| `DatabaseConnectionException` | Provider is not connected and all retry attempts are exhausted            |
| `DatabaseQueryErrorException` | Server returns an error for the query                                     |
| `DatabaseOperationException`  | On failures that other types of exceptions cannot represent the exception |

#### implementation notes

1. Send query to the SurrealDB
	- On failure:
		- If the query fails (exceptions due to query syntax), raise `DatabaseQueryErrorException`
		- If the request times out or the server is unconnectable, retry following the retry options, and then raise `DatabaseConnectionException` if all the retries fail.
		- On other kinds of failures: raise `DatabaseOperationException`
2. Extract the query `result` from the raw response
3. Return the extracted result as is. (The returned value usually be a list or a dictionary)

---

### `_unwrap_query_raw_result`

```python
def _unwrap_query_raw_result(raw_result: Any) -> Any
```

| property | value |
|----------|-------|
| async | false |
| description | Extract the payload from a SurrealDB statement result list. Returns the `result` field of the last statement. |

#### implementation note

SurrealDB client returns a list of statement results:

```
[{"status": "...", "time": "...", "result": [...]}, ...]
```

so, this method unwraps the result from the raw response.

---

### `_unwrap_record`

```python
def _unwrap_record(obj: Any) -> dict[str, Any]
```

| property    | value                                                                                                                           |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------- |
| async       | false                                                                                                                           |
| description | Convert a SurrealDB driver record object into a plain `dict`. Handles `RecordID` normalization (strips table prefix from `id`). |

#### implementation note

1. Unwrap a collection entry from the `result` unwrapped by `_unwrap_query_raw_result` method.

---

### close

```python
async def close() -> None
```

| property    | value                                                                    |
| ----------- | ------------------------------------------------------------------------ |
| async       | true                                                                     |
| description | Shut down the embedded database instance and set status to `TERMINATED`. |

#### implementation note

1. This method can potentially cause an exception, but the application can do nothing for such an exception. So, if an exception is detected, do nothing to resolve it, but simply log it as ERROR, and finish the operation (return None).

## retry behavior

- Retry is attempted only on connection errors (`DatabaseConnectionException`).
- Query errors (`DatabaseQueryErrorException`) are **never** retried.
- The effective `RetryOptions` for a request is resolved in priority order: per-request `retry_options` → `options.retry_options` → `RetryOptions` defaults.
- Wait before retry `n` (1-based) = `retry_interval × n` seconds.

## storage backends

| `LocalSurrealDbStorageType` | URL scheme | persistence |
|-----------------------------|------------|-------------|
| `MEM` | `mem://` | none (in-memory only) |
| `SURREALKV` | `surrealkv://{path}` | persistent (default) |
| `ROCKSDB` | `rocksdb://{path}` | persistent |
| `FILE` | `file://{path}` | persistent |
