---
class: ISecretManager
kind: abstract_class
module: gafs.dynamicaiagent.common.secretmanager
inherits: [ABC]
dependencies:
  - Secret
  - SecretKey
  - IDatabaseManager
  - CryptoUtil
  - CryptoType
exceptions_used:
  - SecretManagerInitializationException
  - SecretManagerNotInitializedException
  - SecretManagerOperationException
  - SecretManagerSecretNotFoundException
  - SecretManagerInvalidSecretEntryException
  - SecretManagerCryptoException
  - SecretManagerKeyNotFoundException
---

## responsibilities

- Key registry: load, store, and generate `SecretKey` entries per `CryptoType` (currently defaults to AES-256-GCM; extensible to asymmetric algorithms). Keys are sourced in priority order: component config → `secret_keys.json` in the application data folder → auto-generated and persisted
- Secret catalogue: persist encrypted `Secret` entries in the `Secrets` collection
- Crypto: transparently encrypt values in `raw_secret` to `secret` on write, and decrypt `secret` back to `raw_secret` on read

## initialization_sequence

`SecretManager.initialize()` is Phase-2 of the application startup sequence. Refer to `IDatabaseManager.initialization_sequence` for the full 3-phase sequence.

| step  | actor             | method                                                  | phase |
| ----- | ----------------- | ------------------------------------------------------- | ----- |
| 1     | DatabaseManager   | `initialize_default_connection(config)`                 | 1     |
| **2** | **SecretManager** | **`initialize(database_manager, crypto_util, config)`** | **2** |
| 3     | DatabaseManager   | `initialize(secret_manager)`                            | 3     |

## methods

---

### initialize

```python
def initialize(
    database_manager: IDatabaseManager,
    crypto_util: CryptoUtil,
    config: dict[str, Any],
) -> bool
```

| property    | value                                                                                                                                                                          |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| async       | false                                                                                                                                                                          |
| description | Register the `IDatabaseManager` and `CryptoUtil`, then load keys via priority order A → B → C. Must be called after Phase-1 (`DatabaseManager.initialize_default_connection`). |

#### parameters

| name               | type               | required | description                                                                                                                                                                                 |
| ------------------ | ------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `database_manager` | `IDatabaseManager` | yes      | Already Phase-1-initialized `DatabaseManager` instance                                                                                                                                      |
| `crypto_util`      | `CryptoUtil`       | yes      | Utility used to perform encryption and decryption                                                                                                                                           |
| `config`           | `dict`             | yes      | Component configuration. `config["secret_keys"]` (`list[dict]`, optional) provides key entries directly (path A). The application data folder is resolved internally by the implementation. |

#### key loading priority

| priority | label | condition | action |
|----------|-------|-----------|--------|
| A | Config | `config["secret_keys"]` is present and non-empty | Deserialize each entry as `SecretKey` and register |
| B | File | `secret_keys` absent in config | Load `secret_keys.json` from the application data folder; deserialize and register each `SecretKey` |
| C | Generate | File not found or empty | Generate a `SecretKey` per default `CryptoType` via `CryptoUtil`, register, and write to `secret_keys.json` in the application data folder |

#### returns

| type | value | description |
|------|-------|-------------|
| `bool` | `True` | Successfully initialized |

#### raises

| exception | condition |
|-----------|-----------|
| `SecretManagerInitializationException` | Initialization fails (e.g. default database provider not available) |

---

### add_key

```python
def add_key(key: SecretKey) -> None
```

| property | value |
|----------|-------|
| async | false |
| description | Register a `SecretKey` entry. The key's `name` must match a valid `CryptoType.value`. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `key` | `SecretKey` | yes | Key entry to register |

#### raises

| exception | condition |
|-----------|-----------|
| `SecretManagerInvalidSecretEntryException` | A key for `key.name` is already registered |

---

### get_key

```python
def get_key(crypto_type: CryptoType) -> SecretKey
```

| property | value |
|----------|-------|
| async | false |
| description | Retrieve the registered `SecretKey` for the specified crypto type. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `crypto_type` | `CryptoType` | yes | Crypto type to retrieve the key for |

#### returns

| type | description |
|------|-------------|
| `SecretKey` | Registered key entry |

#### raises

| exception | condition |
|-----------|-----------|
| `SecretManagerKeyNotFoundException` | No key is registered for the specified crypto type |

---

### generate_key

```python
def generate_key(crypto_type: CryptoType) -> SecretKey
```

| property | value |
|----------|-------|
| async | false |
| description | Generate a new `SecretKey` for the specified crypto type, register it, and persist all registered keys to `secret_keys.json` in the application data folder. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `crypto_type` | `CryptoType` | yes | Crypto type for which a key will be generated |

#### returns

| type | description |
|------|-------------|
| `SecretKey` | The newly generated and registered key entry |

#### raises

| exception | condition |
|-----------|-----------|
| `SecretManagerNotInitializedException` | SecretManager is not initialized |
| `SecretManagerInvalidSecretEntryException` | A key for the specified crypto type is already registered |

---

### create_secret

```python
async def create_secret(secret: Secret) -> Secret
```

| property | value |
|----------|-------|
| description | Encrypt and persist a new `Secret` entry in the `Secrets` collection. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `secret` | `Secret` | yes | Secret entry to create. `raw_*` keys in `secret.secret` will be encrypted before persisting. If `id` is not set, the database assigns one automatically. |

#### returns

| type | description |
|------|-------------|
| `Secret` | Created entry with all values returned as `raw_*` keys. |

#### raises

| exception | condition |
|-----------|-----------|
| `SecretManagerNotInitializedException` | SecretManager is not initialized |
| `SecretManagerInvalidSecretEntryException` | Entry is invalid (e.g. `name` is missing) |
| `SecretManagerCryptoException` | Encryption of a secret value fails |
| `SecretManagerOperationException` | Database operation fails |

#### rules

1. All values in `secret.raw_secret` are encrypted individually and stored in `secret.secret`. Keys are preserved as-is. `raw_secret` is never persisted.
2. The returned entry has `raw_secret` populated with the original plaintext values and `secret` set to `None`.

---

### update_secret

```python
async def update_secret(secret: Secret) -> Secret
```

| property | value |
|----------|-------|
| description | Merge-update an existing `Secret` entry. `secret.id` is required. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `secret` | `Secret` | yes | Updated secret entry. `id` is required. `raw_*` keys in `secret.secret` will be encrypted before persisting. |

#### returns

| type | description |
|------|-------------|
| `Secret` | Updated entry with all values returned as `raw_*` keys. |

#### raises

| exception | condition |
|-----------|-----------|
| `SecretManagerNotInitializedException` | SecretManager is not initialized |
| `SecretManagerInvalidSecretEntryException` | `id` is not set |
| `SecretManagerSecretNotFoundException` | No record exists for the given `id` |
| `SecretManagerCryptoException` | Encryption of a secret value fails |
| `SecretManagerOperationException` | Database operation fails |

#### rules

1. Only fields present (non-`None`) in the given `secret` are updated (MERGE semantics).
2. If `raw_secret` is provided, it replaces the entire stored `secret` dict (the `raw_secret` values are encrypted and stored as `secret`).
3. Each value in `raw_secret` is encrypted individually. Keys are not encrypted.
4. In the returned entry, `raw_secret` is populated with the plaintext values and `secret` is set to `None`.

---

### get_secret

```python
async def get_secret(secret_id: str, decrypt: bool = False) -> Secret | None
```

| property | value |
|----------|-------|
| description | Retrieve a `Secret` entry by record id. Behavior depends on `decrypt`. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `secret_id` | `str` | yes | Record id to look up |
| `decrypt` | `bool` | no (default: `False`) | If `True`, decrypt and return plaintext values for internal use. If `False`, return the entry in masked form for external clients. |

#### returns

| type | condition | description |
|------|-----------|-------------|
| `Secret` | found, `decrypt=True` | `raw_secret` is populated with plaintext values; `secret` is set to `None`. |
| `Secret` | found, `decrypt=False` | `secret` dict is returned with all values replaced by `"******"` (keys preserved); `raw_secret` is set to `None`. |
| `None` | not found | No matching record |

#### raises

| exception | condition |
|-----------|-----------|
| `SecretManagerNotInitializedException` | SecretManager is not initialized |
| `SecretManagerCryptoException` | Decryption of a secret value fails (only when `decrypt=True`) |
| `SecretManagerOperationException` | Database operation fails |
---

### search_secrets

```python
async def search_secrets(criteria: SecretSearchCriteria, decrypt: bool = False) -> list[Secret]
```

| property | value |
|----------|-------|
| description | Search `Secret` entries by criteria. Behavior depends on `decrypt`. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `criteria` | `SecretSearchCriteria` | yes | Search criteria |
| `decrypt` | `bool` | no (default: `False`) | If `True`, decrypt and return plaintext values for internal use. If `False`, return entries in masked form for external clients. |

#### returns

| type | description |
|------|-------------|
| `list[Secret]` | Matching entries. When `decrypt=True`, each entry has `raw_secret` populated with plaintext values and `secret` set to `None`. When `decrypt=False`, each entry has `secret` dict with all values replaced by `"******"` (keys preserved) and `raw_secret` set to `None`. Empty list if no entries found. |

#### raises

| exception | condition |
|-----------|-----------|
| `SecretManagerNotInitializedException` | SecretManager is not initialized |
| `SecretManagerCryptoException` | Decryption of a secret value fails (only when `decrypt=True`) |
| `SecretManagerOperationException` | Database operation fails |
---

### delete_secret

```python
async def delete_secret(secret_id: str) -> None
```

| property | value |
|----------|-------|
| description | Delete a `Secret` entry by record id. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `secret_id` | `str` | yes | Record id of the secret to delete |

#### raises

| exception | condition |
|-----------|-----------|
| `SecretManagerNotInitializedException` | SecretManager is not initialized |
| `SecretManagerSecretNotFoundException` | No record exists for the given `id` |
| `SecretManagerOperationException` | Database operation fails |

---

## related class: SecretSearchCriteria

Search criteria for `search_secrets`. All fields are optional; omitted fields are not included in the query filter.

### attributes

| name                   | type                | default | description                                          |
| ---------------------- | ------------------- | ------- | ---------------------------------------------------- |
| `name`                 | `str \| None`       | `None`  | Partial match on `name` (contains)                   |
| `description_keywords` | `list[str] \| None` | `None`  | Keywords matched against `description` with OR logic |
| `created_at_from`      | `datetime \| None`  | `None`  | Lower bound for `created_at` (inclusive)             |
| `created_at_to`        | `datetime \| None`  | `None`  | Upper bound for `created_at` (inclusive)             |
| `updated_at_from`      | `datetime \| None`  | `None`  | Lower bound for `updated_at` (inclusive)             |
| `updated_at_to`        | `datetime \| None`  | `None`  | Upper bound for `updated_at` (inclusive)             |
| `valid_until_from`     | `datetime \| None`  | `None`  | Lower bound for `valid_until` (inclusive)            |
| `valid_until_to`       | `datetime \| None`  | `None`  | Upper bound for `valid_until` (inclusive)            |
| `limit`                | `int`               | `100`   | Maximum number of results. `0` means no limit.       |

### notes

- `datetime` fields also accept ISO 8601 strings and Unix epoch integers (auto-converted).
- The query is currently implemented using SurrealDB-specific syntax and only supports `SurrealDbRemoteProvider`.
