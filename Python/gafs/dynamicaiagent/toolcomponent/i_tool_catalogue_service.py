"""i_tool_catalogue_service.py - Abstract interface for the ToolCatalogueService."""

from __future__ import annotations

from abc import ABC, abstractmethod

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager

from .models import (
    ToolCatalogueEntry,
    ToolCatalogueSearchCriteria,
    ToolCatalogueSearchResultEntry,
    ToolComponentConfigurations,
    ToolVersionEntry,
    ToolVersionEntrySearchCriteria,
)


class IToolCatalogueService(ABC):
    """Abstract interface for CRUD and search on ToolCatalogueEntry and ToolVersionEntry.

    Implementations manage indexes on ToolCatalogue and ToolVersions collections,
    and synchronise tool code to the filesystem.
    """

    @abstractmethod
    async def initialize(
        self,
        database_manager: IDatabaseManager,
        component_configurations: ToolComponentConfigurations,
    ) -> bool:
        """Initialize the catalogue service and create required indexes.

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
        """Create or update indexes on ToolCatalogue and ToolVersions collections.

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
    async def create_tool_catalogue_entry(
        self, catalogue: ToolCatalogueEntry
    ) -> ToolCatalogueEntry:
        """Persist a new tool catalogue record.

        Args:
            catalogue: Tool catalogue entry to create.

        Returns:
            The created ToolCatalogueEntry with the generated ID.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidToolCatalogueEntryException: Validation failure.
            ConflictingToolCatalogueEntryException: Duplicate name.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def update_tool_catalogue_entry(
        self, catalogue: ToolCatalogueEntry
    ) -> ToolCatalogueEntry:
        """Update an existing tool catalogue record.

        Args:
            catalogue: Tool catalogue entry with updated fields. id must be set.

        Returns:
            The updated ToolCatalogueEntry.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidToolCatalogueEntryException: Validation failure or empty id.
            ToolCatalogueEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def delete_tool_catalogue_entry(self, catalogue_id: str) -> None:
        """Delete a tool catalogue record and all associated version entries.

        Args:
            catalogue_id: ID of the tool catalogue entry to delete.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            ToolCatalogueEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def get_tool_catalogue_entry(self, catalogue_id: str) -> ToolCatalogueEntry:
        """Retrieve a single tool catalogue record by its id.

        Args:
            catalogue_id: ID of the tool catalogue entry.

        Returns:
            The matching ToolCatalogueEntry.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            ToolCatalogueEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def get_all_tool_catalogue_entries(self) -> list[ToolCatalogueEntry]:
        """Return all tool catalogue records.

        Returns:
            List of all ToolCatalogueEntry records.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def search_tool_catalogue_entries(
        self, search_criteria: ToolCatalogueSearchCriteria
    ) -> list[ToolCatalogueSearchResultEntry]:
        """Search tool catalogue records using search_criteria.

        Args:
            search_criteria: Filter and search parameters.

        Returns:
            List of ToolCatalogueSearchResultEntry records.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidToolCatalogueSearchCriteriaException: Invalid search criteria.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def create_tool_version_entry(
        self, version: ToolVersionEntry
    ) -> ToolVersionEntry:
        """Persist a new tool version record.

        Args:
            version: Tool version entry to create.

        Returns:
            The created ToolVersionEntry with the generated ID.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidToolVersionEntryException: Validation failure.
            ToolCatalogueEntryNotFoundException: Referenced tool_id does not exist.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def update_tool_version_entry(
        self, version: ToolVersionEntry
    ) -> ToolVersionEntry:
        """Update an existing tool version record.

        Args:
            version: Tool version entry with updated fields. id must be set.

        Returns:
            The updated ToolVersionEntry.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidToolVersionEntryException: Validation failure or empty id.
            ToolVersionEntryNotFoundException: No record with the given id.
            ToolCatalogueEntryNotFoundException: Referenced tool_id does not exist.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def delete_tool_version_entry(self, version_id: str) -> None:
        """Delete a tool version record.

        Args:
            version_id: ID of the tool version entry to delete.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            ToolVersionEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def get_tool_version_entry(self, version_id: str) -> ToolVersionEntry:
        """Retrieve a single tool version record by its id.

        Args:
            version_id: ID of the tool version entry.

        Returns:
            The matching ToolVersionEntry.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            ToolVersionEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def get_all_tool_version_entries(
        self, tool_id: str | None = None
    ) -> list[ToolVersionEntry]:
        """Return all tool version records, optionally filtered by tool_id.

        Args:
            tool_id: Optional tool catalogue ID to filter by.

        Returns:
            List of matching ToolVersionEntry records.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            ToolCatalogueEntryNotFoundException: tool_id not found (when provided).
            ToolComponentOperationException: Database operation failure.
        """
        ...

    @abstractmethod
    async def search_tool_version_entries(
        self, search_criteria: ToolVersionEntrySearchCriteria
    ) -> list[ToolVersionEntry]:
        """Search tool version records using search_criteria.

        Args:
            search_criteria: Filter and search parameters.

        Returns:
            List of matching ToolVersionEntry records.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidToolVersionSearchCriteriaException: Invalid search criteria.
            ToolComponentOperationException: Database operation failure.
        """
        ...
