"""Concrete DatabaseManager exception types by error category."""

from __future__ import annotations

from .database_manager_exception import DatabaseManagerException


class DatabaseManagerConfigurationException(DatabaseManagerException):
    """Invalid manager/provider configuration such as unsupported database type."""

    ERROR_NAME: str = "DatabaseManagerConfigurationException"
    DEFAULT_MESSAGE: str = "Invalid DatabaseManager configuration."


class DatabaseManagerProviderInitializationException(DatabaseManagerException):
    """Database provider creation or initialization failed."""

    ERROR_NAME: str = "DatabaseManagerProviderInitializationException"
    DEFAULT_MESSAGE: str = "Database provider initialization failed."


class DatabaseManagerProviderCloseException(DatabaseManagerException):
    """Database provider close operation failed."""

    ERROR_NAME: str = "DatabaseManagerProviderCloseException"
    DEFAULT_MESSAGE: str = "Database provider close operation failed."


class DatabaseManagerNotInitializedException(DatabaseManagerException):
    """DatabaseManager phase-3 initialisation (``initialize()``) has not been called.

    Methods that depend on :py:class:`ISecretManager` will raise this
    exception until :py:meth:`DatabaseManager.initialize` is called.
    """

    ERROR_NAME: str = "DatabaseManagerNotInitializedException"
    DEFAULT_MESSAGE: str = (
        "DatabaseManager is not fully initialized. "
        "Call initialize() with a SecretManager first."
    )


class DatabaseManagerConnectionNotFoundException(DatabaseManagerException):
    """No DatabaseConnection record or provider was found for the given id or name."""

    ERROR_NAME: str = "DatabaseManagerConnectionNotFoundException"
    DEFAULT_MESSAGE: str = "DatabaseConnection not found."


class DatabaseManagerSecretNotFoundException(DatabaseManagerException):
    """The Secret referenced by a DatabaseConnection does not exist."""

    ERROR_NAME: str = "DatabaseManagerSecretNotFoundException"
    DEFAULT_MESSAGE: str = "Secret referenced by DatabaseConnection not found."


class DatabaseManagerInvalidOperationException(DatabaseManagerException):
    """The requested operation is not permitted in the current context.

    Examples:

    * Attempting to update or delete the ``default`` connection.
    * Providing ``raw_secret`` in an update request.
    * Providing both ``raw_secret`` and ``secret`` in the same request.
    """

    ERROR_NAME: str = "DatabaseManagerInvalidOperationException"
    DEFAULT_MESSAGE: str = "Invalid operation on DatabaseManager."
