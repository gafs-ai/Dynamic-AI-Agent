# Secret Manager Test Documentation

## 1. Test Target Classes, Methods, and Test Items

### 1.1 Secret (entity class)

Basic tests for the Secret entity (similar in scope to DatabaseProvider data class tests).

#### `__init__`
- All fields are initialized to None

#### `__setattr__(name, value)`
- Type validation for id (str or RecordID), name (str), secret (dict), description (str)
- Datetime fields (created_at, updated_at, valid_until) accept datetime, ISO string, or epoch int
- ValueError raised for invalid types

#### `to_dict(recursive, exclude_id)`
- Returns dictionary representation with correct fields
- recursive=True converts datetime to ISO strings
- exclude_id=True omits id field

#### `to_json(exclude_id)`
- Produces valid JSON string

#### `from_dict(cls, data)`
- Creates Secret from dictionary
- Invalid keys are ignored

#### `from_json(cls, json_str)`
- Creates Secret from JSON string
- ValueError when JSON is not a dict

#### Round-trip
- `object -> dict -> object` preserves data
- `object -> json -> object` preserves data

---

### 1.2 SecretSearchCriteria (search criteria class)

#### `to_query(database_provider, collection_name)`
- Correctly converts criteria to SurrealQL query string
- NotImplementedError when provider is not SurrealDbRemoteProvider
- Empty criteria yields `WHERE true`
- Each criterion (name, description_keywords, created_at_*, updated_at_*, valid_until_*, limit) is reflected in query when set

---

### 1.3 ISecretManager / SecretManager

#### `initialize(database_manager, crypto_util, keys)`
- **Success**: Initialization succeeds and returns True when default DatabaseProvider exists
- **Failure**: Returns False when default DatabaseProvider is not set

#### `add_symmetric_key(crypto_type, key)`
- **Success (SymmetricCryptoType.AES_256_GCM)**: Registers when not yet registered; value can be retrieved via `get_symmetric_key`
- **Failure (duplicate)**: Returns False when already registered; `get_symmetric_key` returns unchanged value

#### `get_symmetric_key(crypto_type)`
- Returns None (or equivalent) before any key is added (SecretManager holds keys in memory; "None" means KeyError when no key)
- Returns the key value after `add_symmetric_key` registers it

#### `generate_symmetric_key(crypto_type)`
- **Success**: Generates key for SymmetricCryptoType.AES_256_GCM
- **Failure**: ValueError when crypto_util is not initialized

#### `create_secret(secret)`
- **Success (with id)**: Creates secret with specified id; same record can be retrieved via `get_secret`
- **Success (without id)**: Creates secret with auto-generated id; same record can be retrieved via `get_secret`
- **Failure (duplicate id)**: Error raised when creating with an existing id

#### `update_secret(secret)`
- **Success**: Update succeeds; updated content is retrievable via `get_secret`
- **Failure**: Error raised when updating non-existent secret

#### `get_secret(secret_id)`
- **Success**: Returns secret with decrypted values when it exists
- **Not found**: Returns None when secret does not exist

#### `search_secrets(secret_search_criteria)`
- **Diverse criteria**: Each criterion value is tested at least once; at least one test uses a criterion combined with at least one other criterion
- **Results found**: Returns list of secrets
- **No results**: Returns empty list

#### `delete_secret(secret_id)`
- **Success**: Deletion succeeds; `get_secret` returns None afterwards
- **Failure**: Error raised when deleting non-existent id

---

## 2. Test Workflows

### 2.1 Data class / criteria test group (no database)

**Characteristics**:
- No database connection required
- No test data creation or cleanup

---

#### Test: `test_secret_serialization`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. Create Secret instance and set fields
2. to_dict() -> verify result
3. to_json() -> verify valid JSON
4. from_dict() -> verify round-trip
5. from_json() -> verify round-trip
```

---

#### Test: `test_secret_validation`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. Create Secret instance
2. Set valid values -> verify accepted
3. Set invalid type for a field -> expect ValueError
4. from_json with non-dict -> expect ValueError
```

---

#### Test: `test_secret_search_criteria_to_query`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. Create SecretSearchCriteria with various combinations
2. Create SurrealDbRemoteProvider (or mock) for to_query
3. Call to_query() -> verify SurrealQL string
4. Test empty criteria -> WHERE true
5. Test each criterion (name, description_keywords, dates, limit)
6. Test combined criteria
7. Non-SurrealDbRemoteProvider -> expect NotImplementedError
```

---

#### Test: `test_add_symmetric_key_success`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. Create SecretManager (no DB)
2. add_symmetric_key(AES_256_GCM, "key1") -> assert True
3. get_symmetric_key(AES_256_GCM) -> assert "key1"
```

---

#### Test: `test_add_symmetric_key_duplicate`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. Create SecretManager (no DB)
2. add_symmetric_key(AES_256_GCM, "key1")
3. add_symmetric_key(AES_256_GCM, "key2") -> assert False
4. get_symmetric_key(AES_256_GCM) -> assert "key1" (unchanged)
```

---

#### Test: `test_get_symmetric_key_missing`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. Create SecretManager (no DB)
2. get_symmetric_key(AES_256_GCM) -> expect KeyError
```

---

#### Test: `test_generate_symmetric_key_success`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. Create SecretManager, set _crypto_util = SymmetricCryptoUtil()
2. generate_symmetric_key(AES_256_GCM) -> assert non-empty string
3. get_symmetric_key(AES_256_GCM) -> assert returns the generated key
```

---

#### Test: `test_generate_symmetric_key_without_crypto_util`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. Create SecretManager (no _crypto_util)
2. generate_symmetric_key(AES_256_GCM) -> expect ValueError
```

---

### 2.2 Database test group (requires config and SurrealDB)

**Test data lifecycle**:
- **Per-test**: Each test creates the secrets it needs.
- **Cleanup**: Each test deletes all secrets it created in a `finally` block before exiting.
- No shared persistent data; on success, no created secrets remain.

---

#### Fixture: `initialized_secret_manager`
- Loads config from `secret_test_config_0.json`
- Creates DatabaseManager, adds provider, sets default
- Creates SecretManager, calls initialize
- Yields SecretManager
- No per-fixture cleanup of secrets (each test manages its own)

---

#### Test: `test_initialize_success`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. Create DatabaseManager with provider (default set)
2. Create SecretManager, initialize(db_manager, crypto_util, keys)
3. Assert returns True
```

**Dependencies**: Config file, SurrealDB

---

#### Test: `test_initialize_failure_no_default_provider`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. Create DatabaseManager without default provider
2. Create SecretManager, initialize(...)
3. Assert returns False
```

**Dependencies**: None (no DB needed)

---

#### Test: `test_create_secret_with_id`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. initialized_secret_manager fixture
2. Create Secret with id="test_create_with_id_001", name, description, secret
3. create_secret(secret)
4. get_secret("test_create_with_id_001") -> assert matches
5. finally: delete_secret("test_create_with_id_001")
```

---

#### Test: `test_create_secret_without_id`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. initialized_secret_manager fixture
2. Create Secret without id
3. created = create_secret(secret)
4. Assert created.id is not None
5. get_secret(created.id) -> assert matches
6. finally: delete_secret(created.id)
```

---

#### Test: `test_create_secret_duplicate_id`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. initialized_secret_manager fixture
2. Create and create_secret with id="test_dup_001"
3. Create another Secret with same id
4. create_secret(second) -> expect error (DatabaseQueryErrorException or similar)
5. finally: delete_secret("test_dup_001")
```

---

#### Test: `test_update_secret_success`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. initialized_secret_manager fixture
2. Create secret with id="test_update_001", create_secret
3. Update description, update_secret
4. get_secret -> assert updated description
5. finally: delete_secret("test_update_001")
```

---

#### Test: `test_update_secret_not_found`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. initialized_secret_manager fixture
2. Create Secret with id="test_update_nonexistent_001" (do NOT create in DB)
3. update_secret(secret) -> expect DatabaseRecordNotFoundException
```

---

#### Test: `test_get_secret_success`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. initialized_secret_manager fixture
2. Create secret, create_secret
3. get_secret(id) -> assert returns secret with decrypted values
4. finally: delete_secret(id)
```

---

#### Test: `test_get_secret_not_found`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. initialized_secret_manager fixture
2. get_secret("nonexistent_secret_id_999") -> assert None
```

---

#### Test: `test_search_secrets_*` (multiple tests for diverse criteria)
**File**: `test_secret_manager.py`

**Workflow** (each test follows this pattern):
```
1. initialized_secret_manager fixture
2. Create 2-3 test secrets with distinct name, description
3. Build SecretSearchCriteria (single + combined criteria)
4. search_secrets(criteria) -> assert list
5. Assert result count/content as expected
6. finally: delete all created secrets
```

**Diverse criteria coverage**:
- `test_search_secrets_by_name`: name only
- `test_search_secrets_by_description_keywords`: description_keywords only (single and multiple)
- `test_search_secrets_by_limit`: limit
- `test_search_secrets_combined`: name + description_keywords (or name + limit)
- `test_search_secrets_empty_result`: criteria matching nothing -> empty list

---

#### Test: `test_delete_secret_success`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. initialized_secret_manager fixture
2. Create secret, create_secret
3. delete_secret(id) -> assert True
4. get_secret(id) -> assert None
```

---

#### Test: `test_delete_secret_not_found`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. initialized_secret_manager fixture
2. delete_secret("nonexistent_id_999") -> expect DatabaseRecordNotFoundException
```

---

#### Test: `test_create_secret_without_initialization`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. Create SecretManager (no initialize)
2. Create Secret
3. create_secret(secret) -> expect ValueError
```

---

#### Test: `test_get_secret_without_initialization`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. Create SecretManager (no initialize)
2. get_secret("any_id") -> expect ValueError
```

---

#### Test: `test_delete_secret_without_initialization`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. Create SecretManager (no initialize)
2. delete_secret("any_id") -> expect ValueError
```

---

#### Test: `test_search_secrets_without_initialization`
**File**: `test_secret_manager.py`

**Workflow**:
```
1. Create SecretManager (no initialize)
2. search_secrets(SecretSearchCriteria()) -> expect ValueError
```

---

## 3. Prerequisites and Run Command

### 3.1 Prerequisites

#### Required libraries
```bash
pytest>=8.2
pytest-asyncio>=1.3.0
```

#### Config file
**Path**: `Python/gafs/dynamicaiagent/utils/databaseprovider/test/secret_test_config_0.json`

**Contents** (example):
```json
{
  "endpoint": "wss://your-surrealdb-endpoint.com/rpc",
  "namespace": "your-namespace",
  "database": "your-database",
  "username": "your-username",
  "password": "your-password"
}
```

#### pytest config
**Path**: `Python/pytest.ini`

```ini
[pytest]
pythonpath = .
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

### 3.2 Run command

```bash
cd Python
pytest gafs/dynamicaiagent/common/secretmanager/test/test_secret_manager.py -v
```

### 3.3 Run build tests (after Nuitka build)

```bash
cd Python
pytest gafs/dynamicaiagent/common/secretmanager/test/test_build_secret_manager.py -v
```
