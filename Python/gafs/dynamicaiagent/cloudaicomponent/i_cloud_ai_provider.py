"""Cloud AI Provider interface.

ICloudAiProvider uses Model Component's AiRequest and AiResponse.
Connection parameters are provided via AiConnectionParameters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.ai_response import AiResponse

from gafs.dynamicaiagent.modelcomponent.models.ai_connection_parameters import AiConnectionParameters


class ICloudAiProvider(ABC):
    """Cloud AI provider interface.

    Abstracts inference, embedding, etc. into a single invoke method for
    Dependency Injection of Azure OpenAI, OpenAI, etc.
    Uses Model Component's AiRequest and AiResponse.
    Connection information is passed via AiConnectionParameters.
    """

    @classmethod
    @abstractmethod
    async def invoke(
        cls, connection_parameters: AiConnectionParameters, request: AiRequest
    ) -> AiResponse:
        """Invoke Cloud AI."""
        raise NotImplementedError
