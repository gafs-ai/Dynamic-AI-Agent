"""database_manager_operation_exception.py - Raised when a database operation fails."""

from typing import Any
from .database_manager_exception import DatabaseManagerException


class DatabaseManagerOperationException(DatabaseManagerException):
    """Raised when a database query or connection operation fails.

    This is the general-purpose exception for database operation failures within
    DatabaseManager, such as query errors or unexpected database responses.
    """

    ERROR_NAME: str = "DatabaseManagerOperationException"
    DEFAULT_MESSAGE: str = "A database operation failed."

    @staticmethod
    def ERROR_NAME_STATIC() -> str:
        """Return the error name constant."""
        return "DatabaseManagerOperationException"

    @staticmethod
    def DEFAULT_MESSAGE_STATIC() -> str:
        """Return the default message constant."""
        return "A database operation failed."

    def __init__(
        self,
        message: str = "A database operation failed.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
