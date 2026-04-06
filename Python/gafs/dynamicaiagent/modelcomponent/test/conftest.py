"""Shared integration fixtures for modelcomponent tests.

All tests in this folder are integration tests that require a reachable
SurrealDB instance. Connection settings are read from:

- `secret_test_db_config.json`

If the file is missing, tests are skipped.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

import pytest

from gafs.dynamicaiagent.cloudaicomponent.i_cloud_ai_component import ICloudAiComponent
from gafs.dynamicaiagent.common.databasemanager import DatabaseManager, IDatabaseManager
from gafs.dynamicaiagent.modelcomponent.model_catalogue_service import ModelCatalogueService
from gafs.dynamicaiagent.modelcomponent.model_component import ModelComponent
from gafs.dynamicaiagent.modelcomponent.model_service import ModelService
from gafs.dynamicaiagent.modelcomponent.models.ai_connection_parameters import (
    AiConnectionParameters,
)
from gafs.dynamicaiagent.modelcomponent.models.ai_output import ChatCompletionOutput, EmbeddingOutput
from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.ai_response import AiResponse
from gafs.dynamicaiagent.modelcomponent.models.model_component_configurations import (
    ModelComponentConfigurations,
)
from gafs.dynamicaiagent.utils.databaseprovider import DatabaseProviderType, IDatabaseProvider
from gafs.dynamicaiagent.utils.databaseprovider.surrealdb_remote_provider import (
    RemoteSurrealDbOptions,
)


TEST_DIR = Path(__file__).resolve().parent
DB_CONFIG_FILENAME = "secret_test_db_config.json"

SECRET_FIXTURE = "secret_test_secret_azure_openai_japan_east.json"
SECRET_ID = "secret_test_azure_openai_japan_east"


def _logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s - %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def _load_db_config() -> dict[str, Any] | None:
    path = TEST_DIR / DB_CONFIG_FILENAME
    if path.is_file():
        with path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            return loaded
    return None


def _build_options(config: dict[str, Any]) -> RemoteSurrealDbOptions:
    options = RemoteSurrealDbOptions()
    options.endpoint = config["endpoint"]
    options.namespace = config["namespace"]
    options.database = config["database"]
    options.username = config["username"]
    options.password = config["password"]
    options.database_type = DatabaseProviderType.SURREALDB_REMOTE
    options.database_name = IDatabaseManager.DEFAULT_DATABASE_NAME()
    return options


def load_json_fixture(name: str) -> dict[str, Any]:
    path = TEST_DIR / name
    with path.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    if not isinstance(loaded, dict):
        raise ValueError(f"Fixture must be an object: {path}")
    return loaded


class _StubCloudAiComponent(ICloudAiComponent):
    """Stub cloud component that returns deterministic outputs."""

    def __init__(self) -> None:
        self.last_connection: AiConnectionParameters | None = None
        self.last_request: AiRequest | None = None

    async def invoke(
        self, connection_parameters: AiConnectionParameters, request: AiRequest
    ) -> AiResponse:
        self.last_connection = connection_parameters
        self.last_request = request

        response = AiResponse()
        if request.operation_type.value == "embedding":
            out = EmbeddingOutput()
            out.embedding = [0.0, 0.0, 0.0, 0.0]
            response.output = out
        else:
            out = ChatCompletionOutput()
            out.messages = [{"role": "assistant", "parts": [{"type": "text", "text": "ok"}]}]
            response.output = out
        return response


class IntegrationEnv:
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


async def _create_env() -> IntegrationEnv:
    config = _load_db_config()
    if not config:
        raise RuntimeError(
            "DB config is missing. Add secret_test_db_config.json."
        )

    logger = _logger("test_modelcomponent_integration")
    manager = DatabaseManager(logger)
    await manager.add_provider(_build_options(config))

    provider = manager.get_default_database_provider()
    if provider is None:
        raise RuntimeError("Default database provider is not available.")

    catalogue_service = ModelCatalogueService(logger)
    model_service = ModelService(logger=logger)
    stub_cloud = _StubCloudAiComponent()
    component = ModelComponent(
        logger=logger,
        model_catalogue_service=catalogue_service,
        model_service=model_service,
        cloud_ai_component=stub_cloud,
    )
    await component.initialize(manager)

    return IntegrationEnv(
        logger=logger,
        manager=manager,
        provider=provider,
        catalogue_service=catalogue_service,
        model_service=model_service,
        component=component,
        stub_cloud=stub_cloud,
    )


async def _cleanup_env(env: IntegrationEnv) -> None:
    await env.manager.remove_provider(IDatabaseManager.DEFAULT_DATABASE_NAME())


@pytest.fixture
def integration_env_async() -> Any:
    """Async-friendly environment factory.

    Usage:
        async def test_x(integration_env_async):
            env = await integration_env_async()
    """

    config = _load_db_config()
    if not config:
        pytest.skip(
            "DB config is missing. Add secret_test_db_config.json."
        )

    logger = _logger("test_modelcomponent_integration")
    manager = DatabaseManager(logger)

    async def factory() -> IntegrationEnv:
        await manager.add_provider(_build_options(config))
        provider = manager.get_default_database_provider()
        if provider is None:
            raise RuntimeError("Default database provider is not available.")

        catalogue_service = ModelCatalogueService(logger)
        model_service = ModelService(logger=logger)
        stub_cloud = _StubCloudAiComponent()
        component = ModelComponent(
            logger=logger,
            model_catalogue_service=catalogue_service,
            model_service=model_service,
            cloud_ai_component=stub_cloud,
        )
        await component.initialize(manager)
        return IntegrationEnv(
            logger=logger,
            manager=manager,
            provider=provider,
            catalogue_service=catalogue_service,
            model_service=model_service,
            component=component,
            stub_cloud=stub_cloud,
        )

    async def cleanup() -> None:
        await manager.remove_provider(IDatabaseManager.DEFAULT_DATABASE_NAME())

    factory.cleanup = cleanup  # type: ignore[attr-defined]
    return factory


def unique_suffix() -> str:
    return str(int(time.time()))

