"""conftest.py - Shared integration fixtures for toolcomponent tests.

All tests in this folder are integration tests that require a reachable
SurrealDB instance.  Connection settings are read from:

    test/secret_test_db_config.json

Docker-based tests additionally require Docker Desktop to be running.
Those tests are automatically skipped if Docker is unavailable.

Structure of secret_test_db_config.json:
    {
        "endpoint":  "wss://...",
        "namespace": "...",
        "database":  "...",
        "username":  "...",
        "password":  "..."
    }
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from gafs.dynamicaiagent.common.databasemanager import DatabaseConnection, DatabaseManager
from gafs.dynamicaiagent.toolcomponent import (
    DockerSandboxService,
    SandboxCatalogueService,
    ToolCatalogueService,
    ToolComponent,
    ToolComponentConfigurations,
)
from gafs.dynamicaiagent.utils.databaseprovider import DatabaseProviderType, IDatabaseProvider

TEST_DIR = Path(__file__).resolve().parent
DB_CONFIG_FILENAME = "secret_test_db_config.json"


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def pytest_configure(config: pytest.Config) -> None:
    """Add file handler for all test logs."""
    log_file = TEST_DIR / "test_run.log"
    if not any(
        isinstance(h, logging.FileHandler)
        for h in logging.root.handlers
    ):
        logging.root.setLevel(logging.DEBUG)
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        logging.root.addHandler(handler)


def _logger(name: str) -> logging.Logger:
    lg = logging.getLogger(name)
    if not lg.handlers:
        h = logging.StreamHandler()
        h.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s - %(message)s")
        )
        lg.addHandler(h)
    lg.setLevel(logging.DEBUG)
    return lg


# ---------------------------------------------------------------------------
# DB config helpers
# ---------------------------------------------------------------------------

def _load_db_config() -> dict[str, Any] | None:
    path = TEST_DIR / DB_CONFIG_FILENAME
    if path.is_file():
        with path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            return loaded
    return None


def _build_connection(config: dict[str, Any]) -> DatabaseConnection:
    """Build a DatabaseConnection from the secret_test_db_config dict."""
    conn = DatabaseConnection()
    conn.id = "default"
    conn.name = "default"
    conn.description = "ToolComponent integration test database"
    conn.database_type = DatabaseProviderType.SURREALDB_REMOTE
    conn.parameters = {
        "endpoint": config["endpoint"],
        "namespace": config["namespace"],
        "database": config["database"],
    }
    conn.raw_secret = {
        "username": config["username"],
        "password": config["password"],
    }
    return conn


# ---------------------------------------------------------------------------
# Minimal SecretManager for DatabaseManager phase-3 initialization
# ---------------------------------------------------------------------------

class _SimpleSecret:
    def __init__(self, secret_id: str, credentials: dict[str, Any]) -> None:
        self.id = secret_id
        self.secret = credentials
        self.raw_secret = credentials


class _TestSecretManager:
    """Minimal SecretManager for enabling phase-3 DatabaseManager initialization."""

    def __init__(self) -> None:
        self._secrets: dict[str, _SimpleSecret] = {}
        self._counter = 0

    async def create_secret(self, secret: Any) -> _SimpleSecret:
        self._counter += 1
        sid = f"test_secret_{self._counter}"
        creds: dict[str, Any] = {}
        if hasattr(secret, "raw_secret") and isinstance(secret.raw_secret, dict):
            creds = secret.raw_secret
        elif hasattr(secret, "secret") and isinstance(secret.secret, dict):
            creds = secret.secret
        result = _SimpleSecret(sid, creds)
        self._secrets[sid] = result
        return result

    async def get_secret(self, secret_id: str, decrypt: bool = False) -> _SimpleSecret | None:
        return self._secrets.get(secret_id)


# ---------------------------------------------------------------------------
# Integration environment container
# ---------------------------------------------------------------------------

class IntegrationEnv:
    """Container for all objects needed in integration tests."""

    def __init__(
        self,
        *,
        logger: logging.Logger,
        manager: DatabaseManager,
        provider: IDatabaseProvider,
        catalogue_service: ToolCatalogueService,
        sandbox_service: SandboxCatalogueService,
        docker_service: DockerSandboxService,
        component: ToolComponent,
        app_data_folder: str,
    ) -> None:
        self.logger = logger
        self.manager = manager
        self.provider = provider
        self.catalogue_service = catalogue_service
        self.sandbox_service = sandbox_service
        self.docker_service = docker_service
        self.component = component
        self.app_data_folder = app_data_folder


# ---------------------------------------------------------------------------
# Async fixture factory
# ---------------------------------------------------------------------------

@pytest.fixture
def integration_env_async(tmp_path: Any) -> Any:
    """Return an async factory that builds a fully initialized IntegrationEnv.

    Skips if ``secret_test_db_config.json`` is absent.
    """
    config = _load_db_config()
    if not config:
        pytest.skip(
            f"DB config is missing. Add {DB_CONFIG_FILENAME} to the test folder."
        )

    lg = _logger("test_toolcomponent_integration")
    conn_config = _build_connection(config)
    manager = DatabaseManager(lg)
    app_data_folder = str(tmp_path / "tool_app_data")

    async def factory() -> IntegrationEnv:
        await manager.initialize_default_connection(conn_config)
        await manager.initialize(_TestSecretManager())

        provider = manager.get_default_provider()

        # Create (or upsert) ToolComponentConfigurations record in DB
        # (required for ToolComponent.initialize())
        configurations = ToolComponentConfigurations()
        configurations.app_data_folder = app_data_folder
        config_json = configurations.to_json(exclude_id=True)
        await provider.query_raw(
            f"UPSERT component_configurations:tool_component MERGE {config_json};"
        )

        catalogue_service = ToolCatalogueService(lg)
        sandbox_service = SandboxCatalogueService(lg)
        docker_service = DockerSandboxService(lg)
        component = ToolComponent(
            logger=lg,
            tool_catalogue_service=catalogue_service,
            sandbox_catalogue_service=sandbox_service,
            docker_sandbox_service=docker_service,
        )
        await component.initialize(manager)

        return IntegrationEnv(
            logger=lg,
            manager=manager,
            provider=provider,
            catalogue_service=catalogue_service,
            sandbox_service=sandbox_service,
            docker_service=docker_service,
            component=component,
            app_data_folder=app_data_folder,
        )

    return factory
