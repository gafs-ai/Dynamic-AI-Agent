"""
gafs.dynamicaiagent.utils.databaseprovider.exceptions
"""

from .database_provider_exception import DatabaseProviderException
from .database_provider_initialization_exception import (
    DatabaseProviderInitializationException,
    DatabaseProviderOptionsException,
    DatabaseProviderUnconnectableException,
    DatabaseProviderAuthenticationException,
)
from .database_operation_exception import (
    DatabaseOperationException,
    UnpermittedDatabaseOperationException,
    UnsupportedDatabaseOperationException,
    MalformedDatabaseQueryException,
    DatabaseQueryErrorException,
    DatabaseQueryTimeoutException,
    DatabaseDisconnectedException,
    DatabaseConnectionLimitExceededException,
    DatabaseRecordNotFoundException,
    DatabaseRecordAlreadyExistsException,
    DatabaseConstraintViolationException,
    DatabaseTransactionException,
    DatabaseDeadlockException,
)
from .embedded_database_exception import (
    EmbeddedDatabaseException,
    EmbeddedDatabaseInitializationException,
    DatabaseProviderServerStartupException,
    DatabaseProviderPortConflictException,
    DatabaseProviderResourceException,
    EmbeddedDatabaseStoppedException,
    EmbeddedDatabaseCrashException,
    EmbeddedDatabaseResourceExhaustionException,
    EmbeddedDatabaseMemoryExhaustionException,
    EmbeddedDatabaseDiskSpaceExhaustionException,
)

__all__ = [
    # Base exceptions
    "DatabaseProviderException",
    # Initialization exceptions
    "DatabaseProviderInitializationException",
    "DatabaseProviderOptionsException",
    "DatabaseProviderUnconnectableException",
    "DatabaseProviderAuthenticationException",
    # Operation exceptions
    "DatabaseOperationException",
    "UnpermittedDatabaseOperationException",
    "UnsupportedDatabaseOperationException",
    # Query exceptions
    "MalformedDatabaseQueryException",
    "DatabaseQueryErrorException",
    "DatabaseQueryTimeoutException",
    # Connection exceptions
    "DatabaseDisconnectedException",
    "DatabaseConnectionLimitExceededException",
    # Record operation exceptions
    "DatabaseRecordNotFoundException",
    "DatabaseRecordAlreadyExistsException",
    "DatabaseConstraintViolationException",
    # Transaction exceptions
    "DatabaseTransactionException",
    "DatabaseDeadlockException",
    # Embedded database exceptions
    "EmbeddedDatabaseException",
    "EmbeddedDatabaseInitializationException",
    "DatabaseProviderServerStartupException",
    "DatabaseProviderPortConflictException",
    "DatabaseProviderResourceException",
    "EmbeddedDatabaseStoppedException",
    "EmbeddedDatabaseCrashException",
    "EmbeddedDatabaseResourceExhaustionException",
    "EmbeddedDatabaseMemoryExhaustionException",
    "EmbeddedDatabaseDiskSpaceExhaustionException",
]