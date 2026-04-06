from __future__ import annotations

from typing import Any

from gafs.dynamicaiagent.common.exceptions import ApplicationException

from ..models.cloud_ai_provider_type import CloudAiProviderType


class CloudAiException(ApplicationException):
    """Base exception for Cloud AI component."""

    ERROR_NAME: str = "CloudAiException"
    DEFAULT_MESSAGE: str = "Unexpected Error in Cloud AI component."

    def __init__(
        self,
        message: str | None = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
        provider: CloudAiProviderType | str | None = None
    ):
        details: dict[str, Any] = details if isinstance(details, dict) else {}
        details["component"] = "CloudAiComponent"
        if provider:
            details["ai_provider"] = provider.value if isinstance(provider, CloudAiProviderType) else provider
        else:
            details["ai_provider"] = "unknown"
        super().__init__(message=message, details=details, cause=cause)
