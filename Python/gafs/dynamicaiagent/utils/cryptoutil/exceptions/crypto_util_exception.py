from __future__ import annotations


class CryptoUtilException(Exception):
    """Base exception class for all errors raised by the CryptoUtil component.

    Attributes:
        message: Human-readable error description.
    """

    DEFAULT_MESSAGE: str = "Unexpected Error in Crypto Util."

    def __init__(self, message: str = DEFAULT_MESSAGE) -> None:
        """Initialize CryptoUtilException.

        Args:
            message: Human-readable error description.
                     Defaults to "Unexpected Error in Crypto Util.".
        """
        super().__init__(message)
        # Store the message as an attribute for easy access by callers.
        self.message = message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r})"
