from typing import Any
from gafs.dynamicaiagent.common.exceptions import ApplicationException

class SecretManagerException(ApplicationException):
    ERROR_NAME: str = "SecretManagerException"
    DEFAULT_MESSAGE: str = "Unexpected Error in Secret Manager."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException | None = None):
        details: dict[str, Any] = details if isinstance(details, dict) else {}
        details.setdefault("component", "CommonComponent:SecretManager")
        super().__init__(message=message, details=details, cause=cause)
