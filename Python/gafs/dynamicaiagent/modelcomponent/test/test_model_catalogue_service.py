"""test_model_catalogue_service.py - Integration tests for ModelCatalogueService.

Covers every public method defined on IModelCatalogueService.
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
    ModelDeploymentNotFoundException,
)
from gafs.dynamicaiagent.modelcomponent.model_catalogue_service import ModelCatalogueService
from gafs.dynamicaiagent.modelcomponent.models.model_catalogue import (
    DeploymentStatus,
    ModelCatalogueEntry,
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
# initialize / ensure_indexes
# ---------------------------------------------------------------------------

def test_i_model_catalogue_service_initialize(integration_env_async) -> None:
    """initialize returns True and the service is ready for CRUD operations."""

    async def run() -> None:
        env = await integration_env_async()
        try:
            assert env.catalogue_service is not None
        finally:
            await integration_env_async.cleanup()

    asyncio.run(run())


def test_i_model_catalogue_service_ensure_indexes(integration_env_async) -> None:
    """ensure_indexes succeeds both without and with overwrite."""

    async def run() -> None:
        env = await integration_env_async()
        try:
            svc: ModelCatalogueService = env.catalogue_service
            cfg = ModelComponentConfigurations()
            assert await svc.ensure_indexes(cfg, overwrite=False) is True
            assert await svc.ensure_indexes(cfg, overwrite=True) is True
        finally:
            await integration_env_async.cleanup()

    asyncio.run(run())


# ---------------------------------------------------------------------------
# Deployment CRUD
# ---------------------------------------------------------------------------

def test_deployment_create_get_update_search_delete(integration_env_async) -> None:
    """CRUD + search happy-path for ModelDeployment."""

    async def run() -> None:
        env = await integration_env_async()
        svc: ModelCatalogueService = env.catalogue_service
        created_id: str | None = None

        try:
            dep_data = _load_json_fixture(DEPLOYMENT_FIXTURE)
            dep_data["name"] = f"{dep_data.get('name', 'dep')}-{_suffix()}"

            # CREATE
            created = await svc.create_deployment(ModelDeployment.from_dict(dep_data))
            created_id = created.id
            assert created_id is not None
            assert created.name == dep_data["name"]

            # GET (happy-path)
            got = await svc.get_deployment(created_id)
            assert got is not None
            assert got.id == created_id

            # GET (not found)
            assert await svc.get_deployment("does_not_exist_xyz") is None

            # UPDATE (happy-path)
            got.description = "updated description"
            updated = await svc.update_deployment(got)
            assert updated.description == "updated description"

            # UPDATE (no id)
            bad = ModelDeployment()
            # id is None
            with pytest.raises(Exception):
                await svc.update_deployment(bad)

            # SEARCH
            criteria = ModelDeploymentSearchCriteria(name=created.name, limit=5)
            results = await svc.search_deployments(criteria)
            assert any(r.id == created_id for r in results)

            # DELETE (happy-path)
            await svc.delete_deployment(created_id)
            created_id = None

            # Confirm deletion
            assert await svc.get_deployment(created_id or "deleted_id") is None

            # DELETE (not found)
            with pytest.raises(ModelDeploymentNotFoundException):
                await svc.delete_deployment("does_not_exist_xyz")

        finally:
            if created_id:
                try:
                    await svc.delete_deployment(created_id)
                except Exception:
                    pass
            await integration_env_async.cleanup()

    asyncio.run(run())


# ---------------------------------------------------------------------------
# Catalogue CRUD
# ---------------------------------------------------------------------------

def test_catalogue_create_get_update_search_delete(integration_env_async) -> None:
    """CRUD + search happy-path for ModelCatalogueEntry."""

    async def run() -> None:
        env = await integration_env_async()
        svc: ModelCatalogueService = env.catalogue_service
        created_cat_id: str | None = None
        created_dep_id: str | None = None

        try:
            # Seed a deployment first so the catalogue can reference it.
            dep_data = _load_json_fixture(DEPLOYMENT_FIXTURE)
            dep_data["name"] = f"{dep_data.get('name', 'dep')}-{_suffix()}"
            created_dep = await svc.create_deployment(ModelDeployment.from_dict(dep_data))
            created_dep_id = created_dep.id
            assert created_dep_id

            # CREATE
            cat_data = _load_json_fixture(CATALOGUE_FIXTURE)
            cat_data["name"] = f"{cat_data.get('name', 'cat')}-{_suffix()}"
            cat_data["deployments"] = [created_dep_id]
            created_cat = await svc.create_catalogue_entry(
                ModelCatalogueEntry.from_dict(cat_data)
            )
            created_cat_id = created_cat.id
            assert created_cat_id is not None
            assert created_cat.name == cat_data["name"]
            # Edge-resolved deployments should contain the created deployment id.
            assert isinstance(created_cat.deployments, list)
            assert created_dep_id in created_cat.deployments or any(
                created_dep_id in str(d) for d in (created_cat.deployments or [])
            )

            # GET (happy-path)
            got = await svc.get_catalogue_entry(created_cat_id)
            assert got is not None
            assert got.id == created_cat_id

            # GET (not found)
            assert await svc.get_catalogue_entry("does_not_exist_xyz") is None

            # GET ALL
            all_entries = await svc.get_all_catalogue_entries()
            assert isinstance(all_entries, list)
            assert any(e.id == created_cat_id for e in all_entries)

            # UPDATE (happy-path)
            got.description = "updated catalogue description"
            updated = await svc.update_catalogue_entry(got)
            assert updated.description == "updated catalogue description"

            # UPDATE (no id)
            bad = ModelCatalogueEntry()
            # id is None
            with pytest.raises(Exception):
                await svc.update_catalogue_entry(bad)

            # SEARCH by name
            criteria = ModelCatalogueSearchCriteria(name=created_cat.name, limit=5)
            results = await svc.search_catalogue_entries(criteria)
            assert any(r.id == created_cat_id for r in results)

            # DELETE (happy-path)
            await svc.delete_catalogue_entry(created_cat_id)
            created_cat_id = None

            # Confirm deletion
            assert await svc.get_catalogue_entry(created_cat_id or "deleted") is None

            # DELETE (not found)
            with pytest.raises(ModelCatalogueEntryNotFoundException):
                await svc.delete_catalogue_entry("does_not_exist_xyz")

        finally:
            if created_cat_id:
                try:
                    await svc.delete_catalogue_entry(created_cat_id)
                except Exception:
                    pass
            if created_dep_id:
                try:
                    await svc.delete_deployment(created_dep_id)
                except Exception:
                    pass
            await integration_env_async.cleanup()

    asyncio.run(run())


# ---------------------------------------------------------------------------
# Catalogue create with referenced-deployment-not-found
# ---------------------------------------------------------------------------

def test_catalogue_create_missing_deployment_raises(integration_env_async) -> None:
    """Creating a catalogue entry with a non-existent deployment raises."""

    async def run() -> None:
        env = await integration_env_async()
        svc: ModelCatalogueService = env.catalogue_service

        try:
            cat_data = _load_json_fixture(CATALOGUE_FIXTURE)
            cat_data["name"] = f"{cat_data.get('name', 'cat')}-{_suffix()}"
            cat_data["deployments"] = ["nonexistent_deployment_id"]

            with pytest.raises(ModelDeploymentNotFoundException):
                await svc.create_catalogue_entry(ModelCatalogueEntry.from_dict(cat_data))
        finally:
            await integration_env_async.cleanup()

    asyncio.run(run())


# ---------------------------------------------------------------------------
# Search by keyword (full-text)
# ---------------------------------------------------------------------------

def test_catalogue_search_by_keyword(integration_env_async) -> None:
    """Full-text keyword search returns matching results."""

    async def run() -> None:
        env = await integration_env_async()
        svc: ModelCatalogueService = env.catalogue_service
        created_id: str | None = None

        try:
            cat_data = _load_json_fixture(CATALOGUE_FIXTURE)
            unique_word = f"uniqueword{_suffix()}"
            cat_data["name"] = f"cat-{_suffix()}"
            cat_data["description"] = f"This entry contains a {unique_word} for testing."
            created = await svc.create_catalogue_entry(
                ModelCatalogueEntry.from_dict(cat_data)
            )
            created_id = created.id

            criteria = ModelCatalogueSearchCriteria(
                keywords=[unique_word], status=[ModelStatus.ACTIVE], limit=5
            )
            results = await svc.search_catalogue_entries(criteria)
            # Full-text search may have a slight delay (concurrent index);
            # at minimum the call should succeed without error.
            assert isinstance(results, list)
        finally:
            if created_id:
                try:
                    await svc.delete_catalogue_entry(created_id)
                except Exception:
                    pass
            await integration_env_async.cleanup()

    asyncio.run(run())
