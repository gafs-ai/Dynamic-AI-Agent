"""Backward-compatible facade for model catalogue types.

Unit/integration tests (and some external callers) historically import enums and
entities from ``gafs.dynamicaiagent.modelcomponent.model_catalogue``.

The actual implementations live in ``gafs.dynamicaiagent.modelcomponent.models``.
This module re-exports the public API with compatibility aliases.
"""

from __future__ import annotations

from gafs.dynamicaiagent.modelcomponent.models.ai_deployment_type import AiDeploymentType
from gafs.dynamicaiagent.modelcomponent.models.ai_operation_type import AiOperationType
from gafs.dynamicaiagent.modelcomponent.models.model_catalogue import (
    ModelCatalogue,
    ModelCatalogueSearchResultEntry,
    ModelDeployment,
    ModelStatus,
)

# Compatibility alias (older name expected by tests).
ModelCatalogueSearchResultEntity = ModelCatalogueSearchResultEntry

__all__ = [
    "AiDeploymentType",
    "AiOperationType",
    "ModelCatalogue",
    "ModelCatalogueSearchResultEntry",
    "ModelCatalogueSearchResultEntity",
    "ModelDeployment",
    "ModelStatus",
]

