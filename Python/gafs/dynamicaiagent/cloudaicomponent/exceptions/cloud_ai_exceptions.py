"""Concrete Cloud AI exception types (by error category, not by provider)."""

from __future__ import annotations

from .cloud_ai_exception import CloudAiException


class CloudAiConfigurationException(CloudAiException):
    """Invalid deployment type, connection parameters, or provider selection."""

    ERROR_NAME: str = "CloudAiConfigurationException"
    DEFAULT_MESSAGE: str = "Invalid Cloud AI configuration or connection parameters."


class CloudAiRequestValidationException(CloudAiException):
    """Invalid request payload or message content for Cloud AI."""

    ERROR_NAME: str = "CloudAiRequestValidationException"
    DEFAULT_MESSAGE: str = "Invalid request for Cloud AI operation."


class CloudAiUnsupportedOperationException(CloudAiException):
    """Operation or feature not supported by the Cloud AI component."""

    ERROR_NAME: str = "CloudAiUnsupportedOperationException"
    DEFAULT_MESSAGE: str = "The requested operation is not supported by Cloud AI."


class CloudAiRemoteApiException(CloudAiException):
    """Upstream Cloud AI API or SDK call failed."""

    ERROR_NAME: str = "CloudAiRemoteApiException"
    DEFAULT_MESSAGE: str = "Cloud AI remote API call failed."
