"""
i_configuration_loader.py - Abstract base class for ConfigurationLoader.

Defines the public interface and shared constants for all ConfigurationLoader
implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .exceptions import (
    ConfigurationLoaderFileNotExistException,
    ConfigurationLoaderInvalidConfigurationException,
)


class IConfigurationLoader(ABC):
    """Abstract base class for ConfigurationLoader.

    Defines the contract that all ConfigurationLoader implementations must
    satisfy, including the shared constants for the application name, author,
    and configuration file name.

    Constants:
        APPLICATION_NAME: Name of the Dynamic-AI-Agent application.
        APPLICATION_AUTHOR: Author / publisher identifier of the application.
        CONFIGURATION_FILE_NAME: Standard file name used for all configuration
            files across different search locations.
    """

    APPLICATION_NAME: str = "Dynamic-AI-Agent"
    """Name of the application, used to locate OS-specific data directories."""

    APPLICATION_AUTHOR: str = "GAFS"
    """Author identifier used alongside APPLICATION_NAME for OS data directories."""

    CONFIGURATION_FILE_NAME: str = "dynamic_ai_agent_config.json"
    """Standard JSON configuration file name searched in all locations."""

    @abstractmethod
    def load_configurations(self, config_file_path: str | None) -> dict[str, Any]:
        """Load configuration files and merge them into a single dictionary.

        Searches configuration files in ascending priority order and merges them
        so that higher-priority files overwrite duplicated keys from lower-priority
        ones, while non-duplicated keys from all files are preserved.

        Priority order (lowest to highest):
        1. Default configuration file (required, located in the program folder)
        2. Configuration file in the application data folder (optional)
        3. Configuration file in the user home folder (optional)
        4. Configuration file at ``config_file_path`` (optional; required if given)

        Args:
            config_file_path: Path of a configuration file specified as a launch
                option (e.g. ``--config "/path/to/config.json"``).
                Pass ``None`` if no explicit path was provided.

        Returns:
            A merged dictionary containing all configuration keys, with
            higher-priority values overwriting lower-priority ones.

        Raises:
            ConfigurationLoaderFileNotExistException: A required configuration file
                does not exist (default file or the explicitly given path).
            ConfigurationLoaderInvalidConfigurationException: A configuration file
                exists but its content is not a valid JSON dictionary.
        """
        ...
