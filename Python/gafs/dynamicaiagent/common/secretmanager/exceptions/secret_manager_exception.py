"""secret_manager_exception.py - Base exception for all SecretManager errors."""

from typing import Any

from gafs.dynamicaiagent.common.exceptions import ApplicationException


class SecretManagerException(ApplicationException):
    """Base exception for all SecretManager errors.

    All SecretManager-specific exceptions inherit from this class.
    """

    ERROR_NAME: str = "SecretManagerException"
    DEFAULT_MESSAGE: str = "Unexpected Error in Secret Manager"
    COMPONENT: str = "CommonComponent:SecretManager"

    def __init__(
        self,
        message: str = "Unexpected Error in Secret Manager",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        resolved_details: dict[str, Any] = details if isinstance(details, dict) else {}
        resolved_details.setdefault("component", SecretManagerException.COMPONENT)
        super().__init__(message=message, details=resolved_details, cause=cause)
