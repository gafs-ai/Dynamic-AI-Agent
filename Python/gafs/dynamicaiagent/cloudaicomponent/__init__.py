"""
gafs.dynamicaiagent.cloudaicomponent - Cloud AI component.

Provides Cloud AI services (Azure OpenAI, OpenAI, etc.) for inference,
embedding, and related operations. Uses Model Component's AiRequest and AiResponse.
Connection parameters (Cloud, AzureOpenAi, OpenAi) are provider-specific.
"""

from __future__ import annotations

from importlib import import_module

from .exceptions import (
    CloudAiConfigurationException,
    CloudAiException,
    CloudAiRemoteApiException,
    CloudAiRequestValidationException,
    CloudAiUnsupportedOperationException,
)

__all__ = [
    "CloudAiComponent",
    "CloudAiConfigurationException",
    "CloudAiException",
    "CloudAiRemoteApiException",
    "CloudAiRequestValidationException",
    "CloudAiUnsupportedOperationException",
    "AzureOpenAiProvider",
    "ICloudAiComponent",
    "ICloudAiProvider",
    "OpenAiProvider",
]


def __getattr__(name: str):
    if name == "CloudAiComponent":
        return import_module(".cloud_ai_component", __name__).CloudAiComponent
    if name == "ICloudAiComponent":
        return import_module(".i_cloud_ai_component", __name__).ICloudAiComponent
    if name == "ICloudAiProvider":
        return import_module(".i_cloud_ai_provider", __name__).ICloudAiProvider
    if name == "AzureOpenAiProvider":
        return import_module(
            ".providers.azure_openai.azure_openai_provider", __name__
        ).AzureOpenAiProvider
    if name == "OpenAiProvider":
        return import_module(".providers.openai.openai_provider", __name__).OpenAiProvider
    raise AttributeError(name)
