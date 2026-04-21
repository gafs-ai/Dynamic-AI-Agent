"""AiProviderType — abstract base enum that all provider-specific type enums extend."""

from enum import Enum


class AiProviderType(Enum):
    """Abstract base enum for AI provider types.

    NOTE: Do NOT add provider type values directly here.
    Concrete provider enums (e.g. CloudAiProviderType) extend this class
    for their specific deployment family.
    """
    pass
