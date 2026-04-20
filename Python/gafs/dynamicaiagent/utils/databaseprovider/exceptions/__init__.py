"""gafs.dynamicaiagent.utils.databaseprovider.exceptions - Exception classes for the DatabaseProvider component."""

from .database_provider_exception import DatabaseProviderException
from .database_provider_initialization_exception import (
    DatabaseProviderInitializationException,
    DatabaseProviderOptionsException,
    DatabaseProviderUnconnectableException,
    DatabaseProviderAuthenticationException,
    EmbeddedDatabaseInitializationException,
)
from .database_operation_exception import (
    DatabaseOperationException,
    UnpermittedDatabaseOperationException,
    UnsupportedDatabaseOperationException,
    DatabaseQueryErrorException,
    DatabaseConnectionException,
    DatabaseRecordNotFoundException,
    DatabaseConflictingEntryException,
)

__all__ = [
    # Base
    "DatabaseProviderException",
    # Initialization
    "DatabaseProviderInitializationException",
    "DatabaseProviderOptionsException",
    "DatabaseProviderUnconnectableException",
    "DatabaseProviderAuthenticationException",
    "EmbeddedDatabaseInitializationException",
    # Operations
    "DatabaseOperationException",
    "UnpermittedDatabaseOperationException",
    "UnsupportedDatabaseOperationException",
    "DatabaseQueryErrorException",
    "DatabaseConnectionException",
    "DatabaseRecordNotFoundException",
    "DatabaseConflictingEntryException",
]
