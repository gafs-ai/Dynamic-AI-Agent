"""
gafs.dynamicaiagent.cloudaicomponent - Cloud AI component.

Provides Cloud AI services (Azure OpenAI, OpenAI) for chat completion,
embedding, and related operations. Uses ModelComponent's AiRequest and AiResponse.
"""

from .cloud_ai_component import CloudAiComponent
from .exceptions import (
    CloudAiConfigurationException,
    CloudAiException,
    CloudAiRemoteApiException,
    CloudAiRequestValidationException,
    CloudAiUnsupportedOperationException,
)
from .i_cloud_ai_component import ICloudAiComponent
from .i_cloud_ai_provider import ICloudAiProvider
from .models.cloud_ai_provider_type import CloudAiProviderType
from .providers.azure_openai import AzureOpenAiProvider
from .providers.openai import OpenAiProvider

__all__ = [
    "CloudAiComponent",
    "CloudAiConfigurationException",
    "CloudAiException",
    "CloudAiRemoteApiException",
    "CloudAiRequestValidationException",
    "CloudAiUnsupportedOperationException",
    "ICloudAiComponent",
    "ICloudAiProvider",
    "CloudAiProviderType",
    "AzureOpenAiProvider",
    "OpenAiProvider",
]
