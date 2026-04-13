---
class: Secret
kind: data_class
roles: [stored_model, request, response]
module: gafs.dynamicaiagent.common.secretmanager
collection: Secrets
---

## constants

| name | type | value |
|------|------|-------|
| `COLLECTION_NAME()` | `str` | `"Secrets"` |

## attributes

| name          | type                     | required | persisted | transient | description                                                                                                                                               |
| ------------- | ------------------------ | -------- | --------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`          | `str \| None`            | no       | yes       | no        | Record ID. Normalized from SurrealDB `RecordID` — table prefix stripped (e.g. `"Secrets:abc"` → `"abc"`).                                                 |
| `name`        | `str`                    | yes      | yes       | no        | Unique human-readable name for the secret.                                                                                                                |
| `secret`      | `dict[str, Any] \| None` | yes      | yes       | no        | Encrypted credential values. Keys are stored as-is; only values are encrypted. Always populated when reading from the database.                           |
| `raw_secret`  | `dict[str, Any] \| None` | no       | no        | yes       | Plaintext credential values. Same keys as `secret`, but values are in plaintext. Used for external API (request/response). Never written to the database. |
| `description` | `str \| None`            | no       | yes       | no        | Optional description.                                                                                                                                     |
| `tags`        | `list[str]`              | no       | yes       | no        | Optional tags to manage the entries.                                                                                                                      |
| `created_at`  | `datetime \| None`       | no       | yes       | no        | Timestamp when the record was created. Set automatically by the system.                                                                                   |
| `updated_at`  | `datetime \| None`       | no       | yes       | no        | Timestamp when the record was last updated. Set automatically by the system.                                                                              |
| `valid_until` | `datetime \| None`       | no       | yes       | no        | Optional expiry datetime of the secret.                                                                                                                   |

## indexes

| field  | index_type       | analyzer      | notes     |
| ------ | ---------------- | ------------- | --------- |
| `id`   | auto             | —             | automatic |
| `name` | standard, unique | —             |           |
| `name` | FULL TEXT        | default ngram |           |
| tags   | standard         | —             |           |


## constraints

1. `raw_secret` is never written to the database under any circumstances.
2. `raw_secret` is always excluded from all values returned from the database.
3. When returning a `Secret` to a caller, `raw_secret` is populated with the decrypted values of all keys in `secret`. `secret` is set to `None` in the returned entry.
4. The `created_at` and `updated_at` fields are managed by the system and must not be set by callers.

## secret value encoding

Encrypted values stored in `secret` are encoded as a string in the format `"{crypto_type}:{encrypted_payload}"`. The `crypto_type` prefix identifies the algorithm used, enabling future key rotation and algorithm migration.
