from enum import Enum

from gafs.dynamicaiagent.modelcomponent.models.ai_provider_type import AiProviderType

class CloudAiProviderType(AiProviderType):
    """Cloud AI provider type (e.g. Azure OpenAI, OpenAI)."""

    AZURE_OPENAI = "azure-openai"
    OPENAI = "openai"
