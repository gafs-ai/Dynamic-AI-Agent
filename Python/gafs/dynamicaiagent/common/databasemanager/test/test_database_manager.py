from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from gafs.dynamicaiagent.common.databasemanager.database_connection import DatabaseConnection
from gafs.dynamicaiagent.common.databasemanager.database_manager import DatabaseManager
from gafs.dynamicaiagent.common.databasemanager.exceptions.database_manager_exceptions import (
    DatabaseManagerConfigurationException,
    DatabaseManagerConnectionNotFoundException,
    DatabaseManagerInvalidOperationException,
    DatabaseManagerNotInitializedException,
)
from gafs.dynamicaiagent.common.databasemanager.i_database_manager import IDatabaseManager
from gafs.dynamicaiagent.utils.databaseprovider import DatabaseProviderType
from gafs.dynamicaiagent.utils.databaseprovider.surrealdb_remote_provider import (
    RemoteSurrealDbOptions,
)


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------

class DummyProvider:
    """Test double for IDatabaseProvider; records calls and stores query results."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.initialized_with: list[RemoteSurrealDbOptions] = []
        self.closed: bool = False
        # Set to control the return value of query() / query_raw().
        self.query_result: Any = None
        self.raw_results: list[Any] = []

    async def initialize(self, options: RemoteSurrealDbOptions) -> bool:
        self.initialized_with.append(options)
        return True

    async def close(self) -> None:
        self.closed = True

    async def query(self, query: str, model: type | None = None, many: bool = False) -> Any:
        return self.query_result

    async def query_raw(self, query: str) -> Any:
        if self.raw_results:
            return self.raw_results.pop(0)
        return None


class DummySecretManager:
    """Minimal test double for ISecretManager."""

    def __init__(self) -> None:
        self.created_secrets: list[Any] = []
        self.secret_store: dict[str, Any] = {}

    async def create_secret(self, secret: Any) -> Any:
        self.created_secrets.append(secret)
        secret.id = "generated-secret-id"
        return secret

    async def get_secret(self, secret_id: str) -> Any | None:
        return self.secret_store.get(secret_id)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def logger() -> logging.Logger:
    log = logging.getLogger("database_manager_test")
    log.setLevel(logging.DEBUG)
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s - %(message)s")
        )
        log.addHandler(handler)
    return log


def _make_remote_options(database_name: str) -> RemoteSurrealDbOptions:
    options = RemoteSurrealDbOptions()
    options.endpoint = "wss://example.com/rpc"
    options.namespace = "ns"
    options.database = "db"
    options.username = "user"
    options.password = "pass"
    options.database_type = DatabaseProviderType.SURREALDB_REMOTE
    options.database_name = database_name
    return options


# ---------------------------------------------------------------------------
# _add_provider (internal)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_provider_internal_registers_provider(
    monkeypatch: Any, logger: logging.Logger
) -> None:
    """_add_provider registers the provider under the given id."""
    created: list[DummyProvider] = []

    def _factory(l: logging.Logger) -> DummyProvider:
        p = DummyProvider(l)
        created.append(p)
        return p

    import gafs.dynamicaiagent.common.databasemanager.database_manager as dm_module
    monkeypatch.setattr(dm_module, "SurrealDbRemoteProvider", _factory)

    manager = DatabaseManager(logger)
    options = _make_remote_options("test-db")

    provider = await manager._add_provider(options, "test-id")

    assert provider is created[0]
    assert manager._providers["test-id"] is created[0]


@pytest.mark.asyncio
async def test_add_provider_internal_overwrite_closes_old(
    monkeypatch: Any, logger: logging.Logger
) -> None:
    """_add_provider with overwrite=True closes the old provider."""
    created: list[DummyProvider] = []

    def _factory(l: logging.Logger) -> DummyProvider:
        p = DummyProvider(l)
        created.append(p)
        return p

    import gafs.dynamicaiagent.common.databasemanager.database_manager as dm_module
    monkeypatch.setattr(dm_module, "SurrealDbRemoteProvider", _factory)

    manager = DatabaseManager(logger)
    options = _make_remote_options("test-db")

    first = await manager._add_provider(options, "my-id")
    second = await manager._add_provider(options, "my-id", overwrite=True)

    assert first.closed is True
    assert manager._providers["my-id"] is second


@pytest.mark.asyncio
async def test_add_provider_internal_unsupported_type_raises(
    logger: logging.Logger,
) -> None:
    """_add_provider raises DatabaseManagerConfigurationException for unknown type."""
    manager = DatabaseManager(logger)
    options = _make_remote_options("bad-type-db")
    # Inject a sentinel that does not match any DatabaseProviderType enum member so
    # the match statement falls through to the default case.
    class _FakeType:
        value = "unsupported_fake_type"
    object.__setattr__(options, "database_type", _FakeType())

    with pytest.raises(DatabaseManagerConfigurationException):
        await manager._add_provider(options, "bad-id")


# ---------------------------------------------------------------------------
# get_default_provider
# ---------------------------------------------------------------------------

def test_get_default_provider_raises_when_not_registered(
    logger: logging.Logger,
) -> None:
    """get_default_provider raises if phase-1 init was not done."""
    manager = DatabaseManager(logger)
    with pytest.raises(DatabaseManagerConnectionNotFoundException):
        manager.get_default_provider()


def test_get_default_provider_returns_registered_provider(
    logger: logging.Logger,
) -> None:
    """get_default_provider returns the provider keyed under DEFAULT_DATABASE_NAME."""
    manager = DatabaseManager(logger)
    dummy = DummyProvider(logger)
    manager._providers[IDatabaseManager.DEFAULT_DATABASE_NAME()] = dummy

    assert manager.get_default_provider() is dummy


# ---------------------------------------------------------------------------
# initialize / _check_initialized
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_initialize_registers_secret_manager(logger: logging.Logger) -> None:
    """initialize() stores the SecretManager reference."""
    manager = DatabaseManager(logger)
    sm = DummySecretManager()
    await manager.initialize(sm)  # type: ignore[arg-type]
    assert manager._secret_manager is sm


@pytest.mark.asyncio
async def test_methods_raise_before_initialize(logger: logging.Logger) -> None:
    """add_connection raises NotInitializedException before initialize() is called."""
    manager = DatabaseManager(logger)
    dummy = DummyProvider(logger)
    manager._providers[IDatabaseManager.DEFAULT_DATABASE_NAME()] = dummy

    conn = DatabaseConnection()
    conn.name = "test"

    with pytest.raises(DatabaseManagerNotInitializedException):
        await manager.add_connection(conn)


# ---------------------------------------------------------------------------
# get_provider
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_provider_returns_default_for_default_id(
    logger: logging.Logger,
) -> None:
    """get_provider('default') delegates to get_default_provider."""
    manager = DatabaseManager(logger)
    dummy = DummyProvider(logger)
    manager._providers[IDatabaseManager.DEFAULT_DATABASE_NAME()] = dummy

    result = await manager.get_provider(IDatabaseManager.DEFAULT_DATABASE_NAME())
    assert result is dummy


@pytest.mark.asyncio
async def test_get_provider_returns_cached_if_present(
    logger: logging.Logger,
) -> None:
    """get_provider returns the cached instance when already registered."""
    manager = DatabaseManager(logger)
    dummy_default = DummyProvider(logger)
    dummy_other = DummyProvider(logger)
    manager._providers[IDatabaseManager.DEFAULT_DATABASE_NAME()] = dummy_default
    manager._providers["cached-id"] = dummy_other

    # Phase-3 init not needed when provider is already cached.
    result = await manager.get_provider("cached-id")
    assert result is dummy_other


@pytest.mark.asyncio
async def test_get_provider_raises_not_initialized_for_unknown_id(
    logger: logging.Logger,
) -> None:
    """get_provider raises NotInitializedException for uncached id without init."""
    manager = DatabaseManager(logger)
    dummy = DummyProvider(logger)
    manager._providers[IDatabaseManager.DEFAULT_DATABASE_NAME()] = dummy
    # No secret manager registered.

    with pytest.raises(DatabaseManagerNotInitializedException):
        await manager.get_provider("unknown-id")


# ---------------------------------------------------------------------------
# update_connection – validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_connection_rejects_default(logger: logging.Logger) -> None:
    """update_connection raises when the target id is 'default'."""
    manager = DatabaseManager(logger)
    sm = DummySecretManager()
    await manager.initialize(sm)  # type: ignore[arg-type]

    conn = DatabaseConnection()
    conn.id = IDatabaseManager.DEFAULT_DATABASE_NAME()

    with pytest.raises(DatabaseManagerInvalidOperationException):
        await manager.update_connection(conn)


@pytest.mark.asyncio
async def test_update_connection_rejects_raw_secret(logger: logging.Logger) -> None:
    """update_connection raises when raw_secret is set."""
    manager = DatabaseManager(logger)
    sm = DummySecretManager()
    await manager.initialize(sm)  # type: ignore[arg-type]
    dummy = DummyProvider(logger)
    manager._providers[IDatabaseManager.DEFAULT_DATABASE_NAME()] = dummy

    conn = DatabaseConnection()
    conn.id = "some-id"
    conn.raw_secret = {"raw_password": "s3cr3t"}

    with pytest.raises(DatabaseManagerInvalidOperationException):
        await manager.update_connection(conn)


@pytest.mark.asyncio
async def test_update_connection_rejects_missing_id(logger: logging.Logger) -> None:
    """update_connection raises when database_connection.id is None."""
    manager = DatabaseManager(logger)
    sm = DummySecretManager()
    await manager.initialize(sm)  # type: ignore[arg-type]
    dummy = DummyProvider(logger)
    manager._providers[IDatabaseManager.DEFAULT_DATABASE_NAME()] = dummy

    conn = DatabaseConnection()
    conn.name = "no-id"

    with pytest.raises(DatabaseManagerInvalidOperationException):
        await manager.update_connection(conn)


# ---------------------------------------------------------------------------
# delete_connection – validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_connection_rejects_default(logger: logging.Logger) -> None:
    """delete_connection raises when id is 'default'."""
    manager = DatabaseManager(logger)
    dummy = DummyProvider(logger)
    manager._providers[IDatabaseManager.DEFAULT_DATABASE_NAME()] = dummy

    with pytest.raises(DatabaseManagerInvalidOperationException):
        await manager.delete_connection(IDatabaseManager.DEFAULT_DATABASE_NAME())


@pytest.mark.asyncio
async def test_delete_connection_raises_not_found(logger: logging.Logger) -> None:
    """delete_connection raises when connection record does not exist."""
    manager = DatabaseManager(logger)
    dummy = DummyProvider(logger)
    # get_connection will return None because query result is None
    dummy.query_result = None
    manager._providers[IDatabaseManager.DEFAULT_DATABASE_NAME()] = dummy

    with pytest.raises(DatabaseManagerConnectionNotFoundException):
        await manager.delete_connection("non-existent-id")


# ---------------------------------------------------------------------------
# add_connection – validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_connection_rejects_both_raw_and_secret(
    logger: logging.Logger,
) -> None:
    """add_connection raises when both raw_secret and secret are set."""
    manager = DatabaseManager(logger)
    sm = DummySecretManager()
    await manager.initialize(sm)  # type: ignore[arg-type]
    dummy = DummyProvider(logger)
    manager._providers[IDatabaseManager.DEFAULT_DATABASE_NAME()] = dummy

    conn = DatabaseConnection()
    conn.name = "both"
    conn.raw_secret = {"raw_password": "x"}
    conn.secret = "some-secret-id"

    with pytest.raises(DatabaseManagerInvalidOperationException):
        await manager.add_connection(conn)


# ---------------------------------------------------------------------------
# DatabaseConnection model
# ---------------------------------------------------------------------------

def test_database_connection_raw_secret_field() -> None:
    """DatabaseConnection.raw_secret accepts dict and is excluded from to_dict."""
    conn = DatabaseConnection()
    conn.raw_secret = {"raw_password": "secret"}
    assert conn.raw_secret == {"raw_password": "secret"}
    # Must not appear in serialised form
    assert "raw_secret" not in conn.to_dict()
    assert "raw_secret" not in conn.to_json()


def test_database_connection_from_dict_roundtrip() -> None:
    """DatabaseConnection.from_dict recreates the entity correctly."""
    data = {
        "id": "databases:abc",
        "name": "my-db",
        "database_type": "surrealdb_remote",
        "parameters": {"endpoint": "wss://example.com"},
    }
    conn = DatabaseConnection.from_dict(data)
    assert conn.id == "abc"
    assert conn.name == "my-db"
    # database_type is now stored as a DatabaseProviderType enum
    assert conn.database_type == DatabaseProviderType.SURREALDB_REMOTE
    assert conn.parameters == {"endpoint": "wss://example.com"}
    assert conn.raw_secret is None


def test_database_connection_to_dict_recursive_serializes_enum() -> None:
    """to_dict(recursive=True) converts database_type to its string value."""
    conn = DatabaseConnection()
    conn.database_type = DatabaseProviderType.SURREALDB_REMOTE
    result = conn.to_dict(recursive=True)
    assert result["database_type"] == "surrealdb_remote"


def test_database_connection_to_dict_non_recursive_keeps_enum() -> None:
    """to_dict(recursive=False) keeps database_type as the enum object."""
    conn = DatabaseConnection()
    conn.database_type = DatabaseProviderType.SURREALDB_REMOTE
    result = conn.to_dict(recursive=False)
    assert result["database_type"] is DatabaseProviderType.SURREALDB_REMOTE


def test_database_connection_to_json_exclude_id() -> None:
    """DatabaseConnection.to_json(exclude_id=True) omits the id field."""
    conn = DatabaseConnection()
    conn.id = "my-id"
    conn.name = "my-db"
    result = json.loads(conn.to_json(exclude_id=True))
    assert "id" not in result
    assert result["name"] == "my-db"


# ---------------------------------------------------------------------------
# Integration tests – require real SurrealDB (loaded from JSON config)
# ---------------------------------------------------------------------------

_CONFIG_PATH = (
    Path(__file__).parent / "secret_test_config_default_database_configurations.json"
)


def _load_default_config() -> DatabaseConnection:
    """Load :py:class:`DatabaseConnection` from the integration test config file."""
    with open(_CONFIG_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    return DatabaseConnection.from_dict(data)


@pytest.mark.skipif(
    not _CONFIG_PATH.exists(),
    reason="Integration config not found; skipping real-DB tests.",
)
@pytest.mark.asyncio
async def test_initialize_default_connection_real(logger: logging.Logger) -> None:
    """Integration: initialize_default_connection connects to a real SurrealDB."""
    config = _load_default_config()
    manager = DatabaseManager(logger)
    try:
        await manager.initialize_default_connection(config)
        provider = manager.get_default_provider()
        # Smoke-test the connection with a simple query (SurrealDB requires FROM clause)
        raw = await provider.query_raw("INFO FOR DB")
        assert raw is not None
    finally:
        await manager._remove_provider(IDatabaseManager.DEFAULT_DATABASE_NAME())


@pytest.mark.skipif(
    not _CONFIG_PATH.exists(),
    reason="Integration config not found; skipping real-DB tests.",
)
@pytest.mark.asyncio
async def test_initialize_default_connection_databases_entry_exists(
    logger: logging.Logger,
) -> None:
    """Integration: after init, the 'default' entry exists in the databases collection."""
    config = _load_default_config()
    manager = DatabaseManager(logger)
    try:
        await manager.initialize_default_connection(config)
        entry = await manager.get_connection(IDatabaseManager.DEFAULT_DATABASE_NAME())
        assert entry is not None
        assert entry.name == IDatabaseManager.DEFAULT_DATABASE_NAME()
    finally:
        await manager._remove_provider(IDatabaseManager.DEFAULT_DATABASE_NAME())


# ---------------------------------------------------------------------------
# Integration tests – local (embedded) SurrealDB
# ---------------------------------------------------------------------------

_LOCAL_CONFIG_PATH = (
    Path(__file__).parent / "secret_test_config_default_database_configurations_local.json"
)


def _load_local_config() -> DatabaseConnection:
    """Load DatabaseConnection from the local (embedded) integration test config."""
    with open(_LOCAL_CONFIG_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    return DatabaseConnection.from_dict(data)


@pytest.mark.skipif(
    not _LOCAL_CONFIG_PATH.exists(),
    reason="Local integration config not found; skipping local-DB tests.",
)
@pytest.mark.asyncio
async def test_initialize_default_connection_local_real(
    logger: logging.Logger,
) -> None:
    """Integration: initialize_default_connection works with local (embedded) SurrealDB."""
    config = _load_local_config()
    manager = DatabaseManager(logger)
    try:
        await manager.initialize_default_connection(config)
        provider = manager.get_default_provider()
        raw = await provider.query_raw("INFO FOR DB")
        assert raw is not None
    finally:
        await manager._remove_provider(IDatabaseManager.DEFAULT_DATABASE_NAME())


@pytest.mark.skipif(
    not _LOCAL_CONFIG_PATH.exists(),
    reason="Local integration config not found; skipping local-DB tests.",
)
@pytest.mark.asyncio
async def test_initialize_default_connection_local_databases_entry_exists(
    logger: logging.Logger,
) -> None:
    """Integration: after local init, the 'default' entry exists in the databases collection."""
    config = _load_local_config()
    manager = DatabaseManager(logger)
    try:
        await manager.initialize_default_connection(config)
        entry = await manager.get_connection(IDatabaseManager.DEFAULT_DATABASE_NAME())
        assert entry is not None
        assert entry.name == IDatabaseManager.DEFAULT_DATABASE_NAME()
    finally:
        await manager._remove_provider(IDatabaseManager.DEFAULT_DATABASE_NAME())


@pytest.mark.skipif(
    not _LOCAL_CONFIG_PATH.exists(),
    reason="Local integration config not found; skipping local-DB tests.",
)
@pytest.mark.asyncio
async def test_local_add_and_get_connection(
    logger: logging.Logger,
) -> None:
    """Integration: add_connection and get_connection work with embedded SurrealDB."""
    config = _load_local_config()
    manager = DatabaseManager(logger)
    sm = DummySecretManager()
    try:
        await manager.initialize_default_connection(config)
        await manager.initialize(sm)  # type: ignore[arg-type]

        conn = DatabaseConnection()
        conn.name = "local-test-conn"
        conn.description = "Integration test connection"
        conn.database_type = DatabaseProviderType.SURREALDB_LOCAL

        created = await manager.add_connection(conn)
        assert created is not None
        assert created.id is not None
        assert created.name == "local-test-conn"

        fetched = await manager.get_connection(created.id)
        assert fetched is not None
        assert fetched.name == "local-test-conn"

        # Cleanup
        await manager.delete_connection(created.id)
    finally:
        await manager._remove_provider(IDatabaseManager.DEFAULT_DATABASE_NAME())


@pytest.mark.skipif(
    not _LOCAL_CONFIG_PATH.exists(),
    reason="Local integration config not found; skipping local-DB tests.",
)
@pytest.mark.asyncio
async def test_local_query_raw_via_provider(
    logger: logging.Logger,
) -> None:
    """Integration: query_raw works through the default local provider."""
    config = _load_local_config()
    manager = DatabaseManager(logger)
    try:
        await manager.initialize_default_connection(config)
        provider = manager.get_default_provider()

        await provider.query_raw(
            "CREATE TestRecord:local_mgr_001 SET name = 'Local Manager Test'"
        )
        result = await provider.query_raw(
            "SELECT * FROM TestRecord:local_mgr_001"
        )
        assert result is not None
        if isinstance(result, list):
            assert len(result) >= 1

        await provider.query_raw("DELETE TestRecord:local_mgr_001")
    finally:
        await manager._remove_provider(IDatabaseManager.DEFAULT_DATABASE_NAME())
