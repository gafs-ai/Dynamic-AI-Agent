from enum import Enum


class DatabaseProviderType(Enum):
    """Enumeration of supported database provider backends.

    SURREALDB_REMOTE: Remote SurrealDB server accessed over WebSocket.
    SURREALDB_LOCAL: Embedded SurrealDB instance running within the application process.
    """

    SURREALDB_REMOTE = "surrealdb_remote"
    SURREALDB_LOCAL = "surrealdb_local"
