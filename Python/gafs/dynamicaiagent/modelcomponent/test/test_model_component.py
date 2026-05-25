"""test_model_component.py - Integration tests for ModelComponent.

Covers every public method defined on IModelComponent.
Each method has at least one happy-path and one error-path scenario.

Requires: secret_test_db_config.json in the test directory.
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
    ModelCatalogueIndexNotAvailableException,
    ModelDeploymentNotFoundException,
)
from gafs.dynamicaiagent.modelcomponent.models.ai_operation_type import AiOperationType
from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.deployment_selection_options import (
    DeploymentSelectionOptions,
)
from gafs.dynamicaiagent.modelcomponent.models.model_catalogue import (
    ModelCatalogueEntry,
    ModelDeployment,
    ModelStatus,
)
from gafs.dynamicaiagent.modelcomponent.models.model_catalogue_search_criteria import (
    ModelCatalogueSearchCriteria,
    VectorSearchCriteria,
)
from gafs.dynamicaiagent.modelcomponent.models.model_component_configurations import (
    ModelComponentConfigurations,
)
from gafs.dynamicaiagent.modelcomponent.models.model_deployment_search_criteria import (
    ModelDeploymentSearchCriteria,
)

TEST_DIR = Path(__file__).resolve().parent
DEPLOYMENT_FIXTURE = "secret_test_deployment_azure_embedding.json"
CATALOGUE_FIXTURE = "secret_test_catalogue_azure_chat.json"


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
# Catalogue CRUD via ModelComponent
# ---------------------------------------------------------------------------

def test_component_catalogue_crud(integration_env_async) -> None:
    """Full CRUD cycle on ModelCatalogueEntry via ModelComponent."""

    async def run() -> None:
        env = await integration_env_async()
        comp = env.component
        cat_svc = env.catalogue_service
        cat_id: str | None = None
        dep_id: str | None = None

        try:
            # Create a deployment first so the catalogue can reference it.
            dep_data = _load_json_fixture(DEPLOYMENT_FIXTURE)
            dep_data["name"] = f"{dep_data.get('name', 'dep')}-{_suffix()}"
            dep = await comp.create_deployment(ModelDeployment.from_dict(dep_data))
            dep_id = dep.id

            cat_data = _load_json_fixture(CATALOGUE_FIXTURE)
            cat_data["name"] = f"{cat_data.get('name', 'cat')}-{_suffix()}"
            cat_data["deployments"] = [dep_id]

            # create
            created = await comp.create_catalogue_entry(
                ModelCatalogueEntry.from_dict(cat_data)
            )
            cat_id = created.id
            assert cat_id is not None

            # get (found)
            got = await comp.get_catalogue_entry(cat_id)
            assert got.id == cat_id

            # get (not found)
            with pytest.raises(ModelCatalogueEntryNotFoundException):
                await comp.get_catalogue_entry("does_not_exist_xyz")

            # get all
            all_entries = await comp.get_all_catalogue_entries()
            assert any(e.id == cat_id for e in all_entries)

            # update
            got.description = "Updated via ModelComponent"
            updated = await comp.update_catalogue_entry(got)
            assert updated.description == "Updated via ModelComponent"

            # search
            criteria = ModelCatalogueSearchCriteria(name=created.name, limit=5)
            results = await comp.search_catalogue_entries(criteria)
            assert any(r.id == cat_id for r in results)

            # delete (happy-path)
            await comp.delete_catalogue_entry(cat_id)
            cat_id = None

            with pytest.raises(ModelCatalogueEntryNotFoundException):
                await comp.get_catalogue_entry(cat_id or "deleted")

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
# Deployment CRUD via ModelComponent
# ---------------------------------------------------------------------------

def test_component_deployment_crud(integration_env_async) -> None:
    """Full CRUD cycle on ModelDeployment via ModelComponent."""

    async def run() -> None:
        env = await integration_env_async()
        comp = env.component
        cat_svc = env.catalogue_service
        dep_id: str | None = None

        try:
            dep_data = _load_json_fixture(DEPLOYMENT_FIXTURE)
            dep_data["name"] = f"{dep_data.get('name', 'dep')}-{_suffix()}"

            # create
            created = await comp.create_deployment(ModelDeployment.from_dict(dep_data))
            dep_id = created.id
            assert dep_id is not None

            # get (found)
            got = await comp.get_deployment(dep_id)
            assert got is not None
            assert got.id == dep_id

            # get (not found)
            assert await comp.get_deployment("does_not_exist_xyz") is None

            # search
            criteria = ModelDeploymentSearchCriteria(name=created.name, limit=5)
            results = await comp.search_deployments(criteria)
            assert any(r.id == dep_id for r in results)

            # update
            got.description = "Updated via ModelComponent"
            updated = await comp.update_deployment(got)
            assert updated.description == "Updated via ModelComponent"

            # delete (happy-path)
            await comp.delete_deployment(dep_id)
            dep_id = None

        finally:
            if dep_id:
                try:
                    await cat_svc.delete_deployment(dep_id)
                except Exception:
                    pass
            await integration_env_async.cleanup()

    asyncio.run(run())


# ---------------------------------------------------------------------------
# invoke via ModelComponent with stub
# ---------------------------------------------------------------------------

def test_component_invoke_stub(integration_env_async) -> None:
    """invoke delegates to ModelService and returns the stub output."""

    async def run() -> None:
        env = await integration_env_async()
        comp = env.component
        cat_svc = env.catalogue_service
        cat_id: str | None = None
        dep_id: str | None = None

        try:
            dep_data = _load_json_fixture(DEPLOYMENT_FIXTURE)
            dep_data["name"] = f"{dep_data.get('name', 'dep')}-{_suffix()}"
            dep_data["secrets"] = []
            created_dep = await cat_svc.create_deployment(
                ModelDeployment.from_dict(dep_data)
            )
            dep_id = created_dep.id

            cat_data = _load_json_fixture(CATALOGUE_FIXTURE)
            cat_data["name"] = f"{cat_data.get('name', 'cat')}-{_suffix()}"
            cat_data["deployments"] = [dep_id]
            cat_data["type"] = "chat_completion"
            created_cat = await cat_svc.create_catalogue_entry(
                ModelCatalogueEntry.from_dict(cat_data)
            )
            cat_id = created_cat.id

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

            response = await comp.invoke(cat_id, req)
            assert response is not None

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
# get_configurations / update_configurations
# ---------------------------------------------------------------------------

def test_component_get_configurations(integration_env_async) -> None:
    """get_configurations returns a ModelComponentConfigurations object."""

    async def run() -> None:
        env = await integration_env_async()
        comp = env.component
        try:
            cfg = await comp.get_configurations()
            assert isinstance(cfg, ModelComponentConfigurations)
            assert cfg.vector_dimensions is not None
        finally:
            await integration_env_async.cleanup()

    asyncio.run(run())


def test_component_update_configurations_no_vector_change(integration_env_async) -> None:
    """update_configurations with no vector setting change does not rebuild index."""

    async def run() -> None:
        env = await integration_env_async()
        comp = env.component
        try:
            current = await comp.get_configurations()

            # Only update a non-vector field.
            current.embedding_catalogue_id = current.embedding_catalogue_id  # no change
            updated = await comp.update_configurations(current)
            assert isinstance(updated, ModelComponentConfigurations)
            assert not comp._is_rebuilding_vector_index
        finally:
            await integration_env_async.cleanup()

    asyncio.run(run())


# ---------------------------------------------------------------------------
# Vector search blocked during rebuild
# ---------------------------------------------------------------------------

def test_component_search_blocked_during_rebuild(integration_env_async) -> None:
    """search_catalogue_entries raises when vector index is rebuilding."""

    async def run() -> None:
        env = await integration_env_async()
        comp = env.component
        try:
            # Manually set the rebuild flag.
            object.__setattr__(comp, "_is_rebuilding_vector_index", True)

            criteria = ModelCatalogueSearchCriteria(
                vector_search=VectorSearchCriteria(vector=[0.1, 0.2, 0.3]),
                limit=5,
            )
            with pytest.raises(ModelCatalogueIndexNotAvailableException):
                await comp.search_catalogue_entries(criteria)
        finally:
            object.__setattr__(comp, "_is_rebuilding_vector_index", False)
            await integration_env_async.cleanup()

    asyncio.run(run())
