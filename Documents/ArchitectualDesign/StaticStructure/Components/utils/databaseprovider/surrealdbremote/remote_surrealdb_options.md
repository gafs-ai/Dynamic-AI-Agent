---
class: RemoteSurrealDbOptions
kind: class
roles: [value_object]
module: gafs.dynamicaiagent.utils.databaseprovider.surrealdbremote
inherits: [DatabaseProviderOptions]
---

## attributes

| name | type | required | default | description |
|------|------|----------|---------|-------------|
| `database_type` | `DatabaseProviderType` | fixed | `SURREALDB_REMOTE` | Always `SURREALDB_REMOTE`. Raises `ValueError` if set to any other value. |
| `endpoint` | `str` | yes | — | WebSocket endpoint URL of the SurrealDB server (e.g. `"ws://localhost:8000"`) |
| `namespace` | `str` | yes | — | SurrealDB namespace |
| `database` | `str` | yes | — | SurrealDB database name |
| `username` | `str` | yes | — | Authentication username |
| `password` | `str` | yes | — | Authentication password |
| `auth_level` | `str` | no | `"database"` | Authentication level (e.g. `"database"`, `"namespace"`, `"root"`) |
| `database_name` | `str` | yes | — | Logical name identifying this provider instance (inherited) |
| `retry_options` | `RetryOptions \| None` | no | `None` | Default retry options for connection errors. If `None`, `RetryOptions` defaults apply (inherited). |

## notes

- All attribute assignments are validated via `__setattr__`; invalid types raise `ValueError`.
- `password` must never be logged or stored in plaintext outside of this options object.
