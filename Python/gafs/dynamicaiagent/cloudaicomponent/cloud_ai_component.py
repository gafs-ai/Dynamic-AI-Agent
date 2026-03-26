"""Cloud AI component implementation.

Accepts ICloudAiProvider via Dependency Injection and exposes
a single invoke method for external use.
"""
from __future__ import annotations

from typing import override

from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.ai_response import AiResponse

from gafs.dynamicaiagent.modelcomponent.models.ai_connection_parameters import AiConnectionParameters
from gafs.dynamicaiagent.modelcomponent.models.ai_deployment_type import AiDeploymentType

from .exceptions import (
    CloudAiConfigurationException,
    CloudAiException,
    CloudAiUnsupportedOperationException,
)
from .i_cloud_ai_component import ICloudAiComponent
from .models.cloud_ai_provider_type import CloudAiProviderType
from .providers.azure_openai import AzureOpenAiProvider
from .providers.openai import OpenAiProvider

class CloudAiComponent(ICloudAiComponent):
    """
    Cloud AI component implementation.

    Accepts ICloudAiProvider via DI and delegates invoke to it.
    """

    @override
    async def invoke(
        self, connection_parameters: AiConnectionParameters, request: AiRequest
    ) -> AiResponse:
        """Invoke Cloud AI."""
        provider = connection_parameters.provider_type
        try:
            if connection_parameters.deployment_type != AiDeploymentType.CLOUD:
                raise CloudAiConfigurationException(
                    f"Deployment type must be CLOUD. Deployment type: {connection_parameters.deployment_type.value}"
                )

            if isinstance(provider, CloudAiProviderType):
                match provider:
                    case CloudAiProviderType.AZURE_OPENAI:
                        return await AzureOpenAiProvider.invoke(connection_parameters, request)
                    case CloudAiProviderType.OPENAI:
                        return await OpenAiProvider.invoke(connection_parameters, request)
                    case _:
                        raise CloudAiConfigurationException(
                            f"Unsupported provider type: {provider.value}",
                            provider=provider,
                        )
            if isinstance(provider, str):
                raise CloudAiUnsupportedOperationException(
                    f"Custom provider type is not supported yet. Provider type: {provider}",
                    details={"ai_provider_type": provider},
                    provider=provider,
                )
            raise CloudAiConfigurationException(
                f"Invalid provider type: {type(provider).__name__}",
            )
        except CloudAiException:
            raise
        except Exception as e:
            raise CloudAiException(
                message="Unexpected error while invoking CloudAiComponent.",
                cause=e,
                provider=provider if isinstance(provider, (CloudAiProviderType, str)) else None,
            )
