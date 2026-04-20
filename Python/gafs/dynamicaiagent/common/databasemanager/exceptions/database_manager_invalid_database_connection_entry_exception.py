"""database_manager_invalid_database_connection_entry_exception.py - Raised for invalid connection entries."""

from typing import Any
from .database_manager_exception import DatabaseManagerException


class DatabaseManagerInvalidDatabaseConnectionEntryException(DatabaseManagerException):
    """Raised when a DatabaseConnection entry has invalid data.

    Examples: both secret and raw_secret are set, required fields are missing,
    or field values fail validation.
    """

    ERROR_NAME: str = "DatabaseManagerInvalidDatabaseConnectionEntryException"
    DEFAULT_MESSAGE: str = "Invalid DatabaseConnection entry."

    @staticmethod
    def ERROR_NAME_STATIC() -> str:
        """Return the error name constant."""
        return "DatabaseManagerInvalidDatabaseConnectionEntryException"

    @staticmethod
    def DEFAULT_MESSAGE_STATIC() -> str:
        """Return the default message constant."""
        return "Invalid DatabaseConnection entry."

    def __init__(
        self,
        message: str = "Invalid DatabaseConnection entry.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
