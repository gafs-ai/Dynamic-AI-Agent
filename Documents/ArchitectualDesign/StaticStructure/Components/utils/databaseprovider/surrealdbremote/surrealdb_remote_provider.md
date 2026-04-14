---
class: SurrealDbRemoteProvider
kind: class
module: gafs.dynamicaiagent.utils.databaseprovider.surrealdbremote
implements:
  - IDatabaseProvider
dependencies:
  - RemoteSurrealDbOptions
  - DatabaseProviderStatus
  - RetryOptions
exceptions_used:
  - DatabaseProviderInitializationException
  - DatabaseProviderUnconnectableException
  - DatabaseProviderAuthenticationException
  - DatabaseOperationException
  - DatabaseQueryErrorException
  - DatabaseConnectionException
---

## responsibilities

- Connect to a remote SurrealDB server over WebSocket.
- Authenticate using username/password; cache the session token for reconnection.
- Execute queries via the SurrealDB async Python client (`AsyncSurreal`).

## constants

| name | type | value | description |
|------|------|-------|-------------|
| `PROVIDER_NAME` | `str` | `"SurrealDBRemoteProvider"` | Identifier string for this provider |

## methods

---

### initialize

```python
async def initialize(options: RemoteSurrealDbOptions) -> bool
```

| property | value |
|----------|-------|
| async | true |
| description | Connect to the remote SurrealDB endpoint and authenticate. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `options` | `RemoteSurrealDbOptions` | yes | Connection and authentication options |

#### returns

| type | value | description |
|------|-------|-------------|
| `bool` | `True` | Successfully connected and authenticated |

#### raises

| exception | condition |
|-----------|-----------|
| `DatabaseProviderInitializationException` | Options not set or general initialization failure |
| `DatabaseProviderUnconnectableException` | Endpoint is unreachable |
| `DatabaseProviderAuthenticationException` | Credentials rejected |

#### implementation notes

1. Store `options` internally.
2. Call `_connect()` and return the result.

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

| exception                     | condition |
| ----------------------------- | -------------------------------------------------------------- |
| `DatabaseConnectionException` | Provider is not connected and all retry attempts are exhausted |
| `DatabaseQueryErrorException` | Server returns an error for the query |
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

| exception                     | condition |
| ----------------------------- | -------------------------------------------------------------- |
| `DatabaseConnectionException` | Provider is not connected and all retry attempts are exhausted |
| `DatabaseQueryErrorException` | Server returns an error for the query |
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

| property | value |
|----------|-------|
| async | false |
| description | Convert a SurrealDB driver record object into a plain `dict`. Handles `RecordID` normalization (strips table prefix from `id`, e.g. `"Secrets:abc"` → `"abc"`). |

#### implementation note

1. Unwrap a collection entry from the `result` unwrapped by `_unwrap_query_raw_result` method.

---

### close

```python
async def close() -> None
```

| property | value |
|----------|-------|
| async | true |
| description | Close the WebSocket connection and set status to `TERMINATED`. |

#### implementation note

1. This method can potentially cause an exception, but the application can do nothing for such an exception. So, if an exception is detected, do nothing to resolve it, but simply log it as ERROR, and finish the operation (return None).

## retry behavior

- Retry is attempted only on connection errors (`DatabaseConnectionException`, `DatabaseProviderUnconnectableException`).
- Authentication errors (`DatabaseProviderAuthenticationException`) and query errors (`DatabaseQueryErrorException`) are **never** retried.
- The effective `RetryOptions` for a request is resolved in priority order: per-request `retry_options` → `options.retry_options` → `RetryOptions` defaults.
- Wait before retry `n` (1-based) = `retry_interval × n` seconds.

## reconnection behavior

- `_connect()` first attempts to reuse a cached session token.
- If the token is invalid or absent, username/password authentication is performed and the resulting token is stored for future reconnections.
