---
class: LocalSurrealDbOptions
kind: class
roles: [value_object]
module: gafs.dynamicaiagent.utils.databaseprovider.surrealdblocal
inherits: [DatabaseProviderOptions]
dependencies:
  - LocalSurrealDbStorageType
---

## attributes

| name | type | required | default | description |
|------|------|----------|---------|-------------|
| `database_type` | `DatabaseProviderType` | fixed | `SURREALDB_LOCAL` | Always `SURREALDB_LOCAL`. Raises `ValueError` if set to any other value. |
| `namespace` | `str` | yes | — | SurrealDB namespace |
| `database` | `str` | yes | — | SurrealDB database name |
| `storage_type` | `LocalSurrealDbStorageType` | no | `SURREALKV` | Storage backend to use |
| `path` | `str \| None` | no | `None` | File path for persistent storage backends (`surrealkv`, `rocksdb`, `file`). Ignored when `storage_type` is `MEM`. |
| `database_name` | `str` | yes | — | Logical name identifying this provider instance (inherited) |
| `retry_options` | `RetryOptions \| None` | no | `None` | Default retry options for connection errors. If `None`, `RetryOptions` defaults apply (inherited). |

---

## LocalSurrealDbStorageType

```
kind: enum
module: gafs.dynamicaiagent.utils.databaseprovider.surrealdblocal
```

| name | value | description |
|------|-------|-------------|
| `MEM` | `"mem"` | In-memory storage. No persistence; data is lost on shutdown. |
| `FILE` | `"file"` | File-based persistent storage. |
| `SURREALKV` | `"surrealkv"` | SurrealKV persistent storage (default). |
| `ROCKSDB` | `"rocksdb"` | RocksDB persistent storage. |

## notes

- All attribute assignments are validated via `__setattr__`; invalid types raise `ValueError`.
- When `storage_type` is `MEM`, `path` is ignored.
