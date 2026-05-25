"""Concrete Model Component exception types, grouped by error category.

Exception hierarchy (from model_component_exception.md):

    ModelComponentException
    ├── ModelComponentConfigurationException
    │   ├── ModelComponentInitializationException
    │   ├── ModelComponentNotInitializedException
    │   └── InvalidModelComponentConfigurationException
    ├── ModelComponentValidationException
    │   ├── InvalidModelCatalogueEntryException
    │   ├── InvalidModelCatalogueSearchCriteriaException
    │   ├── InvalidModelDeploymentException
    │   ├── InvalidModelDeploymentSearchCriteriaException
    │   └── InvalidAiRequestException
    ├── ModelComponentConflictException
    │   ├── ConflictingModelCatalogueEntryException
    │   └── ConflictingModelDeploymentException
    ├── ModelComponentResourceNotFoundException
    │   ├── ModelCatalogueEntryNotFoundException
    │   └── ModelDeploymentNotFoundException
    └── ModelComponentOperationException
        ├── ModelCatalogueIndexNotAvailableException
        └── FullTextAnalyzerNotExistException
"""

from __future__ import annotations

from .model_component_exception import ModelComponentException


# ---------------------------------------------------------------------------
# Configuration exceptions
# ---------------------------------------------------------------------------

class ModelComponentConfigurationException(ModelComponentException):
    """Base exception for initialization and configuration failures."""

    ERROR_NAME: str = "ModelComponentConfigurationException"
    DEFAULT_MESSAGE: str = "Invalid ModelComponent configuration."


class ModelComponentInitializationException(ModelComponentConfigurationException):
    """Raised when the model component fails to initialize."""

    ERROR_NAME: str = "ModelComponentInitializationException"
    DEFAULT_MESSAGE: str = "ModelComponent initialization failed."


class ModelComponentNotInitializedException(ModelComponentConfigurationException):
    """Raised when a method is called before the component is initialized."""

    ERROR_NAME: str = "ModelComponentNotInitializedException"
    DEFAULT_MESSAGE: str = "ModelComponent is not initialized."


class InvalidModelComponentConfigurationException(ModelComponentConfigurationException):
    """Raised when the stored ModelComponentConfigurations entry is invalid."""

    ERROR_NAME: str = "InvalidModelComponentConfigurationException"
    DEFAULT_MESSAGE: str = "ModelComponentConfigurations entry is invalid."


# ---------------------------------------------------------------------------
# Validation exceptions
# ---------------------------------------------------------------------------

class ModelComponentValidationException(ModelComponentException):
    """Base exception for input validation failures."""

    ERROR_NAME: str = "ModelComponentValidationException"
    DEFAULT_MESSAGE: str = "Model component input validation failed."


class InvalidModelCatalogueEntryException(ModelComponentValidationException):
    """Raised when a ModelCatalogueEntry fails validation."""

    ERROR_NAME: str = "InvalidModelCatalogueEntryException"
    DEFAULT_MESSAGE: str = "Invalid ModelCatalogueEntry."


class InvalidModelCatalogueSearchCriteriaException(ModelComponentValidationException):
    """Raised when search criteria for the catalogue are invalid."""

    ERROR_NAME: str = "InvalidModelCatalogueSearchCriteriaException"
    DEFAULT_MESSAGE: str = "Invalid model catalogue search criteria."


class InvalidModelDeploymentException(ModelComponentValidationException):
    """Raised when a ModelDeployment entry fails validation."""

    ERROR_NAME: str = "InvalidModelDeploymentException"
    DEFAULT_MESSAGE: str = "Invalid ModelDeployment entry."


class InvalidModelDeploymentSearchCriteriaException(ModelComponentValidationException):
    """Raised when search criteria for deployments are invalid."""

    ERROR_NAME: str = "InvalidModelDeploymentSearchCriteriaException"
    DEFAULT_MESSAGE: str = "Invalid model deployment search criteria."


class InvalidAiRequestException(ModelComponentValidationException):
    """Raised when an AiRequest or its parameters fail validation."""

    ERROR_NAME: str = "InvalidAiRequestException"
    DEFAULT_MESSAGE: str = "Invalid AiRequest."


# ---------------------------------------------------------------------------
# Conflict exceptions
# ---------------------------------------------------------------------------

class ModelComponentConflictException(ModelComponentException):
    """Base exception for resource conflicts."""

    ERROR_NAME: str = "ModelComponentConflictException"
    DEFAULT_MESSAGE: str = "Model component resource conflict."


class ConflictingModelCatalogueEntryException(ModelComponentConflictException):
    """Raised when a catalogue entry conflicts with an existing record (e.g. duplicate id)."""

    ERROR_NAME: str = "ConflictingModelCatalogueEntryException"
    DEFAULT_MESSAGE: str = "Conflicting ModelCatalogueEntry (duplicate id or name)."


class ConflictingModelDeploymentException(ModelComponentConflictException):
    """Raised when a deployment entry conflicts with an existing record."""

    ERROR_NAME: str = "ConflictingModelDeploymentException"
    DEFAULT_MESSAGE: str = "Conflicting ModelDeployment entry (duplicate id or name)."


# ---------------------------------------------------------------------------
# Resource not found exceptions
# ---------------------------------------------------------------------------

class ModelComponentResourceNotFoundException(ModelComponentException):
    """Base exception for resource-not-found errors."""

    ERROR_NAME: str = "ModelComponentResourceNotFoundException"
    DEFAULT_MESSAGE: str = "Model component resource not found."


class ModelCatalogueEntryNotFoundException(ModelComponentResourceNotFoundException):
    """Raised when a requested ModelCatalogueEntry does not exist."""

    ERROR_NAME: str = "ModelCatalogueEntryNotFoundException"
    DEFAULT_MESSAGE: str = "ModelCatalogueEntry not found."


class ModelDeploymentNotFoundException(ModelComponentResourceNotFoundException):
    """Raised when a requested ModelDeployment does not exist."""

    ERROR_NAME: str = "ModelDeploymentNotFoundException"
    DEFAULT_MESSAGE: str = "ModelDeployment not found."


# ---------------------------------------------------------------------------
# Operational exceptions
# ---------------------------------------------------------------------------

class ModelComponentOperationException(ModelComponentException):
    """Base exception for operation failures (database, service, runtime)."""

    ERROR_NAME: str = "ModelComponentOperationException"
    DEFAULT_MESSAGE: str = "Model component operation failed."


class ModelCatalogueIndexNotAvailableException(ModelComponentOperationException):
    """Raised when a vector index operation is attempted while the index is being rebuilt."""

    ERROR_NAME: str = "ModelCatalogueIndexNotAvailableException"
    DEFAULT_MESSAGE: str = "Model catalogue index is not available (rebuild in progress)."


class FullTextAnalyzerNotExistException(ModelComponentOperationException):
    """Raised when the referenced full-text analyzer does not exist in the database."""

    ERROR_NAME: str = "FullTextAnalyzerNotExistException"
    DEFAULT_MESSAGE: str = "The referenced full-text analyzer does not exist."
