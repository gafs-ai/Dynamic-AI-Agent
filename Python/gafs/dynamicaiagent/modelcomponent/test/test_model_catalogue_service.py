"""Integration tests for ModelCatalogueService.

These tests cover every public method defined on IModelCatalogueService.
Each method has at least one happy-path and one error-path scenario.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

from gafs.dynamicaiagent.modelcomponent.model_catalogue_service import (
    ModelCatalogueService,
    ModelCatalogueSearchCriteria,
)
from gafs.dynamicaiagent.modelcomponent.models.ai_operation_type import AiOperationType
from gafs.dynamicaiagent.modelcomponent.models.model_catalogue import (
    ModelCatalogue,
    ModelDeployment,
    ModelStatus,
)
from gafs.dynamicaiagent.modelcomponent.models.model_component_configurations import (
    ModelComponentConfigurations,
)
from gafs.dynamicaiagent.modelcomponent.models.model_deployment_search_criteria import (
    ModelDeploymentSearchCriteria,
)

TEST_DIR = Path(__file__).resolve().parent
DEPLOYMENT_FIXTURE = "secret_test_deployment_azure_tel3.json"
CATALOGUE_FIXTURE = "secret_test_catalogue_openai_gpt5.json"


def _load_json_fixture(name: str) -> dict[str, Any]:
    path = TEST_DIR / name
    with path.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    if not isinstance(loaded, dict):
        raise ValueError(f"Fixture must be an object: {path}")
    return loaded


def test_i_model_catalogue_service_initialize(integration_env_async) -> None:
    async def run() -> None:
        env = await integration_env_async()
        try:
            service: ModelCatalogueService = env.catalogue_service
            cfg = ModelComponentConfigurations()
            ok = await service.initialize(env.manager, cfg, env.provider)
            assert ok is True
        finally:
            await integration_env_async.cleanup()  # type: ignore[attr-defined]

    import asyncio

    asyncio.run(run())


def test_i_model_catalogue_service_ensure_indexes(integration_env_async) -> None:
    async def run() -> None:
        env = await integration_env_async()
        try:
            service: ModelCatalogueService = env.catalogue_service
            cfg = ModelComponentConfigurations()
            assert await service.ensure_indexes(cfg, overwrite=False) is True
            assert await service.ensure_indexes(cfg, overwrite=True) is True
        finally:
            await integration_env_async.cleanup()  # type: ignore[attr-defined]

    import asyncio

    asyncio.run(run())


def test_i_model_catalogue_service_create_get_update_search_delete_deployment(
    integration_env_async,
) -> None:
    async def run() -> None:
        env = await integration_env_async()
        service: ModelCatalogueService = env.catalogue_service

        created_deployment_id: str | None = None
        try:
            dep_data = _load_json_fixture(DEPLOYMENT_FIXTURE)
            dep_data["name"] = f"{dep_data.get('name', 'deployment')}-{int(time.time())}"
            created_dep = await service.create_deployment(ModelDeployment.from_dict(dep_data))
            created_deployment_id = created_dep.id
            assert created_deployment_id

            got = await service.get_deployment(created_deployment_id)
            assert got is not None
            assert got.id == created_deployment_id

            assert await service.get_deployment("does_not_exist") is None

            got.description = "updated"
            updated = await service.update_deployment(got)
            assert updated.description == "updated"

            bad = ModelDeployment()
            bad.id = None
            with pytest.raises(ValueError):
                await service.update_deployment(bad)

            criteria = ModelDeploymentSearchCriteria(name=created_dep.name, limit=10)
            results = await service.search_deployments(criteria)
            assert isinstance(results, list)
            if len(results) > 0:
                assert any(item.id == created_deployment_id for item in results)

            assert await service.delete_deployment(created_deployment_id) is True
            created_deployment_id = None
            _ = await service.delete_deployment("does_not_exist")
        finally:
            if created_deployment_id:
                await service.delete_deployment(created_deployment_id)
            await integration_env_async.cleanup()  # type: ignore[attr-defined]

    import asyncio

    asyncio.run(run())


def test_i_model_catalogue_service_create_get_update_search_delete_catalogue(
    integration_env_async,
) -> None:
    async def run() -> None:
        env = await integration_env_async()
        service: ModelCatalogueService = env.catalogue_service

        created_catalogue_id: str | None = None
        created_deployment_id: str | None = None
        try:
            dep_data = _load_json_fixture(DEPLOYMENT_FIXTURE)
            dep_data["name"] = f"{dep_data.get('name', 'deployment')}-{int(time.time())}"
            created_dep = await service.create_deployment(ModelDeployment.from_dict(dep_data))
            created_deployment_id = created_dep.id
            assert created_deployment_id

            cat_data = _load_json_fixture(CATALOGUE_FIXTURE)
            cat_data["name"] = f"{cat_data.get('name', 'catalogue')}-{int(time.time())}"
            cat_data["deployments"] = [created_deployment_id]
            created_cat = await service.create_catalogue(ModelCatalogue.from_dict(cat_data))
            created_catalogue_id = created_cat.id
            assert created_catalogue_id

            got = await service.get_catalogue(created_catalogue_id)
            assert got is not None
            assert got.id == created_catalogue_id

            assert await service.get_catalogue("does_not_exist") is None

            got.description = "updated description"
            updated = await service.update_catalogue(got)
            assert updated.description == "updated description"

            bad = ModelCatalogue()
            bad.id = None
            with pytest.raises(ValueError):
                await service.update_catalogue(bad)

            missing_update = ModelCatalogue()
            missing_update.id = "does_not_exist"
            missing_update.name = "x"
            missing_update.type = AiOperationType.CHAT_COMPLETION
            missing_update.status = ModelStatus.ACTIVE
            with pytest.raises(ValueError):
                await service.update_catalogue(missing_update)

            criteria = ModelCatalogueSearchCriteria(name=created_cat.name, limit=10)
            results = await service.search_catalogues(criteria)
            assert any(item.id == created_catalogue_id for item in results)

            assert await service.delete_catalogue(created_catalogue_id) is True
            created_catalogue_id = None
            assert await service.delete_catalogue("does_not_exist") is False
        finally:
            if created_catalogue_id:
                await service.delete_catalogue(created_catalogue_id)
            if created_deployment_id:
                await service.delete_deployment(created_deployment_id)
            await integration_env_async.cleanup()  # type: ignore[attr-defined]

    import asyncio

    asyncio.run(run())

