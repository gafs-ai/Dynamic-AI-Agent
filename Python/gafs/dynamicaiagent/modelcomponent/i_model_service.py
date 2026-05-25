"""i_model_service.py - Abstract base class (interface) for ModelService."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Awaitable, Callable

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager

from .models import AiRequest, AiResponse, DeploymentSelectionOptions

if TYPE_CHECKING:
    from gafs.dynamicaiagent.cloudaicomponent import ICloudAiComponent
    from .i_model_catalogue_service import IModelCatalogueService


class IModelService(ABC):
    """Interface for model inference.

    Responsibilities:
        - Select an appropriate ``ModelDeployment`` for a given catalogue entry and request.
        - Delegate the actual inference call to the appropriate AI provider component.
    """

    @abstractmethod
    async def initialize(
        self,
        database_manager: IDatabaseManager,
        model_catalogue_service: "IModelCatalogueService | None" = None,
        cloud_ai_component: "ICloudAiComponent | None" = None,
    ) -> bool:
        """Initialize the model service.

        Args:
            database_manager: Provides the default ``IDatabaseProvider``.
            model_catalogue_service: Catalogue service for deployment lookups.
            cloud_ai_component: Cloud AI component for inference calls.

        Returns:
            ``True`` on success.

        Raises:
            ModelComponentInitializationException: Either ``model_catalogue_service``
                or ``cloud_ai_component`` is ``None``.
        """
        ...

    @abstractmethod
    async def invoke(
        self,
        catalogue_id: str,
        request: AiRequest,
        deployment_selection_options: DeploymentSelectionOptions | None = None,
    ) -> AiResponse:
        """Invoke an AI model.

        Selects a deployment matching the catalogue and options, then delegates the
        request to the appropriate AI provider.

        Args:
            catalogue_id: ID of the ``ModelCatalogueEntry`` record.
            request: Operation type, payload, and inference parameters.
            deployment_selection_options: Optional filters for deployment selection.

        Returns:
            The model output and operation status.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            InvalidAiRequestException: ``AiRequest`` parameters fail validation.
            ModelCatalogueEntryNotFoundException: No catalogue found for ``catalogue_id``.
            ModelDeploymentNotFoundException: No eligible deployment is found.
            ModelComponentOperationException: Database or inference call failures.
        """
        ...
