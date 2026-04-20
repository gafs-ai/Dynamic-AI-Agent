"""secret_manager_initialization_exception.py - Raised when SecretManager initialization fails."""

from typing import Any

from .secret_manager_exception import SecretManagerException


class SecretManagerInitializationException(SecretManagerException):
    """Raised when SecretManager initialization fails.

    Typically raised during ``initialize()`` when the default database provider
    is not available or key loading fails.
    """

    ERROR_NAME: str = "SecretManagerInitializationException"
    DEFAULT_MESSAGE: str = "Secret Manager initialization failed."

    def __init__(
        self,
        message: str = "Secret Manager initialization failed.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
