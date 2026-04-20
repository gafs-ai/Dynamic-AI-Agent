"""database_manager_not_initialized_exception.py - Raised when a method is called before initialization."""

from typing import Any
from .database_manager_exception import DatabaseManagerException


class DatabaseManagerNotInitializedException(DatabaseManagerException):
    """Raised when a DatabaseManager method is called before the required initialization phase.

    Methods requiring phase-1 raise this if initialize_default_connection has not been called.
    Methods requiring phase-3 raise this if initialize (with ISecretManager) has not been called.
    """

    ERROR_NAME: str = "DatabaseManagerNotInitializedException"
    DEFAULT_MESSAGE: str = (
        "DatabaseManager is not initialized. Ensure the required initialization phase has been completed."
    )

    @staticmethod
    def ERROR_NAME_STATIC() -> str:
        """Return the error name constant."""
        return "DatabaseManagerNotInitializedException"

    @staticmethod
    def DEFAULT_MESSAGE_STATIC() -> str:
        """Return the default message constant."""
        return (
            "DatabaseManager is not initialized. Ensure the required initialization phase has been completed."
        )

    def __init__(
        self,
        message: str = (
            "DatabaseManager is not initialized. Ensure the required initialization phase has been completed."
        ),
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
