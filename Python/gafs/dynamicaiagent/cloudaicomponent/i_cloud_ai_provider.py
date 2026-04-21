"""ICloudAiProvider — interface contract for single-provider Cloud AI backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

from gafs.dynamicaiagent.modelcomponent.models.ai_connection_parameters import AiConnectionParameters
from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.ai_response import AiResponse


class ICloudAiProvider(ABC):
    """Interface for a single Cloud AI backend provider.

    Implemented as a stateless class (@classmethod); no instance state is required.
    Converts AiRequest payloads to the provider API format, calls the API,
    and converts the response to AiResponse.
    """

    @classmethod
    @abstractmethod
    async def invoke(
        cls,
        connection_parameters: AiConnectionParameters,
        request: AiRequest,
    ) -> AiResponse:
        """Invoke a Cloud AI operation through this provider.

        Args:
            connection_parameters: Provider-specific connection parameters
                (endpoint, api_key, model, etc.).
            request: AI operation type, payload, and inference parameters.

        Returns:
            The model output and operation status.

        Raises:
            CloudAiConfigurationException: Connection parameters are invalid or
                required parameters are missing.
            CloudAiRequestValidationException: Request payload or message content is invalid.
            CloudAiUnsupportedOperationException: The operation type is not supported
                by this provider.
            CloudAiRemoteApiException: The upstream API call failed.
        """
        raise NotImplementedError
