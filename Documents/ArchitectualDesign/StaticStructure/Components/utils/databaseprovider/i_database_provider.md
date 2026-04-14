---
class: IDatabaseProvider
kind: abstract_class
module: gafs.dynamicaiagent.utils.databaseprovider
inherits: [ABC]
dependencies:
  - DatabaseProviderOptions
  - DatabaseProviderStatus
  - RetryOptions
exceptions_used:
  - DatabaseProviderException
  - DatabaseProviderInitializationException
  - DatabaseOperationException
---

## responsibilities

- Define the unified contract for all database provider implementations.
- Provide two query modes: typed (`query`) and raw (`query_raw`).
- Retry on connection errors according to the effective `RetryOptions`; never retry on authentication or query errors.

## properties

| name | type | description |
|------|------|-------------|
| `status` | `DatabaseProviderStatus` | Current lifecycle status of this provider |

## methods

---

### initialize

```python
async def initialize(options: DatabaseProviderOptions) -> bool
```

| property    | value                                                                                        |
| ----------- | -------------------------------------------------------------------------------------------- |
| async       | true                                                                                         |
| description | Connect to the database and apply the given options. Must be called before any query method. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `options` | `DatabaseProviderOptions` | yes | Provider-specific options (subclass of `DatabaseProviderOptions`) |

#### returns

| type | value | description |
|------|-------|-------------|
| `bool` | `True` | Successfully initialized |

#### raises

| exception | condition |
|-----------|-----------|
| `DatabaseProviderInitializationException` | Connection or authentication fails |

---

### query

```python
async def query(query: str, model: type[T] | None = None, many: bool = False, retry_options: RetryOptions | None = None) -> T | list[T] | None
```

| property | value |
|----------|-----------|
| async | true |
| description | Execute a query and optionally deserialize the result into a typed model. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `query` | `str` | yes | Query string to execute (syntax is provider-specific) |
| `model` | `type[T] \| None` | no | Model class to deserialize each result record into. `None` = do not deserialize; return `None`. |
| `many` | `bool` | no (default: `False`) | `True` = return `list[T]`; `False` = return single `T` or `None` |
| `retry_options` | `RetryOptions \| None` | no (default: `None`) | Per-request retry options. Overrides `DatabaseProviderOptions.retry_options`. If `None`, falls back to provider-level options or `RetryOptions` defaults. |

#### returns

| type | condition |
|------|-----------|
| `T` | `model` given, `many=False`, record found |
| `list[T]` | `model` given, `many=True` |
| `None` | `model` is `None`, or no record found |

#### raises

| exception | condition |
|-----------|-----------|
| `DatabaseOperationException` | Query execution fails |

---

### query_raw

```python
async def query_raw(query: str, retry_options: RetryOptions | None = None) -> Any
```

| property | value |
|----------|-----------|
| async | true |
| description | Execute a query and return the raw driver-level result without any deserialization. The exact return type is driver-specific. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `query` | `str` | yes | Query string to execute |
| `retry_options` | `RetryOptions \| None` | no (default: `None`) | Per-request retry options. Overrides `DatabaseProviderOptions.retry_options`. If `None`, falls back to provider-level options or `RetryOptions` defaults. |

#### returns

| type | description |
|------|-------------|
| `Any` | Raw result as returned by the underlying database driver |

#### raises

| exception | condition |
|-----------|-----------|
| `DatabaseOperationException` | Query execution fails |

---

### close

```python
async def close() -> None
```

| property | value |
|----------|-------|
| async | true |
| description | Close the database connection and release all resources. Implementations must also implement `__aexit__` and call this method inside it. |
