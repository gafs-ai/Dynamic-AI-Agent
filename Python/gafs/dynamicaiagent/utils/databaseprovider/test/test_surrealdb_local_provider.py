"""Pytest-based tests for SurrealDbLocalProvider.

This module contains pytest tests for the SurrealDB local (embedded) provider
implementation. Tests cover normal operations, error handling, and edge cases.

Requirements:
    - pytest
    - pytest-asyncio

Run with:
    pytest test_surrealdb_local_provider.py -v
"""
import json
import logging
import sys
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest

# Ensure that the `Python` source folder is on sys.path
PYTHON_SRC: Path = Path(__file__).resolve().parents[5]
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from gafs.dynamicaiagent.utils.databaseprovider.surrealdb_local_provider import (  # noqa: E402
    SurrealDbLocalProvider,
    LocalSurrealDbOptions,
    LocalSurrealDbStorageType,
)
from gafs.dynamicaiagent.utils.databaseprovider.database_provider_type import (  # noqa: E402
    DatabaseProviderType,
)
from gafs.dynamicaiagent.utils.databaseprovider.exceptions.database_provider_initialization_exception import (  # noqa: E402,E501
    DatabaseProviderInitializationException,
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
    test_logger = logging.getLogger("surrealdb_local_provider_pytest")
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
    config_path = Path(__file__).parent / "secret_test_config_surrealdb_local.json"

    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def valid_options(config: dict[str, Any], tmp_path: Path) -> LocalSurrealDbOptions:
    """Create valid LocalSurrealDbOptions from config."""
    options = LocalSurrealDbOptions()
    options.namespace = config["namespace"]
    options.database = config["database"]
    storage_type_str: str = config.get("storage_type", "mem")
    options.storage_type = LocalSurrealDbStorageType(storage_type_str)
    if options.storage_type != LocalSurrealDbStorageType.MEM:
        options.path = str(tmp_path / "test_db")
    options.database_name = config["database"]
    return options


@pytest.fixture
async def setup_test_database(
    logger: logging.Logger,
    valid_options: LocalSurrealDbOptions,
) -> AsyncGenerator[SurrealDbLocalProvider, None]:
    """Setup test database with TestRecord data; yields the connected provider.

    For in-memory storage the database lives entirely within a single connection,
    so callers must reuse this provider instance to see the inserted data.
    """
    provider = SurrealDbLocalProvider(logger)
    await provider.initialize(valid_options)

    try:
        test_records = [
            ("TestRecord:test_001", "Test Record 1", "First test record"),
            ("TestRecord:test_002", "Test Record 2", "Second test record"),
            ("TestRecord:test_003", "Test Record 3", "Third test record"),
        ]

        for record_id, name, description in test_records:
            query = (
                f"CREATE {record_id} SET"
                f" name = \"{name}\","
                f" description = \"{description}\","
                f" created_at = time::now()"
            )
            await provider.query_raw(query)

        yield provider

        await provider.query_raw("DELETE FROM TestRecord")

    finally:
        await provider.close()


# ==================== Tests ====================

@pytest.mark.asyncio
async def test_initialize_with_valid_options(
    logger: logging.Logger,
    valid_options: LocalSurrealDbOptions,
) -> None:
    """Test initialization with valid configuration.

    Verifies that:
    - Provider can start the embedded database
    - initialize() returns True
    """
    provider = SurrealDbLocalProvider(logger)

    try:
        result = await provider.initialize(valid_options)

        assert result is True, "initialize() should return True with valid options"
        logger.info("Successfully initialized with valid options")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_initialize_mem_storage(logger: logging.Logger) -> None:
    """Test initialization with in-memory storage."""
    options = LocalSurrealDbOptions()
    options.namespace = "test_ns"
    options.database = "test_db"
    options.storage_type = LocalSurrealDbStorageType.MEM
    options.database_name = "test_db"

    provider = SurrealDbLocalProvider(logger)

    try:
        result = await provider.initialize(options)
        assert result is True
        logger.info("In-memory initialization succeeded")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_initialize_surrealkv_storage(logger: logging.Logger) -> None:
    """Test initialization with SurrealKV (file-based) storage.

    Uses a relative path to avoid Windows absolute-path URL parsing limitations
    in the SurrealDB Python SDK embedded engine.
    """
    import shutil
    db_path = "surrealkv_pytest_tmp"
    options = LocalSurrealDbOptions()
    options.namespace = "test_ns"
    options.database = "test_db"
    options.storage_type = LocalSurrealDbStorageType.SURREALKV
    options.path = db_path
    options.database_name = "test_db"

    provider = SurrealDbLocalProvider(logger)

    try:
        result = await provider.initialize(options)
        assert result is True
        logger.info("SurrealKV initialization succeeded")
    finally:
        await provider.close()
        shutil.rmtree(db_path, ignore_errors=True)


@pytest.mark.asyncio
async def test_query_raw(
    logger: logging.Logger,
    setup_test_database: SurrealDbLocalProvider,
) -> None:
    """Test raw query execution.

    Verifies that:
    - query_raw() can be executed
    - Returns raw result from database
    """
    provider = setup_test_database

    result = await provider.query_raw(
        "SELECT * FROM TestRecord WHERE name = 'Test Record 1'"
    )

    assert result is not None, "Result should not be None"
    logger.info(f"Raw query executed successfully, result type: {type(result)}")


@pytest.mark.asyncio
async def test_query_with_valid_id(
    logger: logging.Logger,
    setup_test_database: SurrealDbLocalProvider,
) -> None:
    """Test query execution with a valid record ID."""
    provider = setup_test_database

    result = await provider.query_raw("SELECT * FROM TestRecord:test_001")

    assert result is not None
    if isinstance(result, list) and len(result) >= 1:
        record = result[0]
        if isinstance(record, dict):
            assert "name" in record or "id" in record
    logger.info(f"Query with valid ID returned: {result}")


@pytest.mark.asyncio
async def test_query_with_nonexistent_id(
    logger: logging.Logger,
    valid_options: LocalSurrealDbOptions,
) -> None:
    """Test query execution with a non-existent ID returns empty result."""
    provider = SurrealDbLocalProvider(logger)

    try:
        await provider.initialize(valid_options)

        result = await provider.query_raw(
            "SELECT * FROM TestRecord:nonexistent_id_for_testing;"
        )

        if result is None:
            pass
        elif isinstance(result, list):
            assert len(result) == 0
        else:
            assert result == [] or result is None

        logger.info("Query with non-existent ID correctly returned empty result")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_query_multiple_documents(
    logger: logging.Logger,
    setup_test_database: SurrealDbLocalProvider,
) -> None:
    """Test query returns multiple documents."""
    provider = setup_test_database

    result = await provider.query_raw("SELECT * FROM TestRecord")

    assert result is not None
    if isinstance(result, list):
        flat = result
        if result and isinstance(result[0], list):
            flat = [item for sub in result for item in sub]
        assert len(flat) >= 3, (
            f"Should have at least 3 TestRecord documents, got {len(flat)}"
        )
        logger.info(f"Multiple documents query returned {len(flat)} documents")


@pytest.mark.asyncio
async def test_query_with_dataclass_parsing(
    logger: logging.Logger,
    setup_test_database: SurrealDbLocalProvider,
) -> None:
    """Test query with model parses result into TestRecord."""
    provider = setup_test_database

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


@pytest.mark.asyncio
async def test_query_many_with_dataclass_parsing(
    logger: logging.Logger,
    setup_test_database: SurrealDbLocalProvider,
) -> None:
    """Test query with model=TestRecord, many=True returns a list."""
    provider = setup_test_database

    result = await provider.query(
        "SELECT * FROM TestRecord",
        model=TestRecord,
        many=True,
    )

    assert result is not None
    assert isinstance(result, list)
    assert len(result) >= 3
    assert all(isinstance(r, TestRecord) for r in result)
    logger.info(f"Many-parsing returned {len(result)} records")


@pytest.mark.asyncio
async def test_provider_close(
    logger: logging.Logger,
    valid_options: LocalSurrealDbOptions,
) -> None:
    """Test provider close functionality.

    Verifies that:
    - Provider can be closed without errors
    - Close can be called multiple times safely
    """
    provider = SurrealDbLocalProvider(logger)

    initialized = await provider.initialize(valid_options)
    assert initialized is True

    await provider.close()
    await provider.close()  # safe to call again

    logger.info("Provider closed successfully")


@pytest.mark.asyncio
async def test_connection_reconnect(
    logger: logging.Logger,
    valid_options: LocalSurrealDbOptions,
) -> None:
    """Test reconnect: close then initialize again, query should work."""
    provider = SurrealDbLocalProvider(logger)

    initialized = await provider.initialize(valid_options)
    assert initialized is True
    await provider.close()

    initialized2 = await provider.initialize(valid_options)
    assert initialized2 is True

    result = await provider.query_raw("SELECT * FROM TestRecord LIMIT 1")
    assert result is not None or result == []

    await provider.close()


@pytest.mark.asyncio
async def test_create_and_delete_record(
    logger: logging.Logger,
    valid_options: LocalSurrealDbOptions,
) -> None:
    """Test creating and deleting a record."""
    provider = SurrealDbLocalProvider(logger)

    try:
        await provider.initialize(valid_options)

        await provider.query_raw(
            "CREATE TestRecord:temp_001 SET name = 'Temp Record', description = 'Temporary'"
        )

        result = await provider.query_raw("SELECT * FROM TestRecord:temp_001")
        assert result is not None
        if isinstance(result, list) and len(result) > 0:
            assert isinstance(result[0], dict)

        await provider.query_raw("DELETE TestRecord:temp_001")

        result_after_delete = await provider.query_raw(
            "SELECT * FROM TestRecord:temp_001"
        )
        if result_after_delete is None:
            pass
        elif isinstance(result_after_delete, list):
            assert len(result_after_delete) == 0

        logger.info("Create and delete record test passed")
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_options_serialization(valid_options: LocalSurrealDbOptions) -> None:
    """Test LocalSurrealDbOptions serialization/deserialization.

    Verifies that:
    - to_dict() produces valid dictionary
    - to_json() produces valid JSON string
    - from_dict() reconstructs object correctly
    - from_json() reconstructs object correctly
    """
    options_dict = valid_options.to_dict(recursive=True)
    assert isinstance(options_dict, dict)
    assert "namespace" in options_dict
    assert "database" in options_dict
    assert options_dict["database_type"] == "surrealdb_local"

    json_str = valid_options.to_json()
    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)

    reconstructed_from_dict = LocalSurrealDbOptions.from_dict(options_dict)
    assert reconstructed_from_dict.namespace == valid_options.namespace
    assert reconstructed_from_dict.database == valid_options.database
    assert reconstructed_from_dict.storage_type == valid_options.storage_type
    assert reconstructed_from_dict.database_type == DatabaseProviderType.SURREALDB_LOCAL

    reconstructed_from_json = LocalSurrealDbOptions.from_json(json_str)
    assert reconstructed_from_json.namespace == valid_options.namespace
    assert reconstructed_from_json.database == valid_options.database
    assert reconstructed_from_json.database_type == DatabaseProviderType.SURREALDB_LOCAL


@pytest.mark.asyncio
async def test_options_invalid_json_keys(valid_options: LocalSurrealDbOptions) -> None:
    """Test from_json with invalid (extra) keys — they should be ignored."""
    json_with_extra = valid_options.to_json()
    parsed = json.loads(json_with_extra)
    parsed["unknown_key"] = "should_be_ignored"
    parsed["another_invalid"] = 123
    json_str = json.dumps(parsed)

    options = LocalSurrealDbOptions.from_json(json_str)

    assert options.namespace == valid_options.namespace
    assert options.database == valid_options.database
    assert not hasattr(options, "unknown_key")


@pytest.mark.asyncio
async def test_options_invalid_attribute_validation() -> None:
    """Test __setattr__ raises ValueError for invalid attribute or wrong type."""
    options = LocalSurrealDbOptions()

    with pytest.raises(ValueError):
        setattr(options, "invalid_attribute", "value")

    options.namespace = "valid_ns"
    assert options.namespace == "valid_ns"

    with pytest.raises(ValueError):
        options.namespace = 123  # type: ignore[assignment]


@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected_empty", [
    ("SELECT * FROM TestRecord:non_existing_1;", True),
    ("SELECT * FROM TestRecord:non_existing_2;", True),
])
async def test_query_with_multiple_nonexistent_ids(
    logger: logging.Logger,
    valid_options: LocalSurrealDbOptions,
    query: str,
    expected_empty: bool,
) -> None:
    """Parametrized test for multiple non-existent IDs."""
    provider = SurrealDbLocalProvider(logger)

    try:
        await provider.initialize(valid_options)

        result = await provider.query_raw(query)

        if expected_empty:
            assert result is None or (isinstance(result, list) and len(result) == 0)

        logger.info(f"Parametrized test passed for query: {query}")
    finally:
        await provider.close()
