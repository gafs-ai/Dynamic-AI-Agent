# SurrealDB Remote Provider Test Documentation

## 1. Test Target Classes, Methods, and Test Items

### 1.1 RemoteSurrealDbOptions (data class)

#### `to_dict(recursive: bool = False)`
- All fields are included in the dictionary
- Enum types are converted correctly
- With `recursive=True`, nested objects are also converted to dictionaries
- Parent class fields are included

#### `to_json()`
- Valid JSON string is produced
- Can be read with `json.loads()`
- Date and Enum types are serialized appropriately

#### `from_dict(cls, data: dict)`
- Valid data produces the correct object
- Invalid keys are ignored
- Automatic conversion from string to Enum type
- Parent class fields are set correctly

#### `from_json(cls, json_str: str)`
- Valid JSON string produces the correct object
- JSON with invalid keys does not raise; only valid fields are set
- Type conversion is applied correctly

#### `__repr__()`
- Returns a string
- Contains information useful for debugging

#### `__setattr__(name, value)`
- `ValueError` is raised when setting an undefined attribute
- Appropriate error when setting a value of wrong type
- Values of correct type are set successfully

#### Round-trip conversion
- `object -> dict -> object` preserves the original data
- `object -> json -> object` preserves the original data

---

### 1.2 TestRecord (test data class)

Data model used by tests. Represents test records stored in the database.

#### Fields
- `id`: Record ID (string, e.g. `"TestRecord:test_001"`)
- `name`: Record name (string)
- `description`: Description (string)
- `created_at`: Creation time (datetime)

#### `from_dict(cls, data: dict)`
- TestRecord instance can be created from a dictionary
- `id` field is set correctly
- `name` and `description` fields are set correctly
- `created_at` is converted to datetime

#### `__setattr__(name, value)`
- Only defined fields can be set
- `ValueError` when setting an invalid field
- Type validation is enforced

#### Purpose
- Pass to `query()` as `parse_class` to test dataclass parsing
- Used to validate structure of records returned from the database

---

### 1.3 SurrealDbRemoteProvider (provider implementation)

#### 1.3.1 initialize(options: RemoteSurrealDbOptions)

**Success cases**:
- Connection succeeds with valid configuration
- Status after connection is `DatabaseProviderStatus.AVAILABLE`
- Connection to the database is established
- WebSocket or HTTP connection (per config) is established successfully

**Error case: invalid endpoint**:
- `DatabaseProviderUnconnectableException` is raised
- Error message includes connection failure details
- Resources are cleaned up appropriately

**Error case: invalid credentials**:
- `DatabaseProviderAuthenticationException` is raised
- Error message includes authentication failure details
- Connection is established but authentication fails

#### 1.3.2 query(query: str, parse_class: type = None)

**Success: single document**:
- Document can be retrieved by existing single ID
- Result structure is `list[dict]`
- Data content is correct

**Success: multiple documents**:
- Multiple documents can be retrieved by valid IDs
- Result has expected count and structure
- Each document has correct ID and data

**Success: dataclass parsing**:
- With `parse_class`, results are converted to instances of that class
- Parsed objects have correct type and field values
- Date, Enum, etc. are converted correctly

**Edge case: non-existent document**:
- Non-existent ID returns empty list `[]`
- No exception is raised

**Edge case: multiple non-existent IDs**:
- Various non-existent ID patterns return empty list `[]`
- Behavior is consistent across patterns

**Error case: authentication**:
- Appropriate exception when provider has authentication failure
- No data is returned

#### 1.3.3 query_raw(query: str)

**Success**:
- Arbitrary SurrealQL query can be executed
- Result is returned in raw form (`list[dict]`)
- Result structure is as expected

**Error case: authentication**:
- Appropriate exception when provider has authentication failure
- Query is not executed

#### 1.3.4 close()

**Success**:
- `close()` runs successfully
- WebSocket connection is released appropriately
- No exception is raised
- Safe to call multiple times

#### 1.3.5 Connection management

**Timeout**:
- Appropriate exception on connection timeout
- Timeout setting works correctly
- Resources are released after timeout

**Reconnect**:
- Reconnection succeeds after connection is lost
- Queries work after reconnect
- Authentication is performed again on reconnect
- Appropriate exception when reconnect fails

---

## 2. Test Workflows

### 2.1 Data class test group (no dependencies, can run in isolation)

**Characteristics**:
- No database connection required
- No test data (only data classes are tested)
- No cleanup required

---

#### Test: `test_options_serialization`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. Create RemoteSurrealDbOptions instance
2. Set values on each field
3. Serialize with to_dict() → verify result
4. Serialize with to_json() → verify JSON validity
5. Deserialize with from_dict() → verify result
6. Deserialize with from_json() → verify result
7. Get string representation with __repr__() → verify result
8. Verify round-trip conversion
9. Verify parent class fields are included
```

**Dependencies**: None

---

#### Test: `test_options_invalid_json_keys`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. Create JSON string with invalid keys
2. Deserialize with from_json()
3. Confirm invalid keys are ignored
4. Confirm valid keys are set correctly
5. Confirm no exception is raised
```

**Dependencies**: None

---

#### Test: `test_options_invalid_attribute_validation`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. Create RemoteSurrealDbOptions instance
2. Try to set undefined attribute → expect ValueError
3. Try to set value of wrong type → expect appropriate error
4. Verify error message
```

**Dependencies**: None

---

### 2.2 Connection test group (requires config file and network)

**Characteristics**:
- Tests database connection
- No test data (only connection is tested)
- No cleanup required

---

#### Test: `test_initialize_with_valid_options`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. Load config from config fixture (secret_test_config_0.json)
2. Create RemoteSurrealDbOptions with valid_options fixture
3. Create SurrealDbRemoteProvider instance
4. Call initialize()
5. Confirm connection success
6. Confirm provider status is DatabaseProviderStatus.AVAILABLE
7. Confirm connection is established
8. Call close() for cleanup
```

**Dependencies**:
- Config file (`secret_test_config_0.json`)
- SurrealDB server running
- Network connectivity

---

#### Test: `test_initialize_with_invalid_endpoint`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. Create invalid endpoint config with invalid_endpoint_options fixture
2. Create SurrealDbRemoteProvider instance
3. Call initialize()
4. Confirm DatabaseProviderUnconnectableException is raised
5. Verify error message
```

**Dependencies**: None (tests network error)

---

#### Test: `test_initialize_with_invalid_credentials`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. Create invalid credentials config with invalid_credentials_options fixture
2. Create SurrealDbRemoteProvider instance
3. Call initialize()
4. Confirm DatabaseProviderAuthenticationException is raised
5. Verify error message
```

**Dependencies**:
- SurrealDB server running
- Network connectivity

---

### 2.3 Query test group (requires successful connection)

**Test data lifecycle**:
- **Setup**: `setup_test_database` fixture (module scope) creates `TestRecord:test_001`, `test_002`, `test_003` before tests
- **Execution**: Each test uses this data for query tests

**Notes**:
- Test data is shared across all tests (module scope)
- Modifying data in one test may affect others

---

#### Test: `test_query_with_valid_id`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. setup_test_database fixture prepares test data (TestRecord:test_001, test_002, test_003)
2. valid_options fixture creates config
3. Create SurrealDbRemoteProvider and call initialize()
4. Run query() with existing single ID (e.g. "SELECT * FROM TestRecord:test_001")
5. Confirm result is list[dict]
6. Verify data (name, description fields)
7. Call close() for cleanup
```

**Test data used**:
- `TestRecord:test_001` (name: "Test Record 1", description: "First test record")

**Dependencies**:
- `test_initialize_with_valid_options` succeeds
- Test data created by `setup_test_database` fixture

---

#### Test: `test_query_with_nonexistent_id`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. valid_options fixture creates config
2. Create SurrealDbRemoteProvider and call initialize()
3. Run query() with non-existent ID (e.g. "SELECT * FROM TestRecord:nonexistent")
4. Confirm empty list [] is returned
5. Confirm no exception is raised
6. Call close() for cleanup
```

**Test data used**: None (tests non-existent ID)

**Dependencies**:
- `test_initialize_with_valid_options` succeeds

---

#### Test: `test_query_with_multiple_nonexistent_ids`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. valid_options fixture creates config
2. Create SurrealDbRemoteProvider and call initialize()
3. Run query() with parameterized non-existent ID patterns
4. Confirm empty list [] for each pattern
5. Call close() for cleanup
```

**Test data used**: None (tests non-existent IDs)

**Dependencies**:
- `test_initialize_with_valid_options` succeeds

**Parameters**:
- `"SELECT * FROM TestRecord:non_existing_1;"`
- `"SELECT * FROM TestRecord:non_existing_2;"`

---

#### Test: `test_query_multiple_documents`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. setup_test_database fixture prepares test data
2. valid_options fixture creates config
3. Create SurrealDbRemoteProvider and call initialize()
4. Run query() with multi-record query (e.g. "SELECT * FROM TestRecord")
5. Confirm result is list[dict] with 3 elements
6. Verify ID, name, description of each document
7. Confirm expected count (3) is returned
8. Call close() for cleanup
```

**Test data used**:
- `TestRecord:test_001`, `TestRecord:test_002`, `TestRecord:test_003`

**Dependencies**:
- `test_initialize_with_valid_options` succeeds
- Multiple test records from `setup_test_database` fixture

---

#### Test: `test_query_with_dataclass_parsing`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. setup_test_database fixture prepares test data
2. valid_options fixture creates config
3. Create SurrealDbRemoteProvider and call initialize()
4. Import TestRecord (data_models.py)
5. Run query("SELECT * FROM TestRecord:test_001", parse_class=TestRecord)
6. Confirm result is TestRecord instance
7. Verify field types and values (id, name, description, created_at)
8. Confirm created_at is converted to datetime
9. Call close() for cleanup
```

**Test data used**:
- `TestRecord:test_001` (parsed as TestRecord)

**Dependencies**:
- `test_initialize_with_valid_options` succeeds
- TestRecord defined in data_models.py
- Test data from `setup_test_database` fixture

---

#### Test: `test_query_with_authentication_error`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. Try connection with invalid credentials (catch exception and continue)
2. Or implement a way to clear auth after connection
3. Run query()
4. Confirm appropriate exception is raised
5. Confirm no data is returned
```

**Dependencies**:
- Ability to run query in authentication-failure state

---

### 2.4 Raw query test group (requires successful connection)

**Test data lifecycle**:
- Same `setup_test_database` fixture as query test group (2.3)
- Test data is created during setup

---

#### Test: `test_query_raw`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. setup_test_database fixture prepares test data
2. valid_options fixture creates config
3. Create SurrealDbRemoteProvider and call initialize()
4. Run query_raw() with SurrealQL (e.g. "SELECT * FROM TestRecord WHERE name = 'Test Record 1'")
5. Confirm result is list[dict]
6. Verify result structure and fields
7. Call close() for cleanup
```

**Test data used**:
- `TestRecord:test_001` etc.

**Dependencies**:
- `test_initialize_with_valid_options` succeeds
- Test data from `setup_test_database` fixture

---

#### Test: `test_query_raw_with_authentication_error`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. Try connection with invalid credentials (catch exception and continue)
2. Or implement a way to clear auth after connection
3. Run query_raw()
4. Confirm appropriate exception is raised
5. Confirm query is not executed
```

**Dependencies**:
- Ability to run raw query in authentication-failure state

---

### 2.5 Connection management test group (requires successful connection)

**Characteristics**:
- Tests connection lifecycle
- No test data (only connection management)
- No cleanup required

---

#### Test: `test_provider_close`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. valid_options fixture creates config
2. Create SurrealDbRemoteProvider and call initialize()
3. Call close()
4. Confirm no exception is raised
5. Confirm resources are released
6. Optionally confirm multiple close() calls are safe
```

**Dependencies**:
- `test_initialize_with_valid_options` succeeds

---

#### Test: `test_connection_timeout`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. Create RemoteSurrealDbOptions with short timeout
2. Create SurrealDbRemoteProvider and call initialize()
3. Run an operation that takes time
4. Confirm timeout exception is raised
5. Confirm resources are released
```

**Dependencies**:
- Timeout configuration is implemented
- Operation that triggers timeout is defined

---

#### Test: `test_connection_reconnect`
**Implementation file**: `test_surrealdb_remote_provider.py`

**Workflow**:
```
1. valid_options fixture creates config
2. Create SurrealDbRemoteProvider and call initialize()
3. Run a query to confirm connection
4. Intentionally disconnect
5. Trigger reconnect
6. Confirm reconnect succeeds
7. Confirm query works after reconnect
8. Confirm authentication is performed again
9. Call close() for cleanup
```

**Dependencies**:
- `test_initialize_with_valid_options` succeeds
- Reconnect logic is implemented
- Way to disconnect is implemented

---

## 3. Prerequisites and Run Command

### 3.1 Prerequisites

#### 3.1.1 Required libraries

```bash
# pytest and pytest-asyncio are required
pytest>=8.2
pytest-asyncio>=1.3.0
```

**Install**:
```bash
# With .venv
.venv\Scripts\python.exe -m pip install pytest pytest-asyncio

# Global
pip install pytest pytest-asyncio
```

#### 3.1.2 Config file

**Path**: `Python/gafs/dynamicaiagent/utils/databaseprovider/test/secret_test_config_0.json`

**Contents**:
```json
{
  "endpoint": "wss://your-surrealdb-endpoint.com/rpc",
  "namespace": "your-namespace",
  "database": "your-database",
  "username": "your-username",
  "password": "your-password"
}
```

**Notes**:
- Filename must be exactly `secret_test_config_0.json`
- Ensure valid JSON
- Endpoint must be a WebSocket URL starting with `wss://`

#### 3.1.3 pytest config

**Path**: `Python/pytest.ini`

**Contents**:
```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

#### 3.1.4 Test data class

Defines the data class used by tests. It must have an `id` field. Test data is created inside the `setup_test_database` fixture, so no separate script needs to be run.

**Path**: `Python/gafs/dynamicaiagent/utils/databaseprovider/test/data_models.py`

**Contents summary**:
- `TestRecord` class with fields `id`, `name`, `description`, `created_at`
- Attribute validation via `__setattr__`
- Construction from dict via `from_dict(cls, data)`

#### 3.1.5 Run command

```bash
cd Python
pytest gafs/dynamicaiagent/utils/databaseprovider/test/test_surrealdb_remote_provider.py -v
```

## Important notes

### Test execution order

- With `scope="module"` fixtures, test data is shared across all tests
- Test order is not guaranteed; avoid relying on shared state between tests
- If a test modifies data, restore it inside the test or use isolated test data
