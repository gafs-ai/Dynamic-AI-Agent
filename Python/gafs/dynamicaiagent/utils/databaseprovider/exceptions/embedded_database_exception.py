from . import DatabaseProviderException, DatabaseProviderInitializationException

# NOTE: Exceptions related to embedded database are separately defined here.
#       We do this because exceptions related to embedded database can be caught and resolved by the application.

class EmbeddedDatabaseException(DatabaseProviderException):
    """
    Base exception for embedded database related errors.
    Embedded database refers to databases that are started as a subprocess or embedded within the application.
    This exception is catchable to handle embedded database issues that can potentially be resolved by the application.
    """
    ERROR_NAME: str = "EmbeddedDatabaseException"
    DEFAULT_MESSAGE: str = "Embedded Database Error."

    def __init__(self, message: str = DEFAULT_MESSAGE, cause: BaseException = None):
        super().__init__(message=message, cause=cause)

# ------------ Initialization Related ------------

class EmbeddedDatabaseInitializationException(EmbeddedDatabaseException, DatabaseProviderInitializationException):
    """
    This exception is thrown when embedded database initialization fails.
    This exception inherits from both EmbeddedDatabaseException and DatabaseProviderInitializationException.
    """
    ERROR_NAME: str = "EmbeddedDatabaseInitializationException"
    DEFAULT_MESSAGE: str = "Failed to initialize Embedded Database."

    def __init__(self, message: str = DEFAULT_MESSAGE, cause: BaseException = None):
        # Call both parent constructors explicitly
        EmbeddedDatabaseException.__init__(self, message=message, cause=cause)
        DatabaseProviderInitializationException.__init__(self, message=message, cause=cause)

class DatabaseProviderServerStartupException(EmbeddedDatabaseInitializationException):
    """
    This exception is thrown when the database server fails to start.
    """
    ERROR_NAME: str = "DatabaseProviderServerStartupException"
    DEFAULT_MESSAGE: str = "Database Server Startup Failed."

    def __init__(self, message: str = DEFAULT_MESSAGE, cause: BaseException = None):
        super().__init__(message=message, cause=cause)

class DatabaseProviderPortConflictException(EmbeddedDatabaseInitializationException):
    """
    This exception is thrown when the requested port is already in use.
    """
    ERROR_NAME: str = "DatabaseProviderPortConflictException"
    DEFAULT_MESSAGE: str = "Database Provider Port Conflict."

    def __init__(self, message: str = DEFAULT_MESSAGE, cause: BaseException = None):
        super().__init__(message=message, cause=cause)

class DatabaseProviderResourceException(EmbeddedDatabaseInitializationException):
    """
    This exception is thrown when there are insufficient resources (e.g., memory, disk space) for database provider initialization.
    """
    ERROR_NAME: str = "DatabaseProviderResourceException"
    DEFAULT_MESSAGE: str = "Database Provider Resource Insufficient."

    def __init__(self, message: str = DEFAULT_MESSAGE, cause: BaseException = None):
        super().__init__(message=message, cause=cause)

# ------------ Runtime Related ------------

class EmbeddedDatabaseStoppedException(EmbeddedDatabaseException):
    """
    This exception is thrown when the embedded database process stops unexpectedly during runtime.
    This can occur due to various reasons such as resource exhaustion, crashes, or external termination.
    """
    ERROR_NAME: str = "EmbeddedDatabaseStoppedException"
    DEFAULT_MESSAGE: str = "Embedded Database Stopped Unexpectedly."

    def __init__(self, message: str = DEFAULT_MESSAGE, cause: BaseException = None):
        super().__init__(message=message, cause=cause)

class EmbeddedDatabaseCrashException(EmbeddedDatabaseException):
    """
    This exception is thrown when the embedded database process crashes during runtime.
    """
    ERROR_NAME: str = "EmbeddedDatabaseCrashException"
    DEFAULT_MESSAGE: str = "Embedded Database Crashed."

    def __init__(self, message: str = DEFAULT_MESSAGE, cause: BaseException = None):
        super().__init__(message=message, cause=cause)

class EmbeddedDatabaseResourceExhaustionException(EmbeddedDatabaseException):
    """
    This exception is thrown when the embedded database stops due to resource exhaustion (e.g., memory, disk space) during runtime.
    """
    ERROR_NAME: str = "EmbeddedDatabaseResourceExhaustionException"
    DEFAULT_MESSAGE: str = "Embedded Database Resource Exhaustion."

    def __init__(self, message: str = DEFAULT_MESSAGE, cause: BaseException = None):
        super().__init__(message=message, cause=cause)

class EmbeddedDatabaseMemoryExhaustionException(EmbeddedDatabaseResourceExhaustionException):
    """
    This exception is thrown when the embedded database stops due to memory exhaustion during runtime.
    """
    ERROR_NAME: str = "EmbeddedDatabaseMemoryExhaustionException"
    DEFAULT_MESSAGE: str = "Embedded Database Memory Exhaustion."

    def __init__(self, message: str = DEFAULT_MESSAGE, cause: BaseException = None):
        super().__init__(message=message, cause=cause)

class EmbeddedDatabaseDiskSpaceExhaustionException(EmbeddedDatabaseResourceExhaustionException):
    """
    This exception is thrown when the embedded database stops due to disk space exhaustion during runtime.
    """
    ERROR_NAME: str = "EmbeddedDatabaseDiskSpaceExhaustionException"
    DEFAULT_MESSAGE: str = "Embedded Database Disk Space Exhaustion."

    def __init__(self, message: str = DEFAULT_MESSAGE, cause: BaseException = None):
        super().__init__(message=message, cause=cause)
