from typing import Any
from . import DatabaseProviderException

class DatabaseOperationException(DatabaseProviderException):
    """Base exception for errors that occur during database query or operation execution."""

    ERROR_NAME: str = "DatabaseOperationException"
    DEFAULT_MESSAGE: str = "Failed to execute Database Operation."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

# ------------ Operation Permission and Support ------------

class UnpermittedDatabaseOperationException(DatabaseOperationException):
    """
    This exception is thrown when the database operation is not permitted.
    """
    ERROR_NAME: str = "UnpermittedDatabaseOperationException"
    DEFAULT_MESSAGE: str = "Unpermitted Database Operation."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

class UnsupportedDatabaseOperationException(DatabaseOperationException):
    """
    This exception is thrown when the database operation is not supported.
    """
    ERROR_NAME: str = "UnsupportedDatabaseOperationException"
    DEFAULT_MESSAGE: str = "Unsupported Database Operation."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

# ------------ Query Related ------------

class MalformedDatabaseQueryException(DatabaseOperationException):
    """
    This exception is thrown when the database query is malformed.
    This means the validation failure of the query, and the query is not sent to the database.
    """
    ERROR_NAME: str = "MalformedDatabaseQueryException"
    DEFAULT_MESSAGE: str = "Malformed Database Query."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

class DatabaseQueryErrorException(DatabaseOperationException):
    """
    This exception is thrown when the database query returns an error.
    """
    ERROR_NAME: str = "DatabaseQueryErrorException"
    DEFAULT_MESSAGE: str = "Database Query Error."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

class DatabaseQueryTimeoutException(DatabaseOperationException):
    """
    This exception is thrown when the database query times out.
    """
    ERROR_NAME: str = "DatabaseQueryTimeoutException"
    DEFAULT_MESSAGE: str = "Database Query Timeout."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

# ------------ Connection Related ------------

class DatabaseDisconnectedException(DatabaseOperationException):
    """
    This exception is thrown when the database unreachable and the operation cannot be executed.
    """
    ERROR_NAME: str = "DatabaseDisconnectedException"
    DEFAULT_MESSAGE: str = "Database Disconnected."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

class DatabaseConnectionLimitExceededException(DatabaseOperationException):
    """
    This exception is thrown when the database connection limit is exceeded.
    """
    ERROR_NAME: str = "DatabaseConnectionLimitExceededException"
    DEFAULT_MESSAGE: str = "Database Connection Limit Exceeded."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

# ------------ Record Operation Related ------------

class DatabaseRecordNotFoundException(DatabaseOperationException):
    """
    This exception is thrown when the requested record is not found in the database.
    """
    ERROR_NAME: str = "DatabaseRecordNotFoundException"
    DEFAULT_MESSAGE: str = "Database Record Not Found."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

class DatabaseRecordAlreadyExistsException(DatabaseOperationException):
    """
    This exception is thrown when attempting to create a record that already exists.
    """
    ERROR_NAME: str = "DatabaseRecordAlreadyExistsException"
    DEFAULT_MESSAGE: str = "Database Record Already Exists."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

class DatabaseConstraintViolationException(DatabaseOperationException):
    """
    This exception is thrown when a database constraint is violated (e.g., unique constraint, foreign key constraint).
    """
    ERROR_NAME: str = "DatabaseConstraintViolationException"
    DEFAULT_MESSAGE: str = "Database Constraint Violation."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

# ------------ Transaction Related ------------

class DatabaseTransactionException(DatabaseOperationException):
    """
    This exception is thrown when a database transaction fails.
    """
    ERROR_NAME: str = "DatabaseTransactionException"
    DEFAULT_MESSAGE: str = "Database Transaction Error."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)

class DatabaseDeadlockException(DatabaseOperationException):
    """
    This exception is thrown when a database deadlock is detected.
    """
    ERROR_NAME: str = "DatabaseDeadlockException"
    DEFAULT_MESSAGE: str = "Database Deadlock Detected."

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message=message, details=details, cause=cause)
