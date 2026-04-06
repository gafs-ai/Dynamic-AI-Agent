"""Interface for the knowledge catalogue service."""
from __future__ import annotations

from abc import ABC, abstractmethod

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider

from .models.catalogue_search_criteria import CatalogueSearchCriteria
from .models.knowledge_component_configurations import KnowledgeComponentConfigurations
from .models.knowledge_catalogue import KnowledgeCatalogue


class IKnowledgeCatalogueService(ABC):
    """Contract for CRUD and search operations on knowledge catalogues."""

    @staticmethod
    def CATALOGUE_COLLECTION_NAME() -> str:
        """Return the default table name for knowledge catalogues."""
        return "knowledge_catalogues"

    @abstractmethod
    async def initialize(
        self,
        database_manager: IDatabaseManager,
        component_configurations: KnowledgeComponentConfigurations,
        database_provider: IDatabaseProvider | None = None,
    ) -> bool:
        """Initialize the service with database dependencies."""
        raise NotImplementedError

    @abstractmethod
    async def create_catalogue(self, catalogue: KnowledgeCatalogue) -> KnowledgeCatalogue:
        """Create a knowledge catalogue."""
        raise NotImplementedError

    @abstractmethod
    async def update_catalogue(self, catalogue: KnowledgeCatalogue) -> KnowledgeCatalogue:
        """Update an existing knowledge catalogue."""
        raise NotImplementedError

    @abstractmethod
    async def get_catalogue(self, catalogue_id: str) -> KnowledgeCatalogue | None:
        """Get one knowledge catalogue by id."""
        raise NotImplementedError

    @abstractmethod
    async def search_catalogues(
        self,
        search_criteria: CatalogueSearchCriteria,
    ) -> list[KnowledgeCatalogue]:
        """Search knowledge catalogues by criteria."""
        raise NotImplementedError

    @abstractmethod
    async def delete_catalogue(self, catalogue_id: str) -> bool:
        """Delete one knowledge catalogue by id."""
        raise NotImplementedError
