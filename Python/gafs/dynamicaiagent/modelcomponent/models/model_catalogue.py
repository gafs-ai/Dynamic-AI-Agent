"""model_catalogue.py - ModelCatalogueEntry, ModelDeployment, and related enums.

Defines the persisted data models for AI model catalogue entries and deployments,
their lifecycle status enums, and the search result wrapper used by catalogue search.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from surrealdb import RecordID

from gafs.dynamicaiagent.common.models import AttributeDefinition
from .ai_deployment_type import AiDeploymentType
from .ai_operation_type import AiOperationType
from .ai_provider_type import AiProviderType


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ModelStatus(Enum):
    """Lifecycle status of a model in the catalogue."""

    RECOMMENDED = "recommended"
    """Preferred model for new usage."""

    ACTIVE = "active"
    """Available for use."""

    MAINTENANCE = "maintenance"
    """Temporarily limited availability."""

    DEPRECATED = "deprecated"
    """Scheduled for retirement; avoid new usage."""

    RETIRED = "retired"
    """No longer available."""


class DeploymentStatus(Enum):
    """Lifecycle status of a model deployment."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


# ---------------------------------------------------------------------------
# ModelDeployment
# ---------------------------------------------------------------------------

class ModelDeployment:
    """Persisted descriptor for an AI model deployment configuration.

    A deployment describes how to reach a specific model instance: which
    provider to use, connection parameters, and optional secret references.

    Attributes:
        id: Record ID (stripped of table prefix).
        name: Unique deployment name.
        description: Optional free-text description.
        tags: Optional list of string tags.
        secrets: IDs of linked ``Secret`` entries (resolved from edges at read time).
        deployment_type: Where the model runs (CLOUD, LOCAL, REMOTE).
        provider_type: Specific AI provider (e.g. ``CloudAiProviderType``).
        connection_parameters: Non-secret connection parameters dict.
        priority: Deployment priority; higher value = higher priority.
        max_confidence_level: Maximum data confidence level this deployment accepts.
        status: Deployment lifecycle status.
    """

    @staticmethod
    def COLLECTION_NAME() -> str:  # noqa: N802
        """SurrealDB collection name for model deployment records."""
        return "model_deployments"

    def __init__(self) -> None:
        # Initialize all fields to None, bypassing __setattr__ validation.
        object.__setattr__(self, "id", None)                    # str | None
        object.__setattr__(self, "name", None)                  # str
        object.__setattr__(self, "description", None)           # str | None
        object.__setattr__(self, "tags", None)                  # list[str] | None
        object.__setattr__(self, "secrets", None)               # list[str] | None
        object.__setattr__(self, "deployment_type", None)       # AiDeploymentType
        object.__setattr__(self, "provider_type", None)         # AiProviderType
        object.__setattr__(self, "connection_parameters", None) # dict[str, Any] | None
        object.__setattr__(self, "priority", None)              # int | None
        object.__setattr__(self, "max_confidence_level", None)  # int | None
        object.__setattr__(self, "status", None)                # DeploymentStatus | None

    def __setattr__(self, name: str, value: Any) -> None:  # noqa: C901 (complexity)
        if name in ("id", "$id"):
            # Normalize SurrealDB RecordID to a bare string id.
            if value is None:
                object.__setattr__(self, "id", None)
            elif isinstance(value, str):
                object.__setattr__(self, "id", value.rsplit(":", 1)[-1])
            elif isinstance(value, RecordID):
                object.__setattr__(self, "id", str(value.id).rsplit(":", 1)[-1])
            else:
                raise ValueError(f"id must be str or RecordID, got {type(value)}")
        elif name == "name":
            if isinstance(value, str):
                object.__setattr__(self, "name", value)
            else:
                raise ValueError(f"name must be str, got {type(value)}")
        elif name == "description":
            if isinstance(value, str):
                object.__setattr__(self, "description", value)
            else:
                raise ValueError(f"description must be str, got {type(value)}")
        elif name == "tags":
            if isinstance(value, list) and all(isinstance(t, str) for t in value):
                object.__setattr__(self, "tags", value)
            else:
                raise ValueError("tags must be list[str]")
        elif name == "secrets":
            if isinstance(value, list) and all(isinstance(s, str) for s in value):
                object.__setattr__(self, "secrets", value)
            else:
                raise ValueError("secrets must be list[str]")
        elif name == "deployment_type":
            if isinstance(value, AiDeploymentType):
                object.__setattr__(self, "deployment_type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "deployment_type", AiDeploymentType(value))
            else:
                raise ValueError(f"deployment_type must be AiDeploymentType or str, got {type(value)}")
        elif name == "provider_type":
            # provider_type is typed as AiProviderType (abstract base) but in
            # practice a subclass enum value (e.g. CloudAiProviderType) is stored.
            # We try to cast via the parent enum using value.value to support any
            # registered subclass.
            if isinstance(value, AiProviderType):
                object.__setattr__(self, "provider_type", value)
            elif isinstance(value, str):
                # Attempt to import CloudAiProviderType dynamically to avoid
                # a hard circular dependency while still supporting the most
                # common provider type.
                try:
                    from gafs.dynamicaiagent.cloudaicomponent.models.cloud_ai_provider_type import CloudAiProviderType
                    object.__setattr__(self, "provider_type", CloudAiProviderType(value))
                except (ImportError, ValueError):
                    # Fall back to storing as raw string if the provider type is unknown.
                    object.__setattr__(self, "provider_type", value)
            else:
                raise ValueError(f"provider_type must be AiProviderType or str, got {type(value)}")
        elif name == "connection_parameters":
            if isinstance(value, dict):
                object.__setattr__(self, "connection_parameters", value)
            else:
                raise ValueError("connection_parameters must be dict")
        elif name == "priority":
            if isinstance(value, int):
                object.__setattr__(self, "priority", value)
            else:
                raise ValueError(f"priority must be int, got {type(value)}")
        elif name == "max_confidence_level":
            if isinstance(value, int):
                object.__setattr__(self, "max_confidence_level", value)
            else:
                raise ValueError(f"max_confidence_level must be int, got {type(value)}")
        elif name == "status":
            if isinstance(value, DeploymentStatus):
                object.__setattr__(self, "status", value)
            elif isinstance(value, str):
                object.__setattr__(self, "status", DeploymentStatus(value))
            else:
                raise ValueError(f"status must be DeploymentStatus or str, got {type(value)}")
        else:
            # Silently ignore unknown keys (e.g. extra DB fields).
            pass

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(
        self,
        recursive: bool = False,
        exclude_id: bool = False,
    ) -> dict[str, Any]:
        """Convert to a plain dictionary.

        Args:
            recursive: When ``True``, enum values are serialized as strings.
            exclude_id: When ``True``, the ``id`` field is omitted.

        Returns:
            Dictionary representation (``None`` fields omitted, ``secrets`` always omitted
            because it is managed via DB edges and must not be persisted as a field).
        """
        result: dict[str, Any] = {}
        if not exclude_id and self.id is not None:
            result["id"] = self.id
        if self.name is not None:
            result["name"] = self.name
        if self.description is not None:
            result["description"] = self.description
        if self.tags is not None:
            result["tags"] = self.tags
        # ``secrets`` is managed via ``references_secret`` edges — never written as a field.
        if self.deployment_type is not None:
            result["deployment_type"] = (
                self.deployment_type.value if recursive else self.deployment_type
            )
        if self.provider_type is not None:
            if recursive:
                result["provider_type"] = (
                    self.provider_type.value
                    if hasattr(self.provider_type, "value")
                    else self.provider_type
                )
            else:
                result["provider_type"] = self.provider_type
        if self.connection_parameters is not None:
            result["connection_parameters"] = self.connection_parameters
        if self.priority is not None:
            result["priority"] = self.priority
        if self.max_confidence_level is not None:
            result["max_confidence_level"] = self.max_confidence_level
        if self.status is not None:
            result["status"] = self.status.value if recursive else self.status
        return result

    def to_json(self, exclude_id: bool = False) -> str:
        """Serialize to a JSON string.

        Args:
            exclude_id: When ``True``, the ``id`` field is excluded.
        """
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelDeployment":
        """Create a ``ModelDeployment`` from a dictionary.

        ``None`` values in *data* are skipped to allow partial updates.

        Args:
            data: Source dictionary. May include extra keys which are silently ignored.

        Returns:
            New ``ModelDeployment`` instance.
        """
        if not isinstance(data, dict):
            raise ValueError("data must be a dict")
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "ModelDeployment":
        """Create a ``ModelDeployment`` from a JSON string."""
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError("JSON must represent an object")
        return cls.from_dict(converted)


# ---------------------------------------------------------------------------
# ModelCatalogueEntry
# ---------------------------------------------------------------------------

class ModelCatalogueEntry:
    """Persisted metadata record for an AI model in the model catalogue.

    Attributes:
        id: Record ID (stripped of table prefix). ``None`` for new records.
        name: Unique model name.
        type: Type of operation this model supports.
        status: Lifecycle status.
        description: Optional free-text description.
        description_vector: Embedding vector for similarity search.
        priority: Model priority; higher value = higher priority.
        tags: Optional tags for filtering.
        deployments: IDs of linked ``ModelDeployment`` entries (from edges).
        default_inference_parameters: Default provider-specific parameters.
        available_inference_parameters: Schema of supported inference parameters.
    """

    @staticmethod
    def CollectionName() -> str:  # noqa: N802
        """SurrealDB collection name for model catalogue records."""
        return "ModelCatalogue"

    def __init__(self) -> None:
        object.__setattr__(self, "id", None)                           # str | None
        object.__setattr__(self, "name", None)                         # str
        object.__setattr__(self, "type", None)                         # AiOperationType
        object.__setattr__(self, "status", None)                       # ModelStatus | None
        object.__setattr__(self, "description", None)                  # str | None
        object.__setattr__(self, "description_vector", None)           # list[float] | None
        object.__setattr__(self, "priority", None)                     # int | None
        object.__setattr__(self, "tags", None)                         # list[str] | None
        object.__setattr__(self, "deployments", None)                  # list[str] | None
        object.__setattr__(self, "default_inference_parameters", None) # dict[str, Any] | None
        object.__setattr__(self, "available_inference_parameters", None) # list[AttributeDefinition] | None

    def __setattr__(self, name: str, value: Any) -> None:  # noqa: C901
        if name in ("id", "$id"):
            if value is None:
                object.__setattr__(self, "id", None)
            elif isinstance(value, str):
                object.__setattr__(self, "id", value.rsplit(":", 1)[-1])
            elif isinstance(value, RecordID):
                object.__setattr__(self, "id", str(value.id).rsplit(":", 1)[-1])
            else:
                raise ValueError(f"id must be str or RecordID, got {type(value)}")
        elif name == "name":
            if isinstance(value, str):
                object.__setattr__(self, "name", value)
            else:
                raise ValueError(f"name must be str, got {type(value)}")
        elif name == "type":
            if isinstance(value, AiOperationType):
                object.__setattr__(self, "type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "type", AiOperationType(value))
            else:
                raise ValueError(f"type must be AiOperationType or str, got {type(value)}")
        elif name == "status":
            if isinstance(value, ModelStatus):
                object.__setattr__(self, "status", value)
            elif isinstance(value, str):
                object.__setattr__(self, "status", ModelStatus(value))
            else:
                raise ValueError(f"status must be ModelStatus or str, got {type(value)}")
        elif name == "description":
            if isinstance(value, str):
                object.__setattr__(self, "description", value)
            else:
                raise ValueError(f"description must be str, got {type(value)}")
        elif name == "description_vector":
            if isinstance(value, list):
                object.__setattr__(self, "description_vector", [float(v) for v in value])
            else:
                raise ValueError("description_vector must be list[float]")
        elif name == "priority":
            if isinstance(value, int):
                object.__setattr__(self, "priority", value)
            else:
                raise ValueError(f"priority must be int, got {type(value)}")
        elif name == "tags":
            if isinstance(value, list) and all(isinstance(t, str) for t in value):
                object.__setattr__(self, "tags", value)
            else:
                raise ValueError("tags must be list[str]")
        elif name == "deployments":
            if isinstance(value, list) and all(isinstance(d, str) for d in value):
                object.__setattr__(self, "deployments", value)
            else:
                raise ValueError("deployments must be list[str]")
        elif name == "default_inference_parameters":
            if isinstance(value, dict):
                object.__setattr__(self, "default_inference_parameters", value)
            else:
                raise ValueError("default_inference_parameters must be dict")
        elif name == "available_inference_parameters":
            # Accept list[AttributeDefinition] or list[dict]; auto-convert dicts.
            if isinstance(value, list):
                converted: list[AttributeDefinition] = []
                for item in value:
                    if isinstance(item, AttributeDefinition):
                        converted.append(item)
                    elif isinstance(item, dict):
                        converted.append(AttributeDefinition.from_dict(item))
                    else:
                        raise ValueError("available_inference_parameters items must be AttributeDefinition or dict")
                object.__setattr__(self, "available_inference_parameters", converted)
            else:
                raise ValueError("available_inference_parameters must be list")
        else:
            # Silently ignore unknown DB fields.
            pass

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(
        self,
        recursive: bool = False,
        exclude_id: bool = False,
    ) -> dict[str, Any]:
        """Convert to a plain dictionary.

        Args:
            recursive: When ``True``, enum values are serialized as strings and
                nested objects are also converted to dicts.
            exclude_id: When ``True``, the ``id`` field is omitted.

        Returns:
            Dictionary representation. ``deployments`` and ``description_vector``
            are omitted from the output because they are managed via edges and
            should not be stored as direct fields on the record.
        """
        result: dict[str, Any] = {}
        if not exclude_id and self.id is not None:
            result["id"] = self.id
        if self.name is not None:
            result["name"] = self.name
        if self.type is not None:
            result["type"] = self.type.value if recursive else self.type
        if self.status is not None:
            result["status"] = self.status.value if recursive else self.status
        if self.description is not None:
            result["description"] = self.description
        if self.description_vector is not None:
            result["description_vector"] = self.description_vector
        if self.priority is not None:
            result["priority"] = self.priority
        if self.tags is not None:
            result["tags"] = self.tags
        # ``deployments`` is managed via ``deployed_as`` edges — not stored as a field.
        if self.default_inference_parameters is not None:
            result["default_inference_parameters"] = self.default_inference_parameters
        if self.available_inference_parameters is not None:
            if recursive:
                result["available_inference_parameters"] = [
                    item.to_dict(recursive=True)
                    for item in self.available_inference_parameters
                ]
            else:
                result["available_inference_parameters"] = self.available_inference_parameters
        return result

    def to_json(self, exclude_id: bool = False) -> str:
        """Serialize to a JSON string.

        Args:
            exclude_id: When ``True``, the ``id`` field is excluded.
        """
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelCatalogueEntry":
        """Create a ``ModelCatalogueEntry`` from a dictionary.

        ``None`` values in *data* are skipped.

        Args:
            data: Source dictionary.

        Returns:
            New ``ModelCatalogueEntry`` instance.
        """
        if not isinstance(data, dict):
            raise ValueError("data must be a dict")
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "ModelCatalogueEntry":
        """Create a ``ModelCatalogueEntry`` from a JSON string."""
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError("JSON must represent an object")
        return cls.from_dict(converted)


# ---------------------------------------------------------------------------
# ModelCatalogueSearchResultEntry
# ---------------------------------------------------------------------------

class ModelCatalogueSearchResultEntry(ModelCatalogueEntry):
    """A ``ModelCatalogueEntry`` augmented with a vector similarity distance score.

    Returned by ``IModelCatalogueService.search_catalogue_entries`` when a
    vector search is performed.  The ``distance`` field is ``None`` when no
    vector search was requested.

    Attributes:
        distance: Vector similarity distance from the query vector. ``None`` when
            the result was not returned by a vector search.
    """

    def __init__(self) -> None:
        super().__init__()
        object.__setattr__(self, "distance", None)  # float | None

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("distance", "dist"):
            # Accept both field name variants (SurrealDB may return "dist").
            if value is None:
                object.__setattr__(self, "distance", None)
            elif isinstance(value, float):
                object.__setattr__(self, "distance", value)
            elif isinstance(value, int):
                object.__setattr__(self, "distance", float(value))
            else:
                raise ValueError(f"distance must be float or int, got {type(value)}")
        else:
            super().__setattr__(name, value)

    def to_dict(
        self,
        recursive: bool = False,
        exclude_id: bool = False,
    ) -> dict[str, Any]:
        result = super().to_dict(recursive=recursive, exclude_id=exclude_id)
        if self.distance is not None:
            result["distance"] = self.distance
        return result

    def to_json(self, exclude_id: bool = False) -> str:
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))
