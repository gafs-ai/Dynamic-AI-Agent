"""database_manager_initialization_exception.py - Raised when initialization fails."""

from typing import Any
from .database_manager_exception import DatabaseManagerException


class DatabaseManagerInitializationException(DatabaseManagerException):
    """Raised when DatabaseManager initialization fails.

    This is raised during phase-1 (initialize_default_connection) when the
    database connection cannot be established or indexes cannot be set up.
    """

    ERROR_NAME: str = "DatabaseManagerInitializationException"
    DEFAULT_MESSAGE: str = "Database provider initialization failed."

    @staticmethod
    def ERROR_NAME_STATIC() -> str:
        """Return the error name constant."""
        return "DatabaseManagerInitializationException"

    @staticmethod
    def DEFAULT_MESSAGE_STATIC() -> str:
        """Return the default message constant."""
        return "Database provider initialization failed."

    def __init__(
        self,
        message: str = "Database provider initialization failed.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
