# secretmanager

`gafs.dynamicaiagent.common.secretmanager` — Encrypted credential management component.

Provides a unified interface for storing, retrieving, and rotating encrypted secrets in
the `Secrets` SurrealDB collection. Secrets are encrypted with configurable cryptographic
algorithms before being persisted to the database.

---

## Overview

`SecretManager` is responsible for:

- **Key management** — registering, loading, and auto-generating cryptographic keys per `CryptoType`.
- **Secret CRUD** — creating, reading, updating, and deleting encrypted `Secret` entries.
- **Search** — querying secrets by name substring, description keywords, and date ranges.

---

## Initialization Sequence

`SecretManager` depends on `DatabaseManager`. Initialization must follow this
three-phase sequence together with `DatabaseManager`:

```python
import logging
from gafs.dynamicaiagent.common.databasemanager import DatabaseManager, DatabaseConnection
from gafs.dynamicaiagent.common.secretmanager import SecretManager
from gafs.dynamicaiagent.utils.cryptoutil import CryptoUtil
from gafs.dynamicaiagent.utils.databaseprovider import DatabaseProviderType

logger = logging.getLogger(__name__)

# Phase 1 — database-only initialization
config = DatabaseConnection()
config.id = "default"
config.name = "default"
config.database_type = DatabaseProviderType.SURREALDB_LOCAL
config.parameters = {"namespace": "my-ns", "database": "my-db", "storage_type": "mem"}

db_manager = DatabaseManager(logger)
await db_manager.initialize_default_connection(config)

# Phase 2 — SecretManager initialization (uses DatabaseManager)
secret_manager = SecretManager(logger)
secret_manager.initialize(db_manager, CryptoUtil(), config={})

# Phase 3 — complete DatabaseManager setup (injects SecretManager)
await db_manager.initialize(secret_manager)
```

After phase 2, all `SecretManager` methods are available.

### Key Loading Priority

During `initialize()`, cryptographic keys are loaded in the following order:

| Priority | Source | Description |
|---|---|---|
| A | `config["secret_keys"]` | Keys provided directly in the config dict. |
| B | `secret_keys.json` | Keys loaded from the application data folder. |
| C | Auto-generate | One key per `CryptoType` is generated and saved to `secret_keys.json`. |

The key file is stored at:
```
platformdirs.user_data_dir("Dynamic-AI-Agent", "GAFS") / "secret_keys.json"
```

---

## Model Classes

### `Secret`

Represents an encrypted credential entry stored in the `Secrets` collection.

| Field | Type | Description |
|---|---|---|
| `id` | `str \| None` | Record id (SurrealDB table prefix stripped automatically) |
| `name` | `str \| None` | Human-readable name for the secret |
| `secret` | `dict \| None` | Encrypted key-value pairs (persisted) |
| `raw_secret` | `dict \| None` | Plaintext key-value pairs (**transient — never persisted**) |
| `description` | `str \| None` | Optional description |
| `tags` | `list[str] \| None` | Optional tags for categorization |
| `created_at` | `datetime \| None` | Creation timestamp |
| `updated_at` | `datetime \| None` | Last update timestamp |
| `valid_until` | `datetime \| None` | Expiry timestamp |

```python
from gafs.dynamicaiagent.common.secretmanager import Secret

s = Secret()
s.name = "my-api-key"
s.raw_secret = {"api_key": "sk-abc123", "api_secret": "supersecret"}
s.description = "Production API credentials"
s.tags = ["production", "api"]
```

**Notes:**
- `raw_secret` is never included in `to_dict()` or `to_json()`.
- `id` is automatically stripped of the SurrealDB table prefix.
- Datetime fields accept `datetime`, ISO-format strings, or epoch integers.

### `SecretKey`

Value object representing a cryptographic key pair used for encryption/decryption.

| Field | Type | Description |
|---|---|---|
| `name` | `str \| None` | Matches `CryptoType.value` (e.g. `"aes-256-gcm"`) |
| `encryption_key` | `str \| None` | Base64-encoded encryption key |
| `decryption_key` | `str \| None` | Base64-encoded decryption key |

---

## Usage

### Create a Secret

```python
from gafs.dynamicaiagent.common.secretmanager import Secret

s = Secret()
s.name = "db-credentials"
s.raw_secret = {"username": "admin", "password": "s3cr3t"}

created = await secret_manager.create_secret(s)
print(created.id)  # "abc123xyz"
print(created.raw_secret)  # {"username": "admin", "password": "s3cr3t"}
```

### Retrieve a Secret (with decryption)

```python
secret = await secret_manager.get_secret("abc123xyz", decrypt=True)
print(secret.raw_secret)  # {"username": "admin", "password": "s3cr3t"}
```

### Search Secrets

```python
from gafs.dynamicaiagent.common.secretmanager import SecretSearchCriteria

criteria = SecretSearchCriteria(name="db-", limit=50)
results = await secret_manager.search_secrets(criteria)
for s in results:
    print(s.id, s.name)
```

### Update a Secret

```python
secret = await secret_manager.get_secret("abc123xyz", decrypt=True)
secret.raw_secret["password"] = "newpassword"
updated = await secret_manager.update_secret(secret)
```

### Delete a Secret

```python
await secret_manager.delete_secret("abc123xyz")
```

---

## Key Management

```python
from gafs.dynamicaiagent.utils.cryptoutil import CryptoType

# Generate a new AES-256-GCM key pair
key = await secret_manager.generate_key(CryptoType.AES_256_GCM)

# Add an existing key
from gafs.dynamicaiagent.common.secretmanager import SecretKey
sk = SecretKey()
sk.name = CryptoType.AES_256_GCM.value
sk.encryption_key = "<base64>"
sk.decryption_key = "<base64>"
secret_manager.add_key(sk)

# Retrieve a key
key = secret_manager.get_key(CryptoType.AES_256_GCM)
```

---

## Exception Classes

All exceptions inherit from `SecretManagerException` (→ `ApplicationException`).

| Exception | Raised When |
|---|---|
| `SecretManagerInitializationException` | `initialize()` fails to connect to the database |
| `SecretManagerNotInitializedException` | Any method called before `initialize()` |
| `SecretManagerInvalidSecretEntryException` | Missing required fields or duplicate key in `add_key()` |
| `SecretManagerKeyNotFoundException` | `get_key()` called for an unregistered `CryptoType` |
| `SecretManagerSecretNotFoundException` | `update_secret()` or `delete_secret()` for non-existent id |
| `SecretManagerOperationException` | Database operation failure (create/update/delete) |
| `SecretManagerCryptoException` | Encrypt or decrypt failure |

---

## Encrypted Value Format

Secret values are stored in the `secret` dict as:

```
"<crypto_type>:<encrypted_payload>"
```

Example for AES-256-GCM:
```json
{
  "api_key": "aes-256-gcm:BASE64_ENCODED_CIPHERTEXT"
}
```

---

## Building

Build the compiled extension module with Nuitka (run from `Python/`):

```bash
python gafs/dynamicaiagent/common/secretmanager/build_nuitka.py
```

Output is placed at `build/win_x64/gafs/dynamicaiagent/common/secretmanager.cp312-win_amd64.pyd`.
