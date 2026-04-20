"""database_manager_exception.py - Base exception for all DatabaseManager errors."""

from typing import Any

from gafs.dynamicaiagent.common.exceptions import ApplicationException


class DatabaseManagerException(ApplicationException):
    """Base exception for all DatabaseManager errors.

    All DatabaseManager-specific exceptions inherit from this class.
    """

    ERROR_NAME: str = "DatabaseManagerException"
    DEFAULT_MESSAGE: str = "Unexpected Error in Database Manager"
    COMPONENT: str = "CommonComponent:DatabaseManager"

    @staticmethod
    def ERROR_NAME_STATIC() -> str:
        """Return the error name constant."""
        return "DatabaseManagerException"

    @staticmethod
    def DEFAULT_MESSAGE_STATIC() -> str:
        """Return the default message constant."""
        return "Unexpected Error in Database Manager"

    @staticmethod
    def COMPONENT_NAME() -> str:
        """Return the component name constant."""
        return "DatabaseManager"

    def __init__(
        self,
        message: str = "Unexpected Error in Database Manager",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        resolved_details: dict[str, Any] = details if isinstance(details, dict) else {}
        resolved_details.setdefault("component", DatabaseManagerException.COMPONENT)
        super().__init__(message=message, details=resolved_details, cause=cause)
