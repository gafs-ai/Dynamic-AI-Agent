from abc import ABC, abstractmethod
from typing import Any

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager
from .models.ai_request import AiRequest
from .models.ai_response import AiResponse
from .models.deployment_selection_options import DeploymentSelectionOptions

class IModelService(ABC):
    """Interface for the model service."""

    @abstractmethod
    async def initialize(
        self,
        database_manager: IDatabaseManager,
        model_catalogue_service: Any | None = None,
        cloud_ai_component: Any | None = None,
    ) -> bool:
        """Initialize the model service."""
        raise NotImplementedError
    
    # Model Operations
    @abstractmethod
    async def invoke(
        self,
        catalogue_id: str,
        request: AiRequest,
        deployment_selection_options: DeploymentSelectionOptions | None = None,
    ) -> AiResponse:
        """Invoke the model."""
        raise NotImplementedError
