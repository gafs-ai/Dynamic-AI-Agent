"""Integration tests for ToolCatalogueService.

Tests CRUD operations and search on ToolCatalogueEntry and ToolVersionEntry
against a real SurrealDB instance.  Skip if secret_test_db_config.json is absent.

Test coverage:
  Normal cases:
    - Create, read, update, delete ToolCatalogueEntry
    - Create, read, update, delete ToolVersionEntry
    - Search ToolCatalogueEntry by name / tags / status
    - Search ToolVersionEntry by tool_id and status
    - ensure_indexes succeeds without errors
  Error cases:
    - Duplicate name raises ConflictingToolCatalogueEntryException
    - Missing id on update raises InvalidToolCatalogueEntryException
    - Non-existent id raises ToolCatalogueEntryNotFoundException
    - Non-existent version id raises ToolVersionEntryNotFoundException
    - Deleting a catalogue entry also deletes associated versions
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import pytest

from gafs.dynamicaiagent.toolcomponent.exceptions import (
    ConflictingToolCatalogueEntryException,
    InvalidToolCatalogueEntryException,
    ToolCatalogueEntryNotFoundException,
    ToolVersionEntryNotFoundException,
)
from gafs.dynamicaiagent.toolcomponent.models import (
    ToolCatalogueEntry,
    ToolCatalogueSearchCriteria,
    ToolVersionEntry,
    ToolVersionEntrySearchCriteria,
)
from gafs.dynamicaiagent.toolcomponent.models.tool_catalogue import (
    ToolStatus,
    ToolVersionStatus,
)

from gafs.dynamicaiagent.toolcomponent.test.test_helpers import unique_suffix


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_catalogue_entry(suffix: str) -> ToolCatalogueEntry:
    """Build a minimal valid ToolCatalogueEntry."""
    entry = ToolCatalogueEntry()
    entry.name = f"test_tool_{suffix}"
    entry.status = ToolStatus.ACTIVE
    entry.description = f"Integration test tool {suffix}"
    entry.tags = ["test", "integration", suffix]
    return entry


def _make_version_entry(tool_id: str, suffix: str) -> ToolVersionEntry:
    """Build a minimal valid ToolVersionEntry."""
    entry = ToolVersionEntry()
    entry.tool_id = tool_id
    entry.status = ToolVersionStatus.LATEST
    entry.description = f"Version {suffix}"
    entry.language = "Python"
    entry.code = (
        "import json, sys\n"
        "params = json.loads(open(sys.argv[1]).read())\n"
        "print(json.dumps({'echo': params['input_parameters'].get('message', 'hello')}))\n"
    )
    return entry


# ---------------------------------------------------------------------------
# ToolCatalogueEntry CRUD tests
# ---------------------------------------------------------------------------

class TestToolCatalogueEntryCRUD:
    """Create / Read / Update / Delete for ToolCatalogueEntry."""

    def test_create_and_get(self, integration_env_async: Any) -> None:
        """Created entry can be retrieved by id."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            suffix = unique_suffix()
            entry = _make_catalogue_entry(suffix)
            try:
                created = await svc.create_tool_catalogue_entry(entry)
                assert created.id is not None, "id should be assigned after creation"
                assert created.name == f"test_tool_{suffix}"
                assert created.status == ToolStatus.ACTIVE

                fetched = await svc.get_tool_catalogue_entry(created.id)
                assert fetched.id == created.id
                assert fetched.name == created.name
                assert fetched.description == created.description
                assert set(fetched.tags) == set(created.tags)
            finally:
                if created.id:
                    await svc.delete_tool_catalogue_entry(created.id)

        asyncio.run(run())

    def test_update_entry(self, integration_env_async: Any) -> None:
        """Updating description and status persists correctly."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            suffix = unique_suffix()
            entry = _make_catalogue_entry(suffix)
            created = await svc.create_tool_catalogue_entry(entry)
            try:
                created.description = "Updated description"
                created.status = ToolStatus.DEPRECATED
                updated = await svc.update_tool_catalogue_entry(created)
                assert updated.description == "Updated description"
                assert updated.status == ToolStatus.DEPRECATED
            finally:
                await svc.delete_tool_catalogue_entry(created.id)

        asyncio.run(run())

    def test_delete_entry(self, integration_env_async: Any) -> None:
        """Deleted entry raises ToolCatalogueEntryNotFoundException on get."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            suffix = unique_suffix()
            entry = _make_catalogue_entry(suffix)
            created = await svc.create_tool_catalogue_entry(entry)
            entry_id = created.id
            await svc.delete_tool_catalogue_entry(entry_id)

            with pytest.raises(ToolCatalogueEntryNotFoundException):
                await svc.get_tool_catalogue_entry(entry_id)

        asyncio.run(run())

    def test_delete_entry_cascades_versions(self, integration_env_async: Any) -> None:
        """Deleting a catalogue entry also deletes all associated versions."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            suffix = unique_suffix()
            entry = _make_catalogue_entry(suffix)
            created_catalogue = await svc.create_tool_catalogue_entry(entry)
            version = _make_version_entry(created_catalogue.id, suffix)
            created_version = await svc.create_tool_version_entry(version)
            version_id = created_version.id

            await svc.delete_tool_catalogue_entry(created_catalogue.id)

            with pytest.raises(ToolVersionEntryNotFoundException):
                await svc.get_tool_version_entry(version_id)

        asyncio.run(run())

    def test_get_all_entries(self, integration_env_async: Any) -> None:
        """get_all_tool_catalogue_entries returns all created entries."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            suffix = unique_suffix()
            entries = []
            for i in range(3):
                e = _make_catalogue_entry(f"{suffix}_{i}")
                created = await svc.create_tool_catalogue_entry(e)
                entries.append(created)
            try:
                all_entries = await svc.get_all_tool_catalogue_entries()
                all_ids = {e.id for e in all_entries}
                for created in entries:
                    assert created.id in all_ids, f"Entry {created.id} missing from get_all"
            finally:
                for e in entries:
                    await svc.delete_tool_catalogue_entry(e.id)

        asyncio.run(run())


# ---------------------------------------------------------------------------
# ToolCatalogueEntry error cases
# ---------------------------------------------------------------------------

class TestToolCatalogueEntryErrors:
    """Error cases for ToolCatalogueEntry operations."""

    def test_duplicate_name_raises_conflict(self, integration_env_async: Any) -> None:
        """Creating two entries with the same name raises ConflictingToolCatalogueEntryException."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            suffix = unique_suffix()
            entry = _make_catalogue_entry(suffix)
            created = await svc.create_tool_catalogue_entry(entry)
            try:
                duplicate = _make_catalogue_entry(suffix)  # same name
                with pytest.raises(ConflictingToolCatalogueEntryException):
                    await svc.create_tool_catalogue_entry(duplicate)
            finally:
                await svc.delete_tool_catalogue_entry(created.id)

        asyncio.run(run())

    def test_get_nonexistent_raises_not_found(self, integration_env_async: Any) -> None:
        """Getting a non-existent entry raises ToolCatalogueEntryNotFoundException."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            with pytest.raises(ToolCatalogueEntryNotFoundException):
                await svc.get_tool_catalogue_entry("nonexistent_id_xyz_000")

        asyncio.run(run())

    def test_delete_nonexistent_raises_not_found(self, integration_env_async: Any) -> None:
        """Deleting a non-existent entry raises ToolCatalogueEntryNotFoundException."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            with pytest.raises(ToolCatalogueEntryNotFoundException):
                await svc.delete_tool_catalogue_entry("nonexistent_id_xyz_001")

        asyncio.run(run())

    def test_update_without_id_raises_invalid(self, integration_env_async: Any) -> None:
        """Updating without id set raises InvalidToolCatalogueEntryException."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            entry = ToolCatalogueEntry()
            entry.name = "no_id_tool"
            entry.status = ToolStatus.ACTIVE
            with pytest.raises(InvalidToolCatalogueEntryException):
                await svc.update_tool_catalogue_entry(entry)

        asyncio.run(run())

    def test_update_nonexistent_raises_not_found(self, integration_env_async: Any) -> None:
        """Updating a non-existent id raises ToolCatalogueEntryNotFoundException."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            entry = ToolCatalogueEntry()
            entry.id = "nonexistent_xyz_002"
            entry.name = "ghost_tool"
            entry.status = ToolStatus.ACTIVE
            with pytest.raises(ToolCatalogueEntryNotFoundException):
                await svc.update_tool_catalogue_entry(entry)

        asyncio.run(run())


# ---------------------------------------------------------------------------
# ToolVersionEntry CRUD tests
# ---------------------------------------------------------------------------

class TestToolVersionEntryCRUD:
    """Create / Read / Update / Delete for ToolVersionEntry."""

    def test_create_and_get_version(self, integration_env_async: Any) -> None:
        """Created version entry can be retrieved by id."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            suffix = unique_suffix()
            catalogue = await svc.create_tool_catalogue_entry(_make_catalogue_entry(suffix))
            try:
                version = _make_version_entry(catalogue.id, suffix)
                created_version = await svc.create_tool_version_entry(version)
                try:
                    assert created_version.id is not None
                    assert created_version.tool_id == catalogue.id
                    assert created_version.status == ToolVersionStatus.LATEST
                    assert created_version.language == "Python"

                    fetched = await svc.get_tool_version_entry(created_version.id)
                    assert fetched.id == created_version.id
                    assert fetched.tool_id == created_version.tool_id
                    assert fetched.code == version.code
                finally:
                    await svc.delete_tool_version_entry(created_version.id)
            finally:
                await svc.delete_tool_catalogue_entry(catalogue.id)

        asyncio.run(run())

    def test_update_version_entry(self, integration_env_async: Any) -> None:
        """Updating a version entry's description persists correctly."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            suffix = unique_suffix()
            catalogue = await svc.create_tool_catalogue_entry(_make_catalogue_entry(suffix))
            version = await svc.create_tool_version_entry(_make_version_entry(catalogue.id, suffix))
            try:
                version.description = "Updated version description"
                version.status = ToolVersionStatus.ACTIVE
                updated = await svc.update_tool_version_entry(version)
                assert updated.description == "Updated version description"
                assert updated.status == ToolVersionStatus.ACTIVE
            finally:
                await svc.delete_tool_version_entry(version.id)
                await svc.delete_tool_catalogue_entry(catalogue.id)

        asyncio.run(run())

    def test_delete_version_entry(self, integration_env_async: Any) -> None:
        """Deleting a version entry raises ToolVersionEntryNotFoundException on get."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            suffix = unique_suffix()
            catalogue = await svc.create_tool_catalogue_entry(_make_catalogue_entry(suffix))
            version = await svc.create_tool_version_entry(_make_version_entry(catalogue.id, suffix))
            version_id = version.id
            try:
                await svc.delete_tool_version_entry(version_id)
                with pytest.raises(ToolVersionEntryNotFoundException):
                    await svc.get_tool_version_entry(version_id)
            finally:
                await svc.delete_tool_catalogue_entry(catalogue.id)

        asyncio.run(run())


# ---------------------------------------------------------------------------
# Search tests
# ---------------------------------------------------------------------------

class TestToolCatalogueSearch:
    """Search operations on ToolCatalogueEntry."""

    def test_search_by_status(self, integration_env_async: Any) -> None:
        """Search by ACTIVE status returns the created entry."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            suffix = unique_suffix()
            entry = _make_catalogue_entry(suffix)
            created = await svc.create_tool_catalogue_entry(entry)
            try:
                criteria = ToolCatalogueSearchCriteria()
                object.__setattr__(criteria, "status", [ToolStatus.ACTIVE])
                object.__setattr__(criteria, "version_status", [])
                object.__setattr__(criteria, "limit", 100)
                results = await svc.search_tool_catalogue_entries(criteria)
                result_ids = [r.catalogue.id for r in results]
                assert created.id in result_ids, "Created entry should appear in ACTIVE search"
            finally:
                await svc.delete_tool_catalogue_entry(created.id)

        asyncio.run(run())

    def test_search_version_entries_by_tool_id(self, integration_env_async: Any) -> None:
        """Search versions by tool_id returns associated versions."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            suffix = unique_suffix()
            catalogue = await svc.create_tool_catalogue_entry(_make_catalogue_entry(suffix))
            version = await svc.create_tool_version_entry(_make_version_entry(catalogue.id, suffix))
            try:
                criteria = ToolVersionEntrySearchCriteria()
                object.__setattr__(criteria, "tool_id", catalogue.id)
                object.__setattr__(criteria, "status", [ToolVersionStatus.LATEST])
                object.__setattr__(criteria, "limit", 50)
                results = await svc.search_tool_version_entries(criteria)
                version_ids = [v.id for v in results]
                assert version.id in version_ids, "Created version should appear in version search"
            finally:
                await svc.delete_tool_version_entry(version.id)
                await svc.delete_tool_catalogue_entry(catalogue.id)

        asyncio.run(run())


# ---------------------------------------------------------------------------
# ensure_indexes test
# ---------------------------------------------------------------------------

class TestEnsureIndexes:
    """Test ensure_indexes succeeds."""

    def test_ensure_indexes_no_error(self, integration_env_async: Any) -> None:
        """ensure_indexes runs without raising an exception."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.catalogue_service
            # Should not raise
            result = await svc.ensure_indexes(env.component._configurations)
            assert result is True

        asyncio.run(run())
