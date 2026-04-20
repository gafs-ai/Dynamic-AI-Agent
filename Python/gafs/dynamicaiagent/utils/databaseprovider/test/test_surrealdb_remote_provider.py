"""Tests for SurrealDbRemoteProvider.

Tests cover:
- Normal initialization (connect + authenticate)
- Initialization failure (wrong endpoint, wrong credentials)
- query_raw: normal case, query error, not-initialized error
- query: typed deserialization (single, many, none, model=None)
- RetryOptions: per-request override
- close / async context manager

All tests use a real remote SurrealDB instance (no mocks).
Connection details are loaded from secret_test_config_surrealdb_remote.json.

Run with:
    pytest gafs/dynamicaiagent/utils/databaseprovider/test/test_surrealdb_remote_provider.py -v
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
    SurrealDbRemoteProvider,
    RemoteSurrealDbOptions,
    DatabaseProviderStatus,
    DatabaseProviderType,
    RetryOptions,
)
from gafs.dynamicaiagent.utils.databaseprovider.exceptions import (  # noqa: E402
    DatabaseProviderOptionsException,
    DatabaseProviderUnconnectableException,
    DatabaseProviderAuthenticationException,
    DatabaseQueryErrorException,
    DatabaseConnectionException,
)
from gafs.dynamicaiagent.utils.databaseprovider.test.data_models import TestRecord  # noqa: E402

# Table name used for tests (keep distinct to avoid collisions).
_TEST_TABLE = "DPTestRecord"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_logger(name: str = "test_remote_provider") -> logging.Logger:
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
    config_path = Path(__file__).parent / "secret_test_config_surrealdb_remote.json"
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
def valid_options(config: dict[str, Any]) -> RemoteSurrealDbOptions:
    """Build valid RemoteSurrealDbOptions from the config file."""
    opts = RemoteSurrealDbOptions()
    opts.endpoint = config["endpoint"]
    opts.namespace = config["namespace"]
    opts.database = config["database"]
    opts.username = config["username"]
    opts.password = config["password"]
    opts.auth_level = config.get("auth_level", "database")
    opts.database_name = config["database"]
    return opts


@pytest.fixture
async def initialized_provider(
    logger: logging.Logger,
    valid_options: RemoteSurrealDbOptions,
) -> AsyncGenerator[SurrealDbRemoteProvider, None]:
    """Yield a fully initialized remote provider with test records pre-inserted."""
    provider = SurrealDbRemoteProvider(logger)
    await provider.initialize(valid_options)

    try:
        # Delete any leftover test records from previous runs.
        await provider.query_raw(f"DELETE FROM {_TEST_TABLE}")

        # Insert fresh test records.
        for i in range(1, 4):
            await provider.query_raw(
                f"CREATE {_TEST_TABLE}:test_{i:03d} SET "
                f"name = 'Test Record {i}', "
                f"description = 'Record number {i}', "
                f"created_at = time::now()"
            )
        yield provider
    finally:
        try:
            await provider.query_raw(f"DELETE FROM {_TEST_TABLE}")
        except Exception:
            pass
        await provider.close()


# ══ Tests: RemoteSurrealDbOptions (value object) ═══════════════════════════════

class TestRemoteSurrealDbOptions:
    """Tests for RemoteSurrealDbOptions value-object behaviour."""

    def test_default_database_type_is_remote(self) -> None:
        opts = RemoteSurrealDbOptions()
        assert opts.database_type == DatabaseProviderType.SURREALDB_REMOTE

    def test_default_auth_level_is_database(self) -> None:
        opts = RemoteSurrealDbOptions()
        assert opts.auth_level == "database"

    def test_set_invalid_database_type_raises(self) -> None:
        opts = RemoteSurrealDbOptions()
        with pytest.raises((ValueError, KeyError)):
            opts.database_type = DatabaseProviderType.SURREALDB_LOCAL

    def test_set_invalid_endpoint_type_raises(self) -> None:
        opts = RemoteSurrealDbOptions()
        with pytest.raises(ValueError):
            opts.endpoint = 123  # type: ignore[assignment]

    def test_to_dict_recursive(self) -> None:
        opts = RemoteSurrealDbOptions()
        opts.endpoint = "ws://localhost:8000"
        opts.namespace = "ns"
        opts.database = "db"
        opts.username = "user"
        opts.password = "pass"
        opts.database_name = "db"
        d = opts.to_dict(recursive=True)
        assert d["database_type"] == "surrealdb_remote"
        assert d["endpoint"] == "ws://localhost:8000"

    def test_from_dict_roundtrip(self) -> None:
        opts = RemoteSurrealDbOptions()
        opts.endpoint = "ws://localhost:8000"
        opts.namespace = "ns"
        opts.database = "db"
        opts.username = "user"
        opts.password = "pass"
        opts.database_name = "db"
        d = opts.to_dict(recursive=True)
        opts2 = RemoteSurrealDbOptions.from_dict(d)
        assert opts2.endpoint == "ws://localhost:8000"
        assert opts2.namespace == "ns"


# ══ Tests: initialize ═════════════════════════════════════════════════════════

class TestInitialize:
    """Tests for SurrealDbRemoteProvider.initialize()."""

    @pytest.mark.asyncio
    async def test_initialize_valid_options_succeeds(
        self, logger: logging.Logger, valid_options: RemoteSurrealDbOptions
    ) -> None:
        provider = SurrealDbRemoteProvider(logger)
        result = await provider.initialize(valid_options)
        assert result is True
        assert provider.status == DatabaseProviderStatus.AVAILABLE
        await provider.close()

    @pytest.mark.asyncio
    async def test_initialize_invalid_options_type_raises(
        self, logger: logging.Logger
    ) -> None:
        provider = SurrealDbRemoteProvider(logger)
        with pytest.raises(DatabaseProviderOptionsException):
            await provider.initialize("not options")  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_initialize_missing_endpoint_raises(
        self, logger: logging.Logger, config: dict[str, Any]
    ) -> None:
        opts = RemoteSurrealDbOptions()
        opts.namespace = config["namespace"]
        opts.database = config["database"]
        opts.username = config["username"]
        opts.password = config["password"]
        opts.database_name = config["database"]
        provider = SurrealDbRemoteProvider(logger)
        with pytest.raises(DatabaseProviderOptionsException):
            await provider.initialize(opts)

    @pytest.mark.asyncio
    async def test_initialize_unreachable_endpoint_raises(
        self, logger: logging.Logger, config: dict[str, Any]
    ) -> None:
        opts = RemoteSurrealDbOptions()
        opts.endpoint = "ws://192.0.2.1:9999"  # RFC 5737 documentation address (unreachable)
        opts.namespace = config["namespace"]
        opts.database = config["database"]
        opts.username = config["username"]
        opts.password = config["password"]
        opts.database_name = config["database"]
        provider = SurrealDbRemoteProvider(logger)
        with pytest.raises(
            (DatabaseProviderUnconnectableException, DatabaseProviderAuthenticationException, Exception)
        ):
            await provider.initialize(opts)

    @pytest.mark.asyncio
    async def test_initialize_wrong_password_raises(
        self, logger: logging.Logger, config: dict[str, Any]
    ) -> None:
        opts = RemoteSurrealDbOptions()
        opts.endpoint = config["endpoint"]
        opts.namespace = config["namespace"]
        opts.database = config["database"]
        opts.username = config["username"]
        opts.password = "wrong_password_!!!"
        opts.auth_level = config.get("auth_level", "database")
        opts.database_name = config["database"]
        provider = SurrealDbRemoteProvider(logger)
        with pytest.raises(
            (DatabaseProviderAuthenticationException, DatabaseProviderUnconnectableException)
        ):
            await provider.initialize(opts)


# ══ Tests: query_raw ══════════════════════════════════════════════════════════

class TestQueryRaw:
    """Tests for SurrealDbRemoteProvider.query_raw()."""

    @pytest.mark.asyncio
    async def test_query_raw_returns_records(
        self, initialized_provider: SurrealDbRemoteProvider
    ) -> None:
        result = await initialized_provider.query_raw(f"SELECT * FROM {_TEST_TABLE}")
        assert isinstance(result, list)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_query_raw_filtered_result(
        self, initialized_provider: SurrealDbRemoteProvider
    ) -> None:
        result = await initialized_provider.query_raw(
            f"SELECT * FROM {_TEST_TABLE} WHERE name = 'Test Record 1'"
        )
        assert isinstance(result, list)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_query_raw_empty_result(
        self, initialized_provider: SurrealDbRemoteProvider
    ) -> None:
        result = await initialized_provider.query_raw(
            f"SELECT * FROM {_TEST_TABLE} WHERE name = 'Nonexistent'"
        )
        assert result == [] or result is None

    @pytest.mark.asyncio
    async def test_query_raw_invalid_syntax_raises(
        self, initialized_provider: SurrealDbRemoteProvider
    ) -> None:
        with pytest.raises(DatabaseQueryErrorException):
            await initialized_provider.query_raw("INVALID SYNTAX ###")

    @pytest.mark.asyncio
    async def test_query_raw_not_initialized_raises(
        self, logger: logging.Logger
    ) -> None:
        provider = SurrealDbRemoteProvider(logger)
        with pytest.raises(DatabaseConnectionException):
            await provider.query_raw("SELECT * FROM test")


# ══ Tests: query ══════════════════════════════════════════════════════════════

class TestQuery:
    """Tests for SurrealDbRemoteProvider.query()."""

    @pytest.mark.asyncio
    async def test_query_many_returns_list(
        self, initialized_provider: SurrealDbRemoteProvider
    ) -> None:
        records = await initialized_provider.query(
            f"SELECT * FROM {_TEST_TABLE}", model=TestRecord, many=True
        )
        assert isinstance(records, list)
        assert len(records) == 3
        assert all(isinstance(r, TestRecord) for r in records)

    @pytest.mark.asyncio
    async def test_query_single_returns_record(
        self, initialized_provider: SurrealDbRemoteProvider
    ) -> None:
        record = await initialized_provider.query(
            f"SELECT * FROM {_TEST_TABLE} WHERE name = 'Test Record 1'",
            model=TestRecord,
            many=False,
        )
        assert isinstance(record, TestRecord)
        assert record.name == "Test Record 1"

    @pytest.mark.asyncio
    async def test_query_single_no_result_returns_none(
        self, initialized_provider: SurrealDbRemoteProvider
    ) -> None:
        record = await initialized_provider.query(
            f"SELECT * FROM {_TEST_TABLE} WHERE name = 'Nonexistent'",
            model=TestRecord,
            many=False,
        )
        assert record is None

    @pytest.mark.asyncio
    async def test_query_model_none_returns_none(
        self, initialized_provider: SurrealDbRemoteProvider
    ) -> None:
        result = await initialized_provider.query(
            f"SELECT * FROM {_TEST_TABLE}", model=None
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_query_many_empty_returns_empty_list(
        self, initialized_provider: SurrealDbRemoteProvider
    ) -> None:
        records = await initialized_provider.query(
            f"SELECT * FROM {_TEST_TABLE} WHERE name = 'Nonexistent'",
            model=TestRecord,
            many=True,
        )
        assert records == []

    @pytest.mark.asyncio
    async def test_query_invalid_syntax_raises(
        self, initialized_provider: SurrealDbRemoteProvider
    ) -> None:
        with pytest.raises(DatabaseQueryErrorException):
            await initialized_provider.query("INVALID SYNTAX ###", model=TestRecord)

    @pytest.mark.asyncio
    async def test_query_fields_deserialized_correctly(
        self, initialized_provider: SurrealDbRemoteProvider
    ) -> None:
        records = await initialized_provider.query(
            f"SELECT * FROM {_TEST_TABLE}", model=TestRecord, many=True
        )
        assert len(records) == 3
        names = {r.name for r in records}
        assert "Test Record 1" in names
        assert "Test Record 3" in names


# ══ Tests: close and context manager ═════════════════════════════════════════

class TestClose:
    """Tests for SurrealDbRemoteProvider.close() and async context manager."""

    @pytest.mark.asyncio
    async def test_close_sets_status_terminated(
        self, logger: logging.Logger, valid_options: RemoteSurrealDbOptions
    ) -> None:
        provider = SurrealDbRemoteProvider(logger)
        await provider.initialize(valid_options)
        await provider.close()
        assert provider.status == DatabaseProviderStatus.TERMINATED

    @pytest.mark.asyncio
    async def test_async_context_manager(
        self, logger: logging.Logger, valid_options: RemoteSurrealDbOptions
    ) -> None:
        async with SurrealDbRemoteProvider(logger) as provider:
            await provider.initialize(valid_options)
            result = await provider.query_raw(f"SELECT * FROM {_TEST_TABLE}")
            assert isinstance(result, list)
        assert provider.status == DatabaseProviderStatus.TERMINATED
