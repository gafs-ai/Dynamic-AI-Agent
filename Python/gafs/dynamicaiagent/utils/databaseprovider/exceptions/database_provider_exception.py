from typing import Any
from gafs.dynamicaiagent.common.exceptions import ApplicationException

class DatabaseProviderException(ApplicationException):
    """
    Base exception for database provider related errors.
    """
    ERROR_NAME: str = "DatabaseProviderException"
    DEFAULT_MESSAGE: str = "Unexpected Error in Database Provider."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ):
        details: dict[str, Any] = details if isinstance(details, dict) else {}
        details.setdefault("component", "DatabaseProviderUtility")
        super().__init__(message=message, details=details, cause=cause)
