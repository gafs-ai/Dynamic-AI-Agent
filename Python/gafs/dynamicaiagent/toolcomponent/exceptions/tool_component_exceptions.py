"""tool_component_exceptions.py - Concrete Tool Component exception types, grouped by category.

Exception hierarchy (from tool_component_exception.md):

    ToolComponentException
    ├── ToolComponentConfigurationException
    │   ├── ToolComponentInitializationException
    │   ├── ToolComponentNotInitializedException
    │   └── InvalidToolComponentConfigurationException
    ├── ToolComponentValidationException
    │   ├── InvalidToolCatalogueEntryException
    │   ├── InvalidToolCatalogueSearchCriteriaException
    │   ├── InvalidToolVersionEntryException
    │   ├── InvalidToolVersionSearchCriteriaException
    │   ├── InvalidSandboxCatalogueEntryException
    │   ├── InvalidSandboxCatalogueSearchCriteriaException
    │   └── InvalidToolInvocationException
    ├── ToolComponentConflictException
    │   ├── ConflictingToolCatalogueEntryException
    │   ├── ConflictingToolVersionEntryException
    │   └── ConflictingSandboxCatalogueEntryException
    ├── ToolComponentResourceNotFoundException
    │   ├── ToolCatalogueEntryNotFoundException
    │   ├── ToolVersionEntryNotFoundException
    │   └── SandboxCatalogueEntryNotFoundException
    └── ToolComponentOperationException
        ├── ToolCatalogueIndexNotAvailableException
        └── FullTextAnalyzerNotExistException
"""

from __future__ import annotations

from .tool_component_exception import ToolComponentException


# ---------------------------------------------------------------------------
# Configuration exceptions
# ---------------------------------------------------------------------------

class ToolComponentConfigurationException(ToolComponentException):
    """Base exception for initialization and configuration failures."""

    ERROR_NAME: str = "ToolComponentConfigurationException"
    DEFAULT_MESSAGE: str = "Invalid ToolComponent configuration."


class ToolComponentInitializationException(ToolComponentConfigurationException):
    """Raised when the tool component fails to initialize."""

    ERROR_NAME: str = "ToolComponentInitializationException"
    DEFAULT_MESSAGE: str = "ToolComponent initialization failed."


class ToolComponentNotInitializedException(ToolComponentConfigurationException):
    """Raised when a method is called before the component is initialized."""

    ERROR_NAME: str = "ToolComponentNotInitializedException"
    DEFAULT_MESSAGE: str = "ToolComponent is not initialized."


class InvalidToolComponentConfigurationException(ToolComponentConfigurationException):
    """Raised when the stored ToolComponentConfigurations entry is invalid."""

    ERROR_NAME: str = "InvalidToolComponentConfigurationException"
    DEFAULT_MESSAGE: str = "ToolComponentConfigurations entry is invalid."


# ---------------------------------------------------------------------------
# Validation exceptions
# ---------------------------------------------------------------------------

class ToolComponentValidationException(ToolComponentException):
    """Base exception for input validation failures."""

    ERROR_NAME: str = "ToolComponentValidationException"
    DEFAULT_MESSAGE: str = "Tool component input validation failed."


class InvalidToolCatalogueEntryException(ToolComponentValidationException):
    """Raised when a ToolCatalogueEntry fails validation."""

    ERROR_NAME: str = "InvalidToolCatalogueEntryException"
    DEFAULT_MESSAGE: str = "Invalid ToolCatalogueEntry."


class InvalidToolCatalogueSearchCriteriaException(ToolComponentValidationException):
    """Raised when search criteria for the tool catalogue are invalid."""

    ERROR_NAME: str = "InvalidToolCatalogueSearchCriteriaException"
    DEFAULT_MESSAGE: str = "Invalid tool catalogue search criteria."


class InvalidToolVersionEntryException(ToolComponentValidationException):
    """Raised when a ToolVersionEntry fails validation."""

    ERROR_NAME: str = "InvalidToolVersionEntryException"
    DEFAULT_MESSAGE: str = "Invalid ToolVersionEntry."


class InvalidToolVersionSearchCriteriaException(ToolComponentValidationException):
    """Raised when search criteria for tool versions are invalid."""

    ERROR_NAME: str = "InvalidToolVersionSearchCriteriaException"
    DEFAULT_MESSAGE: str = "Invalid tool version search criteria."


class InvalidSandboxCatalogueEntryException(ToolComponentValidationException):
    """Raised when a SandboxCatalogueEntry fails validation."""

    ERROR_NAME: str = "InvalidSandboxCatalogueEntryException"
    DEFAULT_MESSAGE: str = "Invalid SandboxCatalogueEntry."


class InvalidSandboxCatalogueSearchCriteriaException(ToolComponentValidationException):
    """Raised when search criteria for the sandbox catalogue are invalid."""

    ERROR_NAME: str = "InvalidSandboxCatalogueSearchCriteriaException"
    DEFAULT_MESSAGE: str = "Invalid sandbox catalogue search criteria."


class InvalidToolInvocationException(ToolComponentValidationException):
    """Raised when tool invocation parameters fail validation."""

    ERROR_NAME: str = "InvalidToolInvocationException"
    DEFAULT_MESSAGE: str = "Invalid tool invocation parameters."


# ---------------------------------------------------------------------------
# Conflict exceptions
# ---------------------------------------------------------------------------

class ToolComponentConflictException(ToolComponentException):
    """Base exception for resource conflicts."""

    ERROR_NAME: str = "ToolComponentConflictException"
    DEFAULT_MESSAGE: str = "Tool component resource conflict."


class ConflictingToolCatalogueEntryException(ToolComponentConflictException):
    """Raised when a tool catalogue entry conflicts with an existing record (e.g. duplicate name)."""

    ERROR_NAME: str = "ConflictingToolCatalogueEntryException"
    DEFAULT_MESSAGE: str = "Conflicting ToolCatalogueEntry (duplicate name)."


class ConflictingToolVersionEntryException(ToolComponentConflictException):
    """Raised when a tool version entry conflicts with an existing record."""

    ERROR_NAME: str = "ConflictingToolVersionEntryException"
    DEFAULT_MESSAGE: str = "Conflicting ToolVersionEntry."


class ConflictingSandboxCatalogueEntryException(ToolComponentConflictException):
    """Raised when a sandbox catalogue entry conflicts with an existing record (e.g. duplicate name)."""

    ERROR_NAME: str = "ConflictingSandboxCatalogueEntryException"
    DEFAULT_MESSAGE: str = "Conflicting SandboxCatalogueEntry (duplicate name)."


# ---------------------------------------------------------------------------
# Resource not found exceptions
# ---------------------------------------------------------------------------

class ToolComponentResourceNotFoundException(ToolComponentException):
    """Base exception for resource-not-found errors."""

    ERROR_NAME: str = "ToolComponentResourceNotFoundException"
    DEFAULT_MESSAGE: str = "Tool component resource not found."


class ToolCatalogueEntryNotFoundException(ToolComponentResourceNotFoundException):
    """Raised when a requested ToolCatalogueEntry does not exist."""

    ERROR_NAME: str = "ToolCatalogueEntryNotFoundException"
    DEFAULT_MESSAGE: str = "ToolCatalogueEntry not found."


class ToolVersionEntryNotFoundException(ToolComponentResourceNotFoundException):
    """Raised when a requested ToolVersionEntry does not exist."""

    ERROR_NAME: str = "ToolVersionEntryNotFoundException"
    DEFAULT_MESSAGE: str = "ToolVersionEntry not found."


class SandboxCatalogueEntryNotFoundException(ToolComponentResourceNotFoundException):
    """Raised when a requested SandboxCatalogueEntry does not exist."""

    ERROR_NAME: str = "SandboxCatalogueEntryNotFoundException"
    DEFAULT_MESSAGE: str = "SandboxCatalogueEntry not found."


# ---------------------------------------------------------------------------
# Operation exceptions
# ---------------------------------------------------------------------------

class ToolComponentOperationException(ToolComponentException):
    """Raised when a database or operational failure occurs."""

    ERROR_NAME: str = "ToolComponentOperationException"
    DEFAULT_MESSAGE: str = "Tool component operation failed."


class ToolCatalogueIndexNotAvailableException(ToolComponentOperationException):
    """Raised when the tool catalogue vector index is not available (rebuilding)."""

    ERROR_NAME: str = "ToolCatalogueIndexNotAvailableException"
    DEFAULT_MESSAGE: str = "Tool catalogue index is not currently available."


class FullTextAnalyzerNotExistException(ToolComponentOperationException):
    """Raised when a referenced full-text analyzer does not exist in the database."""

    ERROR_NAME: str = "FullTextAnalyzerNotExistException"
    DEFAULT_MESSAGE: str = "The referenced full-text analyzer does not exist."
