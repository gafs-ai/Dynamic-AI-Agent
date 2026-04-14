---
class: DatabaseProviderOptions
kind: abstract_class
roles: [value_object]
module: gafs.dynamicaiagent.utils.databaseprovider
inherits: [ABC]
dependencies:
  - DatabaseProviderType
  - RetryOptions
---

## responsibilities

- Base value object for all database provider configuration.
- Concrete subclasses add provider-specific fields (connection string, credentials, etc.).
- All attribute assignments are validated via `__setattr__`.

## attributes

| name | type | required | default | description |
|------|------|----------|---------|-------------|
| `database_type` | `DatabaseProviderType` | yes | — | Provider type. Accepts `DatabaseProviderType` enum or its string value. |
| `database_name` | `str` | yes | — | Logical name identifying this provider instance. |
| `retry_options` | `RetryOptions \| None` | no | `None` | Default retry options for connection errors. If `None`, the `RetryOptions` defaults apply. |

## notes

- `database_type` accepts both `DatabaseProviderType` enum instances and their string values; invalid values raise `ValueError`.
- All attributes are validated on assignment; invalid types raise `ValueError`.
