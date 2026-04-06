"""Integration tests for ModelService.

These tests cover every public method defined on IModelService.
Each method has at least one happy-path and one error-path scenario.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

from gafs.dynamicaiagent.modelcomponent.model_service import ModelService
from gafs.dynamicaiagent.modelcomponent.models.ai_operation_type import AiOperationType
from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.deployment_selection_options import (
    DeploymentSelectionOptions,
)
from gafs.dynamicaiagent.modelcomponent.models.model_catalogue import (
    DeploymentStatus,
    ModelCatalogue,
    ModelDeployment,
    ModelStatus,
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


def test_i_model_service_initialize(integration_env_async) -> None:
    async def run() -> None:
        env = await integration_env_async()
        try:
            service = ModelService(logger=env.logger)
            with pytest.raises(ValueError):
                await service.initialize(env.manager)

            ok = await service.initialize(env.manager, env.catalogue_service, env.stub_cloud)
            assert ok is True
        finally:
            await integration_env_async.cleanup()  # type: ignore[attr-defined]

    import asyncio

    asyncio.run(run())


@pytest.mark.parametrize("invoke_fixture", INVOKE_FIXTURES)
def test_i_model_service_invoke(integration_env_async, invoke_fixture: str) -> None:
    async def run() -> None:
        env = await integration_env_async()
        provider = env.provider
        service = ModelService(logger=env.logger)
        await service.initialize(env.manager, env.catalogue_service, env.stub_cloud)

        if not INVOKE_FIXTURES:
            raise AssertionError("No invoke fixtures found: secret_test_invoke_*.json")

        created_catalogue_id: str | None = None
        created_deployment_id: str | None = None
        created_empty_catalogue_id: str | None = None
        created_missing_secret_catalogue_id: str | None = None
        created_missing_secret_deployment_id: str | None = None

        try:
            # Seed secret record used by deployments.
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

            # Create deployment from fixture and attach secret link.
            dep_data = _load_json_fixture(deployment_fixture)
            dep_data["name"] = f"{dep_data.get('name', 'deployment')}-{int(time.time())}"
            dep_data["secrets"] = [f"secret:{SECRET_ID}"]
            created_dep = await env.catalogue_service.create_deployment(
                ModelDeployment.from_dict(dep_data)
            )
            created_deployment_id = created_dep.id
            assert created_deployment_id

            # Create catalogue from fixture, point it to created deployment.
            cat_data = _load_json_fixture(catalogue_fixture)
            cat_data["name"] = f"{cat_data.get('name', 'catalogue')}-{int(time.time())}"
            cat_data["deployments"] = [created_deployment_id]
            created_cat = await env.catalogue_service.create_catalogue(
                ModelCatalogue.from_dict(cat_data)
            )
            created_catalogue_id = created_cat.id
            assert created_catalogue_id

            # error: missing catalogue
            with pytest.raises(ValueError):
                await service.invoke("does_not_exist", req)

            # happy
            resp = await service.invoke(created_catalogue_id, req, DeploymentSelectionOptions())
            assert resp.output is not None
            assert env.stub_cloud.last_connection is not None
            assert env.stub_cloud.last_request is not None

            # error: no deployments (must still have inference parameter defs)
            empty_cat_data = _load_json_fixture(catalogue_fixture)
            empty_cat_data["name"] = f"cat-empty-{int(time.time())}"
            empty_cat_data["deployments"] = []
            created_empty = await env.catalogue_service.create_catalogue(
                ModelCatalogue.from_dict(empty_cat_data)
            )
            created_empty_catalogue_id = created_empty.id
            with pytest.raises(ValueError):
                req2 = AiRequest.from_dict(req_data)
                await service.invoke(created_empty_catalogue_id, req2)

            # error: missing secret
            dep_missing = _load_json_fixture(deployment_fixture)
            dep_missing["name"] = f"{dep_missing.get('name', 'deployment')}-missing-secret-{int(time.time())}"
            dep_missing["secrets"] = ["secret:does_not_exist"]
            created_d2 = await env.catalogue_service.create_deployment(
                ModelDeployment.from_dict(dep_missing)
            )
            created_missing_secret_deployment_id = created_d2.id

            c3 = ModelCatalogue()
            c3.name = f"cat-missing-secret-{int(time.time())}"
            c3.type = req.operation_type
            c3.status = ModelStatus.ACTIVE
            c3.deployments = [created_missing_secret_deployment_id]
            created_c3 = await env.catalogue_service.create_catalogue(c3)
            created_missing_secret_catalogue_id = created_c3.id

            with pytest.raises(ValueError):
                req3 = AiRequest.from_dict(req_data)
                await service.invoke(created_missing_secret_catalogue_id, req3)
        finally:
            if created_missing_secret_catalogue_id:
                await env.catalogue_service.delete_catalogue(created_missing_secret_catalogue_id)
            if created_missing_secret_deployment_id:
                await env.catalogue_service.delete_deployment(created_missing_secret_deployment_id)
            if created_empty_catalogue_id:
                await env.catalogue_service.delete_catalogue(created_empty_catalogue_id)
            if created_catalogue_id:
                await env.catalogue_service.delete_catalogue(created_catalogue_id)
            if created_deployment_id:
                await env.catalogue_service.delete_deployment(created_deployment_id)
            try:
                await provider.query_raw(f"DELETE secret:{SECRET_ID};")
            except Exception:
                pass
            await integration_env_async.cleanup()  # type: ignore[attr-defined]

    import asyncio

    asyncio.run(run())

