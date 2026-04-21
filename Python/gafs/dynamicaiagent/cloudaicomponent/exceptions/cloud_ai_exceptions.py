"""Concrete Cloud AI exception types, categorized by error kind."""

from __future__ import annotations

from .cloud_ai_exception import CloudAiException


class CloudAiConfigurationException(CloudAiException):
    """Raised when deployment type, connection parameters, or provider selection is invalid."""

    ERROR_NAME: str = "CloudAiConfigurationException"
    DEFAULT_MESSAGE: str = "Invalid Cloud AI configuration or connection parameters."


class CloudAiRequestValidationException(CloudAiException):
    """Raised when the request payload or message content is invalid."""

    ERROR_NAME: str = "CloudAiRequestValidationException"
    DEFAULT_MESSAGE: str = "Invalid request for Cloud AI operation."


class CloudAiUnsupportedOperationException(CloudAiException):
    """Raised when an operation or feature is not supported by the selected provider."""

    ERROR_NAME: str = "CloudAiUnsupportedOperationException"
    DEFAULT_MESSAGE: str = "The requested operation is not supported by Cloud AI."


class CloudAiRemoteApiException(CloudAiException):
    """Raised when the upstream provider SDK or API call fails."""

    ERROR_NAME: str = "CloudAiRemoteApiException"
    DEFAULT_MESSAGE: str = "Cloud AI remote API call failed."
