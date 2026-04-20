"""database_manager_analyzer_operation_exception.py - Raised when an analyzer DB operation fails."""

from typing import Any
from .database_manager_exception import DatabaseManagerException


class DatabaseManagerAnalyzerOperationException(DatabaseManagerException):
    """Raised when a database operation related to FullTextAnalyzer fails.

    This includes creation, alteration, removal, and query operations for analyzers.
    """

    ERROR_NAME: str = "DatabaseManagerAnalyzerOperationException"
    DEFAULT_MESSAGE: str = "A database operation related to FullTextAnalyzer failed."

    @staticmethod
    def ERROR_NAME_STATIC() -> str:
        """Return the error name constant."""
        return "DatabaseManagerAnalyzerOperationException"

    @staticmethod
    def DEFAULT_MESSAGE_STATIC() -> str:
        """Return the default message constant."""
        return "A database operation related to FullTextAnalyzer failed."

    def __init__(
        self,
        message: str = "A database operation related to FullTextAnalyzer failed.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
