"""Base exception class for the Cloud AI component."""

from __future__ import annotations

from typing import Any

from gafs.dynamicaiagent.common.exceptions import ApplicationException

from ..models.cloud_ai_provider_type import CloudAiProviderType


class CloudAiException(ApplicationException):
    """Base exception for all Cloud AI component errors."""

    ERROR_NAME: str = "CloudAiException"
    DEFAULT_MESSAGE: str = "Unexpected Error in Cloud AI component."

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
        provider: CloudAiProviderType | str | None = None,
    ) -> None:
        if message is None:
            message = self.DEFAULT_MESSAGE
        details = details if isinstance(details, dict) else {}
        # Always set component and ai_provider in details
        details["component"] = "CloudAiComponent"
        if provider is not None:
            details["ai_provider"] = provider.value if isinstance(provider, CloudAiProviderType) else provider
        else:
            details["ai_provider"] = "unknown"
        super().__init__(message=message, details=details, cause=cause)
