"""
configuration_loader_exception.py - Base exception class for the ConfigurationLoader component.

All exceptions raised within the ConfigurationLoader should extend ConfigurationLoaderException
so that error context is consistently captured and the component origin is clearly identified.
"""

from __future__ import annotations

from gafs.dynamicaiagent.common.exceptions import ApplicationException


class ConfigurationLoaderException(ApplicationException):
    """Base exception for all errors raised by the ConfigurationLoader component.

    All ConfigurationLoader-specific exceptions extend this class so that
    callers can catch them at a coarse-grained level if needed.

    Class Attributes:
        ERROR_NAME: Identifies this exception type in string representations.
        DEFAULT_MESSAGE: Fallback message when no message is supplied.
        COMPONENT_NAME: Human-readable name of the component that owns these exceptions.
        DEFAULT_COMPONENT_NAME: Overrides the base class default so that the
            ``component`` field in ``details`` is always set to ``"ConfigurationLoader"``.
    """

    ERROR_NAME: str = "ConfigurationLoaderException"
    DEFAULT_MESSAGE: str = "Unexpected Error in Configuration Loader"

    # Override the base class component name to identify this component.
    COMPONENT_NAME: str = "ConfigurationLoader"
    DEFAULT_COMPONENT_NAME: str = "ConfigurationLoader"
