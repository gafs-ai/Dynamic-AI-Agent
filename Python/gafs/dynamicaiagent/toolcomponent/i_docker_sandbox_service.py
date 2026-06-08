"""i_docker_sandbox_service.py - Abstract interface for the DockerSandboxService."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager

from .i_sandbox_catalogue_service import ISandboxCatalogueService
from .models import (
    SandboxCatalogueDockerEntry,
    ToolComponentConfigurations,
    ToolVersionEntry,
)


class IDockerSandboxService(ABC):
    """Abstract interface for Docker image/container lifecycle management.

    Manages pre-built images and standby containers for sandboxed tool execution.
    Executes tool code inside containers, injects input parameters, and collects
    output parameters.
    """

    @abstractmethod
    async def initialize(
        self,
        database_manager: IDatabaseManager,
        sandbox_catalogue_service: ISandboxCatalogueService,
        configurations: ToolComponentConfigurations,
    ) -> bool:
        """Initialize the Docker sandbox service and pre-build standby containers.

        Args:
            database_manager: Initialized database manager.
            sandbox_catalogue_service: Initialized sandbox catalogue service.
            configurations: Tool component configuration.

        Returns:
            True on success.

        Raises:
            ToolComponentInitializationException: Initialization failure.
        """
        ...

    @abstractmethod
    async def execute_code(
        self,
        version_entry: ToolVersionEntry,
        sandbox_entry: SandboxCatalogueDockerEntry,
        input_parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute tool code inside a Docker container.

        Args:
            version_entry: Tool version record containing the code and parameter definitions.
            sandbox_entry: Docker sandbox definition (Dockerfile, run options).
            input_parameters: Actual values for the input parameters.

        Returns:
            Output parameter values keyed by name.

        Raises:
            ToolComponentNotInitializedException: Service is not initialized.
            SandboxCatalogueEntryNotFoundException: sandbox_entry not registered.
            ToolComponentOperationException: Container creation/execution failure.
        """
        ...
