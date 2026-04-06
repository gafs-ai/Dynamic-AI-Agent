from typing import Any
from gafs.dynamicaiagent.common.exceptions import ApplicationException

class DatabaseManagerException(ApplicationException):
    ERROR_NAME: str = "DatabaseManagerException"
    DEFAULT_MESSAGE: str = "Unexpected Error in Database Manager."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException | None = None):
        details: dict[str, Any] = details if isinstance(details, dict) else {}
        details.setdefault("component", "CommonComponent:DatabaseManager")
        super().__init__(message=message, details=details, cause=cause)
