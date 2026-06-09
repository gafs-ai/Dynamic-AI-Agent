"""docker_sandbox_service.py - Concrete implementation of IDockerSandboxService.

Manages Docker image/container lifecycle for sandboxed tool execution.
Pre-builds images and pools standby containers for active sandbox definitions.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import shutil
from typing import Any

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager

from .exceptions import (
    SandboxCatalogueEntryNotFoundException,
    ToolComponentInitializationException,
    ToolComponentNotInitializedException,
    ToolComponentOperationException,
)
from .i_docker_sandbox_service import IDockerSandboxService
from .i_sandbox_catalogue_service import ISandboxCatalogueService
from .models import (
    SandboxCatalogueDockerEntry,
    SandboxCatalogueSearchCriteria,
    ToolComponentConfigurations,
    ToolVersionEntry,
)
from .models.sandbox_catalogue import SandboxStatus


class DockerSandboxService(IDockerSandboxService):
    """Docker image and container lifecycle manager for sandboxed tool execution.

    Manages a pool of standby containers per sandbox definition to reduce
    per-invocation latency. Tool code is executed via ``docker exec`` inside
    long-running ``sleep infinity`` containers.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the service.

        Args:
            logger: Logger instance for operational messages.
        """
        self._logger: logging.Logger = logger
        self._database_manager: IDatabaseManager | None = None
        self._sandbox_catalogue_service: ISandboxCatalogueService | None = None
        self._configurations: ToolComponentConfigurations | None = None
        # Maps sandbox_entry.id -> list of standby container names
        self._standby_containers: dict[str, list[str]] = {}
        # Maps sandbox_entry.id -> next container sequence number
        self._container_counts: dict[str, int] = {}

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _get_docker_client(self) -> Any:
        """Return a Docker SDK client instance.

        Raises:
            ToolComponentOperationException: Docker SDK not available or daemon unreachable.
        """
        try:
            import docker
            client = docker.from_env()
            return client
        except ImportError as exc:
            raise ToolComponentOperationException(
                "Docker SDK is not installed. Install it with: pip install docker",
                cause=exc,
            ) from exc
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to connect to Docker daemon.", cause=exc
            ) from exc

    async def _create_image(
        self, sandbox_entry: SandboxCatalogueDockerEntry
    ) -> str:
        """Build a Docker image from sandbox_entry.docker_file.

        Args:
            sandbox_entry: Docker sandbox definition with Dockerfile content.

        Returns:
            The image name (= sandbox_entry.id).

        Raises:
            ToolComponentOperationException: Docker image build failure.
        """
        image_name = sandbox_entry.id

        def _build() -> str:
            client = self._get_docker_client()
            try:
                # Check if image already exists
                existing = client.images.list(name=image_name)
                if existing:
                    self._logger.debug("Docker image '%s' already exists; reusing.", image_name)
                    return image_name
            except Exception:
                pass

            # Build a new image from the Dockerfile content
            self._logger.debug("Building Docker image '%s'...", image_name)
            dockerfile_bytes = sandbox_entry.docker_file.encode("utf-8")
            fileobj = io.BytesIO(dockerfile_bytes)
            try:
                _image, _logs = client.images.build(
                    fileobj=fileobj,
                    tag=image_name,
                    rm=True,
                )
                self._logger.info("Built Docker image '%s'.", image_name)
                return image_name
            except Exception as exc:
                raise ToolComponentOperationException(
                    f"Failed to build Docker image '{image_name}'.",
                    cause=exc,
                ) from exc

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _build)

    async def _create_container(
        self,
        sandbox_entry: SandboxCatalogueDockerEntry,
        container_count: int,
    ) -> str:
        """Create and start a Docker container for a sandbox.

        Args:
            sandbox_entry: Docker sandbox definition.
            container_count: Sequential counter to name this container.

        Returns:
            The container name.

        Raises:
            ToolComponentOperationException: Container creation failure.
        """
        if self._configurations is None or self._configurations.app_data_folder is None:
            raise ToolComponentOperationException("App data folder is not configured.")

        container_name = f"{sandbox_entry.id}_{container_count}"
        host_data_dir = os.path.join(
            self._configurations.app_data_folder,
            "tools", "files", container_name
        )
        app_codes_dir = os.path.join(self._configurations.app_data_folder, "tools", "codes")

        def _run_container() -> str:
            # Create required host directories
            for subdir in ("input", "output", "tmp"):
                os.makedirs(os.path.join(host_data_dir, subdir), exist_ok=True)
            os.makedirs(app_codes_dir, exist_ok=True)

            client = self._get_docker_client()

            # Build volume mapping
            volumes = {
                app_codes_dir: {"bind": "/app/codes", "mode": "ro"},
                host_data_dir: {"bind": "/app/data", "mode": "rw"},
            }

            # Parse additional run options
            run_kwargs: dict[str, Any] = {
                "name": container_name,
                "volumes": volumes,
                "command": "sleep infinity",
                "detach": True,
                "labels": {"gafs.toolcomponent": "true"},
            }

            # Apply sandbox run_options if set
            if sandbox_entry.run_options:
                import shlex
                tokens = shlex.split(sandbox_entry.run_options)
                i = 0
                while i < len(tokens):
                    tok = tokens[i]
                    if tok == "--memory" and i + 1 < len(tokens):
                        run_kwargs["mem_limit"] = tokens[i + 1]
                        i += 2
                    elif tok == "--cpus" and i + 1 < len(tokens):
                        run_kwargs["nano_cpus"] = int(float(tokens[i + 1]) * 1e9)
                        i += 2
                    else:
                        i += 1

            try:
                client.containers.run(sandbox_entry.id, **run_kwargs)
                self._logger.debug("Started container '%s'.", container_name)
            except Exception as exc:
                # If the container already exists (name conflict), reuse it if running
                exc_msg = str(exc)
                if "409" in exc_msg or "already in use" in exc_msg.lower():
                    try:
                        existing = client.containers.get(container_name)
                        if existing.status == "running":
                            self._logger.debug("Reusing existing container '%s'.", container_name)
                            return container_name
                        existing.start()
                        self._logger.debug("Restarted existing container '%s'.", container_name)
                        return container_name
                    except Exception:
                        pass
                raise ToolComponentOperationException(
                    f"Failed to start container '{container_name}'.",
                    cause=exc,
                ) from exc
            return container_name

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _run_container)

    async def _destroy_container(self, container_name: str) -> None:
        """Stop and remove a Docker container (best-effort).

        Args:
            container_name: Name of the container to destroy.
        """
        if self._configurations is None:
            return

        host_data_dir = os.path.join(
            self._configurations.app_data_folder,
            "tools", "files", container_name
        )

        def _destroy() -> None:
            try:
                client = self._get_docker_client()
                try:
                    container = client.containers.get(container_name)
                    container.stop(timeout=5)
                    container.remove(force=True)
                    self._logger.debug("Removed container '%s'.", container_name)
                except Exception as exc:
                    self._logger.warning(
                        "Failed to stop/remove container '%s': %s", container_name, exc
                    )
            except Exception as exc:
                self._logger.warning("Docker client error during destroy: %s", exc)

            # Delete host data directory
            if os.path.exists(host_data_dir):
                try:
                    shutil.rmtree(host_data_dir)
                except OSError as exc:
                    self._logger.warning(
                        "Failed to delete data dir '%s': %s", host_data_dir, exc
                    )

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _destroy)

    async def _remove_image(self, image_name: str) -> None:
        """Remove a Docker image (best-effort).

        Args:
            image_name: Name/tag of the Docker image to remove.
        """
        def _remove() -> None:
            try:
                client = self._get_docker_client()
                client.images.remove(image_name, force=True)
                self._logger.debug("Removed Docker image '%s'.", image_name)
            except Exception as exc:
                self._logger.warning("Failed to remove Docker image '%s': %s", image_name, exc)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _remove)

    async def _exit(self) -> None:
        """Destroy all standby containers and clear the standby pool."""
        for sandbox_id, containers in list(self._standby_containers.items()):
            for container_name in containers:
                await self._destroy_container(container_name)
        self._standby_containers.clear()

    async def _replenish_standby_pool(
        self, sandbox_entry: SandboxCatalogueDockerEntry
    ) -> None:
        """Add standby containers up to the configured limits.

        Args:
            sandbox_entry: Docker sandbox definition to replenish for.
        """
        if self._configurations is None:
            return

        per_sandbox_limit = self._configurations.docker_default_image_max_stand_by
        total_limit = self._configurations.docker_total_default_image_max_stand_by
        current_count = len(self._standby_containers.get(sandbox_entry.id, []))
        total_current = sum(len(v) for v in self._standby_containers.values())
        slots_available = min(
            per_sandbox_limit - current_count,
            total_limit - total_current,
        )

        if slots_available <= 0:
            return

        for _ in range(slots_available):
            count = self._container_counts.get(sandbox_entry.id, 0)
            self._container_counts[sandbox_entry.id] = count + 1
            try:
                container_name = await self._create_container(sandbox_entry, count)
                self._standby_containers.setdefault(sandbox_entry.id, []).append(container_name)
            except Exception as exc:
                self._logger.warning(
                    "Failed to add standby container for sandbox '%s': %s",
                    sandbox_entry.id, exc,
                )
                break

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    async def initialize(
        self,
        database_manager: IDatabaseManager,
        sandbox_catalogue_service: ISandboxCatalogueService,
        configurations: ToolComponentConfigurations,
    ) -> bool:
        """Initialize the Docker sandbox service.

        Fetches all active Docker sandbox definitions, builds their images,
        and pre-creates standby containers.

        Args:
            database_manager: Initialized database manager (stored for future use).
            sandbox_catalogue_service: Initialized sandbox catalogue service.
            configurations: Tool component configuration.

        Returns:
            True on success.

        Raises:
            ToolComponentInitializationException: Critical failure during initialization.
        """
        self._logger.debug("Initializing DockerSandboxService...")
        self._database_manager = database_manager
        self._sandbox_catalogue_service = sandbox_catalogue_service
        self._configurations = configurations
        self._standby_containers = {}
        self._container_counts = {}

        # Fetch all active Docker sandbox definitions
        try:
            criteria = SandboxCatalogueSearchCriteria()
            object.__setattr__(criteria, "status", [SandboxStatus.ACTIVE])
            all_sandboxes = await sandbox_catalogue_service.search_catalogue_entries(criteria)
            docker_sandboxes = [
                s for s in all_sandboxes if isinstance(s, SandboxCatalogueDockerEntry)
            ]
        except Exception as exc:
            raise ToolComponentInitializationException(
                "Failed to fetch active Docker sandbox entries during initialization.",
                cause=exc,
            ) from exc

        # Cleanup orphaned standby containers from previous runs
        # (containers labeled 'gafs.toolcomponent=true' whose sandbox is no longer active)
        active_sandbox_ids = {s.id for s in docker_sandboxes if s.id}
        try:
            def _cleanup_orphans() -> None:
                client = self._get_docker_client()
                orphans = client.containers.list(
                    filters={"label": "gafs.toolcomponent=true"}
                )
                for container in orphans:
                    name = container.name
                    parts = name.rsplit("_", 1)
                    if len(parts) == 2 and parts[1].isdigit() and parts[0] not in active_sandbox_ids:
                        try:
                            container.stop(timeout=5)
                            container.remove()
                            self._logger.debug("Removed orphaned container '%s'.", name)
                        except Exception as exc:  # noqa: BLE001
                            self._logger.warning(
                                "Failed to remove orphaned container '%s': %s", name, exc
                            )
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _cleanup_orphans)
        except Exception as exc:  # noqa: BLE001
            self._logger.warning("Orphaned container cleanup failed: %s", exc)

        # For each sandbox: build image and replenish pool
        for sandbox_entry in docker_sandboxes:
            if not sandbox_entry.id:
                continue
            try:
                await self._create_image(sandbox_entry)
            except Exception as exc:
                # Best-effort: log error but do not abort initialization
                self._logger.error(
                    "Failed to build image for sandbox '%s': %s", sandbox_entry.id, exc
                )
                continue

            self._standby_containers[sandbox_entry.id] = []
            self._container_counts[sandbox_entry.id] = 0

            try:
                await self._replenish_standby_pool(sandbox_entry)
            except Exception as exc:
                self._logger.error(
                    "Failed to replenish standby pool for sandbox '%s': %s",
                    sandbox_entry.id, exc,
                )

        self._logger.info("DockerSandboxService initialized.")
        return True

    # -------------------------------------------------------------------------
    # Code execution
    # -------------------------------------------------------------------------

    async def execute_code(
        self,
        version_entry: ToolVersionEntry,
        sandbox_entry: SandboxCatalogueDockerEntry,
        input_parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute tool code inside a Docker container.

        Args:
            version_entry: Tool version record containing code and parameter defs.
            sandbox_entry: Docker sandbox definition.
            input_parameters: Actual input parameter values.

        Returns:
            Output parameter values produced by the tool.

        Raises:
            ToolComponentNotInitializedException: Service is not initialized.
            SandboxCatalogueEntryNotFoundException: sandbox_entry not registered.
            ToolComponentOperationException: Execution failure.
        """
        if self._configurations is None:
            raise ToolComponentNotInitializedException(
                "DockerSandboxService is not initialized."
            )

        if sandbox_entry.id is None:
            raise SandboxCatalogueEntryNotFoundException(
                "sandbox_entry has no id."
            )

        # Verify the sandbox was registered at initialization
        if sandbox_entry.id not in self._standby_containers:
            # Register it on-demand if possible
            try:
                await self._create_image(sandbox_entry)
                self._standby_containers[sandbox_entry.id] = []
                self._container_counts[sandbox_entry.id] = 0
            except Exception as exc:
                raise SandboxCatalogueEntryNotFoundException(
                    f"Sandbox '{sandbox_entry.id}' is not registered and could not be created.",
                    cause=exc,
                ) from exc

        # Obtain a container to use
        container_name: str
        if self._standby_containers[sandbox_entry.id]:
            container_name = self._standby_containers[sandbox_entry.id].pop(0)
            self._logger.debug(
                "Using standby container '%s' for sandbox '%s'.",
                container_name, sandbox_entry.id,
            )
        else:
            # Provision a new container on demand
            count = self._container_counts.get(sandbox_entry.id, 0)
            self._container_counts[sandbox_entry.id] = count + 1
            try:
                container_name = await self._create_container(sandbox_entry, count)
            except Exception as exc:
                raise ToolComponentOperationException(
                    f"Failed to create on-demand container for sandbox '{sandbox_entry.id}'.",
                    cause=exc,
                ) from exc

        # Validate and apply defaults for input parameters
        effective_params: dict[str, Any] = dict(input_parameters)
        if version_entry.input_parameters:
            for param_def in version_entry.input_parameters:
                if param_def.name and param_def.name not in effective_params:
                    if param_def.required and param_def.default is None:
                        await self._destroy_container(container_name)
                        raise ToolComponentOperationException(
                            f"Required input parameter '{param_def.name}' is missing."
                        )
                    if param_def.default is not None:
                        effective_params[param_def.name] = param_def.default

        # Write input parameters to _params.json
        host_data_dir = os.path.join(
            self._configurations.app_data_folder,
            "tools", "files", container_name
        )
        params_file = os.path.join(host_data_dir, "input", "_params.json")
        params_payload = {
            "input_parameters": effective_params,
            "input_dir": "/app/data/input",
            "output_dir": "/app/data/output",
            "tmp_dir": "/app/data/tmp",
        }
        try:
            os.makedirs(os.path.join(host_data_dir, "input"), exist_ok=True)
            with open(params_file, "w", encoding="utf-8") as f:
                json.dump(params_payload, f)
        except OSError as exc:
            await self._destroy_container(container_name)
            raise ToolComponentOperationException(
                f"Failed to write input parameters to '{params_file}'.",
                cause=exc,
            ) from exc

        # Execute the tool code inside the container
        code_path = f"/app/codes/{version_entry.tool_id}_{version_entry.id}/main.py"
        exec_cmd = f"python {code_path} /app/data/input/_params.json"

        def _docker_exec() -> str:
            client = self._get_docker_client()
            try:
                container = client.containers.get(container_name)
                exit_code, output = container.exec_run(exec_cmd, stdout=True, stderr=True)
                if exit_code != 0:
                    raise ToolComponentOperationException(
                        f"Tool execution failed with exit code {exit_code}. "
                        f"Output: {output.decode('utf-8', errors='replace') if output else ''}"
                    )
                return output.decode("utf-8", errors="replace") if output else ""
            except ToolComponentOperationException:
                raise
            except Exception as exc:
                raise ToolComponentOperationException(
                    f"Docker exec failed for container '{container_name}'.",
                    cause=exc,
                ) from exc

        loop = asyncio.get_event_loop()
        try:
            stdout_text = await loop.run_in_executor(None, _docker_exec)
        except ToolComponentOperationException:
            await self._destroy_container(container_name)
            raise
        except Exception as exc:
            await self._destroy_container(container_name)
            raise ToolComponentOperationException(
                f"Tool execution failed for container '{container_name}'.",
                cause=exc,
            ) from exc

        # Parse stdout as JSON to get output parameters
        try:
            output_parameters: dict[str, Any] = json.loads(stdout_text.strip())
        except json.JSONDecodeError as exc:
            await self._destroy_container(container_name)
            raise ToolComponentOperationException(
                f"Tool output is not valid JSON. Output: {stdout_text[:500]}",
                cause=exc,
            ) from exc

        # Destroy the container and clean up data directory
        await self._destroy_container(container_name)

        # Asynchronously replenish the standby pool in the background
        asyncio.ensure_future(self._replenish_standby_pool(sandbox_entry))

        self._logger.debug(
            "Tool execution complete: tool_id=%s version_id=%s",
            version_entry.tool_id, version_entry.id,
        )
        return output_parameters
