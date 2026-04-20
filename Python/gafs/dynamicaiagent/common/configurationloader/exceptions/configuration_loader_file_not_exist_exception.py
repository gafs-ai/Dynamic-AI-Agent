"""
configuration_loader_file_not_exist_exception.py - Exception for missing configuration files.

Raised when a required configuration file cannot be found on the file system.
"""

from __future__ import annotations

from typing import Any

from .configuration_loader_exception import ConfigurationLoaderException


class ConfigurationLoaderFileNotExistException(ConfigurationLoaderException):
    """Raised when a required configuration file does not exist.

    This exception is raised in two situations:
    - The default configuration file (in the program folder) does not exist.
    - A configuration file specified via ``config_file_path`` does not exist.

    Attributes:
        details["file_path"]: Path of the configuration file that was not found.
    """

    ERROR_NAME: str = "ConfigurationLoaderFileNotExistException"
    DEFAULT_MESSAGE: str = "Required configuration file does not exist"

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        file_path: str = "",
        cause: BaseException | None = None,
    ) -> None:
        """Initialize ConfigurationLoaderFileNotExistException.

        Args:
            message: Human-readable description of the error.
                Defaults to ``DEFAULT_MESSAGE``.
            file_path: Absolute path of the configuration file that was not found.
            cause: The original exception that triggered this one, if any.
        """
        # Pre-populate the details dict with the file path so it is available
        # in the structured details even before the base class adds its fields.
        details: dict[str, Any] = {"file_path": file_path}
        super().__init__(message=message, details=details, cause=cause)
