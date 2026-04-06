from typing import Any
from gafs.dynamicaiagent.common.exceptions import ApplicationException

class ModelComponentException(ApplicationException):
    ERROR_NAME: str = "ModelComponentException"
    DEFAULT_MESSAGE: str = "Unexpected Error in Model Component."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        details: dict[str, Any] = details if isinstance(details, dict) else {}
        details.setdefault("component", "ModelComponent")
        super().__init__(message=message, details=details, cause=cause)
