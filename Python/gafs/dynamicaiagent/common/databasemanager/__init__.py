"""
gafs.dynamicaiagent.common.databasemanager - Database manager functionality.
"""

from .database_connection import DatabaseConnection
from .database_manager import DatabaseManager
from .i_database_manager import IDatabaseManager
from .exceptions import (
    DatabaseManagerException,
    DatabaseManagerConfigurationException,
    DatabaseManagerProviderInitializationException,
    DatabaseManagerProviderCloseException,
    DatabaseManagerNotInitializedException,
    DatabaseManagerConnectionNotFoundException,
    DatabaseManagerSecretNotFoundException,
    DatabaseManagerInvalidOperationException,
)

__all__ = [
    "DatabaseConnection",
    "DatabaseManager",
    "IDatabaseManager",
    "DatabaseManagerException",
    "DatabaseManagerConfigurationException",
    "DatabaseManagerProviderInitializationException",
    "DatabaseManagerProviderCloseException",
    "DatabaseManagerNotInitializedException",
    "DatabaseManagerConnectionNotFoundException",
    "DatabaseManagerSecretNotFoundException",
    "DatabaseManagerInvalidOperationException",
]

