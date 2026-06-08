"""Integration tests for DockerSandboxService.

Tests tool execution inside Docker containers against a real Docker daemon
and a real SurrealDB instance.  All tests in this module are automatically
SKIPPED if either the DB config file is missing or Docker is not reachable.

Test scenarios (per user requirements):
  1. Parameter input/output    - tool echoes input_parameters back as output
  2. File read/write           - tool reads a file from input_dir and writes one to output_dir
  3. tmp folder usage          - tool creates and reads a temp file under tmp_dir
  4. Code stored in DB (code field)   - default for all above scenarios
  5. Code stored as file (code field) - tool code written to filesystem before container runs

All five scenarios share the same Docker sandbox (python:3.12-slim image) and
verify that DockerSandboxService correctly:
  - Writes _params.json to the container's input directory
  - Mounts input/output/tmp directories into the container
  - Parses JSON from the tool's stdout as the result dict
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pytest

from gafs.dynamicaiagent.toolcomponent.models import (
    ToolCatalogueEntry,
    ToolVersionEntry,
)
from gafs.dynamicaiagent.toolcomponent.models.sandbox_catalogue import (
    SandboxCatalogueDockerEntry,
    SandboxStatus,
)
from gafs.dynamicaiagent.toolcomponent.models.tool_catalogue import (
    ToolStatus,
    ToolVersionStatus,
)

from gafs.dynamicaiagent.toolcomponent.test.test_helpers import is_docker_available, unique_suffix

# ---------------------------------------------------------------------------
# Skip marker
# ---------------------------------------------------------------------------

requires_docker = pytest.mark.skipif(
    not is_docker_available(),
    reason="Docker daemon is not reachable; skipping Docker sandbox tests.",
)

# ---------------------------------------------------------------------------
# Test tool code snippets
# ---------------------------------------------------------------------------

# Scenario 1: Parameter input/output
# The tool reads all input_parameters from the params JSON file and echoes
# them back as output.
_CODE_PARAM_IO = """\
import json
import sys

params = json.loads(open(sys.argv[1], encoding="utf-8").read())
inputs = params.get("input_parameters", {})
# Echo all input parameters as output
result = {k: v for k, v in inputs.items()}
print(json.dumps(result))
"""

# Scenario 2: File read/write
# The tool reads input_file.txt from input_dir and writes output_file.txt to output_dir.
_CODE_FILE_RW = """\
import json
import sys
import os

params = json.loads(open(sys.argv[1], encoding="utf-8").read())
input_dir = params["input_dir"]
output_dir = params["output_dir"]

input_file_path = os.path.join(input_dir, "input_file.txt")
content = open(input_file_path, encoding="utf-8").read().strip()

output_file_path = os.path.join(output_dir, "output_file.txt")
with open(output_file_path, "w", encoding="utf-8") as f:
    f.write(content.upper())

print(json.dumps({"output_file": "output_file.txt", "content_length": len(content)}))
"""

# Scenario 3: tmp folder usage
# The tool creates a temp file in tmp_dir, reads it back, and returns the value.
_CODE_TMP_FOLDER = """\
import json
import sys
import os

params = json.loads(open(sys.argv[1], encoding="utf-8").read())
tmp_dir = params["tmp_dir"]
inputs = params.get("input_parameters", {})
value = inputs.get("value", "default")

# Write to tmp
tmp_path = os.path.join(tmp_dir, "scratch.txt")
with open(tmp_path, "w", encoding="utf-8") as f:
    f.write(value)

# Read back from tmp
read_back = open(tmp_path, encoding="utf-8").read()

print(json.dumps({"tmp_written": value, "tmp_read_back": read_back}))
"""

# ---------------------------------------------------------------------------
# Sandbox Dockerfile for tests (minimal Python image)
# ---------------------------------------------------------------------------
_TEST_DOCKERFILE = "FROM python:3.12-slim\nWORKDIR /app\n"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

async def _create_test_sandbox(
    svc: Any, suffix: str
) -> SandboxCatalogueDockerEntry:
    """Create and return a minimal Docker sandbox entry."""
    entry = SandboxCatalogueDockerEntry()
    entry.name = f"test_exec_sandbox_{suffix}"
    entry.status = SandboxStatus.ACTIVE
    entry.description = "Docker execution test sandbox"
    entry.tags = ["test", "docker", "execution"]
    entry.docker_file = _TEST_DOCKERFILE
    return await svc.create_catalogue_entry(entry)


async def _create_test_catalogue(svc: Any, suffix: str) -> ToolCatalogueEntry:
    """Create and return a minimal ToolCatalogueEntry."""
    entry = ToolCatalogueEntry()
    entry.name = f"test_exec_tool_{suffix}"
    entry.status = ToolStatus.ACTIVE
    entry.description = "Execution test tool"
    entry.tags = ["test", "execution"]
    return await svc.create_tool_catalogue_entry(entry)


async def _create_test_version(
    svc: Any, tool_id: str, sandbox_id: str, code: str, suffix: str
) -> ToolVersionEntry:
    """Create and return a ToolVersionEntry with the given code."""
    entry = ToolVersionEntry()
    entry.tool_id = tool_id
    entry.status = ToolVersionStatus.LATEST
    entry.description = f"Execution test version {suffix}"
    entry.language = "Python"
    entry.sandbox_id = sandbox_id
    entry.code = code
    return await svc.create_tool_version_entry(entry)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDockerSandboxExecution:
    """Execute tool code inside Docker containers."""

    @requires_docker
    def test_scenario1_parameter_io(self, integration_env_async: Any) -> None:
        """Scenario 1: Input parameters are echoed back as output parameters."""
        async def run() -> None:
            env = await integration_env_async()
            suffix = unique_suffix()
            cat_svc = env.catalogue_service
            sbx_svc = env.sandbox_service
            docker_svc = env.docker_service

            sandbox = await _create_test_sandbox(sbx_svc, suffix)
            catalogue = await _create_test_catalogue(cat_svc, suffix)
            version = await _create_test_version(
                cat_svc, catalogue.id, sandbox.id, _CODE_PARAM_IO, suffix
            )

            try:
                # execute_code registers the sandbox on-demand if not already initialized
                result = await docker_svc.execute_code(
                    version,
                    sandbox,
                    {"message": "hello", "count": 42},
                )
                assert result["message"] == "hello"
                assert result["count"] == 42
            finally:
                await cat_svc.delete_tool_version_entry(version.id)
                await cat_svc.delete_tool_catalogue_entry(catalogue.id)
                await sbx_svc.delete_catalogue_entry(sandbox.id)

        asyncio.run(run())

    @requires_docker
    def test_scenario2_file_read_write(self, integration_env_async: Any) -> None:
        """Scenario 2: Tool reads a file from input_dir and writes to output_dir.

        The first container name for a freshly created sandbox is deterministic:
        {sandbox_id}_0.  We pre-write the input file to the expected host path so
        it is available inside the container's /app/data/input/ volume mount.
        The tool reports what it read/wrote via JSON stdout; we verify that output
        because the host directory is cleaned up by execute_code when it destroys
        the container.
        """
        async def run() -> None:
            env = await integration_env_async()
            suffix = unique_suffix()
            cat_svc = env.catalogue_service
            sbx_svc = env.sandbox_service
            docker_svc = env.docker_service

            sandbox = await _create_test_sandbox(sbx_svc, suffix)
            catalogue = await _create_test_catalogue(cat_svc, suffix)
            version = await _create_test_version(
                cat_svc, catalogue.id, sandbox.id, _CODE_FILE_RW, suffix
            )

            try:
                # Pre-write input_file.txt to the expected container host path.
                # The first container for a new sandbox is always named {sandbox_id}_0.
                expected_container_name = f"{sandbox.id}_0"
                input_dir = (
                    Path(env.app_data_folder)
                    / "tools" / "files" / expected_container_name / "input"
                )
                input_dir.mkdir(parents=True, exist_ok=True)
                (input_dir / "input_file.txt").write_text("hello world", encoding="utf-8")

                result = await docker_svc.execute_code(version, sandbox, {})
                assert result["output_file"] == "output_file.txt"
                assert result["content_length"] == len("hello world")
            finally:
                await cat_svc.delete_tool_version_entry(version.id)
                await cat_svc.delete_tool_catalogue_entry(catalogue.id)
                await sbx_svc.delete_catalogue_entry(sandbox.id)

        asyncio.run(run())

    @requires_docker
    def test_scenario3_tmp_folder(self, integration_env_async: Any) -> None:
        """Scenario 3: Tool creates and reads a temp file in tmp_dir."""
        async def run() -> None:
            env = await integration_env_async()
            suffix = unique_suffix()
            cat_svc = env.catalogue_service
            sbx_svc = env.sandbox_service
            docker_svc = env.docker_service

            sandbox = await _create_test_sandbox(sbx_svc, suffix)
            catalogue = await _create_test_catalogue(cat_svc, suffix)
            version = await _create_test_version(
                cat_svc, catalogue.id, sandbox.id, _CODE_TMP_FOLDER, suffix
            )

            try:
                result = await docker_svc.execute_code(
                    version, sandbox, {"value": "scratch_data"}
                )
                assert result["tmp_written"] == "scratch_data"
                assert result["tmp_read_back"] == "scratch_data"
            finally:
                await cat_svc.delete_tool_version_entry(version.id)
                await cat_svc.delete_tool_catalogue_entry(catalogue.id)
                await sbx_svc.delete_catalogue_entry(sandbox.id)

        asyncio.run(run())

    @requires_docker
    def test_scenario4_code_stored_in_db(self, integration_env_async: Any) -> None:
        """Scenario 4: Tool code is stored in the DB (code field).

        Verifies that execute_code uses the code written to the filesystem from
        the DB-stored code field.
        """
        async def run() -> None:
            env = await integration_env_async()
            suffix = unique_suffix()
            cat_svc = env.catalogue_service
            sbx_svc = env.sandbox_service
            docker_svc = env.docker_service

            # The code field is used when creating versions; ToolCatalogueService
            # writes it to {app_data_folder}/tools/codes/{tool_id}_{version_id}/main.py
            db_code = (
                "import json, sys\n"
                "params = json.loads(open(sys.argv[1]).read())\n"
                "print(json.dumps({'source': 'db', 'msg': params['input_parameters'].get('msg', '')}))\n"
            )

            sandbox = await _create_test_sandbox(sbx_svc, suffix)
            catalogue = await _create_test_catalogue(cat_svc, suffix)
            version = await _create_test_version(
                cat_svc, catalogue.id, sandbox.id, db_code, suffix
            )

            # Confirm code was written to disk
            code_dir = Path(env.app_data_folder) / "tools" / "codes" / f"{catalogue.id}_{version.id}"
            assert (code_dir / "main.py").exists(), "DB code should be written to main.py"

            try:
                result = await docker_svc.execute_code(
                    version, sandbox, {"msg": "from_db"}
                )
                assert result["source"] == "db"
                assert result["msg"] == "from_db"
            finally:
                await cat_svc.delete_tool_version_entry(version.id)
                await cat_svc.delete_tool_catalogue_entry(catalogue.id)
                await sbx_svc.delete_catalogue_entry(sandbox.id)

        asyncio.run(run())

    @requires_docker
    def test_scenario5_code_stored_as_file(self, integration_env_async: Any) -> None:
        """Scenario 5: Tool code is stored as a file on the filesystem.

        Simulates the code_link scenario by pre-writing code to the expected
        filesystem path (as if tool_catalogue_service had already done the
        git clone or direct write) and verifies execute_code picks it up.
        """
        async def run() -> None:
            env = await integration_env_async()
            suffix = unique_suffix()
            cat_svc = env.catalogue_service
            sbx_svc = env.sandbox_service
            docker_svc = env.docker_service

            file_code = (
                "import json, sys\n"
                "params = json.loads(open(sys.argv[1]).read())\n"
                "print(json.dumps({'source': 'file', "
                "'value': params['input_parameters'].get('value', '')}))\n"
            )

            sandbox = await _create_test_sandbox(sbx_svc, suffix)
            catalogue = await _create_test_catalogue(cat_svc, suffix)

            # Create version entry WITHOUT setting code so no file is written from DB
            version_entry = ToolVersionEntry()
            version_entry.tool_id = catalogue.id
            version_entry.status = ToolVersionStatus.LATEST
            version_entry.language = "Python"
            version_entry.sandbox_id = sandbox.id
            # code and code_link both None => no filesystem write by service
            version = await cat_svc.create_tool_version_entry(version_entry)

            # Pre-write code to expected path (simulating file-based storage)
            code_dir = Path(env.app_data_folder) / "tools" / "codes" / f"{catalogue.id}_{version.id}"
            code_dir.mkdir(parents=True, exist_ok=True)
            (code_dir / "main.py").write_text(file_code, encoding="utf-8")

            try:
                result = await docker_svc.execute_code(
                    version, sandbox, {"value": "from_file"}
                )
                assert result["source"] == "file"
                assert result["value"] == "from_file"
            finally:
                await cat_svc.delete_tool_version_entry(version.id)
                await cat_svc.delete_tool_catalogue_entry(catalogue.id)
                await sbx_svc.delete_catalogue_entry(sandbox.id)

        asyncio.run(run())
