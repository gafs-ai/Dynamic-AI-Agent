"""secret_manager_operation_exception.py - Raised when a database operation in SecretManager fails."""

from typing import Any

from .secret_manager_exception import SecretManagerException


class SecretManagerOperationException(SecretManagerException):
    """Raised when a database operation in SecretManager fails unexpectedly.

    This exception wraps errors from the underlying database provider during
    CRUD operations on the ``Secrets`` collection.
    """

    ERROR_NAME: str = "SecretManagerOperationException"
    DEFAULT_MESSAGE: str = "A database operation in Secret Manager failed."

    def __init__(
        self,
        message: str = "A database operation in Secret Manager failed.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
