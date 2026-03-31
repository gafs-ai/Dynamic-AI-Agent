"""Database provider abstraction and implementations for Dynamic AI Agent.

This package exposes the public API: interfaces, options, provider implementations,
and commonly used exception types. Additional exception subclasses are available
from .exceptions.
"""
from __future__ import annotations

from .database_provider_type import DatabaseProviderType
from .database_provider_status import DatabaseProviderStatus
from .database_provider_options import DatabaseProviderOptions
from .i_database_provider import IDatabaseProvider
from .surrealdb_remote_provider import (
    SurrealDbRemoteProvider,
    RemoteSurrealDbOptions,
)
from .surrealdb_local_provider import (
    SurrealDbLocalProvider,
    LocalSurrealDbOptions,
    LocalSurrealDbStorageType,
)
from .exceptions import (
    DatabaseProviderException,
    DatabaseProviderInitializationException,
    DatabaseProviderUnconnectableException,
    DatabaseProviderAuthenticationException,
    DatabaseOperationException,
    DatabaseDisconnectedException,
    DatabaseQueryErrorException,
    EmbeddedDatabaseException,
)

__all__ = [
    "IDatabaseProvider",
    "DatabaseProviderStatus",
    "DatabaseProviderOptions",
    "DatabaseProviderType",
    "SurrealDbRemoteProvider",
    "RemoteSurrealDbOptions",
    "SurrealDbLocalProvider",
    "LocalSurrealDbOptions",
    "LocalSurrealDbStorageType",
    "DatabaseProviderException",
    "DatabaseProviderInitializationException",
    "DatabaseProviderUnconnectableException",
    "DatabaseProviderAuthenticationException",
    "DatabaseOperationException",
    "DatabaseDisconnectedException",
    "DatabaseQueryErrorException",
    "EmbeddedDatabaseException",
]

