"""secret_manager_key_not_found_exception.py - Raised when a key for a CryptoType is not registered."""

from typing import Any

from .secret_manager_exception import SecretManagerException


class SecretManagerKeyNotFoundException(SecretManagerException):
    """Raised when no key is registered for the requested ``CryptoType``.

    Callers must ensure a key has been registered via ``add_key`` or generated
    via ``generate_key`` before calling operations that require encryption/decryption.
    """

    ERROR_NAME: str = "SecretManagerKeyNotFoundException"
    DEFAULT_MESSAGE: str = "Key not found for the specified crypto type."

    def __init__(
        self,
        message: str = "Key not found for the specified crypto type.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
