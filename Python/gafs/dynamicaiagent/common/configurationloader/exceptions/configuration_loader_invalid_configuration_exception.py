"""
configuration_loader_invalid_configuration_exception.py - Exception for invalid config content.

Raised when a configuration file exists but its content is not a valid JSON dictionary.
"""

from __future__ import annotations

from typing import Any

from .configuration_loader_exception import ConfigurationLoaderException


class ConfigurationLoaderInvalidConfigurationException(ConfigurationLoaderException):
    """Raised when a configuration file contains content that is not a valid JSON dictionary.

    ConfigurationLoader only validates that the file is parseable JSON and that
    the top-level value is a dictionary. Validation of component-specific keys
    is the responsibility of each consuming component.

    Attributes:
        details["file_path"]: Path of the configuration file with invalid content.
    """

    ERROR_NAME: str = "ConfigurationLoaderInvalidConfigurationException"
    DEFAULT_MESSAGE: str = "Invalid configuration file"

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        file_path: str = "",
        cause: BaseException | None = None,
    ) -> None:
        """Initialize ConfigurationLoaderInvalidConfigurationException.

        Args:
            message: Human-readable description of the error.
                Defaults to ``DEFAULT_MESSAGE``.
            file_path: Absolute path of the configuration file with invalid content.
            cause: The original exception that triggered this one, if any.
        """
        # Pre-populate the details dict with the file path before the base
        # class auto-fills the remaining standard fields.
        details: dict[str, Any] = {"file_path": file_path}
        super().__init__(message=message, details=details, cause=cause)
