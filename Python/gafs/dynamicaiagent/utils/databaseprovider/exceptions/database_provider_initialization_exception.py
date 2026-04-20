from typing import Any

from .database_provider_exception import DatabaseProviderException


class DatabaseProviderInitializationException(DatabaseProviderException):
    """Raised when a provider fails to initialize (connect, authenticate, or apply options).

    This is the base class for all initialization-phase failures.
    """

    DEFAULT_MESSAGE: str = "Failed to initialize Database Provider."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)


class DatabaseProviderOptionsException(DatabaseProviderInitializationException):
    """Raised when the provided DatabaseProviderOptions are invalid or incomplete."""

    DEFAULT_MESSAGE: str = "Invalid Database Provider Options."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)


class DatabaseProviderUnconnectableException(DatabaseProviderInitializationException):
    """Raised when the provider cannot establish a network connection to the database endpoint."""

    DEFAULT_MESSAGE: str = "Database Provider is not connectable."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)


class DatabaseProviderAuthenticationException(DatabaseProviderInitializationException):
    """Raised when credentials are rejected during provider initialization."""

    DEFAULT_MESSAGE: str = "Database Provider Authentication Failed."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)


class EmbeddedDatabaseInitializationException(DatabaseProviderInitializationException):
    """Raised when an embedded database provider fails during startup.

    Covers all failure cases including server process startup failure,
    port conflicts, and insufficient resources.
    """

    DEFAULT_MESSAGE: str = "Failed to initialize Embedded Database."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
