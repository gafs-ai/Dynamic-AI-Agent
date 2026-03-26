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
