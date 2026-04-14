---
class: DatabaseConnection
kind: data_class
roles: [stored_model, request, response]
module: gafs.dynamicaiagent.common.databasemanager
collection: DatabaseConnections
dependencies:
  - DatabaseProviderType
---

## constants

| name | type | value |
|------|------|-------|
| `COLLECTION_NAME()` | `str` | `"DatabaseConnections"` |

## attributes

| name            | type                   | required | persisted | transient | description                                                                                                                                                    |
| --------------- | ---------------------- | -------- | --------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`            | `str`                  | no       | yes       | no        | Record ID. Normalized from SurrealDB `RecordID` — table prefix stripped (e.g. `"table:abc"` → `"abc"`).                                                        |
| `name`          | `str`                  | yes      | yes       | no        | Unique human-readable name for the connection.                                                                                                                 |
| `description`   | `str`                  | no       | yes       | no        | Optional description.                                                                                                                                          |
| `database_type` | `DatabaseProviderType` | yes      | yes       | no        | Database provider type. Accepts both enum instance and its string representation (auto-converted).                                                             |
| `secret`        | `str`                  | no       | yes       | no        | ID of the associated `Secret` record containing credentials. Normalized from SurrealDB `RecordID`.                                                             |
| `raw_secret`    | `dict`                 | no       | no        | yes       | Raw credential dict. Used only during initial config loading or internal connection management. Never written to the database. Always excluded from responses. |
| `parameters`    | `dict`                 | no       | yes       | no        | Non-secret connection parameters (e.g. endpoint, namespace, database name).                                                                                    |

## indexes

| field  | index_type       | analyzer        | notes    |
| ------ | ---------------- | --------------- | -------- |
| `id`   | auto             | —               | automatic |
| `name` | standard, unique | —               |          |
| `name` | FULL TEXT        | default ngram   |          |
| `description` | FULL TEXT | default English |         |

## constraints

1. `raw_secret` is never written to the database under any circumstances.
2. `raw_secret` is excluded from all values returned to callers.
3. The `default` entry has `id = "default"` and `name = "default"` and is created automatically during initialization of `DatabaseManager`. External callers are not allowed to update or delete `default` entry.

## config_file_schema

The `default` database connection is defined in configuration files under the `default_database` key.

| field | type | required | constraint |
|-------|------|----------|------------|
| `id` | `str` | yes | must be `"default"` |
| `name` | `str` | yes | must be `"default"` |
| `description` | `str` | no | |
| `database_type` | `str` | yes | `"surrealdb_local"` or `"surrealdb_remote"` |
| `raw_secret` | `dict` | conditional | required when `database_type` is `"surrealdb_remote"` |
| `parameters` | `dict` | yes | parameters required to establish local or remote connection |
