from typing import Any
from gafs.dynamicaiagent.common.exceptions.application_exception import ApplicationException

class SymmetricCryptoUtilException(ApplicationException):
    ERROR_NAME: str = "SymmetricCryptoUtilException"
    DEFAULT_MESSAGE: str = "Unexpected Error in Symmetric Crypto Util."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ):
        details: dict[str, Any] = details if isinstance(details, dict) else {}
        details.setdefault("component", "SymmetricCryptoUtility")
        super().__init__(message=message, details=details, cause=cause)
