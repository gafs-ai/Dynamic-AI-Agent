"""secret_manager_secret_not_found_exception.py - Raised when a Secret record is not found."""

from typing import Any

from .secret_manager_exception import SecretManagerException


class SecretManagerSecretNotFoundException(SecretManagerException):
    """Raised when no matching ``Secret`` entry is found for the given id.

    Raised by ``update_secret`` and ``delete_secret`` when the target record
    does not exist in the database.
    """

    ERROR_NAME: str = "SecretManagerSecretNotFoundException"
    DEFAULT_MESSAGE: str = "Secret not found."

    def __init__(
        self,
        message: str = "Secret not found.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
