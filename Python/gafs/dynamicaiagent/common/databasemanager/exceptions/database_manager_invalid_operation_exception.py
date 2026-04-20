"""database_manager_invalid_operation_exception.py - Raised for disallowed operations."""

from typing import Any
from .database_manager_exception import DatabaseManagerException


class DatabaseManagerInvalidOperationException(DatabaseManagerException):
    """Raised when a caller requests an operation that is not permitted.

    For example: attempting to update or delete the 'default' connection,
    which is a protected entry managed by DatabaseManager itself.
    """

    ERROR_NAME: str = "DatabaseManagerInvalidOperationException"
    DEFAULT_MESSAGE: str = "Invalid operation on DatabaseManager."

    @staticmethod
    def ERROR_NAME_STATIC() -> str:
        """Return the error name constant."""
        return "DatabaseManagerInvalidOperationException"

    @staticmethod
    def DEFAULT_MESSAGE_STATIC() -> str:
        """Return the default message constant."""
        return "Invalid operation on DatabaseManager."

    def __init__(
        self,
        message: str = "Invalid operation on DatabaseManager.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
