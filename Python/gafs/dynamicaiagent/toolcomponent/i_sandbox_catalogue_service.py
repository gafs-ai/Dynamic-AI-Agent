"""i_sandbox_catalogue_service.py - Abstract interface for the SandboxCatalogueService."""

from __future__ import annotations

from abc import ABC, abstractmethod

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager

from .models import (
    SandboxCatalogueEntry,
    SandboxCatalogueSearchCriteria,
    ToolComponentConfigurations,
)


class ISandboxCatalogueService(ABC):
    """Abstract interface for CRUD and search on SandboxCatalogueEntry records.

    Implementations manage indexes on the SandboxCatalogue collection.
    """

    @abstractmethod
    async def initialize(
        self,
        database_manager: IDatabaseManager,
        component_configurations: ToolComponentConfigurations,
    ) -> bool:
        """Initialize the sandbox catalogue service and create required indexes.

        Args:
            database_manager: Initialized database manager.
            component_configurations: Tool component configuration.

        Returns:
            True on success.

        Raises:
            ToolComponentInitializationException: Initialization failure.
        """
        ...

    @abstractmethod
    async def ensure_indexes(
        self,
        configurations: ToolComponentConfigurations,
        overwrite: bool = False,
    ) -> bool:
        """Create or update indexes on the SandboxCatalogue collection.

        Args:
            configurations: Tool component configuration.
            overwrite: If True, use DEFINE INDEX OVERWRITE; else IF NOT EXISTS.

        Returns:
            True on success.

        Raises:
            ToolComponentNotInitializedException: No IDatabaseManager available.
            ToolComponentOperationException: Index creation failure.
            FullTextAnalyzerNotExistException: Referenced analyzer does not exist.
        """
        ...

    @abstractmethod
    async def create_catalogue_entry(
        self, catalogue: SandboxCatalogueEntry
    ) -> SandboxCatalogueEntry:
        """Persist a new sandbox catalogue record.

        Args:
            catalogue: Sandbox catalogue entry to create.

        Returns:
            The created SandboxCatalogueEntry with the generated ID.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidSandboxCatalogueEntryException: Validation failure.
            ConflictingSandboxCatalogueEntryException: Duplicate name.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def update_catalogue_entry(
        self, catalogue: SandboxCatalogueEntry
    ) -> SandboxCatalogueEntry:
        """Update an existing sandbox catalogue record.

        Args:
            catalogue: Sandbox catalogue entry with updated fields. id must be set.

        Returns:
            The updated SandboxCatalogueEntry.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidSandboxCatalogueEntryException: Validation failure or empty id.
            SandboxCatalogueEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def delete_catalogue_entry(self, catalogue_id: str) -> None:
        """Delete a sandbox catalogue record.

        Args:
            catalogue_id: ID of the sandbox catalogue entry to delete.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            SandboxCatalogueEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def get_catalogue_entry(self, catalogue_id: str) -> SandboxCatalogueEntry:
        """Retrieve a single sandbox catalogue record by its id.

        Args:
            catalogue_id: ID of the sandbox catalogue entry.

        Returns:
            The matching SandboxCatalogueEntry.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            SandboxCatalogueEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def get_all_catalogue_entries(self) -> list[SandboxCatalogueEntry]:
        """Return all sandbox catalogue records.

        Returns:
            List of all SandboxCatalogueEntry records.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def search_catalogue_entries(
        self, search_criteria: SandboxCatalogueSearchCriteria
    ) -> list[SandboxCatalogueEntry]:
        """Search sandbox catalogue records using search_criteria.

        Args:
            search_criteria: Filter and search parameters.

        Returns:
            List of matching SandboxCatalogueEntry records.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidSandboxCatalogueSearchCriteriaException: Invalid search criteria.
            ToolComponentOperationException: Database operation failure.
        """
        ...
