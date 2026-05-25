"""model_component_configurations.py - Persisted configuration for the Model Component.

Stored as a single document in the ``component_configurations`` collection
under the record id ``model_component``.
"""

from __future__ import annotations

import json
from typing import Any

from surrealdb import RecordID

from gafs.dynamicaiagent.common.models import HnswSearchMethod, VectorDataType


class ModelComponentConfigurations:
    """Global configuration document for the Model Component.

    Controls which embedding model is used for vector generation, and the
    parameters of the HNSW vector index on ``ModelCatalogue.description_vector``.
    Also stores the names of the full-text analyzers used for ``name`` and
    ``description`` fields.

    All attributes have sensible defaults so a new ``ModelComponentConfigurations()``
    is ready to use without any further configuration.

    Attributes:
        embedding_catalogue_id: ID of the ``ModelCatalogueEntry`` used to generate
            description vectors. Required for vector search.
        embedding_deployment_id: Preferred deployment ID for embedding.
        vector_data_type: Numeric type of vector elements.
        vector_dimensions: Number of dimensions in the embedding vector.
        vector_search_method: Distance metric for HNSW similarity search.
        vector_exploration_factor: HNSW ``ef_construction`` / ``ef`` parameter.
        vector_max_connections: HNSW ``m`` parameter (max connections per node).
        name_analyzer: Full-text analyzer name for the ``name`` field.
        description_analyzer: Full-text analyzer name for the ``description`` field.
    """

    # ---- Class-level constants ----

    @staticmethod
    def COLLECTION_NAME() -> str:  # noqa: N802
        """SurrealDB collection name for this configuration document."""
        return "component_configurations"

    @staticmethod
    def DEFAULT_DOCUMENT_ID() -> str:  # noqa: N802
        """Record ID of the single configuration document."""
        return "model_component"

    @staticmethod
    def DEFAULT_VECTOR_DATA_TYPE() -> VectorDataType:  # noqa: N802
        """Default vector element type."""
        return VectorDataType.F32

    @staticmethod
    def DEFAULT_DIMENSIONS() -> int:  # noqa: N802
        """Default vector dimensions (matches text-embedding-3-large)."""
        return 3072

    @staticmethod
    def DEFAULT_VECTOR_SEARCH_METHOD() -> HnswSearchMethod:  # noqa: N802
        """Default HNSW distance metric."""
        return HnswSearchMethod.COSINE

    @staticmethod
    def DEFAULT_VECTOR_EXPLORATION_FACTOR() -> int:  # noqa: N802
        """Default HNSW ef parameter."""
        return 150

    @staticmethod
    def DEFAULT_VECTOR_MAX_CONNECTIONS() -> int:  # noqa: N802
        """Default HNSW m parameter."""
        return 12

    @staticmethod
    def DEFAULT_NAME_ANALYZER() -> str:  # noqa: N802
        """Default full-text analyzer name for the ``name`` field."""
        return "default_ngram_analyzer"

    @staticmethod
    def DEFAULT_DESCRIPTION_ANALYZER() -> str:  # noqa: N802
        """Default full-text analyzer name for the ``description`` field."""
        return "default_english_analyzer"

    # ---- Constructor ----

    def __init__(self) -> None:
        # All fields initialized to defaults, bypassing __setattr__ validation.
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

    # ---- Validation ----

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
        elif name == "embedding_catalogue_id":
            if isinstance(value, str):
                object.__setattr__(self, "embedding_catalogue_id", value)
            else:
                raise ValueError(f"embedding_catalogue_id must be str, got {type(value)}")
        elif name == "embedding_deployment_id":
            if isinstance(value, str):
                object.__setattr__(self, "embedding_deployment_id", value)
            else:
                raise ValueError(f"embedding_deployment_id must be str, got {type(value)}")
        elif name == "vector_data_type":
            if isinstance(value, VectorDataType):
                object.__setattr__(self, "vector_data_type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "vector_data_type", VectorDataType(value))
            else:
                raise ValueError(f"vector_data_type must be VectorDataType or str, got {type(value)}")
        elif name == "vector_dimensions":
            if isinstance(value, int):
                object.__setattr__(self, "vector_dimensions", value)
            else:
                raise ValueError(f"vector_dimensions must be int, got {type(value)}")
        elif name == "vector_search_method":
            if isinstance(value, HnswSearchMethod):
                object.__setattr__(self, "vector_search_method", value)
            elif isinstance(value, str):
                object.__setattr__(self, "vector_search_method", HnswSearchMethod(value))
            else:
                raise ValueError(f"vector_search_method must be HnswSearchMethod or str, got {type(value)}")
        elif name == "vector_exploration_factor":
            if isinstance(value, int):
                object.__setattr__(self, "vector_exploration_factor", value)
            else:
                raise ValueError(f"vector_exploration_factor must be int, got {type(value)}")
        elif name == "vector_max_connections":
            if isinstance(value, int):
                object.__setattr__(self, "vector_max_connections", value)
            else:
                raise ValueError(f"vector_max_connections must be int, got {type(value)}")
        elif name == "name_analyzer":
            if isinstance(value, str):
                object.__setattr__(self, "name_analyzer", value)
            else:
                raise ValueError(f"name_analyzer must be str, got {type(value)}")
        elif name == "description_analyzer":
            if isinstance(value, str):
                object.__setattr__(self, "description_analyzer", value)
            else:
                raise ValueError(f"description_analyzer must be str, got {type(value)}")
        else:
            # Silently ignore unknown DB fields.
            pass

    def __repr__(self) -> str:
        return self.to_json()

    # ---- Serialization ----

    def to_dict(
        self,
        recursive: bool = False,
        exclude_id: bool = False,
    ) -> dict[str, Any]:
        """Convert to a plain dictionary.

        Args:
            recursive: When ``True``, enum values are serialized as strings.
            exclude_id: When ``True``, the ``id`` field is omitted.
        """
        result: dict[str, Any] = {}
        if not exclude_id and self.id is not None:
            result["id"] = self.id
        if self.embedding_catalogue_id is not None:
            result["embedding_catalogue_id"] = self.embedding_catalogue_id
        if self.embedding_deployment_id is not None:
            result["embedding_deployment_id"] = self.embedding_deployment_id
        result["vector_data_type"] = (
            self.vector_data_type.value if recursive else self.vector_data_type
        )
        result["vector_dimensions"] = self.vector_dimensions
        result["vector_search_method"] = (
            self.vector_search_method.value if recursive else self.vector_search_method
        )
        result["vector_exploration_factor"] = self.vector_exploration_factor
        result["vector_max_connections"] = self.vector_max_connections
        result["name_analyzer"] = self.name_analyzer
        result["description_analyzer"] = self.description_analyzer
        return result

    def to_json(self, exclude_id: bool = False) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelComponentConfigurations":
        """Create a ``ModelComponentConfigurations`` from a dictionary.

        Args:
            data: Source dictionary.

        Returns:
            New ``ModelComponentConfigurations`` instance.
        """
        if not isinstance(data, dict):
            raise ValueError("data must be a dict")
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "ModelComponentConfigurations":
        """Create a ``ModelComponentConfigurations`` from a JSON string."""
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError("JSON must represent an object")
        return cls.from_dict(converted)
