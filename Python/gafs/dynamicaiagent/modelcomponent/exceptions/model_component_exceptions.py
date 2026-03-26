"""Concrete ModelComponent exception types by error category."""

from __future__ import annotations

from .model_component_exception import ModelComponentException


class ModelComponentConfigurationException(ModelComponentException):
    """Invalid component configuration or not-initialized state."""

    ERROR_NAME: str = "ModelComponentConfigurationException"
    DEFAULT_MESSAGE: str = "Invalid ModelComponent configuration."


class ModelComponentResourceNotFoundException(ModelComponentException):
    """Requested catalogue/deployment/configuration resource is not found."""

    ERROR_NAME: str = "ModelComponentResourceNotFoundException"
    DEFAULT_MESSAGE: str = "Requested model resource was not found."


class ModelComponentOperationException(ModelComponentException):
    """Model operation failed due to service/provider/runtime errors."""

    ERROR_NAME: str = "ModelComponentOperationException"
    DEFAULT_MESSAGE: str = "Model component operation failed."

class ModelCatalogueIndexNotAvailableException(ModelComponentOperationException):
    """Raised while model catalogue index is not available."""

    ERROR_NAME: str = "ModelCatalogueIndexNotAvailableException"
    DEFAULT_MESSAGE: str = "Model catalogue index is not available."
