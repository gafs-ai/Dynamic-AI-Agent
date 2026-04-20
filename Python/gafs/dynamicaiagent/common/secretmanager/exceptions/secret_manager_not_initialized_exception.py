"""secret_manager_not_initialized_exception.py - Raised when SecretManager is used before initialization."""

from typing import Any

from .secret_manager_exception import SecretManagerException


class SecretManagerNotInitializedException(SecretManagerException):
    """Raised when a SecretManager operation is called before ``initialize()`` completes.

    Callers must call ``initialize()`` and wait for it to succeed before invoking
    any other SecretManager method.
    """

    ERROR_NAME: str = "SecretManagerNotInitializedException"
    DEFAULT_MESSAGE: str = (
        "SecretManager is not initialized. Ensure initialize() has been called."
    )

    def __init__(
        self,
        message: str = (
            "SecretManager is not initialized. Ensure initialize() has been called."
        ),
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
