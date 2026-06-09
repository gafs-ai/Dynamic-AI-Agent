"""Integration tests for SandboxCatalogueService.

Tests CRUD and search operations on SandboxCatalogueEntry (both Host and Docker
subtypes) against a real SurrealDB instance.  Skipped when secret_test_db_config.json
is absent.

Test coverage:
  Normal cases:
    - Create, read, update, delete SandboxCatalogueHostEntry
    - Create, read, update, delete SandboxCatalogueDockerEntry
    - Search entries by status and tags
  Error cases:
    - Duplicate name raises ConflictingSandboxCatalogueEntryException
    - Missing id on update raises InvalidSandboxCatalogueEntryException
    - Non-existent id raises SandboxCatalogueEntryNotFoundException
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from gafs.dynamicaiagent.toolcomponent.exceptions import (
    ConflictingSandboxCatalogueEntryException,
    InvalidSandboxCatalogueEntryException,
    SandboxCatalogueEntryNotFoundException,
)
from gafs.dynamicaiagent.toolcomponent.models import SandboxCatalogueSearchCriteria
from gafs.dynamicaiagent.toolcomponent.models.sandbox_catalogue import (
    SandboxCatalogueDockerEntry,
    SandboxCatalogueHostEntry,
    SandboxStatus,
)

from gafs.dynamicaiagent.toolcomponent.test.test_helpers import unique_suffix


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MINIMAL_DOCKERFILE = (
    "FROM python:3.12-slim\n"
    "WORKDIR /app\n"
)


def _make_host_entry(suffix: str) -> SandboxCatalogueHostEntry:
    entry = SandboxCatalogueHostEntry()
    entry.name = f"test_host_sandbox_{suffix}"
    entry.status = SandboxStatus.ACTIVE
    entry.description = f"Host sandbox for integration test {suffix}"
    entry.tags = ["test", "host", suffix]
    return entry


def _make_docker_entry(suffix: str) -> SandboxCatalogueDockerEntry:
    entry = SandboxCatalogueDockerEntry()
    entry.name = f"test_docker_sandbox_{suffix}"
    entry.status = SandboxStatus.ACTIVE
    entry.description = f"Docker sandbox for integration test {suffix}"
    entry.tags = ["test", "docker", suffix]
    entry.docker_file = _MINIMAL_DOCKERFILE
    return entry


# ---------------------------------------------------------------------------
# SandboxCatalogueHostEntry CRUD tests
# ---------------------------------------------------------------------------

class TestSandboxCatalogueHostCRUD:
    """CRUD tests for host-type sandbox entries."""

    def test_create_and_get_host_entry(self, integration_env_async: Any) -> None:
        """Create a host entry and retrieve it by id."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.sandbox_service
            suffix = unique_suffix()
            entry = _make_host_entry(suffix)
            try:
                created = await svc.create_catalogue_entry(entry)
                assert created.id is not None
                assert created.name == f"test_host_sandbox_{suffix}"
                assert created.status == SandboxStatus.ACTIVE

                fetched = await svc.get_catalogue_entry(created.id)
                assert fetched.id == created.id
                assert fetched.name == created.name
                assert isinstance(fetched, SandboxCatalogueHostEntry)
            finally:
                if created.id:
                    await svc.delete_catalogue_entry(created.id)

        asyncio.run(run())

    def test_update_host_entry(self, integration_env_async: Any) -> None:
        """Updating a host entry persists the changes."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.sandbox_service
            suffix = unique_suffix()
            entry = _make_host_entry(suffix)
            created = await svc.create_catalogue_entry(entry)
            try:
                created.description = "Updated host description"
                created.status = SandboxStatus.DEPRECATED
                updated = await svc.update_catalogue_entry(created)
                assert updated.description == "Updated host description"
                assert updated.status == SandboxStatus.DEPRECATED
            finally:
                await svc.delete_catalogue_entry(created.id)

        asyncio.run(run())

    def test_delete_host_entry(self, integration_env_async: Any) -> None:
        """Deleted host entry raises SandboxCatalogueEntryNotFoundException on get."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.sandbox_service
            suffix = unique_suffix()
            created = await svc.create_catalogue_entry(_make_host_entry(suffix))
            entry_id = created.id
            await svc.delete_catalogue_entry(entry_id)
            with pytest.raises(SandboxCatalogueEntryNotFoundException):
                await svc.get_catalogue_entry(entry_id)

        asyncio.run(run())


# ---------------------------------------------------------------------------
# SandboxCatalogueDockerEntry CRUD tests
# ---------------------------------------------------------------------------

class TestSandboxCatalogueDockerCRUD:
    """CRUD tests for Docker-type sandbox entries."""

    def test_create_and_get_docker_entry(self, integration_env_async: Any) -> None:
        """Create a Docker entry and retrieve it by id."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.sandbox_service
            suffix = unique_suffix()
            entry = _make_docker_entry(suffix)
            created: Any = None
            try:
                created = await svc.create_catalogue_entry(entry)
                assert created.id is not None
                assert created.name == f"test_docker_sandbox_{suffix}"
                assert isinstance(created, SandboxCatalogueDockerEntry)
                assert created.docker_file == _MINIMAL_DOCKERFILE

                fetched = await svc.get_catalogue_entry(created.id)
                assert fetched.id == created.id
                assert isinstance(fetched, SandboxCatalogueDockerEntry)
                assert fetched.docker_file == _MINIMAL_DOCKERFILE
            finally:
                if created and created.id:
                    await svc.delete_catalogue_entry(created.id)

        asyncio.run(run())

    def test_update_docker_entry(self, integration_env_async: Any) -> None:
        """Updating a Docker entry persists the changes."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.sandbox_service
            suffix = unique_suffix()
            created = await svc.create_catalogue_entry(_make_docker_entry(suffix))
            try:
                created.description = "Updated Docker description"
                updated_dockerfile = _MINIMAL_DOCKERFILE + "RUN echo 'updated'\n"
                created.docker_file = updated_dockerfile
                updated = await svc.update_catalogue_entry(created)
                assert updated.description == "Updated Docker description"
                assert updated.docker_file == updated_dockerfile
            finally:
                await svc.delete_catalogue_entry(created.id)

        asyncio.run(run())

    def test_delete_docker_entry(self, integration_env_async: Any) -> None:
        """Deleted Docker entry raises SandboxCatalogueEntryNotFoundException."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.sandbox_service
            suffix = unique_suffix()
            created = await svc.create_catalogue_entry(_make_docker_entry(suffix))
            entry_id = created.id
            await svc.delete_catalogue_entry(entry_id)
            with pytest.raises(SandboxCatalogueEntryNotFoundException):
                await svc.get_catalogue_entry(entry_id)

        asyncio.run(run())

    def test_get_all_entries(self, integration_env_async: Any) -> None:
        """get_all_catalogue_entries returns all created entries."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.sandbox_service
            suffix = unique_suffix()
            created_entries = []
            for i in range(2):
                created = await svc.create_catalogue_entry(_make_docker_entry(f"{suffix}_{i}"))
                created_entries.append(created)
            try:
                all_entries = await svc.get_all_catalogue_entries()
                all_ids = {e.id for e in all_entries}
                for e in created_entries:
                    assert e.id in all_ids
            finally:
                for e in created_entries:
                    await svc.delete_catalogue_entry(e.id)

        asyncio.run(run())


# ---------------------------------------------------------------------------
# SandboxCatalogueEntry error cases
# ---------------------------------------------------------------------------

class TestSandboxCatalogueErrors:
    """Error cases for SandboxCatalogueService operations."""

    def test_duplicate_name_raises_conflict(self, integration_env_async: Any) -> None:
        """Two entries with the same name raise ConflictingSandboxCatalogueEntryException."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.sandbox_service
            suffix = unique_suffix()
            created = await svc.create_catalogue_entry(_make_docker_entry(suffix))
            try:
                duplicate = _make_docker_entry(suffix)  # same name
                with pytest.raises(ConflictingSandboxCatalogueEntryException):
                    await svc.create_catalogue_entry(duplicate)
            finally:
                await svc.delete_catalogue_entry(created.id)

        asyncio.run(run())

    def test_get_nonexistent_raises_not_found(self, integration_env_async: Any) -> None:
        """Getting a non-existent sandbox raises SandboxCatalogueEntryNotFoundException."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.sandbox_service
            with pytest.raises(SandboxCatalogueEntryNotFoundException):
                await svc.get_catalogue_entry("nonexistent_sandbox_xyz_000")

        asyncio.run(run())

    def test_delete_nonexistent_raises_not_found(self, integration_env_async: Any) -> None:
        """Deleting a non-existent sandbox raises SandboxCatalogueEntryNotFoundException."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.sandbox_service
            with pytest.raises(SandboxCatalogueEntryNotFoundException):
                await svc.delete_catalogue_entry("nonexistent_sandbox_xyz_001")

        asyncio.run(run())

    def test_update_without_id_raises_invalid(self, integration_env_async: Any) -> None:
        """Updating a sandbox entry without id raises InvalidSandboxCatalogueEntryException."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.sandbox_service
            entry = SandboxCatalogueDockerEntry()
            entry.name = "no_id_sandbox"
            entry.status = SandboxStatus.ACTIVE
            entry.docker_file = _MINIMAL_DOCKERFILE
            with pytest.raises(InvalidSandboxCatalogueEntryException):
                await svc.update_catalogue_entry(entry)

        asyncio.run(run())

    def test_update_nonexistent_raises_not_found(self, integration_env_async: Any) -> None:
        """Updating a non-existent id raises SandboxCatalogueEntryNotFoundException."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.sandbox_service
            entry = SandboxCatalogueDockerEntry()
            entry.id = "nonexistent_xyz_sandbox_002"
            entry.name = "ghost_sandbox"
            entry.status = SandboxStatus.ACTIVE
            entry.docker_file = _MINIMAL_DOCKERFILE
            with pytest.raises(SandboxCatalogueEntryNotFoundException):
                await svc.update_catalogue_entry(entry)

        asyncio.run(run())


# ---------------------------------------------------------------------------
# Search tests
# ---------------------------------------------------------------------------

class TestSandboxCatalogueSearch:
    """Search operations on SandboxCatalogueEntry."""

    def test_search_by_status(self, integration_env_async: Any) -> None:
        """Searching by ACTIVE status returns the created docker entry."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.sandbox_service
            suffix = unique_suffix()
            created = await svc.create_catalogue_entry(_make_docker_entry(suffix))
            try:
                criteria = SandboxCatalogueSearchCriteria()
                object.__setattr__(criteria, "status", [SandboxStatus.ACTIVE])
                object.__setattr__(criteria, "limit", 100)
                results = await svc.search_catalogue_entries(criteria)
                result_ids = [r.id for r in results]
                assert created.id in result_ids
            finally:
                await svc.delete_catalogue_entry(created.id)

        asyncio.run(run())

    def test_search_by_name(self, integration_env_async: Any) -> None:
        """Searching by name returns the matching entry."""
        async def run() -> None:
            env = await integration_env_async()
            svc = env.sandbox_service
            suffix = unique_suffix()
            created = await svc.create_catalogue_entry(_make_docker_entry(suffix))
            try:
                criteria = SandboxCatalogueSearchCriteria()
                object.__setattr__(criteria, "name", f"test_docker_sandbox_{suffix}")
                object.__setattr__(criteria, "limit", 10)
                results = await svc.search_catalogue_entries(criteria)
                assert any(r.id == created.id for r in results), "Name search should return the created entry"
            finally:
                await svc.delete_catalogue_entry(created.id)

        asyncio.run(run())
