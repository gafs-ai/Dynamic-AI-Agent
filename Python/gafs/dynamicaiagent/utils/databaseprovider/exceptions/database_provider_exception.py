from typing import Any


class DatabaseProviderException(Exception):
    """Base exception for all errors raised by the DatabaseProvider component.

    Does not depend on any application-level exception hierarchy; inherits
    directly from ``Exception`` so that callers can catch it independently
    of any other component exceptions.

    Attributes:
        message: Human-readable error description.
        details: Optional structured details dictionary.
        cause: Underlying exception that caused this error, if any.
    """

    DEFAULT_MESSAGE: str = "Unexpected Error in Database Provider."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.details: dict[str, Any] | None = details
        self.cause: BaseException | None = cause
