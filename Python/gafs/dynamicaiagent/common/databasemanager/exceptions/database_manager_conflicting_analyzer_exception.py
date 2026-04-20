"""database_manager_conflicting_analyzer_exception.py - Raised when an analyzer entry conflicts."""

from typing import Any
from .database_manager_exception import DatabaseManagerException


class DatabaseManagerConflictingAnalyzerException(DatabaseManagerException):
    """Raised when a FullTextAnalyzer entry conflicts with an existing one.

    This is raised when a caller attempts to create an analyzer with a name or id
    that already exists in the FullTextAnalyzers collection.
    """

    ERROR_NAME: str = "DatabaseManagerConflictingAnalyzerException"
    DEFAULT_MESSAGE: str = "FullTextAnalyzer entry conflicts with another entry."

    @staticmethod
    def ERROR_NAME_STATIC() -> str:
        """Return the error name constant."""
        return "DatabaseManagerConflictingAnalyzerException"

    @staticmethod
    def DEFAULT_MESSAGE_STATIC() -> str:
        """Return the default message constant."""
        return "FullTextAnalyzer entry conflicts with another entry."

    def __init__(
        self,
        message: str = "FullTextAnalyzer entry conflicts with another entry.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
