"""Integration tests for ToolComponent (top-level facade).

Tests initialization, configuration management, and delegation of CRUD and
invocation to sub-services.  All tests connect to a real SurrealDB instance
and are skipped if secret_test_db_config.json is absent.

Docker-dependent tests (invoke scenario) are additionally skipped if
Docker is not reachable.

Test coverage:
  Normal cases:
    - ToolComponent initializes successfully with a valid config record
    - get_configurations returns the loaded ToolComponentConfigurations
    - update_configurations persists changes to the database
    - create/get/delete ToolCatalogueEntry via component facade
    - create/get ToolVersionEntry via component facade
    - create/get/delete SandboxCatalogueEntry via component facade
    - invoke tool (Docker required)
  Error cases:
    - initialize fails when component_configurations record is absent
    - invoke raises ToolCatalogueEntryNotFoundException for unknown tool_id
    - invoke raises ToolVersionEntryNotFoundException for unknown version_id
    - invoke raises InvalidToolInvocationException when a required param is missing
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from gafs.dynamicaiagent.toolcomponent.exceptions import (
    InvalidToolComponentConfigurationException,
    InvalidToolInvocationException,
    ToolCatalogueEntryNotFoundException,
    ToolComponentInitializationException,
    ToolVersionEntryNotFoundException,
)
from gafs.dynamicaiagent.toolcomponent.models import (
    ToolCatalogueEntry,
    ToolComponentConfigurations,
    ToolVersionEntry,
)
from gafs.dynamicaiagent.toolcomponent.models.sandbox_catalogue import (
    SandboxCatalogueDockerEntry,
    SandboxStatus,
)
from gafs.dynamicaiagent.toolcomponent.models.tool_catalogue import (
    InputParameterDefinition,
    ToolStatus,
    ToolVersionStatus,
)
from gafs.dynamicaiagent.common.models import FieldAttributeType

from gafs.dynamicaiagent.toolcomponent.test.test_helpers import (
    is_docker_available,
    unique_suffix,
)
from gafs.dynamicaiagent.toolcomponent.test.conftest import (
    _TestSecretManager,
    _build_connection,
    _load_db_config,
    _logger,
)
from gafs.dynamicaiagent.common.databasemanager import DatabaseManager
from gafs.dynamicaiagent.toolcomponent import (
    DockerSandboxService,
    SandboxCatalogueService,
    ToolCatalogueService,
    ToolComponent,
)

requires_docker = pytest.mark.skipif(
    not is_docker_available(),
    reason="Docker daemon is not reachable; skipping Docker-dependent ToolComponent tests.",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_catalogue(suffix: str) -> ToolCatalogueEntry:
    entry = ToolCatalogueEntry()
    entry.name = f"tc_test_tool_{suffix}"
    entry.status = ToolStatus.ACTIVE
    entry.description = f"ToolComponent integration test {suffix}"
    entry.tags = ["test", "tc_integration"]
    return entry


def _make_version(tool_id: str, sandbox_id: str, suffix: str) -> ToolVersionEntry:
    entry = ToolVersionEntry()
    entry.tool_id = tool_id
    entry.status = ToolVersionStatus.LATEST
    entry.language = "Python"
    entry.sandbox_id = sandbox_id
    entry.code = (
        "import json, sys\n"
        "params = json.loads(open(sys.argv[1]).read())\n"
        "inputs = params['input_parameters']\n"
        "print(json.dumps({'result': inputs.get('value', 'default')}))\n"
    )
    # Add a required input parameter definition
    param = InputParameterDefinition()
    param.name = "value"
    param.type = FieldAttributeType.STR
    param.required = True
    entry.input_parameters = [param]
    return entry


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------

class TestToolComponentInitialization:
    """Tests for ToolComponent.initialize()."""

    def test_initialize_succeeds(self, integration_env_async: Any) -> None:
        """ToolComponent initializes successfully when the config record exists."""
        async def run() -> None:
            env = await integration_env_async()
            # If we got here, initialize already succeeded in the fixture
            assert env.component is not None

        asyncio.run(run())

    def test_initialize_fails_without_config(self) -> None:
        """ToolComponent.initialize() raises when no config record exists in DB."""
        config = _load_db_config()
        if not config:
            pytest.skip("DB config is missing.")

        async def run() -> None:
            conn_config = _build_connection(config)
            lg = _logger("test_tc_init_fail")
            manager = DatabaseManager(lg)
            await manager.initialize_default_connection(conn_config)
            await manager.initialize(_TestSecretManager())

            provider = manager.get_default_provider()

            # Back up and remove the config record so initialize() cannot find it
            raw_backup = await provider.query_raw(
                "SELECT * FROM component_configurations:tool_component;"
            )
            await provider.query_raw("DELETE component_configurations:tool_component;")

            try:
                catalogue_service = ToolCatalogueService(lg)
                sandbox_service = SandboxCatalogueService(lg)
                docker_service = DockerSandboxService(lg)
                component = ToolComponent(
                    logger=lg,
                    tool_catalogue_service=catalogue_service,
                    sandbox_catalogue_service=sandbox_service,
                    docker_sandbox_service=docker_service,
                )

                with pytest.raises(ToolComponentInitializationException):
                    await component.initialize(manager)
            finally:
                # Restore the config record from backup
                backup_list = raw_backup
                if isinstance(backup_list, list) and backup_list:
                    first = backup_list[0]
                    if isinstance(first, dict) and "result" in first:
                        backup_list = first["result"]
                if isinstance(backup_list, list) and backup_list:
                    record = backup_list[0]
                    record_dict = record if isinstance(record, dict) else getattr(record, "__dict__", {})
                    record_dict.pop("id", None)
                    restore_json = json.dumps(record_dict)
                    await provider.query_raw(
                        f"UPSERT component_configurations:tool_component MERGE {restore_json};"
                    )

        asyncio.run(run())


# ---------------------------------------------------------------------------
# Configuration tests
# ---------------------------------------------------------------------------

class TestToolComponentConfigurations:
    """Tests for get_configurations and update_configurations."""

    def test_get_configurations(self, integration_env_async: Any) -> None:
        """get_configurations returns the loaded ToolComponentConfigurations."""
        async def run() -> None:
            env = await integration_env_async()
            configs = await env.component.get_configurations()
            assert isinstance(configs, ToolComponentConfigurations)
            assert configs.app_data_folder is not None
            assert len(configs.app_data_folder) > 0

        asyncio.run(run())

    def test_update_configurations(self, integration_env_async: Any) -> None:
        """update_configurations persists changes to the database."""
        async def run() -> None:
            env = await integration_env_async()
            configs = await env.component.get_configurations()
            original_limit = configs.docker_default_image_max_stand_by

            # Update the limit
            configs.docker_default_image_max_stand_by = original_limit + 1
            await env.component.update_configurations(configs)

            # Re-load and verify
            reloaded = await env.component.get_configurations()
            assert reloaded.docker_default_image_max_stand_by == original_limit + 1

            # Restore
            configs.docker_default_image_max_stand_by = original_limit
            await env.component.update_configurations(configs)

        asyncio.run(run())


# ---------------------------------------------------------------------------
# ToolCatalogueEntry delegation tests
# ---------------------------------------------------------------------------

class TestToolComponentCatalogueDelegation:
    """Tests for ToolCatalogueEntry / ToolVersionEntry delegation through ToolComponent."""

    def test_create_and_get_catalogue_entry(self, integration_env_async: Any) -> None:
        """ToolComponent creates and retrieves a ToolCatalogueEntry."""
        async def run() -> None:
            env = await integration_env_async()
            suffix = unique_suffix()
            entry = _make_catalogue(suffix)
            created = await env.component.create_tool_catalogue_entry(entry)
            try:
                assert created.id is not None
                fetched = await env.component.get_tool_catalogue_entry(created.id)
                assert fetched.id == created.id
            finally:
                if created.id:
                    await env.component.delete_tool_catalogue_entry(created.id)

        asyncio.run(run())

    def test_delete_catalogue_entry(self, integration_env_async: Any) -> None:
        """ToolComponent deletes a ToolCatalogueEntry by id."""
        async def run() -> None:
            env = await integration_env_async()
            suffix = unique_suffix()
            created = await env.component.create_tool_catalogue_entry(_make_catalogue(suffix))
            entry_id = created.id
            await env.component.delete_tool_catalogue_entry(entry_id)
            with pytest.raises(ToolCatalogueEntryNotFoundException):
                await env.component.get_tool_catalogue_entry(entry_id)

        asyncio.run(run())

    def test_get_nonexistent_raises_not_found(self, integration_env_async: Any) -> None:
        """Getting a non-existent ToolCatalogueEntry raises ToolCatalogueEntryNotFoundException."""
        async def run() -> None:
            env = await integration_env_async()
            with pytest.raises(ToolCatalogueEntryNotFoundException):
                await env.component.get_tool_catalogue_entry("nonexistent_tc_xyz_000")

        asyncio.run(run())


# ---------------------------------------------------------------------------
# SandboxCatalogueEntry delegation tests
# ---------------------------------------------------------------------------

class TestToolComponentSandboxDelegation:
    """Tests for SandboxCatalogueEntry delegation through ToolComponent."""

    def test_create_and_get_sandbox_entry(self, integration_env_async: Any) -> None:
        """ToolComponent creates and retrieves a SandboxCatalogueDockerEntry."""
        async def run() -> None:
            env = await integration_env_async()
            suffix = unique_suffix()
            entry = SandboxCatalogueDockerEntry()
            entry.name = f"tc_sandbox_{suffix}"
            entry.status = SandboxStatus.ACTIVE
            entry.docker_file = "FROM python:3.12-slim\nWORKDIR /app\n"
            entry.tags = ["test", "tc_sandbox"]

            created = await env.component.create_sandbox_catalogue_entry(entry)
            try:
                assert created.id is not None
                fetched = await env.component.get_sandbox_catalogue_entry(created.id)
                assert fetched.id == created.id
                assert isinstance(fetched, SandboxCatalogueDockerEntry)
            finally:
                if created.id:
                    await env.component.delete_sandbox_catalogue_entry(created.id)

        asyncio.run(run())


# ---------------------------------------------------------------------------
# Tool invocation tests (require Docker)
# ---------------------------------------------------------------------------

class TestToolComponentInvoke:
    """Tests for ToolComponent.invoke()."""

    @requires_docker
    def test_invoke_tool_with_valid_params(self, integration_env_async: Any) -> None:
        """invoke returns the tool's output when valid parameters are provided."""
        async def run() -> None:
            env = await integration_env_async()
            suffix = unique_suffix()

            # Create sandbox
            sandbox = SandboxCatalogueDockerEntry()
            sandbox.name = f"tc_invoke_sandbox_{suffix}"
            sandbox.status = SandboxStatus.ACTIVE
            sandbox.docker_file = "FROM python:3.12-slim\nWORKDIR /app\n"
            sandbox = await env.component.create_sandbox_catalogue_entry(sandbox)

            catalogue = await env.component.create_tool_catalogue_entry(_make_catalogue(suffix))
            version = await env.component._tool_catalogue_service.create_tool_version_entry(
                _make_version(catalogue.id, sandbox.id, suffix)
            )

            try:
                result = await env.component.invoke(
                    catalogue.id, version.id, {"value": "hello_invoke"}
                )
                assert result["result"] == "hello_invoke"
            finally:
                await env.docker_service._exit()
                await env.component._tool_catalogue_service.delete_tool_version_entry(version.id)
                await env.component.delete_tool_catalogue_entry(catalogue.id)
                await env.component.delete_sandbox_catalogue_entry(sandbox.id)

        asyncio.run(run())

    def test_invoke_unknown_tool_id_raises(self, integration_env_async: Any) -> None:
        """invoke raises ToolCatalogueEntryNotFoundException for unknown tool_id."""
        async def run() -> None:
            env = await integration_env_async()
            with pytest.raises(ToolCatalogueEntryNotFoundException):
                await env.component.invoke("unknown_tool_xyz", "some_version", {})

        asyncio.run(run())

    def test_invoke_unknown_version_id_raises(self, integration_env_async: Any) -> None:
        """invoke raises ToolVersionEntryNotFoundException for unknown version_id."""
        async def run() -> None:
            env = await integration_env_async()
            suffix = unique_suffix()
            catalogue = await env.component.create_tool_catalogue_entry(_make_catalogue(suffix))
            try:
                with pytest.raises(ToolVersionEntryNotFoundException):
                    await env.component.invoke(catalogue.id, "unknown_version_xyz", {})
            finally:
                await env.component.delete_tool_catalogue_entry(catalogue.id)

        asyncio.run(run())

    @requires_docker
    def test_invoke_missing_required_param_raises(self, integration_env_async: Any) -> None:
        """invoke raises InvalidToolInvocationException when a required param is missing."""
        async def run() -> None:
            env = await integration_env_async()
            suffix = unique_suffix()

            sandbox = SandboxCatalogueDockerEntry()
            sandbox.name = f"tc_val_sandbox_{suffix}"
            sandbox.status = SandboxStatus.ACTIVE
            sandbox.docker_file = "FROM python:3.12-slim\nWORKDIR /app\n"
            sandbox = await env.component.create_sandbox_catalogue_entry(sandbox)
            catalogue = await env.component.create_tool_catalogue_entry(_make_catalogue(suffix))
            version = await env.component._tool_catalogue_service.create_tool_version_entry(
                _make_version(catalogue.id, sandbox.id, suffix)
            )

            try:
                with pytest.raises(InvalidToolInvocationException):
                    # 'value' is required; not passing it should raise
                    await env.component.invoke(catalogue.id, version.id, {})
            finally:
                await env.docker_service._exit()
                await env.component._tool_catalogue_service.delete_tool_version_entry(version.id)
                await env.component.delete_tool_catalogue_entry(catalogue.id)
                await env.component.delete_sandbox_catalogue_entry(sandbox.id)

        asyncio.run(run())
