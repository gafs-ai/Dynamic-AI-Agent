"""conftest.py - Shared integration fixtures for modelcomponent tests.

All tests in this folder are integration tests that require a reachable
SurrealDB instance.  Connection settings are read from:

    test/secret_test_db_config.json

If the file is missing, all tests are skipped.

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
import time
from pathlib import Path
from typing import Any

import pytest

from gafs.dynamicaiagent.cloudaicomponent import CloudAiComponent
from gafs.dynamicaiagent.common.databasemanager import DatabaseConnection, DatabaseManager
from gafs.dynamicaiagent.modelcomponent import (
    ModelCatalogueService,
    ModelComponent,
    ModelService,
)
from gafs.dynamicaiagent.modelcomponent.models.ai_connection_parameters import (
    AiConnectionParameters,
)
from gafs.dynamicaiagent.modelcomponent.models.ai_output import (
    ChatCompletionOutput,
    EmbeddingOutput,
)
from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.ai_response import AiResponse
from gafs.dynamicaiagent.utils.databaseprovider import DatabaseProviderType, IDatabaseProvider


TEST_DIR = Path(__file__).resolve().parent
DB_CONFIG_FILENAME = "secret_test_db_config.json"

SECRET_FIXTURE = "secret_test_secret_azure_openai_japan_east.json"
SECRET_ID = "secret_test_azure_openai_japan_east"


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
    lg.setLevel(logging.INFO)
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
    conn.description = "ModelComponent integration test database"
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


def load_json_fixture(name: str) -> dict[str, Any]:
    """Load a JSON fixture file from the test directory.

    Args:
        name: Filename relative to the test directory.

    Returns:
        Loaded JSON object.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the JSON is not an object (dict).
    """
    path = TEST_DIR / name
    with path.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    if not isinstance(loaded, dict):
        raise ValueError(f"Fixture must be a JSON object: {path}")
    return loaded


def unique_suffix() -> str:
    """Return a timestamp-based suffix for unique test record names."""
    return str(int(time.time() * 1000))


# ---------------------------------------------------------------------------
# Stub AI component
# ---------------------------------------------------------------------------

class _StubCloudAiComponent:
    """Stub AI component returning deterministic outputs without real API calls."""

    def __init__(self) -> None:
        self.last_connection: AiConnectionParameters | None = None
        self.last_request: AiRequest | None = None

    async def invoke(
        self,
        connection: AiConnectionParameters,
        request: AiRequest,
    ) -> AiResponse:
        """Return a deterministic response based on operation type."""
        self.last_connection = connection
        self.last_request = request

        response = AiResponse()
        op_type = getattr(request.operation_type, "value", str(request.operation_type))
        if op_type == "embedding":
            out = EmbeddingOutput()
            out.embedding = [0.1, 0.2, 0.3, 0.4]
            response.output = out
        else:
            out = ChatCompletionOutput()
            from gafs.dynamicaiagent.modelcomponent.models.message import Message
            msg = Message()
            msg.role = "assistant"
            from gafs.dynamicaiagent.modelcomponent.models.message import TextMessagePart
            part = TextMessagePart()
            part.text = "ok"
            msg.content = [part]
            out.messages = [msg]
            response.output = out
        return response


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
        catalogue_service: ModelCatalogueService,
        model_service: ModelService,
        component: ModelComponent,
        stub_cloud: _StubCloudAiComponent,
    ) -> None:
        self.logger = logger
        self.manager = manager
        self.provider = provider
        self.catalogue_service = catalogue_service
        self.model_service = model_service
        self.component = component
        self.stub_cloud = stub_cloud


# ---------------------------------------------------------------------------
# Minimal test SecretManager for DatabaseManager phase-3 initialization
# ---------------------------------------------------------------------------

class _SimpleSecret:
    def __init__(self, secret_id: str, credentials: dict[str, Any]) -> None:
        self.id = secret_id
        self.secret = credentials
        self.raw_secret = credentials


class _TestSecretManager:
    """Minimal concrete SecretManager for enabling phase-3 DatabaseManager init."""

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
# Async fixture factory
# ---------------------------------------------------------------------------

@pytest.fixture
def integration_env_async() -> Any:
    """Return an async factory that builds a fully initialized IntegrationEnv.

    Usage in tests::

        def test_something(integration_env_async):
            async def run():
                env = await integration_env_async()
                try:
                    # ... test code ...
                finally:
                    await integration_env_async.cleanup()
            asyncio.run(run())

    The fixture skips if ``secret_test_db_config.json`` is absent.
    """
    config = _load_db_config()
    if not config:
        pytest.skip(
            f"DB config is missing. Add {DB_CONFIG_FILENAME} to the test folder."
        )

    lg = _logger("test_modelcomponent_integration")
    conn_config = _build_connection(config)
    manager = DatabaseManager(lg)

    async def factory() -> IntegrationEnv:
        await manager.initialize_default_connection(conn_config)
        await manager.initialize(_TestSecretManager())

        provider = manager.get_default_provider()

        catalogue_service = ModelCatalogueService(lg)
        model_service = ModelService(lg)
        stub_cloud = _StubCloudAiComponent()
        component = ModelComponent(
            logger=lg,
            model_catalogue_service=catalogue_service,
            model_service=model_service,
            cloud_ai_component=stub_cloud,
        )
        await component.initialize(manager)

        return IntegrationEnv(
            logger=lg,
            manager=manager,
            provider=provider,
            catalogue_service=catalogue_service,
            model_service=model_service,
            component=component,
            stub_cloud=stub_cloud,
        )

    async def cleanup() -> None:
        try:
            provider = manager.get_default_provider()
            await provider.close()
        except Exception:
            pass

    factory.cleanup = cleanup  # type: ignore[attr-defined]
    return factory
