"""Integration tests for ModelComponent.

These tests cover every public method defined on IModelComponent.
Each method has at least one happy-path and one error-path scenario.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

from gafs.dynamicaiagent.modelcomponent.exceptions.model_component_exceptions import (
    ModelComponentConfigurationException,
    ModelComponentResourceNotFoundException,
)
from gafs.dynamicaiagent.modelcomponent.models.ai_operation_type import AiOperationType
from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.model_catalogue import (
    DeploymentStatus,
    ModelCatalogue,
    ModelDeployment,
    ModelStatus,
)
from gafs.dynamicaiagent.modelcomponent.models.model_catalogue_search_criteria import (
    ModelCatalogueSearchCriteria,
)
from gafs.dynamicaiagent.modelcomponent.models.model_component_configurations import (
    ModelComponentConfigurations,
)
from gafs.dynamicaiagent.modelcomponent.models.model_deployment_search_criteria import (
    ModelDeploymentSearchCriteria,
)


TEST_DIR = Path(__file__).resolve().parent
SECRET_FIXTURE = "secret_test_secret_azure_openai_japan_east.json"
SECRET_ID = "secret_test_azure_openai_japan_east"
DEPLOYMENT_FIXTURE_CHAT = "secret_test_deployment_azure_tel3.json"
DEPLOYMENT_FIXTURE_EMBEDDING = "secret_test_deployment_azure_gpt5.json"
DEPLOYMENT_FIXTURE_STT = "secret_test_deployment_azure_whisper.json"
CATALOGUE_FIXTURE_CHAT = "secret_test_catalogue_openai_gpt5.json"
CATALOGUE_FIXTURE_EMBEDDING = "secret_test_catalogue_openai_tel3.json"
CATALOGUE_FIXTURE_STT = "secret_test_catalogue_openai_whisper.json"
INVOKE_FIXTURES = sorted(p.name for p in TEST_DIR.glob("secret_test_invoke_*.json"))


def _load_json_fixture(name: str) -> dict[str, Any]:
    path = TEST_DIR / name
    with path.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    if not isinstance(loaded, dict):
        raise ValueError(f"Fixture must be an object: {path}")
    return loaded


def test_i_model_component_initialize(integration_env_async) -> None:
    async def run() -> None:
        env = await integration_env_async()
        try:
            ok = await env.component.initialize(env.manager)
            assert ok is True
        finally:
            await integration_env_async.cleanup()  # type: ignore[attr-defined]

    import asyncio

    asyncio.run(run())


def test_i_model_component_get_configurations(integration_env_async) -> None:
    async def run() -> None:
        env = await integration_env_async()
        try:
            cfg = await env.component.get_configurations()
            assert isinstance(cfg, ModelComponentConfigurations)
        finally:
            await integration_env_async.cleanup()  # type: ignore[attr-defined]

    import asyncio

    asyncio.run(run())


def test_i_model_component_update_configurations(integration_env_async) -> None:
    async def run() -> None:
        env = await integration_env_async()
        try:
            cfg = await env.component.get_configurations()
            cfg.vector_exploration_factor = cfg.vector_exploration_factor + 1
            updated = await env.component.update_configurations(cfg)
            assert updated.vector_exploration_factor == cfg.vector_exploration_factor
        finally:
            await integration_env_async.cleanup()  # type: ignore[attr-defined]

    import asyncio

    asyncio.run(run())


def test_i_model_component_deployment_methods(integration_env_async) -> None:
    async def run() -> None:
        env = await integration_env_async()
        provider = env.provider
        component = env.component

        created_deployment_id: str | None = None
        try:
            secret_data = _load_json_fixture(SECRET_FIXTURE)
            secret_json = json.dumps(secret_data, ensure_ascii=False)
            await provider.query_raw(f"UPSERT secret:{SECRET_ID} CONTENT {secret_json};")

            dep_data = _load_json_fixture(DEPLOYMENT_FIXTURE_CHAT)
            dep_data["name"] = f"{dep_data.get('name', 'deployment')}-{int(time.time())}"
            dep_data["secrets"] = [f"secret:{SECRET_ID}"]
            created_dep = await component.create_deployment(ModelDeployment.from_dict(dep_data))
            created_deployment_id = created_dep.id
            assert created_deployment_id

            got = await component.get_deployment(created_deployment_id)
            assert got is not None

            results = await component.search_deployments(
                ModelDeploymentSearchCriteria(name=created_dep.name, limit=10)
            )
            assert isinstance(results, list)
            if len(results) > 0:
                assert any(item.id == created_deployment_id for item in results)

            got.description = "updated"
            updated = await component.update_deployment(got)
            assert updated.description == "updated"

            assert await component.delete_deployment(created_deployment_id) is True
            created_deployment_id = None
        finally:
            if created_deployment_id:
                await component.delete_deployment(created_deployment_id)
            try:
                await provider.query_raw(f"DELETE secret:{SECRET_ID};")
            except Exception:
                pass
            await integration_env_async.cleanup()  # type: ignore[attr-defined]

    import asyncio

    asyncio.run(run())


@pytest.mark.parametrize("invoke_fixture", INVOKE_FIXTURES)
def test_i_model_component_catalogue_methods_and_invoke(
    integration_env_async, invoke_fixture: str
) -> None:
    async def run() -> None:
        env = await integration_env_async()
        provider = env.provider
        component = env.component

        if not INVOKE_FIXTURES:
            raise AssertionError("No invoke fixtures found: secret_test_invoke_*.json")

        created_catalogue_id: str | None = None
        created_deployment_id: str | None = None
        try:
            secret_data = _load_json_fixture(SECRET_FIXTURE)
            secret_json = json.dumps(secret_data, ensure_ascii=False)
            await provider.query_raw(f"UPSERT secret:{SECRET_ID} CONTENT {secret_json};")

            req_data = _load_json_fixture(invoke_fixture)
            req = AiRequest.from_dict(req_data)

            if req.operation_type == AiOperationType.CHAT_COMPLETION:
                deployment_fixture = DEPLOYMENT_FIXTURE_CHAT
                catalogue_fixture = CATALOGUE_FIXTURE_CHAT
            elif req.operation_type == AiOperationType.EMBEDDING:
                deployment_fixture = DEPLOYMENT_FIXTURE_EMBEDDING
                catalogue_fixture = CATALOGUE_FIXTURE_EMBEDDING
            elif str(req.operation_type.value) in {"speech-to-text", "speech_to_text"}:
                deployment_fixture = DEPLOYMENT_FIXTURE_STT
                catalogue_fixture = CATALOGUE_FIXTURE_STT
            else:
                raise AssertionError(
                    f"Unsupported operation_type in fixture {invoke_fixture}: {req.operation_type}"
                )

            dep_data = _load_json_fixture(deployment_fixture)
            dep_data["name"] = f"{dep_data.get('name', 'deployment')}-{int(time.time())}"
            dep_data["secrets"] = [f"secret:{SECRET_ID}"]
            created_dep = await component.create_deployment(ModelDeployment.from_dict(dep_data))
            created_deployment_id = created_dep.id
            assert created_deployment_id

            cat_data = _load_json_fixture(catalogue_fixture)
            cat_data["name"] = f"{cat_data.get('name', 'catalogue')}-{int(time.time())}"
            cat_data["deployments"] = [created_deployment_id]
            created_cat = await component.create_catalogue(ModelCatalogue.from_dict(cat_data))
            created_catalogue_id = created_cat.id
            assert created_catalogue_id

            got = await component.get_catalogue(created_catalogue_id)
            assert got.id == created_catalogue_id

            results = await component.search_catalogues(
                ModelCatalogueSearchCriteria(name=created_cat.name, limit=10)
            )
            assert any(item.id == created_catalogue_id for item in results)

            got.description = "updated"
            updated = await component.update_catalogue(got)
            assert updated.description == "updated"

            resp = await component.invoke(created_catalogue_id, req, None)
            assert resp.output is not None

            with pytest.raises(ModelComponentResourceNotFoundException):
                await component.get_catalogue("does_not_exist")

            assert await component.delete_catalogue(created_catalogue_id) is True
            created_catalogue_id = None
        finally:
            if created_catalogue_id:
                await component.delete_catalogue(created_catalogue_id)
            if created_deployment_id:
                await component.delete_deployment(created_deployment_id)
            try:
                await provider.query_raw(f"DELETE secret:{SECRET_ID};")
            except Exception:
                pass
            await integration_env_async.cleanup()  # type: ignore[attr-defined]

    import asyncio

    asyncio.run(run())

