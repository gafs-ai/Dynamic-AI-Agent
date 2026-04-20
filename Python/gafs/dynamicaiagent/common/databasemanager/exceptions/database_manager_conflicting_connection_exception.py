"""database_manager_conflicting_connection_exception.py - Raised when a connection entry conflicts."""

from typing import Any
from .database_manager_exception import DatabaseManagerException


class DatabaseManagerConflictingConnectionException(DatabaseManagerException):
    """Raised when a DatabaseConnection entry conflicts with an existing one.

    This is raised when a caller attempts to create a connection with an id
    that already exists in the DatabaseConnections collection.
    """

    ERROR_NAME: str = "DatabaseManagerConflictingConnectionException"
    DEFAULT_MESSAGE: str = "DatabaseConnection entry conflicts with another entry."

    @staticmethod
    def ERROR_NAME_STATIC() -> str:
        """Return the error name constant."""
        return "DatabaseManagerConflictingConnectionException"

    @staticmethod
    def DEFAULT_MESSAGE_STATIC() -> str:
        """Return the default message constant."""
        return "DatabaseConnection entry conflicts with another entry."

    def __init__(
        self,
        message: str = "DatabaseConnection entry conflicts with another entry.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
