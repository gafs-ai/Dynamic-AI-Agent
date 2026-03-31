"""Database provider abstraction and implementations for Dynamic AI Agent.

This package exposes the public API: interfaces, options, provider implementations,
and commonly used exception types. Additional exception subclasses are available
from .exceptions.
"""
from __future__ import annotations

from .database_provider_type import DatabaseProviderType
from .i_database_provider import (
    IDatabaseProvider,
    DatabaseProviderStatus,
    DatabaseProviderOptions,
    DatabaseType,
)
from .surrealdb_remote_provider import (
    SurrealDbRemoteProvider,
    RemoteSurrealDbOptions,
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
    "DatabaseType",
    "DatabaseProviderType",
    "SurrealDbRemoteProvider",
    "RemoteSurrealDbOptions",
    "DatabaseProviderException",
    "DatabaseProviderInitializationException",
    "DatabaseProviderUnconnectableException",
    "DatabaseProviderAuthenticationException",
    "DatabaseOperationException",
    "DatabaseDisconnectedException",
    "DatabaseQueryErrorException",
    "EmbeddedDatabaseException",
]
