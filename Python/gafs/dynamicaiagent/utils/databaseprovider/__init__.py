"""gafs.dynamicaiagent.utils.databaseprovider - Database provider abstraction and implementations."""

from .database_provider_type import DatabaseProviderType
from .database_provider_status import DatabaseProviderStatus
from .database_provider_options import DatabaseProviderOptions
from .retry_options import RetryOptions
from .i_database_provider import IDatabaseProvider
from .surrealdblocal import (
    LocalSurrealDbOptions,
    LocalSurrealDbStorageType,
    SurrealDbLocalProvider,
)
from .surrealdbremote import (
    RemoteSurrealDbOptions,
    SurrealDbRemoteProvider,
)
from .exceptions import (
    DatabaseProviderException,
    DatabaseProviderInitializationException,
    DatabaseProviderOptionsException,
    DatabaseProviderUnconnectableException,
    DatabaseProviderAuthenticationException,
    EmbeddedDatabaseInitializationException,
    DatabaseOperationException,
    UnpermittedDatabaseOperationException,
    UnsupportedDatabaseOperationException,
    DatabaseQueryErrorException,
    DatabaseConnectionException,
    DatabaseRecordNotFoundException,
    DatabaseConflictingEntryException,
)

__all__ = [
    # Core interfaces and enums
    "IDatabaseProvider",
    "DatabaseProviderStatus",
    "DatabaseProviderOptions",
    "DatabaseProviderType",
    "RetryOptions",
    # Local (embedded) provider
    "SurrealDbLocalProvider",
    "LocalSurrealDbOptions",
    "LocalSurrealDbStorageType",
    # Remote provider
    "SurrealDbRemoteProvider",
    "RemoteSurrealDbOptions",
    # Exceptions
    "DatabaseProviderException",
    "DatabaseProviderInitializationException",
    "DatabaseProviderOptionsException",
    "DatabaseProviderUnconnectableException",
    "DatabaseProviderAuthenticationException",
    "EmbeddedDatabaseInitializationException",
    "DatabaseOperationException",
    "UnpermittedDatabaseOperationException",
    "UnsupportedDatabaseOperationException",
    "DatabaseQueryErrorException",
    "DatabaseConnectionException",
    "DatabaseRecordNotFoundException",
    "DatabaseConflictingEntryException",
]
