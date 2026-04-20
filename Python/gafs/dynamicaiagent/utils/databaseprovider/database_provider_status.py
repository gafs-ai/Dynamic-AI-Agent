from enum import Enum


class DatabaseProviderStatus(Enum):
    """Lifecycle status of a database provider.

    UNINITIALIZED: Provider has not been initialized yet.
    INITIALIZING: Provider is in the process of connecting and authenticating.
    AVAILABLE: Provider is connected and ready to accept queries.
    TEMPORARILY_UNAVAILABLE: Provider is temporarily unavailable (e.g. reconnecting).
    ERROR: Provider encountered an unrecoverable error.
    TERMINATING: Provider is in the process of shutting down.
    TERMINATED: Provider has been shut down and all resources released.
    """

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    AVAILABLE = "available"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"
    ERROR = "error"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
