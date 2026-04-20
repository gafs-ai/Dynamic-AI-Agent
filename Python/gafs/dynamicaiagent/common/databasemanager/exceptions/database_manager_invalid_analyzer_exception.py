"""database_manager_invalid_analyzer_exception.py - Raised for invalid analyzer definitions."""

from typing import Any
from .database_manager_exception import DatabaseManagerException


class DatabaseManagerInvalidAnalyzerException(DatabaseManagerException):
    """Raised when a FullTextAnalyzer definition fails validation.

    For example: name is empty, filter parameters are invalid, or
    an unsupported snowball language is specified.
    """

    ERROR_NAME: str = "DatabaseManagerInvalidAnalyzerException"
    DEFAULT_MESSAGE: str = "Invalid Analyzer Definition entry."

    @staticmethod
    def ERROR_NAME_STATIC() -> str:
        """Return the error name constant."""
        return "DatabaseManagerInvalidAnalyzerException"

    @staticmethod
    def DEFAULT_MESSAGE_STATIC() -> str:
        """Return the default message constant."""
        return "Invalid Analyzer Definition entry."

    def __init__(
        self,
        message: str = "Invalid Analyzer Definition entry.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
