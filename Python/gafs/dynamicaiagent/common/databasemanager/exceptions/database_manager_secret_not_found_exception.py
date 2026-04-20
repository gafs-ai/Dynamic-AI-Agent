"""database_manager_secret_not_found_exception.py - Raised when a referenced secret is not found."""

from typing import Any
from .database_manager_exception import DatabaseManagerException


class DatabaseManagerSecretNotFoundException(DatabaseManagerException):
    """Raised when a Secret referenced by a DatabaseConnection entry does not exist.

    This is raised when a caller provides a secret id that does not correspond
    to an existing Secret record in the SecretManager.
    """

    ERROR_NAME: str = "DatabaseManagerSecretNotFoundException"
    DEFAULT_MESSAGE: str = "Secret referenced by DatabaseConnection not found."

    @staticmethod
    def ERROR_NAME_STATIC() -> str:
        """Return the error name constant."""
        return "DatabaseManagerSecretNotFoundException"

    @staticmethod
    def DEFAULT_MESSAGE_STATIC() -> str:
        """Return the default message constant."""
        return "Secret referenced by DatabaseConnection not found."

    def __init__(
        self,
        message: str = "Secret referenced by DatabaseConnection not found.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
