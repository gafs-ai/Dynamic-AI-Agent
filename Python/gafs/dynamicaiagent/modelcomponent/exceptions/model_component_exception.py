"""Base exception class for the Model Component."""

from __future__ import annotations

from typing import Any

from gafs.dynamicaiagent.common.exceptions import ApplicationException


class ModelComponentException(ApplicationException):
    """Base exception for all Model Component errors.

    All component-specific exceptions extend this class. The ``details``
    dict is automatically populated with ``component = "ModelComponent"``.
    """

    ERROR_NAME: str = "ModelComponentException"
    DEFAULT_MESSAGE: str = "Unexpected Error in Model Component."

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        if message is None:
            message = self.DEFAULT_MESSAGE
        details = details if isinstance(details, dict) else {}
        details.setdefault("component", "ModelComponent")
        super().__init__(message=message, details=details, cause=cause)
