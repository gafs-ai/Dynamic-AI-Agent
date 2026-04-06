from typing import Any
import json
from .hnsw_search_method import HnswSearchMethod
from .vector_data_type import VectorDataType

class ModelComponentConfigurations:
    @staticmethod
    def COLLECTION_NAME() -> str:
        """Return the default collection/table name for the model component configurations.
        """
        return "component_configurations"
    
    @staticmethod
    def DEFAULT_DOCUMENT_ID() -> str:
        """Return the default document/record id for the model component configurations.
        """
        return "model_component"

    @staticmethod
    def DEFAULT_VECTOR_DATA_TYPE() -> VectorDataType:
        """Return the default vector data type for the model component configurations.
        """
        return VectorDataType.F32

    @staticmethod
    def DEFAULT_DIMENSIONS() -> int:
        """Return the default dimensions for the model component configurations.
        """
        return 3072
    
    @staticmethod
    def DEFAULT_VECTOR_SEARCH_METHOD() -> HnswSearchMethod:
        """Return the default vector search method for the model component configurations.
        """
        return HnswSearchMethod.COSINE
    
    @staticmethod
    def DEFAULT_VECTOR_EXPLORATION_FACTOR() -> int:
        """Return the default vector exploration factor for the model component configurations.
        """
        return 150

    @staticmethod
    def DEFAULT_VECTOR_MAX_CONNECTIONS() -> int:
        """Return the default vector max connections for the model component configurations.
        """
        return 12


    def __init__(self) -> None:
        object.__setattr__(self, "embedding_catalogue_id", None) # str: Optional, but you cannnot use the vector search without an available embedding model.
        object.__setattr__(self, "embedding_deployment_id", None) # str: Optional, if this value is set, this deployment will be preferred.
        object.__setattr__(self, "vector_data_type", self.DEFAULT_VECTOR_DATA_TYPE()) # VectorDataType
        object.__setattr__(self, "vector_dimensions", self.DEFAULT_DIMENSIONS()) # int
        object.__setattr__(self, "vector_search_method", self.DEFAULT_VECTOR_SEARCH_METHOD())  # HnswSearchMethod
        object.__setattr__(self, "vector_exploration_factor", self.DEFAULT_VECTOR_EXPLORATION_FACTOR()) # int
        object.__setattr__(self, "vector_max_connections", self.DEFAULT_VECTOR_MAX_CONNECTIONS()) # int
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name == "embedding_catalogue_id":
            if isinstance(value, str):
                object.__setattr__(self, "embedding_catalogue_id", value)
            else:
                raise ValueError
        elif name == "embedding_deployment_id":
            if isinstance(value, str):
                object.__setattr__(self, "embedding_deployment_id", value)
            else:
                raise ValueError
        elif name == "vector_data_type":
            if isinstance(value, VectorDataType):
                object.__setattr__(self, "vector_data_type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "vector_data_type", VectorDataType(value))
            else:
                raise ValueError
        elif name == "vector_dimensions":
            if isinstance(value, int):
                object.__setattr__(self, "vector_dimensions", value)
            else:
                raise ValueError
        elif name == "vector_search_method":
            if isinstance(value, HnswSearchMethod):
                object.__setattr__(self, "vector_search_method", value)
            elif isinstance(value, str):
                object.__setattr__(
                    self, "vector_search_method", HnswSearchMethod(value)
                )
            else:
                raise ValueError
        elif name == "vector_exploration_factor":
            if isinstance(value, int):
                object.__setattr__(self, "vector_exploration_factor", value)
            else:
                raise ValueError
        elif name == "vector_max_connections":
            if isinstance(value, int):
                object.__setattr__(self, "vector_max_connections", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        converted: dict[str, Any] = {}
        if self.embedding_catalogue_id is not None:
            converted["embedding_catalogue_id"] = self.embedding_catalogue_id
        if self.embedding_deployment_id is not None:
            converted["embedding_deployment_id"] = self.embedding_deployment_id
        if self.vector_data_type is not None:
            if recursive:
                converted["vector_data_type"] = self.vector_data_type.value
            else:
                converted["vector_data_type"] = self.vector_data_type
        if self.vector_dimensions is not None:
            converted["vector_dimensions"] = self.vector_dimensions
        if self.vector_search_method is not None:
            if recursive:
                converted["vector_search_method"] = self.vector_search_method.value
            else:
                converted["vector_search_method"] = self.vector_search_method
        if self.vector_exploration_factor is not None:
            converted["vector_exploration_factor"] = self.vector_exploration_factor
        if self.vector_max_connections is not None:
            converted["vector_max_connections"] = self.vector_max_connections
        return converted

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelComponentConfigurations":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity
    
    @classmethod
    def from_json(cls, json_str: str) -> "ModelComponentConfigurations":
        converted: Any = json.loads(json_str)
        if isinstance(converted, dict):
            return cls.from_dict(converted)
        else:
            raise ValueError
