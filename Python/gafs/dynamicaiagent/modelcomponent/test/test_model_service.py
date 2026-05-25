"""test_model_service.py - Integration tests for ModelService.

Covers every public method defined on IModelService.
Each method has at least one happy-path and one error-path scenario.

Requires: secret_test_db_config.json in the test directory.
For live invoke tests, also requires the secret and deployment fixture files.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import pytest

from gafs.dynamicaiagent.modelcomponent import (
    ModelCatalogueEntryNotFoundException,
    ModelComponentInitializationException,
    ModelDeploymentNotFoundException,
)
from gafs.dynamicaiagent.modelcomponent.model_service import ModelService
from gafs.dynamicaiagent.modelcomponent.models.ai_operation_type import AiOperationType
from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.deployment_selection_options import (
    DeploymentSelectionOptions,
)
from gafs.dynamicaiagent.modelcomponent.models.model_catalogue import (
    DeploymentStatus,
    ModelCatalogueEntry,
    ModelDeployment,
    ModelStatus,
)

TEST_DIR = Path(__file__).resolve().parent
SECRET_FIXTURE = "secret_test_secret_azure_openai_japan_east.json"
SECRET_ID = "secret_test_azure_openai_japan_east"
DEPLOYMENT_FIXTURE_EMBEDDING = "secret_test_deployment_azure_embedding.json"
DEPLOYMENT_FIXTURE_CHAT = "secret_test_deployment_azure_chat.json"
CATALOGUE_FIXTURE_EMBEDDING = "secret_test_catalogue_azure_embedding.json"
CATALOGUE_FIXTURE_CHAT = "secret_test_catalogue_azure_chat.json"
INVOKE_FIXTURES = sorted(p.name for p in TEST_DIR.glob("secret_test_invoke_*.json"))


def _load_json_fixture(name: str) -> dict[str, Any]:
    path = TEST_DIR / name
    with path.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    if not isinstance(loaded, dict):
        raise ValueError(f"Fixture must be a JSON object: {path}")
    return loaded


def _suffix() -> str:
    return str(int(time.time() * 1000))


# ---------------------------------------------------------------------------
# initialize
# ---------------------------------------------------------------------------

def test_i_model_service_initialize_requires_both_args(integration_env_async) -> None:
    """initialize raises when catalogue_service or cloud_ai_component is None."""

    async def run() -> None:
        env = await integration_env_async()
        try:
            svc = ModelService(env.logger)

            with pytest.raises(ModelComponentInitializationException):
                # Missing both catalogue_service and cloud_ai_component.
                await svc.initialize(env.manager)

            with pytest.raises(ModelComponentInitializationException):
                # Missing cloud_ai_component.
                await svc.initialize(
                    env.manager,
                    model_catalogue_service=env.catalogue_service,
                    cloud_ai_component=None,
                )

            ok = await svc.initialize(
                env.manager,
                model_catalogue_service=env.catalogue_service,
                cloud_ai_component=env.stub_cloud,
            )
            assert ok is True
        finally:
            await integration_env_async.cleanup()

    asyncio.run(run())


# ---------------------------------------------------------------------------
# invoke — stub
# ---------------------------------------------------------------------------

def test_i_model_service_invoke_not_found(integration_env_async) -> None:
    """invoke raises ModelCatalogueEntryNotFoundException for missing catalogue."""

    async def run() -> None:
        env = await integration_env_async()
        try:
            from gafs.dynamicaiagent.modelcomponent.models.ai_payload import (
                ChatCompletionPayload,
            )
            from gafs.dynamicaiagent.modelcomponent.models.message import Message, TextMessagePart
            payload = ChatCompletionPayload()
            msg = Message()
            msg.role = "user"
            part = TextMessagePart()
            part.text = "hi"
            msg.content = [part]
            payload.messages = [msg]
            req = AiRequest(AiOperationType.CHAT_COMPLETION, payload=payload, parameters={})

            with pytest.raises(ModelCatalogueEntryNotFoundException):
                await env.model_service.invoke("does_not_exist", req)
        finally:
            await integration_env_async.cleanup()

    asyncio.run(run())


def test_i_model_service_invoke_no_deployments(integration_env_async) -> None:
    """invoke raises ModelDeploymentNotFoundException when catalogue has no deployments."""

    async def run() -> None:
        env = await integration_env_async()
        svc = env.model_service
        cat_svc = env.catalogue_service
        created_id: str | None = None

        try:
            cat_data = _load_json_fixture(CATALOGUE_FIXTURE_CHAT)
            cat_data["name"] = f"nodeployment-cat-{_suffix()}"
            cat_data["deployments"] = []  # no deployments
            created = await cat_svc.create_catalogue_entry(
                ModelCatalogueEntry.from_dict(cat_data)
            )
            created_id = created.id

            from gafs.dynamicaiagent.modelcomponent.models.ai_payload import (
                ChatCompletionPayload,
            )
            from gafs.dynamicaiagent.modelcomponent.models.message import Message, TextMessagePart
            payload = ChatCompletionPayload()
            msg = Message()
            msg.role = "user"
            part = TextMessagePart()
            part.text = "hi"
            msg.content = [part]
            payload.messages = [msg]
            req = AiRequest(AiOperationType.CHAT_COMPLETION, payload=payload, parameters={})

            with pytest.raises(ModelDeploymentNotFoundException):
                await svc.invoke(created_id, req)
        finally:
            if created_id:
                try:
                    await cat_svc.delete_catalogue_entry(created_id)
                except Exception:
                    pass
            await integration_env_async.cleanup()

    asyncio.run(run())


def test_i_model_service_invoke_stub(integration_env_async) -> None:
    """invoke with stub cloud AI component returns a ChatCompletionOutput."""

    async def run() -> None:
        env = await integration_env_async()
        svc = env.model_service
        cat_svc = env.catalogue_service
        cat_id: str | None = None
        dep_id: str | None = None

        try:
            # Create deployment.
            dep_data = _load_json_fixture(DEPLOYMENT_FIXTURE_CHAT)
            dep_data["name"] = f"{dep_data.get('name', 'dep')}-{_suffix()}"
            dep_data["secrets"] = []
            created_dep = await cat_svc.create_deployment(
                ModelDeployment.from_dict(dep_data)
            )
            dep_id = created_dep.id

            # Create catalogue linked to deployment.
            cat_data = _load_json_fixture(CATALOGUE_FIXTURE_CHAT)
            cat_data["name"] = f"{cat_data.get('name', 'cat')}-{_suffix()}"
            cat_data["deployments"] = [dep_id]
            created_cat = await cat_svc.create_catalogue_entry(
                ModelCatalogueEntry.from_dict(cat_data)
            )
            cat_id = created_cat.id

            # Build request.
            from gafs.dynamicaiagent.modelcomponent.models.ai_payload import (
                ChatCompletionPayload,
            )
            from gafs.dynamicaiagent.modelcomponent.models.message import Message, TextMessagePart
            payload = ChatCompletionPayload()
            msg = Message()
            msg.role = "user"
            part = TextMessagePart()
            part.text = "Say hello."
            msg.content = [part]
            payload.messages = [msg]
            req = AiRequest(AiOperationType.CHAT_COMPLETION, payload=payload, parameters={})

            response = await svc.invoke(cat_id, req)
            assert response is not None
            assert response.output is not None

            # Verify the stub received the call.
            assert env.stub_cloud.last_request is not None

        finally:
            if cat_id:
                try:
                    await cat_svc.delete_catalogue_entry(cat_id)
                except Exception:
                    pass
            if dep_id:
                try:
                    await cat_svc.delete_deployment(dep_id)
                except Exception:
                    pass
            await integration_env_async.cleanup()

    asyncio.run(run())


# ---------------------------------------------------------------------------
# invoke — live (parametrized by fixture files)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("invoke_fixture", INVOKE_FIXTURES)
def test_i_model_service_invoke_live(integration_env_async, invoke_fixture: str) -> None:
    """Invoke a real Azure OpenAI model via ModelService using secret fixtures.

    Skips automatically if fixture files are missing.
    """

    async def run() -> None:
        env = await integration_env_async()

        cat_svc = env.catalogue_service
        provider = env.provider

        created_cat_id: str | None = None
        created_dep_id: str | None = None

        # Re-init model_service with real CloudAiComponent.
        from gafs.dynamicaiagent.cloudaicomponent import CloudAiComponent
        real_cloud = CloudAiComponent()
        real_svc = ModelService(env.logger)
        await real_svc.initialize(
            env.manager,
            model_catalogue_service=cat_svc,
            cloud_ai_component=real_cloud,
        )

        try:
            # Seed the Azure OpenAI secret.
            secret_data = _load_json_fixture(SECRET_FIXTURE)
            secret_json = json.dumps(secret_data, ensure_ascii=False)
            await provider.query_raw(
                f"UPSERT type::thing('Secrets', '{SECRET_ID}') CONTENT {secret_json};"
            )

            req_data = _load_json_fixture(invoke_fixture)
            req = AiRequest.from_dict(req_data)

            if req.operation_type == AiOperationType.CHAT_COMPLETION:
                dep_fixture = DEPLOYMENT_FIXTURE_CHAT
                cat_fixture = CATALOGUE_FIXTURE_CHAT
            elif req.operation_type == AiOperationType.EMBEDDING:
                dep_fixture = DEPLOYMENT_FIXTURE_EMBEDDING
                cat_fixture = CATALOGUE_FIXTURE_EMBEDDING
            else:
                pytest.skip(f"No fixture mapping for operation type: {req.operation_type}")

            # Create deployment with secret reference.
            dep_data = _load_json_fixture(dep_fixture)
            dep_data["name"] = f"{dep_data.get('name', 'dep')}-{_suffix()}"
            dep_data["secrets"] = [SECRET_ID]
            dep_data["status"] = "active"
            created_dep = await cat_svc.create_deployment(
                ModelDeployment.from_dict(dep_data)
            )
            created_dep_id = created_dep.id

            # Create catalogue.
            cat_data = _load_json_fixture(cat_fixture)
            cat_data["name"] = f"{cat_data.get('name', 'cat')}-{_suffix()}"
            cat_data["deployments"] = [created_dep_id]
            created_cat = await cat_svc.create_catalogue_entry(
                ModelCatalogueEntry.from_dict(cat_data)
            )
            created_cat_id = created_cat.id

            response = await real_svc.invoke(created_cat_id, req)
            assert response is not None
            assert response.output is not None

        finally:
            if created_cat_id:
                try:
                    await cat_svc.delete_catalogue_entry(created_cat_id)
                except Exception:
                    pass
            if created_dep_id:
                try:
                    await cat_svc.delete_deployment(created_dep_id)
                except Exception:
                    pass
            # Remove test secret.
            try:
                await provider.query_raw(
                    f"DELETE type::thing('Secrets', '{SECRET_ID}');"
                )
            except Exception:
                pass
            await integration_env_async.cleanup()

    asyncio.run(run())
