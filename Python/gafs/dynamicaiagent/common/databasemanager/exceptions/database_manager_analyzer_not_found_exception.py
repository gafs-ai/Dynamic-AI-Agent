"""database_manager_analyzer_not_found_exception.py - Raised when a FullTextAnalyzer is not found."""

from typing import Any
from .database_manager_exception import DatabaseManagerException


class DatabaseManagerAnalyzerNotFoundException(DatabaseManagerException):
    """Raised when no matching FullTextAnalyzer entry is found.

    This is raised when a lookup by id or a deletion/update attempt finds no matching record.
    """

    ERROR_NAME: str = "DatabaseManagerAnalyzerNotFoundException"
    DEFAULT_MESSAGE: str = "Full Text Analyzer was not found."

    @staticmethod
    def ERROR_NAME_STATIC() -> str:
        """Return the error name constant."""
        return "DatabaseManagerAnalyzerNotFoundException"

    @staticmethod
    def DEFAULT_MESSAGE_STATIC() -> str:
        """Return the default message constant."""
        return "Full Text Analyzer was not found."

    def __init__(
        self,
        message: str = "Full Text Analyzer was not found.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
