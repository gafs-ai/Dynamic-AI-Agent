"""Interface for the model catalogue service.

Defines the contract for create, read, update, delete, and search
operations on the model catalogue store.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from Python.gafs.dynamicaiagent.modelcomponent.models.model_catalogue_search_criteria import ModelCatalogueSearchCriteria
from Python.gafs.dynamicaiagent.modelcomponent.models.model_deployment_search_criteria import ModelDeploymentSearchCriteria
from gafs.dynamicaiagent.modelcomponent.models.model_catalogue import ModelCatalogue, ModelDeployment
from gafs.dynamicaiagent.modelcomponent.models.model_component_configurations import ModelComponentConfigurations
from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider


class IModelCatalogueService(ABC):
    """Interface for model catalogue service.

    Implementations perform CRUD and search over a model catalogue
    store (e.g. SurrealDB) using a database provider.
    """

    @staticmethod
    def CATALOGUE_COLLECTION_NAME() -> str:
        """Return the default collection/table name for the model catalogue.

        Returns:
            Default collection name used when none is specified.
        """
        return "model_catalogues"


    @staticmethod
    def DEPLOYMENT_COLLECTION_NAME() -> str:
        """Return the default collection/table name for the model deployment.
        """
        return "model_deployments"


    @abstractmethod
    async def initialize(
        self,
        database_manager: IDatabaseManager,
        component_configurations: ModelComponentConfigurations,
        database_provider: IDatabaseProvider | None = None,
    ) -> bool:
        """Initialize the model catalogue service.
        """
        raise NotImplementedError

    @abstractmethod
    async def ensure_indexes(
        self,
        component_configurations: ModelComponentConfigurations,
        overwrite: bool = False,
    ) -> bool:
        """Ensure catalogue/deployment indexes are present."""
        raise NotImplementedError

    @abstractmethod
    async def create_catalogue(self, catalogue: ModelCatalogue) -> ModelCatalogue:
        """Create a new model catalogue record.

        Args:
            catalogue: Model catalogue data. id may be empty to let the store
                generate an ID.

        Returns:
            The created catalogue (with id set if generated).

        Raises:
            Exception: When the database provider is unavailable or the
                create operation fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def update_catalogue(self, catalogue: ModelCatalogue) -> ModelCatalogue:
        """Update an existing model catalogue record.

        Args:
            catalogue: Catalogue with id and updated fields.

        Returns:
            The updated catalogue as returned by the store.

        Raises:
            ValueError: When id is None or empty.
            Exception: When the database provider is unavailable or the
                update operation fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_catalogue(self, id: str) -> ModelCatalogue | None:
        """Get a single model catalogue by ID.

        Args:
            id: Record ID of the catalogue.

        Returns:
            The catalogue if found, None otherwise.

        Raises:
            Exception: When the database provider is unavailable or the
                query fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def search_catalogues(
        self, catalogue_search_criteria: ModelCatalogueSearchCriteria
    ) -> list[ModelCatalogue]:
        """Search model catalogues by criteria.

        Args:
            catalogue_search_criteria: Search filters (e.g. name, type,
                status, vector similarity, deployment types).

        Returns:
            List of matching catalogues; empty list if none or on error.

        Raises:
            Exception: When the database provider is unavailable or the
                search fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_catalogue(self, id: str) -> bool:
        """Delete a model catalogue by ID.

        Args:
            id: Record ID of the catalogue to delete.

        Returns:
            True if a record was deleted, False if not found.

        Raises:
            Exception: When the database provider is unavailable or the
                delete operation fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def create_deployment(self, deployment: ModelDeployment) -> ModelDeployment:
        """Create a new model deployment record."""
        raise NotImplementedError

    @abstractmethod
    async def update_deployment(self, deployment: ModelDeployment) -> ModelDeployment:
        """Update an existing model deployment record."""
        raise NotImplementedError

    @abstractmethod
    async def get_deployment(self, id: str) -> ModelDeployment | None:
        """Get a single model deployment by ID."""
        raise NotImplementedError

    @abstractmethod
    async def search_deployments(self, deployment_search_criteria: ModelDeploymentSearchCriteria) -> list[ModelDeployment]:
        """Search model deployments by criteria."""
        raise NotImplementedError

    @abstractmethod
    async def delete_deployment(self, id: str) -> bool:
        """Delete a model deployment by ID."""
        raise NotImplementedError
