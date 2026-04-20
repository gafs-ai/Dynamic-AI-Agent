"""secret_manager_crypto_exception.py - Raised when a cryptographic operation fails."""

from typing import Any

from .secret_manager_exception import SecretManagerException


class SecretManagerCryptoException(SecretManagerException):
    """Raised when encryption or decryption of a secret value fails.

    This exception wraps errors from ``CryptoUtil`` during encrypt/decrypt calls
    inside SecretManager operations.
    """

    ERROR_NAME: str = "SecretManagerCryptoException"
    DEFAULT_MESSAGE: str = "A cryptographic operation in Secret Manager failed."

    def __init__(
        self,
        message: str = "A cryptographic operation in Secret Manager failed.",
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message=message, details=details, cause=cause)
