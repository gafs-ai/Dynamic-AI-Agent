"""tool_component_exception.py - Base exception class for the Tool Component."""

from __future__ import annotations

from typing import Any

from gafs.dynamicaiagent.common.exceptions import ApplicationException


class ToolComponentException(ApplicationException):
    """Base exception for all Tool Component errors.

    All component-specific exceptions extend this class. The ``details``
    dict is automatically populated with ``component = "ToolComponent"``.
    """

    ERROR_NAME: str = "ToolComponentException"
    DEFAULT_MESSAGE: str = "Unexpected Error in Tool Component."

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        if message is None:
            message = self.DEFAULT_MESSAGE
        details = details if isinstance(details, dict) else {}
        details.setdefault("component", "ToolComponent")
        super().__init__(message=message, details=details, cause=cause)
