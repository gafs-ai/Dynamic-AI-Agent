"""ICloudAiComponent — interface contract for the Cloud AI component."""

from __future__ import annotations

from abc import ABC, abstractmethod

from gafs.dynamicaiagent.modelcomponent.models.ai_connection_parameters import AiConnectionParameters
from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.ai_response import AiResponse


class ICloudAiComponent(ABC):
    """Interface for the Cloud AI component.

    Single entry point for invoking Cloud AI operations from the Model Component.
    Routes requests to the appropriate ICloudAiProvider based on provider_type.
    """

    @abstractmethod
    async def invoke(
        self,
        connection_parameters: AiConnectionParameters,
        request: AiRequest,
    ) -> AiResponse:
        """Invoke a Cloud AI operation.

        Args:
            connection_parameters: Contains deployment_type, provider_type, and
                provider-specific parameters (endpoint, api_key, etc.).
            request: AI operation type, payload, and inference parameters.

        Returns:
            The model output and operation status.

        Raises:
            CloudAiConfigurationException: deployment_type is not CLOUD, or connection
                parameters are invalid.
            CloudAiRequestValidationException: Request payload or message content is invalid.
            CloudAiUnsupportedOperationException: The requested operation is not supported
                by the selected provider.
            CloudAiRemoteApiException: The upstream Cloud AI API call failed.
            CloudAiException: Unexpected errors not covered by the above categories.
        """
        raise NotImplementedError
