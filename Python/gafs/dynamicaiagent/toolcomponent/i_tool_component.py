"""i_tool_component.py - Abstract interface for the ToolComponent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager

from .models import (
    SandboxCatalogueEntry,
    SandboxCatalogueSearchCriteria,
    ToolCatalogueEntry,
    ToolCatalogueSearchCriteria,
    ToolCatalogueSearchResultEntry,
    ToolComponentConfigurations,
    ToolVersionEntry,
    ToolVersionEntrySearchCriteria,
)


class IToolComponent(ABC):
    """Top-level interface for all Tool Component operations.

    Exposes operations for:
    - Component initialization
    - Tool invocation
    - Tool Catalogue and Tool Version CRUD/search
    - Sandbox Catalogue CRUD/search
    - Tool component configuration management
    """

    @abstractmethod
    async def initialize(self, database_manager: IDatabaseManager) -> bool:
        """Initialize the tool component using the given database manager.

        Args:
            database_manager: Initialized database manager.

        Returns:
            True on success.

        Raises:
            ToolComponentInitializationException: Initialization failure.
        """
        ...

    @abstractmethod
    async def invoke(
        self,
        tool_id: str,
        version_id: str,
        input_parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a tool identified by tool_id and version_id.

        Args:
            tool_id: ID of the ToolCatalogueEntry record.
            version_id: ID of the ToolVersionEntry record.
            input_parameters: Actual values for the tool's input parameters.

        Returns:
            Output parameter values produced by the tool.

        Raises:
            ToolComponentNotInitializedException: Component not initialized.
            ToolCatalogueEntryNotFoundException: No ToolCatalogueEntry for tool_id.
            ToolVersionEntryNotFoundException: No ToolVersionEntry for version_id.
            InvalidToolInvocationException: input_parameters fail validation.
            SandboxCatalogueEntryNotFoundException: No suitable sandbox found.
            ToolComponentOperationException: Tool execution failure.
        """
        ...

    @abstractmethod
    async def create_tool_catalogue_entry(
        self, catalogue: ToolCatalogueEntry
    ) -> ToolCatalogueEntry:
        """Create a new tool catalogue entry."""
        ...

    @abstractmethod
    async def update_tool_catalogue_entry(
        self, catalogue: ToolCatalogueEntry
    ) -> ToolCatalogueEntry:
        """Update an existing tool catalogue entry."""
        ...

    @abstractmethod
    async def delete_tool_catalogue_entry(self, catalogue_id: str) -> None:
        """Delete a tool catalogue entry."""
        ...

    @abstractmethod
    async def get_tool_catalogue_entry(self, catalogue_id: str) -> ToolCatalogueEntry:
        """Retrieve a tool catalogue entry by ID."""
        ...

    @abstractmethod
    async def get_all_tool_catalogue_entries(self) -> list[ToolCatalogueEntry]:
        """Return all tool catalogue entries."""
        ...

    @abstractmethod
    async def search_tool_catalogue_entries(
        self, search_criteria: ToolCatalogueSearchCriteria
    ) -> list[ToolCatalogueSearchResultEntry]:
        """Search tool catalogue entries using criteria."""
        ...

    @abstractmethod
    async def create_tool_version_entry(
        self, version: ToolVersionEntry
    ) -> ToolVersionEntry:
        """Create a new tool version entry."""
        ...

    @abstractmethod
    async def update_tool_version_entry(
        self, version: ToolVersionEntry
    ) -> ToolVersionEntry:
        """Update an existing tool version entry."""
        ...

    @abstractmethod
    async def delete_tool_version_entry(self, version_id: str) -> None:
        """Delete a tool version entry."""
        ...

    @abstractmethod
    async def get_tool_version_entry(self, version_id: str) -> ToolVersionEntry:
        """Retrieve a tool version entry by ID."""
        ...

    @abstractmethod
    async def get_all_tool_version_entries(
        self, tool_id: str | None = None
    ) -> list[ToolVersionEntry]:
        """Return all tool version entries, optionally filtered by tool_id."""
        ...

    @abstractmethod
    async def search_tool_version_entries(
        self, search_criteria: ToolVersionEntrySearchCriteria
    ) -> list[ToolVersionEntry]:
        """Search tool version entries using criteria."""
        ...

    @abstractmethod
    async def create_sandbox_catalogue_entry(
        self, catalogue: SandboxCatalogueEntry
    ) -> SandboxCatalogueEntry:
        """Create a new sandbox catalogue entry."""
        ...

    @abstractmethod
    async def update_sandbox_catalogue_entry(
        self, catalogue: SandboxCatalogueEntry
    ) -> SandboxCatalogueEntry:
        """Update an existing sandbox catalogue entry."""
        ...

    @abstractmethod
    async def delete_sandbox_catalogue_entry(self, catalogue_id: str) -> None:
        """Delete a sandbox catalogue entry."""
        ...

    @abstractmethod
    async def get_sandbox_catalogue_entry(
        self, catalogue_id: str
    ) -> SandboxCatalogueEntry:
        """Retrieve a sandbox catalogue entry by ID."""
        ...

    @abstractmethod
    async def get_all_sandbox_catalogue_entries(self) -> list[SandboxCatalogueEntry]:
        """Return all sandbox catalogue entries."""
        ...

    @abstractmethod
    async def search_sandbox_catalogue_entries(
        self, search_criteria: SandboxCatalogueSearchCriteria
    ) -> list[SandboxCatalogueEntry]:
        """Search sandbox catalogue entries using criteria."""
        ...

    @abstractmethod
    async def get_configurations(self) -> ToolComponentConfigurations:
        """Return the current ToolComponentConfigurations.

        Raises:
            ToolComponentNotInitializedException: Component not initialized.
            InvalidToolComponentConfigurationException: Configurations invalid.
        """
        ...

    @abstractmethod
    async def update_configurations(
        self, configurations: ToolComponentConfigurations
    ) -> ToolComponentConfigurations:
        """Update the ToolComponentConfigurations.

        Args:
            configurations: New configuration values to persist.

        Returns:
            The updated ToolComponentConfigurations.

        Raises:
            ToolComponentNotInitializedException: Component not initialized.
            InvalidToolComponentConfigurationException: Configurations invalid.
        """
        ...
