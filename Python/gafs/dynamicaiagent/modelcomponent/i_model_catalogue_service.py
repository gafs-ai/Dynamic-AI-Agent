"""i_model_catalogue_service.py - Abstract base class (interface) for ModelCatalogueService."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager

from .models import (
    ModelCatalogueEntry,
    ModelCatalogueSearchCriteria,
    ModelCatalogueSearchResultEntry,
    ModelComponentConfigurations,
    ModelDeployment,
    ModelDeploymentSearchCriteria,
)


class IModelCatalogueService(ABC):
    """Interface for catalogue CRUD and search operations.

    Responsibilities:
        - CRUD operations on ``ModelCatalogueEntry`` and ``ModelDeployment`` records.
        - Manage database indexes on the ``ModelCatalogue`` and ``model_deployments``
          collections.
        - Resolve edge relationships (``deployed_as``, ``references_secret``) at read time.
    """

    @staticmethod
    def CATALOGUE_COLLECTION_NAME() -> str:  # noqa: N802
        """SurrealDB collection name for model catalogue records."""
        return "ModelCatalogue"

    @staticmethod
    def DEPLOYMENT_COLLECTION_NAME() -> str:  # noqa: N802
        """SurrealDB collection name for model deployment records."""
        return "model_deployments"

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    @abstractmethod
    async def initialize(
        self,
        database_manager: IDatabaseManager,
        component_configurations: ModelComponentConfigurations,
        embed_fn: Callable[[str], Awaitable[list[float] | None]] | None = None,
    ) -> bool:
        """Initialize the catalogue service.

        Stores the database manager, component configurations, and optional embedding
        function. Calls ``ensure_indexes`` to create or verify all required indexes.

        Args:
            database_manager: Provides the default ``IDatabaseProvider``.
            component_configurations: Configuration controlling index settings and
                analyzer names. Cached for use in ``ensure_indexes``.
            embed_fn: Optional callable ``(text: str) -> list[float] | None`` used
                to generate description vectors. When ``None``, auto-embedding is
                disabled (vectors are stored as ``None``).

        Returns:
            ``True`` on success.

        Raises:
            ModelComponentInitializationException: Initialization failure (wraps any
                underlying error including ``FullTextAnalyzerNotExistException``).
        """
        ...

    @abstractmethod
    async def ensure_indexes(
        self,
        component_configurations: ModelComponentConfigurations,
        overwrite: bool = False,
    ) -> bool:
        """Create or update indexes on ``ModelCatalogue`` and ``model_deployments``.

        Args:
            component_configurations: Settings for analyzer names and HNSW parameters.
            overwrite: When ``True``, use ``DEFINE INDEX OVERWRITE`` to force-update
                existing indexes. When ``False``, use ``DEFINE INDEX IF NOT EXISTS``.

        Returns:
            ``True`` on success.

        Raises:
            ModelComponentNotInitializedException: No ``IDatabaseManager`` is set.
            ModelComponentOperationException: Index creation failures.
            FullTextAnalyzerNotExistException: A referenced full-text analyzer is missing.
        """
        ...

    # -------------------------------------------------------------------------
    # Catalogue CRUD
    # -------------------------------------------------------------------------

    @abstractmethod
    async def create_catalogue_entry(
        self,
        catalogue: ModelCatalogueEntry,
    ) -> ModelCatalogueEntry:
        """Persist a new catalogue record.

        Args:
            catalogue: Entry to create. ``id`` may be ``None`` for auto-generation.

        Returns:
            The created entry with its assigned ``id``.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            InvalidModelCatalogueEntryException: Validation failure.
            ConflictingModelCatalogueEntryException: Duplicate ``id`` or name.
            ModelDeploymentNotFoundException: A referenced deployment does not exist.
            ModelComponentOperationException: Database failures.
        """
        ...

    @abstractmethod
    async def update_catalogue_entry(
        self,
        catalogue: ModelCatalogueEntry,
    ) -> ModelCatalogueEntry:
        """Update an existing catalogue record.

        ``catalogue.id`` must be set.

        Args:
            catalogue: Entry with updated fields. ``id`` is required.

        Returns:
            The updated entry.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            InvalidModelCatalogueEntryException: ``id`` is missing or invalid.
            ModelCatalogueEntryNotFoundException: No record with the given ``id``.
            ModelDeploymentNotFoundException: A referenced deployment does not exist.
            ModelComponentOperationException: Database failures.
        """
        ...

    @abstractmethod
    async def get_catalogue_entry(
        self,
        id: str,
    ) -> ModelCatalogueEntry | None:
        """Retrieve a catalogue entry by record id.

        Args:
            id: Record id to look up.

        Returns:
            Matching entry (with ``deployments`` resolved from edges), or ``None``.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            ModelComponentOperationException: Database failures.
        """
        ...

    @abstractmethod
    async def get_all_catalogue_entries(self) -> list[ModelCatalogueEntry]:
        """Retrieve all catalogue entries.

        Returns:
            All entries (with ``deployments`` resolved from edges). Empty list if none.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            ModelComponentOperationException: Database failures.
        """
        ...

    @abstractmethod
    async def search_catalogue_entries(
        self,
        catalogue_search_criteria: ModelCatalogueSearchCriteria,
    ) -> list[ModelCatalogueSearchResultEntry]:
        """Search catalogue entries.

        Args:
            catalogue_search_criteria: Filters for the search.

        Returns:
            Matching entries as ``ModelCatalogueSearchResultEntry`` objects.
            Empty list if none.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            ModelComponentOperationException: Database failures.
        """
        ...

    @abstractmethod
    async def delete_catalogue_entry(
        self,
        id: str,
    ) -> None:
        """Delete a catalogue entry and its outbound ``deployed_as`` edges.

        Args:
            id: Record id of the entry to delete.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            ModelCatalogueEntryNotFoundException: No record with the given ``id``.
            ModelComponentOperationException: Database failures.
        """
        ...

    # -------------------------------------------------------------------------
    # Deployment CRUD
    # -------------------------------------------------------------------------

    @abstractmethod
    async def create_deployment(
        self,
        deployment: ModelDeployment,
    ) -> ModelDeployment:
        """Persist a new deployment record.

        Args:
            deployment: Deployment to create. ``id`` may be ``None``.

        Returns:
            The created deployment with its assigned ``id``.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            InvalidModelDeploymentException: Validation failure.
            ConflictingModelDeploymentException: Duplicate ``id`` or name.
            ModelComponentOperationException: Database failures.
        """
        ...

    @abstractmethod
    async def update_deployment(
        self,
        deployment: ModelDeployment,
    ) -> ModelDeployment:
        """Update an existing deployment record.

        ``deployment.id`` must be set.

        Args:
            deployment: Deployment with updated fields. ``id`` is required.

        Returns:
            The updated deployment.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            InvalidModelDeploymentException: ``id`` is missing or invalid.
            ModelDeploymentNotFoundException: No record with the given ``id``.
            ModelComponentOperationException: Database failures.
        """
        ...

    @abstractmethod
    async def get_deployment(
        self,
        id: str,
    ) -> ModelDeployment | None:
        """Retrieve a deployment by record id.

        Args:
            id: Record id (with or without table prefix).

        Returns:
            Matching deployment (with ``secrets`` resolved from edges), or ``None``.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            ModelComponentOperationException: Database failures.
        """
        ...

    @abstractmethod
    async def search_deployments(
        self,
        search_criteria: ModelDeploymentSearchCriteria,
    ) -> list[ModelDeployment]:
        """Search deployments.

        Args:
            search_criteria: Filters for the search.

        Returns:
            Matching deployments. Empty list if none.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            ModelComponentOperationException: Database failures.
        """
        ...

    @abstractmethod
    async def delete_deployment(
        self,
        id: str,
    ) -> None:
        """Delete a deployment record, its outbound ``references_secret`` edges,
        and any inbound ``deployed_as`` edges that point to it.

        Args:
            id: Record id of the deployment to delete.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            ModelDeploymentNotFoundException: No record with the given ``id``.
            ModelComponentOperationException: Database failures.
        """
        ...
