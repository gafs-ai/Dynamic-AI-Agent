"""
configuration_loader.py - Concrete implementation of IConfigurationLoader.

Loads JSON configuration files from multiple locations (program folder,
OS application-data folder, user home folder, and an optional explicit path)
and merges them in priority order into a single dictionary.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import platformdirs

from .exceptions import (
    ConfigurationLoaderFileNotExistException,
    ConfigurationLoaderInvalidConfigurationException,
)
from .i_configuration_loader import IConfigurationLoader


class ConfigurationLoader(IConfigurationLoader):
    """Concrete implementation of IConfigurationLoader.

    Locates and merges configuration files from up to four locations in
    ascending priority order.  Each location is searched for a file named
    ``CONFIGURATION_FILE_NAME``:

    1. **Program folder** – the folder that contains this module (required).
    2. **Application data folder** – OS-specific per-application data directory
       (optional; skipped when the file is absent).
    3. **User home folder** – the user's home directory (optional; skipped when
       the file is absent).
    4. **Explicit path** – a path provided by the caller (optional; required if
       not ``None``).

    NOTE: The constructor accepts optional folder overrides (``program_folder``,
    ``app_data_folder``, ``user_home_folder``) to facilitate unit testing without
    needing to touch real OS directories or use mocking frameworks.
    """

    def __init__(
        self,
        program_folder: Path | None = None,
        app_data_folder: Path | None = None,
        user_home_folder: Path | None = None,
    ) -> None:
        """Initialize ConfigurationLoader.

        Args:
            program_folder: Override for the program folder path.
                When ``None`` (default), the folder containing this module file
                is used.  Provide a value in tests to avoid touching the real
                source tree.
            app_data_folder: Override for the OS application-data folder.
                When ``None`` (default), ``platformdirs.user_data_dir`` is used.
                Provide a value in tests to avoid touching the real OS data
                directory.
            user_home_folder: Override for the user home folder.
                When ``None`` (default), ``Path.home()`` is used.  Provide a
                value in tests to avoid touching the real home directory.
        """
        # Store optional overrides; None means "use the real OS path".
        self._program_folder: Path | None = program_folder
        self._app_data_folder: Path | None = app_data_folder
        self._user_home_folder: Path | None = user_home_folder

    # ------------------------------------------------------------------
    # Private helpers – folder resolution
    # ------------------------------------------------------------------

    def _get_application_program_folder(self) -> Path:
        """Return the folder that contains the Dynamic-AI-Agent program files.

        Returns:
            Path of the directory containing this module (or a test override).
        """
        if self._program_folder is not None:
            # Use the injected override (used in tests).
            return self._program_folder
        # In normal operation, use the directory of this source file.
        # For a Nuitka-compiled module this resolves to the folder that
        # contains the compiled .pyd / .so artifact.
        return Path(__file__).parent

    def _get_application_data_folder(self) -> Path:
        """Return the OS-specific application data folder.

        The path follows OS conventions via the ``platformdirs`` library:
        - Windows : ``%APPDATA%\\GAFS\\Dynamic-AI-Agent``
        - Linux   : ``~/.local/share/Dynamic-AI-Agent``
        - macOS   : ``~/Library/Application Support/Dynamic-AI-Agent``

        Returns:
            Path to the application data directory.
        """
        if self._app_data_folder is not None:
            # Use the injected override (used in tests).
            return self._app_data_folder
        # roaming=True selects the roaming AppData folder on Windows (%APPDATA%).
        return Path(
            platformdirs.user_data_dir(
                self.APPLICATION_NAME,
                self.APPLICATION_AUTHOR,
                roaming=True,
            )
        )

    def _get_user_home_folder(self) -> Path:
        """Return the user's home directory.

        Returns:
            Path to the user's home directory (e.g. ``C:\\Users\\<name>`` on
            Windows or ``/home/<name>`` on Linux / macOS).
        """
        if self._user_home_folder is not None:
            # Use the injected override (used in tests).
            return self._user_home_folder
        # Path.home() is the standard library way to obtain the home directory
        # on all supported platforms.
        return Path.home()

    # ------------------------------------------------------------------
    # Private helper – JSON file loading
    # ------------------------------------------------------------------

    def _load_json_dict(self, path: Path) -> dict[str, Any]:
        """Read a JSON file and return its content as a dictionary.

        Args:
            path: Absolute path to the JSON configuration file to load.

        Returns:
            Parsed content of the file as a ``dict[str, Any]``.

        Raises:
            ConfigurationLoaderFileNotExistException: The file cannot be read
                (e.g. a permission error or unexpected I/O failure).
            ConfigurationLoaderInvalidConfigurationException: The file content
                is not valid JSON, or the top-level JSON value is not a dict.
        """
        # --- Step 1: Read the raw file content ---
        try:
            content: str = path.read_text(encoding="utf-8")
        except Exception as e:
            # Any I/O failure while reading an existing file is treated as a
            # "file not accessible" condition.
            raise ConfigurationLoaderFileNotExistException(
                file_path=str(path),
                cause=e,
            ) from e

        # --- Step 2: Parse the content as JSON ---
        try:
            data: Any = json.loads(content)
        except json.JSONDecodeError as e:
            raise ConfigurationLoaderInvalidConfigurationException(
                file_path=str(path),
                cause=e,
            ) from e

        # --- Step 3: Validate that the top-level value is a dictionary ---
        if not isinstance(data, dict):
            raise ConfigurationLoaderInvalidConfigurationException(
                message=(
                    f"Configuration file is not a JSON object (got "
                    f"{type(data).__name__}): {path}"
                ),
                file_path=str(path),
            )

        return data

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def load_configurations(self, config_file_path: str | None) -> dict[str, Any]:
        """Load configuration files and merge them into a single dictionary.

        Searches configuration files in ascending priority order and merges them
        so that higher-priority files overwrite duplicated keys.  Non-duplicated
        keys from all files are preserved.

        Priority order (lowest → highest):
        1. Default configuration file in the program folder (required)
        2. Configuration file in the application data folder (optional)
        3. Configuration file in the user home folder (optional)
        4. Configuration file at ``config_file_path`` (optional but required if given)

        Args:
            config_file_path: Path of a configuration file specified as a launch
                option.  Pass ``None`` when no explicit path was given.

        Returns:
            A merged ``dict[str, Any]`` containing all configuration keys.

        Raises:
            ConfigurationLoaderFileNotExistException: A required configuration
                file does not exist (default file or the explicitly given path).
            ConfigurationLoaderInvalidConfigurationException: A configuration
                file exists but its content is not a valid JSON dictionary.
        """
        # Accumulate merged configuration here.  Higher-priority updates are
        # applied via dict.update(), which overwrites duplicate keys and adds
        # new ones without removing keys unique to the lower-priority dict.
        result: dict[str, Any] = {}

        # --- 1. Default configuration file (required) ---
        default_path: Path = (
            self._get_application_program_folder() / self.CONFIGURATION_FILE_NAME
        )
        if not default_path.exists():
            # The default config is mandatory; raise immediately if missing.
            raise ConfigurationLoaderFileNotExistException(
                file_path=str(default_path),
            )
        # Load and use as the base configuration.
        result = self._load_json_dict(default_path)

        # --- 2. Application data folder configuration (optional) ---
        app_data_path: Path = (
            self._get_application_data_folder() / self.CONFIGURATION_FILE_NAME
        )
        if app_data_path.exists():
            # Merge: app_data values overwrite matching keys from the default.
            app_data_config: dict[str, Any] = self._load_json_dict(app_data_path)
            result.update(app_data_config)

        # --- 3. User home folder configuration (optional) ---
        home_path: Path = (
            self._get_user_home_folder() / self.CONFIGURATION_FILE_NAME
        )
        if home_path.exists():
            # Merge: home-folder values overwrite matching keys from app_data.
            home_config: dict[str, Any] = self._load_json_dict(home_path)
            result.update(home_config)

        # --- 4. Explicitly specified configuration file (required if given) ---
        if config_file_path is not None:
            custom_path: Path = Path(config_file_path)
            if not custom_path.exists():
                # An explicit path that does not exist is treated as an error.
                raise ConfigurationLoaderFileNotExistException(
                    file_path=str(custom_path),
                )
            # Merge: custom values have the highest priority.
            custom_config: dict[str, Any] = self._load_json_dict(custom_path)
            result.update(custom_config)

        return result
