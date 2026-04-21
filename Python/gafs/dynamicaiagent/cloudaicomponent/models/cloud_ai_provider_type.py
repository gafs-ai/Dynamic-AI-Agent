"""CloudAiProviderType enum — identifies supported Cloud AI providers."""

from gafs.dynamicaiagent.modelcomponent.models.ai_provider_type import AiProviderType


class CloudAiProviderType(AiProviderType):
    """Enum of Cloud AI provider types supported by this component."""

    AZURE_OPENAI = "azure-openai"
    OPENAI = "openai"
