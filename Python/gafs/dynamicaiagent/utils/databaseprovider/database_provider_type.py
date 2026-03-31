from enum import Enum

class DatabaseProviderType(Enum):
    """
    Enumeration of supported database provider types.
    """

    SURREALDB_REMOTE = "surrealdb_remote"
