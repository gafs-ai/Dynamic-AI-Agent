from typing import Any
from . import DatabaseProviderException

class DatabaseProviderInitializationException(DatabaseProviderException):
    """Exception raised when the database provider fails to initialize."""

    ERROR_NAME: str = "DatabaseProviderInitializationException"
    DEFAULT_MESSAGE: str = "Failed to initialize Database Provider."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

# ------------ Options and Configuration ------------

class DatabaseProviderOptionsException(DatabaseProviderException):
    """
    This exception is thrown when the database provider options are invalid.
    """
    ERROR_NAME: str = "DatabaseProviderOptionsException"
    DEFAULT_MESSAGE: str = "Invalid Database Provider Options."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

# ------------ Connection Related ------------

class DatabaseProviderUnconnectableException(DatabaseProviderException):
    """
    This exception is thrown when the database provider cannot be connected.
    """
    ERROR_NAME: str = "DatabaseProviderUnconnectableException"
    DEFAULT_MESSAGE: str = "Database Provider is not connectable."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

class DatabaseProviderAuthenticationException(DatabaseProviderException):
    """
    This exception is thrown when authentication fails during database provider initialization.
    """
    ERROR_NAME: str = "DatabaseProviderAuthenticationException"
    DEFAULT_MESSAGE: str = "Database Provider Authentication Failed."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

# Note: EmbeddedDatabase related exceptions are defined in embedded_database_exception.py
