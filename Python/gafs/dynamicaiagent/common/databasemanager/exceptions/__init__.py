"""DatabaseManager exception package."""

from .database_manager_exception import DatabaseManagerException
from .database_manager_exceptions import (
    DatabaseManagerConfigurationException,
    DatabaseManagerProviderInitializationException,
    DatabaseManagerProviderCloseException,
    DatabaseManagerNotInitializedException,
    DatabaseManagerConnectionNotFoundException,
    DatabaseManagerSecretNotFoundException,
    DatabaseManagerInvalidOperationException,
)

__all__ = [
    "DatabaseManagerException",
    "DatabaseManagerConfigurationException",
    "DatabaseManagerProviderInitializationException",
    "DatabaseManagerProviderCloseException",
    "DatabaseManagerNotInitializedException",
    "DatabaseManagerConnectionNotFoundException",
    "DatabaseManagerSecretNotFoundException",
    "DatabaseManagerInvalidOperationException",
]
