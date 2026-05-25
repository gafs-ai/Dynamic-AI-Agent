"""i_model_component.py - Abstract base class (interface) for ModelComponent."""

from __future__ import annotations

from abc import ABC, abstractmethod

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager

from .models import (
    AiRequest,
    AiResponse,
    DeploymentSelectionOptions,
    ModelCatalogueEntry,
    ModelCatalogueSearchCriteria,
    ModelCatalogueSearchResultEntry,
    ModelComponentConfigurations,
    ModelDeployment,
    ModelDeploymentSearchCriteria,
)


class IModelComponent(ABC):
    """Top-level interface for all Model Component operations.

    Delegates catalogue/deployment CRUD to ``IModelCatalogueService`` and
    inference to ``IModelService``.
    """

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    @abstractmethod
    async def initialize(
        self,
        database_manager: IDatabaseManager,
    ) -> bool:
        """Initialize the model component.

        Args:
            database_manager: Provides the default ``IDatabaseProvider``.

        Returns:
            ``True`` on success.

        Raises:
            ModelComponentInitializationException: Initialization failure.
        """
        ...

    # -------------------------------------------------------------------------
    # Inference
    # -------------------------------------------------------------------------

    @abstractmethod
    async def invoke(
        self,
        catalogue_id: str,
        request: AiRequest,
        deployment_selection_options: DeploymentSelectionOptions | None = None,
    ) -> AiResponse:
        """Invoke an AI model. Delegates to ``IModelService.invoke``.

        Args:
            catalogue_id: ID of the ``ModelCatalogueEntry`` record.
            request: Operation type, payload, and inference parameters.
            deployment_selection_options: Optional filters for deployment selection.

        Returns:
            The model output and operation status.

        Raises:
            ModelComponentNotInitializedException: Component is not initialized.
            InvalidAiRequestException: Request parameters fail validation.
            ModelCatalogueEntryNotFoundException: No catalogue for ``catalogue_id``.
            ModelDeploymentNotFoundException: No eligible deployment found.
            ModelComponentOperationException: Operation failures.
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
        """Create a new catalogue entry. Delegates to ``IModelCatalogueService``."""
        ...

    @abstractmethod
    async def update_catalogue_entry(
        self,
        catalogue: ModelCatalogueEntry,
    ) -> ModelCatalogueEntry:
        """Update an existing catalogue entry. Delegates to ``IModelCatalogueService``."""
        ...

    @abstractmethod
    async def delete_catalogue_entry(
        self,
        catalogue_id: str,
    ) -> None:
        """Delete a catalogue entry. Delegates to ``IModelCatalogueService``."""
        ...

    @abstractmethod
    async def get_catalogue_entry(
        self,
        catalogue_id: str,
    ) -> ModelCatalogueEntry:
        """Get a catalogue entry by id. Delegates to ``IModelCatalogueService``.

        Raises:
            ModelCatalogueEntryNotFoundException: No entry with the given id.
        """
        ...

    @abstractmethod
    async def get_all_catalogue_entries(self) -> list[ModelCatalogueEntry]:
        """Get all catalogue entries. Delegates to ``IModelCatalogueService``."""
        ...

    @abstractmethod
    async def search_catalogue_entries(
        self,
        search_criteria: ModelCatalogueSearchCriteria,
    ) -> list[ModelCatalogueSearchResultEntry]:
        """Search catalogue entries. Delegates to ``IModelCatalogueService``.

        Raises:
            ModelCatalogueIndexNotAvailableException: When a vector search is requested
                while the vector index is being rebuilt.
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
        """Create a new deployment. Delegates to ``IModelCatalogueService``."""
        ...

    @abstractmethod
    async def update_deployment(
        self,
        deployment: ModelDeployment,
    ) -> ModelDeployment:
        """Update an existing deployment. Delegates to ``IModelCatalogueService``."""
        ...

    @abstractmethod
    async def delete_deployment(
        self,
        deployment_id: str,
    ) -> None:
        """Delete a deployment. Delegates to ``IModelCatalogueService``."""
        ...

    @abstractmethod
    async def get_deployment(
        self,
        deployment_id: str,
    ) -> ModelDeployment | None:
        """Get a deployment by id. Delegates to ``IModelCatalogueService``."""
        ...

    @abstractmethod
    async def search_deployments(
        self,
        search_criteria: ModelDeploymentSearchCriteria,
    ) -> list[ModelDeployment]:
        """Search deployments. Delegates to ``IModelCatalogueService``."""
        ...

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------

    @abstractmethod
    async def get_configurations(self) -> ModelComponentConfigurations:
        """Return the current ``ModelComponentConfigurations``.

        Raises:
            ModelComponentNotInitializedException: Component is not initialized.
            InvalidModelComponentConfigurationException: Stored configurations are invalid.
            ModelComponentOperationException: Database failures.
        """
        ...

    @abstractmethod
    async def update_configurations(
        self,
        configurations: ModelComponentConfigurations,
    ) -> ModelComponentConfigurations:
        """Persist and return the updated ``ModelComponentConfigurations``.

        When vector-related settings change (embedding model, data type, dimensions,
        distance method), this method automatically rebuilds the HNSW vector index
        and re-embeds all catalogue descriptions as needed.

        Args:
            configurations: New configuration values to persist.

        Returns:
            The updated ``ModelComponentConfigurations`` as stored in the database.

        Raises:
            ModelComponentNotInitializedException: Component is not initialized.
            InvalidModelComponentConfigurationException: Configurations are invalid.
            ModelComponentOperationException: Database or re-embedding failures.
        """
        ...
