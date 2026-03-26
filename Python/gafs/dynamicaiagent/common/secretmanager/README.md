# secretmanager

Secret manager component for managing symmetric keys and persisting secret entities in the database.

## Structure of the Component

### Folder

```
secretmanager/
├── __init__.py
├── i_secret_manager.py
├── secret_manager.py
├── secret.py
├── README.md
└── requirements.txt
```

### File

| File | Description |
|------|-------------|
| `i_secret_manager.py` | Interface for secret manager (`ISecretManager`). |
| `secret_manager.py` | Implementation of secret manager (`SecretManager`). |
| `secret.py` | Secret entity used to store secret values (`Secret`). |

### Class (Public)

| Class | File | Description |
|-------|------|-------------|
| `ISecretManager` | `i_secret_manager.py` | Abstract interface for secret manager. |
| `SecretManager` | `secret_manager.py` | Secret manager implementation (keys, encryption, CRUD). |
| `Secret` | `secret.py` | Dataclass entity for secret key-value pairs and metadata. |

## List of Methods / Variables (Public)

### ISecretManager

| Method / Variable | Description |
|-------------------|-------------|
| `initialize(database_manager, crypto_util, keys) -> bool` | Initialize with database manager, crypto util and key mapping. |
| `add_symmetric_key(crypto_type, key) -> bool` | Register a symmetric key for the given crypto type. |
| `get_symmetric_key(crypto_type) -> str` | Return the symmetric key for the given crypto type. |
| `generate_symmetric_key(crypto_type) -> str` | Generate and register a symmetric key for the given crypto type. |
| `create_secret(secret) -> Secret` (async) | Create a new secret (encrypted and persisted). |
| `update_secret(secret) -> Secret` (async) | Update an existing secret. |
| `get_secret(secret_id) -> Secret \| None` (async) | Get a secret by id (decrypted). Returns `None` if not found. |
| `delete_secret(secret_id) -> bool` (async) | Delete a secret by id. |

### SecretManager

| Method / Variable | Description |
|-------------------|-------------|
| `DEFAULT_CRYPTO_TYPE` | Class constant: default symmetric crypto type (e.g. AES_256_GCM). |
| `__init__(logger)` | Create an instance with a logger. |
| `initialize(database_manager, crypto_util, keys) -> bool` | Initialize with database manager, crypto util and key mapping. |
| `add_symmetric_key(crypto_type, key) -> bool` | Register a symmetric key for the given crypto type. |
| `get_symmetric_key(crypto_type) -> str` | Return the symmetric key for the given crypto type. |
| `generate_symmetric_key(crypto_type) -> str` | Generate and register a symmetric key for the given crypto type. |
| `create_secret(secret) -> Secret` (async) | Create a new secret (encrypted and persisted). |
| `update_secret(secret) -> Secret` (async) | Update an existing secret. |
| `get_secret(secret_id) -> Secret \| None` (async) | Get a secret by id (decrypted). Returns `None` if not found. |
| `delete_secret(secret_id) -> bool` (async) | Delete a secret by id. |

### Secret

| Method / Variable | Description |
|-------------------|-------------|
| `id` | Optional identifier (without `secret:` prefix). |
| `name` | Optional name. |
| `secret` | Dictionary of key-value pairs (`raw_*` for plain text, `encrypted_*` for encrypted). |
| `description` | Optional description. |
| `created_at` | Creation timestamp. |
| `updated_at` | Last update timestamp. |
| `valid_until` | Optional validity end timestamp. |
| `from_json(json_str)` | Parse JSON string into a `Secret` instance. |
| `to_json()` | Serialize instance to JSON string. |

## Dependencies & Libraries

No external serialization libraries are used.

This component also depends on other packages within the project (e.g. `gafs.dynamicaiagent.common.databasemanager`, `gafs.dynamicaiagent.utils.databaseprovider`, `gafs.dynamicaiagent.utils.symmetriccryptoutil`). Install and satisfy their requirements when using this component.
