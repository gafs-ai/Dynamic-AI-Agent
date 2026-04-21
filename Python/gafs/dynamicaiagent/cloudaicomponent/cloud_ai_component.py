"""CloudAiComponent implementation — routes AI requests to the correct provider."""

from __future__ import annotations

from gafs.dynamicaiagent.modelcomponent.models.ai_connection_parameters import AiConnectionParameters
from gafs.dynamicaiagent.modelcomponent.models.ai_deployment_type import AiDeploymentType
from gafs.dynamicaiagent.modelcomponent.models.ai_request import AiRequest
from gafs.dynamicaiagent.modelcomponent.models.ai_response import AiResponse

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
    """Cloud AI component.

    Routes AI invocation requests to the appropriate provider based on the
    provider_type in connection_parameters. Validates that deployment_type is CLOUD
    before dispatching. Wraps any unexpected exception as CloudAiException.
    """

    async def invoke(
        self,
        connection_parameters: AiConnectionParameters,
        request: AiRequest,
    ) -> AiResponse:
        """Invoke a Cloud AI operation through the appropriate provider.

        Args:
            connection_parameters: Must have deployment_type CLOUD and a recognized
                provider_type (CloudAiProviderType).
            request: AI operation type, payload, and inference parameters.

        Returns:
            The model output and operation status.

        Raises:
            CloudAiConfigurationException: deployment_type is not CLOUD, provider_type
                is unrecognized or invalid.
            CloudAiRequestValidationException: Request payload or messages are invalid.
            CloudAiUnsupportedOperationException: provider_type is a custom string, or
                the operation is not supported by the selected provider.
            CloudAiRemoteApiException: The upstream API call failed.
            CloudAiException: Any other unexpected error.
        """
        provider = connection_parameters.provider_type
        try:
            # Step 1: Validate deployment type
            if connection_parameters.deployment_type != AiDeploymentType.CLOUD:
                raise CloudAiConfigurationException(
                    message=(
                        f"Deployment type must be CLOUD. "
                        f"Got: {connection_parameters.deployment_type.value!r}"
                    ),
                )

            # Step 2: Route to the appropriate provider
            if isinstance(provider, CloudAiProviderType):
                match provider:
                    case CloudAiProviderType.AZURE_OPENAI:
                        return await AzureOpenAiProvider.invoke(connection_parameters, request)
                    case CloudAiProviderType.OPENAI:
                        return await OpenAiProvider.invoke(connection_parameters, request)
                    case _:
                        # A CloudAiProviderType value not handled above
                        raise CloudAiConfigurationException(
                            message=f"Unsupported provider type: {provider.value!r}",
                            provider=provider,
                        )

            if isinstance(provider, str):
                # Custom (non-enum) provider string — not supported
                raise CloudAiUnsupportedOperationException(
                    message=f"Custom provider type is not supported: {provider!r}",
                    details={"ai_provider_type": provider},
                    provider=provider,
                )

            # provider_type is neither a CloudAiProviderType nor a str
            raise CloudAiConfigurationException(
                message=f"Invalid provider_type type: {type(provider).__name__}",
            )

        except CloudAiException:
            # Re-raise known Cloud AI exceptions as-is
            raise
        except Exception as e:
            # Wrap any other unexpected exception
            raise CloudAiException(
                message="Unexpected error while invoking CloudAiComponent.",
                cause=e,
                provider=provider if isinstance(provider, (CloudAiProviderType, str)) else None,
            )
