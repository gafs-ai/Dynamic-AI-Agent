"""secret_manager_invalid_secret_entry_exception.py - Raised for invalid Secret or key entries."""

from typing import Any

from .secret_manager_exception import SecretManagerException


class SecretManagerInvalidSecretEntryException(SecretManagerException):
    """Raised when a Secret entry or key registration attempt is invalid.

    Typical causes:
        - ``create_secret`` / ``update_secret`` called with missing required fields.
        - ``add_key`` called for a crypto type that already has a registered key.
    """

    ERROR_NAME: str = "SecretManagerInvalidSecretEntryException"
    DEFAULT_MESSAGE: str = "Invalid Secret entry."

    def __init__(
        self,
        message: str = "Invalid Secret entry.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
