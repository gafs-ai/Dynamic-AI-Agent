from __future__ import annotations

import logging
from typing import Any

import pytest

from gafs.dynamicaiagent.common.databasemanager.database_manager import DatabaseManager
from gafs.dynamicaiagent.common.databasemanager.exceptions.database_manager_exceptions import (
    DatabaseManagerConfigurationException,
)
from gafs.dynamicaiagent.common.databasemanager.i_database_manager import IDatabaseManager
from gafs.dynamicaiagent.utils.databaseprovider import DatabaseType
from gafs.dynamicaiagent.utils.databaseprovider.surrealdb_remote_provider import (
    RemoteSurrealDbOptions,
)


class DummyProvider:
    """Simple test double for IDatabaseProvider used in DatabaseManager tests."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.initialized_with: list[RemoteSurrealDbOptions] = []
        self.closed: bool = False

    async def initialize(self, options: RemoteSurrealDbOptions) -> bool:
        self.initialized_with.append(options)
        return True

    async def close(self) -> None:
        self.closed = True


@pytest.fixture
def logger() -> logging.Logger:
    """Create a logger for DatabaseManager tests."""
    logger = logging.getLogger("database_manager_test")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def _make_options(database_name: str) -> RemoteSurrealDbOptions:
    """Create simple RemoteSurrealDbOptions for tests (no real DB connection)."""
    options = RemoteSurrealDbOptions()
    options.endpoint = "wss://example.com/rpc"
    options.namespace = "ns"
    options.database = "db"
    options.username = "user"
    options.password = "pass"
    options.database_type = DatabaseType.SURREALDB_REMOTE
    options.database_name = database_name
    return options


@pytest.mark.asyncio
async def test_add_provider_new_sets_and_gets_provider(
    monkeypatch: Any, logger: logging.Logger
) -> None:
    """Adding a new provider stores it and allows retrieval."""
    created_providers: list[DummyProvider] = []

    def _dummy_factory(l: logging.Logger) -> DummyProvider:
        p = DummyProvider(l)
        created_providers.append(p)
        return p

    from gafs.dynamicaiagent.common.databasemanager import database_manager as dm_module

    monkeypatch.setattr(dm_module, "SurrealDbRemoteProvider", _dummy_factory)

    manager = DatabaseManager(logger)
    options = _make_options("test-db")

    result = await manager.add_provider(options)

    assert result is True
    provider = manager.get_provider("test-db")
    assert provider is created_providers[0]


@pytest.mark.asyncio
async def test_add_provider_duplicate_without_overwrite(
    monkeypatch: Any, logger: logging.Logger
) -> None:
    """Duplicate add with overwrite=False returns False and keeps original provider."""
    created_providers: list[DummyProvider] = []

    def _dummy_factory(l: logging.Logger) -> DummyProvider:
        p = DummyProvider(l)
        created_providers.append(p)
        return p

    from gafs.dynamicaiagent.common.databasemanager import database_manager as dm_module

    monkeypatch.setattr(dm_module, "SurrealDbRemoteProvider", _dummy_factory)

    manager = DatabaseManager(logger)
    options = _make_options("dup-db")

    first = await manager.add_provider(options)
    assert first is True
    assert len(created_providers) == 1

    second = await manager.add_provider(options, overwrite=False)
    assert second is False
    assert len(created_providers) == 1


@pytest.mark.asyncio
async def test_add_provider_duplicate_with_overwrite(
    monkeypatch: Any, logger: logging.Logger
) -> None:
    """Duplicate add with overwrite=True replaces the provider and closes the old one."""
    created_providers: list[DummyProvider] = []

    def _dummy_factory(l: logging.Logger) -> DummyProvider:
        p = DummyProvider(l)
        created_providers.append(p)
        return p

    from gafs.dynamicaiagent.common.databasemanager import database_manager as dm_module

    monkeypatch.setattr(dm_module, "SurrealDbRemoteProvider", _dummy_factory)

    manager = DatabaseManager(logger)
    options = _make_options("overwrite-db")

    first = await manager.add_provider(options)
    assert first is True
    assert len(created_providers) == 1
    original = created_providers[0]

    second = await manager.add_provider(options, overwrite=True)
    assert second is True
    assert len(created_providers) == 2
    replacement = created_providers[1]

    assert original.closed is True
    assert manager.get_provider("overwrite-db") is replacement


@pytest.mark.asyncio
async def test_add_provider_unsupported_type_raises(logger: logging.Logger) -> None:
    """Unsupported DatabaseType raises DatabaseManagerConfigurationException."""
    manager = DatabaseManager(logger)
    options = _make_options("unsupported-db")
    # Bypass RemoteSurrealDbOptions.__setattr__ which only accepts SURREALDB_REMOTE
    object.__setattr__(options, "database_type", DatabaseType.SURREALDB_SUBPROCESS)

    with pytest.raises(DatabaseManagerConfigurationException):
        await manager.add_provider(options)


def test_get_provider_existing(logger: logging.Logger) -> None:
    """get_provider returns provider when it exists."""
    manager = DatabaseManager(logger)
    dummy = DummyProvider(logger)
    manager._providers["existing-db"] = dummy  # type: ignore[attr-defined]

    provider = manager.get_provider("existing-db")
    assert provider is dummy


def test_get_provider_not_found(logger: logging.Logger) -> None:
    """get_provider returns None for non-existing database name."""
    manager = DatabaseManager(logger)
    provider = manager.get_provider("non-existing-db")
    assert provider is None


def test_get_default_database_provider_when_present(
    logger: logging.Logger,
) -> None:
    """Default provider is returned when registered under DEFAULT_DATABASE_NAME()."""
    manager = DatabaseManager(logger)
    default_name = IDatabaseManager.DEFAULT_DATABASE_NAME()
    dummy = DummyProvider(logger)
    manager._providers[default_name] = dummy  # type: ignore[attr-defined]
    manager._default_database_provider = dummy  # type: ignore[attr-defined]

    default = manager.get_default_database_provider()
    assert default is dummy


def test_get_default_database_provider_when_absent(logger: logging.Logger) -> None:
    """None is returned when no default provider is registered."""
    manager = DatabaseManager(logger)
    default = manager.get_default_database_provider()
    assert default is None


@pytest.mark.asyncio
async def test_remove_provider_existing_clears_and_closes(
    logger: logging.Logger,
) -> None:
    """remove_provider removes an existing provider and closes it."""
    manager = DatabaseManager(logger)
    dummy = DummyProvider(logger)
    manager._providers["removable-db"] = dummy  # type: ignore[attr-defined]
    manager._default_database_provider = dummy  # type: ignore[attr-defined]

    removed = await manager.remove_provider("removable-db")
    assert removed is True
    assert "removable-db" not in manager._providers  # type: ignore[attr-defined]
    assert dummy.closed is True
    assert manager.get_default_database_provider() is None


@pytest.mark.asyncio
async def test_remove_provider_not_found(logger: logging.Logger) -> None:
    """remove_provider returns False when database_name does not exist."""
    manager = DatabaseManager(logger)
    removed = await manager.remove_provider("non-existing-db")
    assert removed is False

