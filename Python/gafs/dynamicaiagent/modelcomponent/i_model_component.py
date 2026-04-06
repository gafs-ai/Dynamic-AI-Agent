from abc import ABC, abstractmethod

from .models.ai_request import AiRequest
from .models.ai_response import AiResponse
from .models.model_catalogue import (
    ModelCatalogue,
    ModelCatalogueSearchResultEntry,
    ModelDeployment,
)
from .models.model_catalogue_search_criteria import ModelCatalogueSearchCriteria
from .models.deployment_selection_options import DeploymentSelectionOptions
from .models.model_deployment_search_criteria import ModelDeploymentSearchCriteria
from .models.model_component_configurations import ModelComponentConfigurations
from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager

class IModelComponent(ABC):
    """Interface for the model component.
    This Interface defines all the exposed operations of the model component.
    """

    @abstractmethod
    async def initialize(self, database_manager: IDatabaseManager) -> bool:
        """Initialize the model service."""
        raise NotImplementedError
    
    # Model Operations
    @abstractmethod
    async def invoke(
        self,
        catalogue_id: str,
        request: AiRequest,
        deployment_selection_options: DeploymentSelectionOptions|None = None,
    ) -> AiResponse:
        """Invoke the model."""
        raise NotImplementedError
    
    # Model Catalogue Operations
    @abstractmethod
    async def create_catalogue(self, catalogue: ModelCatalogue) -> ModelCatalogue:
        """Create the model catalogue."""
        raise NotImplementedError
    
    @abstractmethod
    async def update_catalogue(self, catalogue: ModelCatalogue) -> ModelCatalogue:
        """Update the model catalogue."""
        raise NotImplementedError
    
    @abstractmethod
    async def delete_catalogue(self, catalogue_id: str) -> bool:
        """Delete the model catalogue."""
        raise NotImplementedError
    
    @abstractmethod
    async def get_catalogue(self, catalogue_id: str) -> ModelCatalogue:
        """Get the model catalogue."""
        raise NotImplementedError

    @abstractmethod
    async def search_catalogues(self, search_criteria: ModelCatalogueSearchCriteria) -> list[ModelCatalogueSearchResultEntry]:
        """Search the model catalogues."""
        raise NotImplementedError

    # Deployment operations
    @abstractmethod
    async def create_deployment(self, deployment: ModelDeployment) -> ModelDeployment:
        """Create deployment."""
        raise NotImplementedError

    @abstractmethod
    async def update_deployment(self, deployment: ModelDeployment) -> ModelDeployment:
        """Update deployment."""
        raise NotImplementedError

    @abstractmethod
    async def delete_deployment(self, deployment_id: str) -> bool:
        """Delete deployment."""
        raise NotImplementedError

    @abstractmethod
    async def get_deployment(self, deployment_id: str) -> ModelDeployment | None:
        """Get deployment."""
        raise NotImplementedError

    @abstractmethod
    async def search_deployments(
        self,
        search_criteria: ModelDeploymentSearchCriteria,
    ) -> list[ModelDeployment]:
        """Search deployments."""
        raise NotImplementedError

    # Configuration operations
    @abstractmethod
    async def get_configurations(self) -> ModelComponentConfigurations:
        """Get model component configurations."""
        raise NotImplementedError

    @abstractmethod
    async def update_configurations(
        self,
        configurations: ModelComponentConfigurations,
    ) -> ModelComponentConfigurations:
        """Update model component configurations."""
        raise NotImplementedError
