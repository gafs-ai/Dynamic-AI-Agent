---
class: SecretManager
kind: class
module: gafs.dynamicaiagent.common.secretmanager
implements: [ISecretManager]
dependencies:
  - IConfigurationLoader
exceptions_used:
  - SecretManagerInitializationException
status: work_in_progress
---

## constants

| name | type | value | description |
|------|------|-------|-------------|
| `DEFAULT_CRYPTO_TYPE()` | `CryptoType` | `CryptoType.AES_256_GCM` | Default crypto type used when encrypting secrets |

## private methods

---

### _get_data_folder

```python
def _get_data_folder() -> Path
```

| property | value |
|----------|-----------|
| description | Resolve the application data folder path using `platformdirs`. |

#### implementation notes

1. Call `platformdirs.user_data_dir(appname=IConfigurationLoader.APPLICATION_NAME, appauthor=IConfigurationLoader.APPLICATION_AUTHOR)` and return as a `Path`.

---

### _load_keys_from_data_folder

```python
def _load_keys_from_data_folder() -> list[SecretKey] | None
```

| property | value |
|----------|-------|
| description | Load `SecretKey` entries from `secret_keys.json` in the application data folder. Returns `None` if the file does not exist or is empty. |

#### implementation notes

1. Resolve the file path: `_get_data_folder() / "secret_keys.json"`.
2. If the file does not exist, return `None`.
3. Read and parse the file as a JSON array.
4. If the parsed array is empty, return `None`.
5. Deserialize each element as a `SecretKey` and return the list.

---

### _save_keys_to_data_folder

```python
def _save_keys_to_data_folder(keys: list[SecretKey]) -> None
```

| property | value |
|----------|-------|
| description | Merge the given `SecretKey` entries into `secret_keys.json` in the application data folder. Existing entries for other algorithm names are preserved; only entries whose `name` matches a key in `keys` are updated. |

#### parameters

| name | type | required | description |
|------|------|----------|-------------|
| `keys` | `list[SecretKey]` | yes | Key entries to add or update |

#### implementation notes

1. Resolve the file path: `_get_data_folder() / "secret_keys.json"`.
2. Create the data folder if it does not exist.
3. If the file exists and is non-empty, read and parse it as a JSON array into `existing` (`list[SecretKey]`). Otherwise, set `existing` to an empty list.
4. Build a merged list: start with `existing`, then for each entry in `keys`, replace the matching entry (by `name`) if present, or append if not.
5. Write the merged list as a JSON array to the file (overwrite).

---

## methods

---

### initialize

```python
def initialize(
    database_manager: IDatabaseManager,
    crypto_util: CryptoUtil,
    config: dict,
) -> bool
```

| property | value |
|----------|-------|
| async | false |

#### implementation notes

1. Register `database_manager` and `crypto_util` to internal fields.
2. Obtain the default `IDatabaseProvider` by calling `database_manager.get_default_provider()`.
   - On failure: raise `SecretManagerInitializationException`.
3. Load keys using the following priority:
   - **(A — Config)** If `config["secret_keys"]` is present and non-empty:
     1. Deserialize each entry as a `SecretKey`.
     2. Register each via `add_key(key)`.
   - **(B — File)** Else, call `_load_keys_from_data_folder()`:
     1. If a non-empty list is returned, register each entry via `add_key(key)`.
   - **(C — Generate)** Else (`_load_keys_from_data_folder()` returned `None`):
     1. For each value in `CryptoType`, call `crypto_util.generate_key_pair(crypto_type)` to get a `KeyPair`.
     2. Construct a `SecretKey` with `name=crypto_type.value`, `encryption_key=key_pair.encryption_key`, `decryption_key=key_pair.decryption_key`.
     3. Register each via `add_key(key)`.
     4. Call `_save_keys_to_data_folder(registered_keys)` to persist all registered keys.
4. Return `True`.

---

### add_key

```python
def add_key(key: SecretKey) -> None
```

| property | value |
|----------|-------|
| async | false |

#### implementation notes

1. If a key with `key.name` is already registered, raise `SecretManagerInvalidSecretEntryException`.
2. Register `key` under `key.name` in the internal key store.

---

### get_key

```python
def get_key(crypto_type: CryptoType) -> SecretKey
```

| property | value |
|----------|-------|
| async | false |

#### implementation notes

1. Look up `crypto_type.value` in the internal key store.
   - If not found: raise `SecretManagerKeyNotFoundException`.
2. Return the `SecretKey` entry.

---

### generate_key

```python
def generate_key(crypto_type: CryptoType) -> SecretKey
```

| property | value |
|----------|-------|
| async | false |

#### implementation notes

1. If not initialized, raise `SecretManagerNotInitializedException`.
2. If a key for `crypto_type` is already registered, raise `SecretManagerInvalidSecretEntryException`.
3. Call `crypto_util.generate_key_pair(crypto_type)` to get a `KeyPair`.
4. Construct a `SecretKey` with `name=crypto_type.value`, `encryption_key=key_pair.encryption_key`, `decryption_key=key_pair.decryption_key`.
5. Register via `add_key(key)`.
6. Call `_save_keys_to_data_folder(all_registered_keys)` to persist all currently registered keys.
7. Return the generated `SecretKey`.

---

### create_secret

```python
async def create_secret(secret: Secret) -> Secret
```

#### implementation notes

1. If not initialized, raise `SecretManagerNotInitializedException`.
2. Validate `secret`.
   - On failure: raise `SecretManagerInvalidSecretEntryException`.
3. Obtain the encryption key: `secret_key = get_key(DEFAULT_CRYPTO_TYPE)`.
4. For each key-value pair in `secret.raw_secret`:
   1. Encrypt the value by calling `crypto_util.encrypt(DEFAULT_CRYPTO_TYPE, value, secret_key.encryption_key)` and format as `"{crypto_type.value}:{encrypted_payload}"`.
      - On failure: raise `SecretManagerCryptoException`.
   2. Store the encrypted result in `secret.secret` under the same key.
5. Persist the entry to the `Secrets` collection (only `secret.secret` is persisted; `secret.raw_secret` is excluded).
   - If `secret.id` is not set, let the database assign the id automatically.
   - On failure: raise `SecretManagerOperationException`.
6. Set `raw_secret` to the original plaintext values on the returned entry and set `secret` to `None`.
7. Return the created `Secret` entry.

---

### update_secret

```python
async def update_secret(secret: Secret) -> Secret
```

#### implementation notes

1. If not initialized, raise `SecretManagerNotInitializedException`.
2. Validate `secret`.
   - `secret.id` must not be `None` or empty.
   - On failure: raise `SecretManagerInvalidSecretEntryException`.
3. Obtain the encryption key: `secret_key = get_key(DEFAULT_CRYPTO_TYPE)`.
4. For each key-value pair in `secret.raw_secret`:
   1. Encrypt the value by calling `crypto_util.encrypt(DEFAULT_CRYPTO_TYPE, value, secret_key.encryption_key)` and format as `"{crypto_type.value}:{encrypted_payload}"`.
      - On failure: raise `SecretManagerCryptoException`.
   2. Store the encrypted result in `secret.secret` under the same key.
5. Update the entry using a MERGE query (`UPDATE Secrets:{id} MERGE ...`) with `secret.secret` as the payload (`secret.raw_secret` is excluded).
   - If no record was updated (not found): raise `SecretManagerSecretNotFoundException`.
   - On other failures: raise `SecretManagerOperationException`.
6. Set `raw_secret` to the original plaintext values on the returned entry and set `secret` to `None`.
7. Return the updated `Secret` entry.

---

### get_secret

```python
async def get_secret(secret_id: str, decrypt: bool = False) -> Secret | None
```

#### implementation notes

1. If not initialized, raise `SecretManagerNotInitializedException`.
2. Query the `Secrets` collection by `id` (`SELECT * FROM Secrets:{secret_id}`).
   - On failure: raise `SecretManagerOperationException`.
3. If no record is found, return `None`.
4. If `decrypt` is `True`:
   1. For each key-value pair in the result's `secret` dict:
      1. Parse the crypto type and payload from the value string (`"{crypto_type}:{payload}"`).
      2. Obtain the decryption key: `secret_key = get_key(crypto_type)`.
      3. Decrypt by calling `crypto_util.decrypt(crypto_type, payload, secret_key.decryption_key)`.
         - On failure: raise `SecretManagerCryptoException`.
      4. Store the decrypted value in `raw_secret` under the same key.
   2. Set `secret` to `None` on the returned entry.
5. Else (`decrypt` is `False`):
   1. Replace every value in the result's `secret` dict with `"******"` (keys are preserved as-is).
   2. Set `raw_secret` to `None` on the returned entry.
6. Return the `Secret` entry.

---

### search_secrets

```python
async def search_secrets(criteria: SecretSearchCriteria, decrypt: bool = False) -> list[Secret]
```

#### implementation notes

1. If not initialized, raise `SecretManagerNotInitializedException`.
2. Build a SurrealQL `SELECT` query from `criteria` using `SecretSearchCriteria.to_query()`.
3. Execute the query against the `Secrets` collection.
   - On failure: raise `SecretManagerOperationException`.
4. If no results are found, return an empty list.
5. For each result, apply the same masking or decryption process as in `get_secret` (steps 4–5), passing through the `decrypt` flag.
6. Return the list of `Secret` entries.

---

### delete_secret

```python
async def delete_secret(secret_id: str) -> None
```

#### implementation notes

1. If not initialized, raise `SecretManagerNotInitializedException`.
2. Delete the entry using `DELETE Secrets:{secret_id} RETURN BEFORE`.
   - If the returned result is empty (no record was deleted): raise `SecretManagerSecretNotFoundException`.
   - On other failures: raise `SecretManagerOperationException`.

---

## Planned Improvements & Limitations

- Key rotation: when a key is rotated, all existing secrets encrypted with expiring key needs to be re-encrypted with the new key. This is not yet implemented.
- `SecretSearchCriteria.to_query()` currently supports only `SurrealDbRemoteProvider`. Other providers are not supported.
- `valid_until` expiry is not enforced automatically. Callers must check the field manually.
- The `secret.secret` field is replaced in full on update. There is currently no mechanism for updating individual keys within the dict without re-supplying the entire dict.
