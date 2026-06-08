"""tool_component_configurations.py - Persisted configuration for the Tool Component.

Stored as a single document in the ``component_configurations`` collection
under the record id ``tool_component``.
"""

from __future__ import annotations

import json
from typing import Any

from surrealdb import RecordID

from gafs.dynamicaiagent.common.models import HnswSearchMethod, VectorDataType


class ToolComponentConfigurations:
    """Global configuration document for the Tool Component.

    Controls which embedding model is used for vector generation, and the
    parameters of the HNSW vector index on ``ToolCatalogue.description_vector``.
    Also stores the names of the full-text analyzers and Docker container limits.

    Attributes:
        embedding_catalogue_id: ID of the ModelCatalogueEntry for embedding.
        embedding_deployment_id: Preferred deployment ID for embedding.
        vector_data_type: Numeric type of vector elements.
        vector_dimensions: Number of dimensions in the embedding vector.
        vector_search_method: Distance metric for HNSW similarity search.
        vector_exploration_factor: HNSW ef parameter.
        vector_max_connections: HNSW m parameter.
        name_analyzer: Full-text analyzer name for the ``name`` field.
        description_analyzer: Full-text analyzer name for ``description`` field.
        docker_default_image_max_stand_by: Max standby containers per sandbox.
        docker_total_default_image_max_stand_by: Max total standby containers.
        app_data_folder: Absolute path to the application data folder.
    """

    @staticmethod
    def COLLECTION_NAME() -> str:
        """SurrealDB collection name for this configuration document."""
        return "component_configurations"

    @staticmethod
    def DEFAULT_DOCUMENT_ID() -> str:
        """Record ID of the single configuration document."""
        return "tool_component"

    @staticmethod
    def DEFAULT_VECTOR_DATA_TYPE() -> VectorDataType:
        """Default vector element type."""
        return VectorDataType.F32

    @staticmethod
    def DEFAULT_DIMENSIONS() -> int:
        """Default vector dimensions (matches text-embedding-3-large)."""
        return 3072

    @staticmethod
    def DEFAULT_VECTOR_SEARCH_METHOD() -> HnswSearchMethod:
        """Default HNSW distance metric."""
        return HnswSearchMethod.COSINE

    @staticmethod
    def DEFAULT_VECTOR_EXPLORATION_FACTOR() -> int:
        """Default HNSW ef parameter."""
        return 150

    @staticmethod
    def DEFAULT_VECTOR_MAX_CONNECTIONS() -> int:
        """Default HNSW m parameter."""
        return 12

    @staticmethod
    def DEFAULT_NAME_ANALYZER() -> str:
        """Default full-text analyzer name for the ``name`` field."""
        return "default_ngram_analyzer"

    @staticmethod
    def DEFAULT_DESCRIPTION_ANALYZER() -> str:
        """Default full-text analyzer name for the ``description`` field."""
        return "default_english_analyzer"

    def __init__(self) -> None:
        object.__setattr__(self, "id", None)
        object.__setattr__(self, "embedding_catalogue_id", None)
        object.__setattr__(self, "embedding_deployment_id", None)
        object.__setattr__(self, "vector_data_type", self.DEFAULT_VECTOR_DATA_TYPE())
        object.__setattr__(self, "vector_dimensions", self.DEFAULT_DIMENSIONS())
        object.__setattr__(self, "vector_search_method", self.DEFAULT_VECTOR_SEARCH_METHOD())
        object.__setattr__(self, "vector_exploration_factor", self.DEFAULT_VECTOR_EXPLORATION_FACTOR())
        object.__setattr__(self, "vector_max_connections", self.DEFAULT_VECTOR_MAX_CONNECTIONS())
        object.__setattr__(self, "name_analyzer", self.DEFAULT_NAME_ANALYZER())
        object.__setattr__(self, "description_analyzer", self.DEFAULT_DESCRIPTION_ANALYZER())
        object.__setattr__(self, "docker_default_image_max_stand_by", 3)
        object.__setattr__(self, "docker_total_default_image_max_stand_by", 10)
        object.__setattr__(self, "app_data_folder", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("id", "$id"):
            if value is None:
                object.__setattr__(self, "id", None)
            elif isinstance(value, RecordID):
                object.__setattr__(self, "id", str(value.id))
            elif isinstance(value, str):
                object.__setattr__(self, "id", value.rsplit(":", 1)[-1] if ":" in value else value)
            else:
                object.__setattr__(self, "id", str(value))
        elif name in ("embedding_catalogue_id", "embedding_deployment_id", "name_analyzer",
                      "description_analyzer", "app_data_folder"):
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "vector_data_type":
            if isinstance(value, VectorDataType):
                object.__setattr__(self, name, value)
            elif isinstance(value, str):
                object.__setattr__(self, name, VectorDataType(value))
            else:
                raise ValueError
        elif name == "vector_search_method":
            if isinstance(value, HnswSearchMethod):
                object.__setattr__(self, name, value)
            elif isinstance(value, str):
                object.__setattr__(self, name, HnswSearchMethod(value))
            else:
                raise ValueError
        elif name in ("vector_dimensions", "vector_exploration_factor", "vector_max_connections",
                      "docker_default_image_max_stand_by", "docker_total_default_image_max_stand_by"):
            if isinstance(value, int):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False, exclude_id: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if not exclude_id:
            if self.id is not None:
                result["id"] = self.id
        if self.embedding_catalogue_id is not None:
            result["embedding_catalogue_id"] = self.embedding_catalogue_id
        if self.embedding_deployment_id is not None:
            result["embedding_deployment_id"] = self.embedding_deployment_id
        if self.vector_data_type is not None:
            result["vector_data_type"] = self.vector_data_type.value if recursive else self.vector_data_type
        if self.vector_dimensions is not None:
            result["vector_dimensions"] = self.vector_dimensions
        if self.vector_search_method is not None:
            result["vector_search_method"] = self.vector_search_method.value if recursive else self.vector_search_method
        if self.vector_exploration_factor is not None:
            result["vector_exploration_factor"] = self.vector_exploration_factor
        if self.vector_max_connections is not None:
            result["vector_max_connections"] = self.vector_max_connections
        if self.name_analyzer is not None:
            result["name_analyzer"] = self.name_analyzer
        if self.description_analyzer is not None:
            result["description_analyzer"] = self.description_analyzer
        if self.docker_default_image_max_stand_by is not None:
            result["docker_default_image_max_stand_by"] = self.docker_default_image_max_stand_by
        if self.docker_total_default_image_max_stand_by is not None:
            result["docker_total_default_image_max_stand_by"] = self.docker_total_default_image_max_stand_by
        if self.app_data_folder is not None:
            result["app_data_folder"] = self.app_data_folder
        return result

    def to_json(self, exclude_id: bool = False) -> str:
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolComponentConfigurations":
        entity = cls()
        for key, value in data.items():
            if value is not None:
                try:
                    setattr(entity, key, value)
                except (ValueError, AttributeError):
                    continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "ToolComponentConfigurations":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
