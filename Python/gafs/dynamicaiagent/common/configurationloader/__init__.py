"""
gafs.dynamicaiagent.common.configurationloader

Provides ConfigurationLoader for loading and merging JSON configuration files
from multiple OS-standard locations.
"""

from .i_configuration_loader import IConfigurationLoader
from .configuration_loader import ConfigurationLoader
from .exceptions import (
    ConfigurationLoaderException,
    ConfigurationLoaderFileNotExistException,
    ConfigurationLoaderInvalidConfigurationException,
)

__all__ = [
    "IConfigurationLoader",
    "ConfigurationLoader",
    "ConfigurationLoaderException",
    "ConfigurationLoaderFileNotExistException",
    "ConfigurationLoaderInvalidConfigurationException",
]
