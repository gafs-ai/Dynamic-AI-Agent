from typing import Any

from .database_provider_exception import DatabaseProviderException


class DatabaseOperationException(DatabaseProviderException):
    """Base class for all errors that occur during query or record operation execution."""

    DEFAULT_MESSAGE: str = "Failed to execute Database Operation."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)


# ── Operation permission / support ───────────────────────────────────────────

class UnpermittedDatabaseOperationException(DatabaseOperationException):
    """Raised when the caller attempts an operation that is not permitted (e.g. access policy)."""

    DEFAULT_MESSAGE: str = "Unpermitted Database Operation."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)


class UnsupportedDatabaseOperationException(DatabaseOperationException):
    """Raised when the caller attempts an operation not supported by this provider implementation."""

    DEFAULT_MESSAGE: str = "Unsupported Database Operation."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)


# ── Query related ─────────────────────────────────────────────────────────────

class DatabaseQueryErrorException(DatabaseOperationException):
    """Raised when a query fails for any reason.

    Includes client-side validation failures and error responses returned by
    the database server (e.g. syntax errors, type mismatches).
    """

    DEFAULT_MESSAGE: str = "Database Query Error."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)


# ── Connection related ────────────────────────────────────────────────────────

class DatabaseConnectionException(DatabaseOperationException):
    """Raised when a query cannot be executed due to a connection problem.

    Includes: provider not connected, query timeout, and connection limit
    exceeded.
    """

    DEFAULT_MESSAGE: str = "Database Disconnected."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)


# ── Record operation related ──────────────────────────────────────────────────

class DatabaseRecordNotFoundException(DatabaseOperationException):
    """Raised when the requested record does not exist in the database."""

    DEFAULT_MESSAGE: str = "Database Record Not Found."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)


class DatabaseConflictingEntryException(DatabaseOperationException):
    """Raised when attempting to create a record that conflicts with another record.

    Examples: conflicting id, unique index violation.
    """

    DEFAULT_MESSAGE: str = "Database Record Conflicts with Another Entry."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
