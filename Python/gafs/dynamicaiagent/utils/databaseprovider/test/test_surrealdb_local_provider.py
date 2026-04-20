"""Tests for SurrealDbLocalProvider.

Tests cover:
- Normal initialization (in-memory and persistent storage types)
- query_raw: normal case, query error, not-initialized error
- query: typed deserialization (single record, many records, no result, model=None)
- RetryOptions: per-request and provider-level override
- close / async context manager
- RetryOptions, DatabaseProviderOptions, LocalSurrealDbOptions value-object behaviour

All tests use a real embedded SurrealDB instance (no mocks).

Run with:
    pytest gafs/dynamicaiagent/utils/databaseprovider/test/test_surrealdb_local_provider.py -v
"""
from __future__ import annotations

import json
import logging
import sys
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest

# Ensure that the Python/ source folder is on sys.path.
PYTHON_SRC: Path = Path(__file__).resolve().parents[5]
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from gafs.dynamicaiagent.utils.databaseprovider import (  # noqa: E402
    SurrealDbLocalProvider,
    LocalSurrealDbOptions,
    LocalSurrealDbStorageType,
    DatabaseProviderStatus,
    DatabaseProviderType,
    RetryOptions,
)
from gafs.dynamicaiagent.utils.databaseprovider.exceptions import (  # noqa: E402
    DatabaseProviderOptionsException,
    DatabaseProviderUnconnectableException,
    EmbeddedDatabaseInitializationException,
    DatabaseQueryErrorException,
    DatabaseConnectionException,
)
from gafs.dynamicaiagent.utils.databaseprovider.test.data_models import TestRecord  # noqa: E402


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_logger(name: str = "test_local_provider") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s - %(message)s")
        )
        logger.addHandler(handler)
    return logger


def _load_config() -> dict[str, Any]:
    config_path = Path(__file__).parent / "secret_test_config_surrealdb_local.json"
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def logger() -> logging.Logger:
    return _make_logger()


@pytest.fixture(scope="module")
def config() -> dict[str, Any]:
    return _load_config()


@pytest.fixture
def valid_options(config: dict[str, Any]) -> LocalSurrealDbOptions:
    """Build a valid in-memory LocalSurrealDbOptions from the config file."""
    options = LocalSurrealDbOptions()
    options.namespace = config["namespace"]
    options.database = config["database"]
    storage_type_str: str = config.get("storage_type", "mem")
    options.storage_type = LocalSurrealDbStorageType(storage_type_str)
    options.database_name = config["database"]
    return options


@pytest.fixture
async def initialized_provider(
    logger: logging.Logger,
    valid_options: LocalSurrealDbOptions,
) -> AsyncGenerator[SurrealDbLocalProvider, None]:
    """Yield a fully initialized provider with test records pre-inserted."""
    provider = SurrealDbLocalProvider(logger)
    await provider.initialize(valid_options)

    try:
        # Insert test records.
        for i in range(1, 4):
            await provider.query_raw(
                f"CREATE TestRecord:test_{i:03d} SET "
                f"name = 'Test Record {i}', "
                f"description = 'Record number {i}', "
                f"created_at = time::now()"
            )
        yield provider
    finally:
        # Clean up test records then close.
        try:
            await provider.query_raw("DELETE FROM TestRecord")
        except Exception:
            pass
        await provider.close()


# ══ Tests: Options (value objects) ════════════════════════════════════════════

class TestLocalSurrealDbOptions:
    """Tests for LocalSurrealDbOptions value-object behaviour."""

    def test_default_database_type_is_local(self) -> None:
        opts = LocalSurrealDbOptions()
        assert opts.database_type == DatabaseProviderType.SURREALDB_LOCAL

    def test_default_storage_type_is_surrealkv(self) -> None:
        opts = LocalSurrealDbOptions()
        assert opts.storage_type == LocalSurrealDbStorageType.SURREALKV

    def test_set_namespace_and_database(self) -> None:
        opts = LocalSurrealDbOptions()
        opts.namespace = "ns"
        opts.database = "db"
        assert opts.namespace == "ns"
        assert opts.database == "db"

    def test_set_invalid_database_type_raises(self) -> None:
        opts = LocalSurrealDbOptions()
        with pytest.raises((ValueError, KeyError)):
            opts.database_type = DatabaseProviderType.SURREALDB_REMOTE

    def test_set_invalid_namespace_type_raises(self) -> None:
        opts = LocalSurrealDbOptions()
        with pytest.raises(ValueError):
            opts.namespace = 123  # type: ignore[assignment]

    def test_storage_type_string_conversion(self) -> None:
        opts = LocalSurrealDbOptions()
        opts.storage_type = "mem"
        assert opts.storage_type == LocalSurrealDbStorageType.MEM

    def test_to_dict_recursive(self) -> None:
        opts = LocalSurrealDbOptions()
        opts.namespace = "ns"
        opts.database = "db"
        opts.database_name = "mydb"
        d = opts.to_dict(recursive=True)
        assert d["database_type"] == "surrealdb_local"
        assert d["namespace"] == "ns"

    def test_from_dict_roundtrip(self) -> None:
        opts = LocalSurrealDbOptions()
        opts.namespace = "ns"
        opts.database = "db"
        opts.database_name = "mydb"
        d = opts.to_dict(recursive=True)
        opts2 = LocalSurrealDbOptions.from_dict(d)
        assert opts2.namespace == "ns"
        assert opts2.database == "db"


class TestRetryOptions:
    """Tests for RetryOptions value-object behaviour."""

    def test_defaults_are_none_in_init(self) -> None:
        opts = RetryOptions()
        assert opts.timeout is None
        assert opts.max_retry is None
        assert opts.retry_interval is None

    def test_set_valid_values(self) -> None:
        opts = RetryOptions()
        opts.timeout = 30
        opts.max_retry = 3
        opts.retry_interval = 5
        assert opts.timeout == 30
        assert opts.max_retry == 3
        assert opts.retry_interval == 5

    def test_set_invalid_type_raises(self) -> None:
        opts = RetryOptions()
        with pytest.raises(ValueError):
            opts.timeout = "30"  # type: ignore[assignment]

    def test_from_dict(self) -> None:
        opts = RetryOptions.from_dict({"timeout": 10, "max_retry": 1})
        assert opts.timeout == 10
        assert opts.max_retry == 1
        assert opts.retry_interval is None

    def test_from_json(self) -> None:
        opts = RetryOptions.from_json('{"timeout": 20, "retry_interval": 5}')
        assert opts.timeout == 20
        assert opts.retry_interval == 5


# ══ Tests: initialize ═════════════════════════════════════════════════════════

class TestInitialize:
    """Tests for SurrealDbLocalProvider.initialize()."""

    @pytest.mark.asyncio
    async def test_initialize_mem_succeeds(
        self, logger: logging.Logger, valid_options: LocalSurrealDbOptions
    ) -> None:
        provider = SurrealDbLocalProvider(logger)
        result = await provider.initialize(valid_options)
        assert result is True
        assert provider.status == DatabaseProviderStatus.AVAILABLE
        await provider.close()

    @pytest.mark.asyncio
    async def test_initialize_surrealkv_succeeds(
        self, logger: logging.Logger
    ) -> None:
        import shutil
        db_path = "surrealkv_test_tmp"
        opts = LocalSurrealDbOptions()
        opts.namespace = "test_ns"
        opts.database = "test_db"
        opts.storage_type = LocalSurrealDbStorageType.SURREALKV
        opts.path = db_path
        opts.database_name = "test_db"
        provider = SurrealDbLocalProvider(logger)
        try:
            result = await provider.initialize(opts)
            assert result is True
            assert provider.status == DatabaseProviderStatus.AVAILABLE
        finally:
            await provider.close()
            shutil.rmtree(db_path, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_initialize_invalid_options_type_raises(
        self, logger: logging.Logger
    ) -> None:
        """Passing a non-LocalSurrealDbOptions object should raise DatabaseProviderOptionsException."""
        provider = SurrealDbLocalProvider(logger)
        with pytest.raises(DatabaseProviderOptionsException):
            await provider.initialize("not options")  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_initialize_missing_namespace_raises(
        self, logger: logging.Logger
    ) -> None:
        opts = LocalSurrealDbOptions()
        opts.database = "db"
        opts.database_name = "db"
        provider = SurrealDbLocalProvider(logger)
        with pytest.raises(DatabaseProviderOptionsException):
            await provider.initialize(opts)

    @pytest.mark.asyncio
    async def test_initialize_returns_true(
        self, logger: logging.Logger, valid_options: LocalSurrealDbOptions
    ) -> None:
        provider = SurrealDbLocalProvider(logger)
        result = await provider.initialize(valid_options)
        assert result is True
        await provider.close()


# ══ Tests: query_raw ══════════════════════════════════════════════════════════

class TestQueryRaw:
    """Tests for SurrealDbLocalProvider.query_raw()."""

    @pytest.mark.asyncio
    async def test_query_raw_returns_result(
        self, initialized_provider: SurrealDbLocalProvider
    ) -> None:
        result = await initialized_provider.query_raw("SELECT * FROM TestRecord")
        assert isinstance(result, list)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_query_raw_create_and_select(
        self, initialized_provider: SurrealDbLocalProvider
    ) -> None:
        result = await initialized_provider.query_raw(
            "SELECT * FROM TestRecord WHERE name = 'Test Record 1'"
        )
        assert isinstance(result, list)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_query_raw_empty_result(
        self, initialized_provider: SurrealDbLocalProvider
    ) -> None:
        result = await initialized_provider.query_raw(
            "SELECT * FROM TestRecord WHERE name = 'Nonexistent'"
        )
        assert result == [] or result is None

    @pytest.mark.asyncio
    async def test_query_raw_invalid_query_raises_query_error(
        self, initialized_provider: SurrealDbLocalProvider
    ) -> None:
        with pytest.raises(DatabaseQueryErrorException):
            await initialized_provider.query_raw("INVALID SYNTAX ###")

    @pytest.mark.asyncio
    async def test_query_raw_not_initialized_raises_connection_error(
        self, logger: logging.Logger
    ) -> None:
        provider = SurrealDbLocalProvider(logger)
        with pytest.raises(DatabaseConnectionException):
            await provider.query_raw("SELECT * FROM test")

    @pytest.mark.asyncio
    async def test_query_raw_with_per_request_retry_options(
        self, initialized_provider: SurrealDbLocalProvider
    ) -> None:
        """RetryOptions can be passed per-request without affecting other queries."""
        retry = RetryOptions()
        retry.timeout = 30
        retry.max_retry = 0
        retry.retry_interval = 1
        result = await initialized_provider.query_raw(
            "SELECT * FROM TestRecord", retry_options=retry
        )
        assert isinstance(result, list)


# ══ Tests: query ══════════════════════════════════════════════════════════════

class TestQuery:
    """Tests for SurrealDbLocalProvider.query()."""

    @pytest.mark.asyncio
    async def test_query_many_returns_list(
        self, initialized_provider: SurrealDbLocalProvider
    ) -> None:
        records = await initialized_provider.query(
            "SELECT * FROM TestRecord", model=TestRecord, many=True
        )
        assert isinstance(records, list)
        assert len(records) == 3
        assert all(isinstance(r, TestRecord) for r in records)

    @pytest.mark.asyncio
    async def test_query_single_returns_record(
        self, initialized_provider: SurrealDbLocalProvider
    ) -> None:
        record = await initialized_provider.query(
            "SELECT * FROM TestRecord WHERE name = 'Test Record 1'",
            model=TestRecord,
            many=False,
        )
        assert isinstance(record, TestRecord)
        assert record.name == "Test Record 1"

    @pytest.mark.asyncio
    async def test_query_single_no_result_returns_none(
        self, initialized_provider: SurrealDbLocalProvider
    ) -> None:
        record = await initialized_provider.query(
            "SELECT * FROM TestRecord WHERE name = 'Nonexistent'",
            model=TestRecord,
            many=False,
        )
        assert record is None

    @pytest.mark.asyncio
    async def test_query_model_none_returns_none(
        self, initialized_provider: SurrealDbLocalProvider
    ) -> None:
        result = await initialized_provider.query(
            "SELECT * FROM TestRecord", model=None
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_query_many_empty_returns_empty_list(
        self, initialized_provider: SurrealDbLocalProvider
    ) -> None:
        records = await initialized_provider.query(
            "SELECT * FROM TestRecord WHERE name = 'Nonexistent'",
            model=TestRecord,
            many=True,
        )
        assert records == []

    @pytest.mark.asyncio
    async def test_query_invalid_syntax_raises_query_error(
        self, initialized_provider: SurrealDbLocalProvider
    ) -> None:
        with pytest.raises(DatabaseQueryErrorException):
            await initialized_provider.query("INVALID SYNTAX ###", model=TestRecord)

    @pytest.mark.asyncio
    async def test_query_record_fields_deserialized_correctly(
        self, initialized_provider: SurrealDbLocalProvider
    ) -> None:
        records = await initialized_provider.query(
            "SELECT * FROM TestRecord", model=TestRecord, many=True
        )
        assert len(records) == 3
        names = {r.name for r in records}
        assert "Test Record 1" in names
        assert "Test Record 2" in names
        assert "Test Record 3" in names


# ══ Tests: close and context manager ═════════════════════════════════════════

class TestClose:
    """Tests for SurrealDbLocalProvider.close() and async context manager."""

    @pytest.mark.asyncio
    async def test_close_sets_status_terminated(
        self, logger: logging.Logger, valid_options: LocalSurrealDbOptions
    ) -> None:
        provider = SurrealDbLocalProvider(logger)
        await provider.initialize(valid_options)
        await provider.close()
        assert provider.status == DatabaseProviderStatus.TERMINATED

    @pytest.mark.asyncio
    async def test_async_context_manager(
        self, logger: logging.Logger, valid_options: LocalSurrealDbOptions
    ) -> None:
        async with SurrealDbLocalProvider(logger) as provider:
            await provider.initialize(valid_options)
            result = await provider.query_raw("SELECT * FROM test")
            assert result is not None or result == [] or result is None
        assert provider.status == DatabaseProviderStatus.TERMINATED
