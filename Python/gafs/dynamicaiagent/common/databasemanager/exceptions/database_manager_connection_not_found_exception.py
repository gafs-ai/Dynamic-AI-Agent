"""database_manager_connection_not_found_exception.py - Raised when a connection entry is not found."""

from typing import Any
from .database_manager_exception import DatabaseManagerException


class DatabaseManagerConnectionNotFoundException(DatabaseManagerException):
    """Raised when no matching DatabaseConnection entry is found.

    This is raised when a lookup by id or a deletion attempt finds no matching record.
    """

    ERROR_NAME: str = "DatabaseManagerConnectionNotFoundException"
    DEFAULT_MESSAGE: str = "DatabaseConnection not found."

    @staticmethod
    def ERROR_NAME_STATIC() -> str:
        """Return the error name constant."""
        return "DatabaseManagerConnectionNotFoundException"

    @staticmethod
    def DEFAULT_MESSAGE_STATIC() -> str:
        """Return the default message constant."""
        return "DatabaseConnection not found."

    def __init__(
        self,
        message: str = "DatabaseConnection not found.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
