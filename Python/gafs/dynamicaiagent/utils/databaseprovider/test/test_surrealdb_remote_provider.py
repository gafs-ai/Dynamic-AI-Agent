"""Pytest-based tests for SurrealDbRemoteProvider.

This module contains pytest tests for the SurrealDB remote provider implementation.
Tests cover normal operations, error handling, and edge cases.

Requirements:
    - pytest
    - pytest-asyncio

Run with:
    pytest test_surrealdb_remote_provider_pytest.py -v
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any

import pytest

# Ensure that the `Python` source folder is on sys.path
PYTHON_SRC: Path = Path(__file__).resolve().parents[5]
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from gafs.dynamicaiagent.utils.databaseprovider.surrealdb_remote_provider import (  # noqa: E402
    SurrealDbRemoteProvider,
    RemoteSurrealDbOptions,
)
from gafs.dynamicaiagent.utils.databaseprovider.i_database_provider import (  # noqa: E402
    DatabaseType,
)
from gafs.dynamicaiagent.utils.databaseprovider.exceptions.database_provider_initialization_exception import (  # noqa: E402,E501
    DatabaseProviderUnconnectableException,
    DatabaseProviderAuthenticationException,
)
from gafs.dynamicaiagent.utils.databaseprovider.exceptions.database_operation_exception import (  # noqa: E402,E501
    DatabaseDisconnectedException,
    DatabaseQueryErrorException,
)
from gafs.dynamicaiagent.utils.databaseprovider.test.data_models import (  # noqa: E402
    TestRecord,
)


# ==================== Fixtures ====================

@pytest.fixture(scope="module")
def logger() -> logging.Logger:
    """Create a logger for tests."""
    test_logger = logging.getLogger("surrealdb_remote_provider_pytest")
    test_logger.setLevel(logging.DEBUG)
    
    if not test_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        test_logger.addHandler(handler)
    
    return test_logger


@pytest.fixture(scope="module")
def config() -> dict[str, Any]:
    """Load test configuration from JSON file."""
    config_path = Path(__file__).parent / "secret_test_config_0.json"
    
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def valid_options(config: dict[str, Any]) -> RemoteSurrealDbOptions:
    """Create valid RemoteSurrealDbOptions from config."""
    options = RemoteSurrealDbOptions()
    options.database_type = DatabaseType.SURREALDB_REMOTE
    options.database_name = config["database"]
    options.endpoint = config["endpoint"]
    options.namespace = config["namespace"]
    options.database = config["database"]
    options.username = config["username"]
    options.password = config["password"]
    return options


@pytest.fixture
def invalid_endpoint_options(config: dict[str, Any]) -> RemoteSurrealDbOptions:
    """Create RemoteSurrealDbOptions with invalid endpoint."""
    options = RemoteSurrealDbOptions()
    options.database_type = DatabaseType.SURREALDB_REMOTE
    options.database_name = config["database"]
    options.endpoint = "wss://invalid-endpoint-for-testing.invalid/rpc"
    options.namespace = config["namespace"]
    options.database = config["database"]
    options.username = config["username"]
    options.password = config["password"]
    return options


@pytest.fixture
def invalid_credentials_options(config: dict[str, Any]) -> RemoteSurrealDbOptions:
    """Create RemoteSurrealDbOptions with invalid credentials."""
    options = RemoteSurrealDbOptions()
    options.database_type = DatabaseType.SURREALDB_REMOTE
    options.database_name = config["database"]
    options.endpoint = config["endpoint"]
    options.namespace = config["namespace"]
    options.database = config["database"]
    options.username = config["username"]
    options.password = "invalid-password-for-testing"
    return options


@pytest.fixture
async def setup_test_database(
    logger: logging.Logger,
    config: dict[str, Any],
) -> None:
    """Setup test database with TestRecord data and cleanup after tests."""
    options = RemoteSurrealDbOptions()
    options.database_type = DatabaseType.SURREALDB_REMOTE
    options.database_name = config["database"]
    options.endpoint = config["endpoint"]
    options.namespace = config["namespace"]
    options.database = config["database"]
    options.username = config["username"]
    options.password = config["password"]

    provider = SurrealDbRemoteProvider(logger)
    await provider.initialize(options)

    try:
        test_records = [
            ("TestRecord:test_001", "Test Record 1", "First test record"),
            ("TestRecord:test_002", "Test Record 2", "Second test record"),
            ("TestRecord:test_003", "Test Record 3", "Third test record"),
        ]

        for record_id, name, description in test_records:
            query = f"""
                CREATE {record_id} SET
                    name = "{name}",
                    description = "{description}",
                    created_at = time::now()
            """
            await provider.query_raw(query)

        yield

        await provider.query_raw("DELETE FROM TestRecord")

    finally:
        await provider.close()


# ==================== Tests ====================

@pytest.mark.asyncio
async def test_initialize_with_valid_options(
    logger: logging.Logger,
    valid_options: RemoteSurrealDbOptions
) -> None:
    """Test initialization with valid configuration.
    
    Verifies that:
    - Provider can connect to the database
    - Authentication succeeds
    - initialize() returns True
    """
    provider = SurrealDbRemoteProvider(logger)
    
    try:
        result = await provider.initialize(valid_options)
        
        assert result is True, "initialize() should return True with valid options"
        
        logger.info("Successfully initialized with valid options")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_initialize_with_invalid_endpoint(
    logger: logging.Logger,
    invalid_endpoint_options: RemoteSurrealDbOptions
) -> None:
    """Test initialization with invalid endpoint.
    
    Verifies that:
    - DatabaseProviderUnconnectableException is raised
    - Error message contains the invalid endpoint
    """
    provider = SurrealDbRemoteProvider(logger)
    
    try:
        with pytest.raises(DatabaseProviderUnconnectableException) as exc_info:
            await provider.initialize(invalid_endpoint_options)
        
        # Verify error message contains the endpoint
        assert "invalid-endpoint-for-testing.invalid" in str(exc_info.value)
        
        logger.info("Correctly raised DatabaseProviderUnconnectableException for invalid endpoint")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_initialize_with_invalid_credentials(
    logger: logging.Logger,
    invalid_credentials_options: RemoteSurrealDbOptions
) -> None:
    """Test initialization with invalid credentials.
    
    Verifies that:
    - DatabaseProviderAuthenticationException is raised
    - Error message indicates authentication failure
    """
    provider = SurrealDbRemoteProvider(logger)
    
    try:
        with pytest.raises(DatabaseProviderAuthenticationException) as exc_info:
            await provider.initialize(invalid_credentials_options)
        
        # Verify error message mentions authentication
        error_message = str(exc_info.value)
        assert "authenticate" in error_message.lower()
        
        logger.info("Correctly raised DatabaseProviderAuthenticationException for invalid credentials")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_query_with_valid_id(
    logger: logging.Logger,
    valid_options: RemoteSurrealDbOptions,
    setup_test_database: None,
) -> None:
    """Test query execution with a valid ID.
    
    Verifies that:
    - Query can be executed without errors
    - Result is returned (raw list from query_raw)
    """
    provider = SurrealDbRemoteProvider(logger)

    try:
        initialized = await provider.initialize(valid_options)
        assert initialized is True, "Provider should be initialized"

        result = await provider.query_raw("SELECT * FROM TestRecord:test_001")

        assert result is not None, "Result should not be None"
        record = None
        if isinstance(result, list) and len(result) >= 1:
            first = result[0]
            if isinstance(first, dict):
                record = first
            elif isinstance(first, list) and len(first) >= 1:
                record = first[0] if isinstance(first[0], dict) else first
            else:
                record = first
        if record is not None:
            assert "name" in record or "id" in record, "Record should have name or id"
        logger.info(f"Query executed successfully, result: {result}")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_query_with_nonexistent_id(
    logger: logging.Logger,
    valid_options: RemoteSurrealDbOptions,
) -> None:
    """Test query execution with a non-existent ID.
    
    Verifies that:
    - Query executes without errors
    - Result is empty (empty list or None)
    """
    provider = SurrealDbRemoteProvider(logger)

    try:
        initialized = await provider.initialize(valid_options)
        assert initialized is True, "Provider should be initialized"

        result = await provider.query_raw(
            "SELECT * FROM TestRecord:nonexistent_id_for_testing;"
        )

        if result is None:
            pass
        elif isinstance(result, list):
            assert len(result) == 0, "Result should be empty for non-existent ID"
        else:
            assert result == [] or result is None, "Result should be empty"

        logger.info("Query with non-existent ID correctly returned empty result")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_query_raw(
    logger: logging.Logger,
    valid_options: RemoteSurrealDbOptions,
    setup_test_database: None,
) -> None:
    """Test raw query execution.
    
    Verifies that:
    - query_raw() can be executed
    - Returns raw result from database
    """
    provider = SurrealDbRemoteProvider(logger)

    try:
        initialized = await provider.initialize(valid_options)
        assert initialized is True, "Provider should be initialized"

        result = await provider.query_raw(
            "SELECT * FROM TestRecord WHERE name = 'Test Record 1'"
        )

        assert result is not None, "Result should not be None"
        logger.info(f"Raw query executed successfully, result type: {type(result)}")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_provider_close(
    logger: logging.Logger,
    valid_options: RemoteSurrealDbOptions
) -> None:
    """Test provider close functionality.
    
    Verifies that:
    - Provider can be closed without errors
    - Close can be called multiple times safely
    """
    provider = SurrealDbRemoteProvider(logger)
    
    # Initialize provider
    initialized = await provider.initialize(valid_options)
    assert initialized is True, "Provider should be initialized"
    
    # Close provider
    await provider.close()
    
    # Verify close can be called multiple times
    await provider.close()
    
    logger.info("Provider closed successfully")


@pytest.mark.asyncio
async def test_options_serialization(valid_options: RemoteSurrealDbOptions) -> None:
    """Test RemoteSurrealDbOptions serialization/deserialization.
    
    Verifies that:
    - to_dict() produces valid dictionary
    - to_json() produces valid JSON string
    - from_dict() reconstructs object correctly
    - from_json() reconstructs object correctly
    """
    # Test to_dict
    options_dict = valid_options.to_dict(recursive=True)
    assert isinstance(options_dict, dict)
    assert "endpoint" in options_dict
    assert "namespace" in options_dict
    assert "database" in options_dict
    assert options_dict["database_type"] == "surrealdb-remote"
    
    # Test to_json
    json_str = valid_options.to_json()
    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    
    # Test from_dict
    reconstructed_from_dict = RemoteSurrealDbOptions.from_dict(options_dict)
    assert reconstructed_from_dict.endpoint == valid_options.endpoint
    assert reconstructed_from_dict.namespace == valid_options.namespace
    assert reconstructed_from_dict.database == valid_options.database
    assert reconstructed_from_dict.database_type == DatabaseType.SURREALDB_REMOTE
    
    # Test from_json
    reconstructed_from_json = RemoteSurrealDbOptions.from_json(json_str)
    assert reconstructed_from_json.endpoint == valid_options.endpoint
    assert reconstructed_from_json.namespace == valid_options.namespace
    assert reconstructed_from_json.database == valid_options.database
    assert reconstructed_from_json.database_type == DatabaseType.SURREALDB_REMOTE


@pytest.mark.asyncio
async def test_options_invalid_json_keys(valid_options: RemoteSurrealDbOptions) -> None:
    """Test from_json with invalid (extra) keys - they should be ignored."""
    json_with_extra = valid_options.to_json()
    parsed = json.loads(json_with_extra)
    parsed["unknown_key"] = "should_be_ignored"
    parsed["another_invalid"] = 123
    json_str = json.dumps(parsed)

    options = RemoteSurrealDbOptions.from_json(json_str)

    assert options.endpoint == valid_options.endpoint
    assert options.namespace == valid_options.namespace
    assert getattr(options, "endpoint", None) == valid_options.endpoint
    assert not hasattr(options, "unknown_key")


@pytest.mark.asyncio
async def test_options_invalid_attribute_validation() -> None:
    """Test __setattr__ raises ValueError for invalid attribute or wrong type."""
    options = RemoteSurrealDbOptions()

    with pytest.raises(ValueError):
        setattr(options, "invalid_attribute", "value")

    options.endpoint = "https://valid.endpoint"
    assert options.endpoint == "https://valid.endpoint"

    with pytest.raises(ValueError):
        options.endpoint = 123


# ==================== Parametrized Tests ====================

@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected_result", [
    ("SELECT * FROM TestRecord:non_existing_1;", None),
    ("SELECT * FROM TestRecord:non_existing_2;", None),
])
async def test_query_with_multiple_nonexistent_ids(
    logger: logging.Logger,
    valid_options: RemoteSurrealDbOptions,
    query: str,
    expected_result: Any,
) -> None:
    """Parametrized test for multiple non-existent IDs."""
    provider = SurrealDbRemoteProvider(logger)

    try:
        initialized = await provider.initialize(valid_options)
        assert initialized is True, "Provider should be initialized"

        result = await provider.query_raw(query)

        if expected_result is None:
            assert result is None or (isinstance(result, list) and len(result) == 0)
        else:
            assert result == expected_result

        logger.info(f"Parametrized test passed for query: {query}")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_query_multiple_documents(
    logger: logging.Logger,
    valid_options: RemoteSurrealDbOptions,
    setup_test_database: None,
) -> None:
    """Test query returns multiple documents."""
    provider = SurrealDbRemoteProvider(logger)

    try:
        initialized = await provider.initialize(valid_options)
        assert initialized is True

        result = await provider.query_raw("SELECT * FROM TestRecord")

        assert result is not None
        if isinstance(result, list):
            flat = result
            if result and isinstance(result[0], list):
                flat = [item for sub in result for item in sub]
            else:
                flat = result
            assert len(flat) >= 3, (
                f"Should have at least 3 TestRecord documents, got {len(flat)}"
            )
            logger.info(f"Multiple documents query returned {len(flat)} documents")
        else:
            logger.info(f"Multiple documents query returned: {result}")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_query_with_dataclass_parsing(
    logger: logging.Logger,
    valid_options: RemoteSurrealDbOptions,
    setup_test_database: None,
) -> None:
    """Test query with model parses result into TestRecord."""
    provider = SurrealDbRemoteProvider(logger)

    try:
        initialized = await provider.initialize(valid_options)
        assert initialized is True

        result = await provider.query(
            "SELECT * FROM TestRecord:test_001",
            model=TestRecord,
            many=False,
        )

        assert result is not None
        assert isinstance(result, TestRecord)
        assert result.name is not None
        assert "Test Record" in str(result.name) or result.name == "Test Record 1"
        logger.info(f"Parsed result: {result}")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_query_with_authentication_error(
    logger: logging.Logger,
    invalid_credentials_options: RemoteSurrealDbOptions,
) -> None:
    """Test query fails when provider is not initialized (auth failed)."""
    provider = SurrealDbRemoteProvider(logger)

    try:
        with pytest.raises(DatabaseProviderAuthenticationException):
            await provider.initialize(invalid_credentials_options)

        with pytest.raises(
            (
                DatabaseDisconnectedException,
                DatabaseQueryErrorException,
                DatabaseProviderAuthenticationException,
            )
        ):
            await provider.query_raw("SELECT * FROM TestRecord:test_001")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_query_raw_with_authentication_error(
    logger: logging.Logger,
    invalid_credentials_options: RemoteSurrealDbOptions,
) -> None:
    """Test query_raw fails when provider is not initialized (auth failed)."""
    provider = SurrealDbRemoteProvider(logger)

    try:
        with pytest.raises(DatabaseProviderAuthenticationException):
            await provider.initialize(invalid_credentials_options)

        with pytest.raises(
            (
                DatabaseDisconnectedException,
                DatabaseQueryErrorException,
                DatabaseProviderAuthenticationException,
            )
        ):
            await provider.query_raw("SELECT * FROM TestRecord:test_001")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_connection_timeout(
    logger: logging.Logger,
    invalid_endpoint_options: RemoteSurrealDbOptions,
) -> None:
    """Test connection to invalid endpoint raises UnconnectableException."""
    provider = SurrealDbRemoteProvider(logger)

    try:
        with pytest.raises(DatabaseProviderUnconnectableException):
            await provider.initialize(invalid_endpoint_options)
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_connection_reconnect(
    logger: logging.Logger,
    valid_options: RemoteSurrealDbOptions,
    setup_test_database: None,
) -> None:
    """Test reconnect: close then initialize again, query should work."""
    provider = SurrealDbRemoteProvider(logger)

    initialized = await provider.initialize(valid_options)
    assert initialized is True
    await provider.close()

    initialized2 = await provider.initialize(valid_options)
    assert initialized2 is True

    try:
        result = await provider.query_raw("SELECT * FROM TestRecord LIMIT 1")
        assert result is not None
    finally:
        await provider.close()
