"""Cloud AI component interface.

Defines the ICloudAiComponent interface for future implementation changes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.ai_response import AiResponse

from gafs.dynamicaiagent.modelcomponent.models.ai_connection_parameters import AiConnectionParameters


class ICloudAiComponent(ABC):
    """Cloud AI component interface.

    Provides a single method for external use of Cloud AI services.
    Uses Model Component's AiRequest and AiResponse.
    """

    @abstractmethod
    async def invoke(
        self, connection_parameters: AiConnectionParameters, request: AiRequest
    ) -> AiResponse:
        """Invoke Cloud AI.

        Raises:
            CloudAiException: Base type; concrete cases use subclasses such as
                CloudAiConfigurationException, CloudAiRequestValidationException,
                CloudAiUnsupportedOperationException, or CloudAiRemoteApiException.
        """
        raise NotImplementedError
