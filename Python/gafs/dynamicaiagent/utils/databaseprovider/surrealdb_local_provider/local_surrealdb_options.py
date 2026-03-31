from __future__ import annotations

import json
from enum import Enum
from typing import Any

from ..database_provider_options import DatabaseProviderOptions
from ..database_provider_type import DatabaseProviderType


class LocalSurrealDbStorageType(Enum):
    """Storage engine options for the embedded SurrealDB provider."""
    MEM = "mem"
    FILE = "file"
    SURREALKV = "surrealkv"
    ROCKSDB = "rocksdb"


class LocalSurrealDbOptions(DatabaseProviderOptions):
    """Options for Local (Embedded) SurrealDB provider.

    Attributes:
        namespace: SurrealDB namespace.
        database: SurrealDB database name.
        storage_type: Storage engine to use (default: SURREALKV).
        path: File path for persistent storage engines (surrealkv, rocksdb).
               Ignored when storage_type is MEM.
        database_type: Database type (should be SURREALDB_LOCAL).
        database_name: Logical database name for the provider.
        support_vector_search: Whether vector search is supported (default: True).
        vector_graph_search_max_depth: Maximum depth for vector graph search (default: 5).
        support_full_text_search: Whether full-text search is supported (default: True).
        max_limit: Maximum query result limit (default: 100).
    """

    def __init__(self) -> None:
        """Initialize all fields to None or appropriate default values."""
        super().__init__()

        object.__setattr__(self, "namespace", None)
        object.__setattr__(self, "database", None)
        object.__setattr__(self, "storage_type", LocalSurrealDbStorageType.SURREALKV)
        object.__setattr__(self, "path", None)

        object.__setattr__(self, "database_type", DatabaseProviderType.SURREALDB_LOCAL)
        object.__setattr__(self, "support_vector_search", True)
        object.__setattr__(self, "vector_graph_search_max_depth", 5)
        object.__setattr__(self, "support_full_text_search", True)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "namespace":
            if isinstance(value, str):
                object.__setattr__(self, "namespace", value)
            else:
                raise ValueError
        elif name == "database":
            if isinstance(value, str):
                object.__setattr__(self, "database", value)
            else:
                raise ValueError
        elif name == "storage_type":
            if isinstance(value, LocalSurrealDbStorageType):
                object.__setattr__(self, "storage_type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "storage_type", LocalSurrealDbStorageType(value))
            else:
                raise ValueError
        elif name == "path":
            if isinstance(value, str):
                object.__setattr__(self, "path", value)
            else:
                raise ValueError
        elif name == "database_type":
            if isinstance(value, DatabaseProviderType):
                if value != DatabaseProviderType.SURREALDB_LOCAL:
                    raise ValueError
            elif isinstance(value, str):
                converted_type = DatabaseProviderType(value)
                if converted_type != DatabaseProviderType.SURREALDB_LOCAL:
                    raise ValueError
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = super().to_dict(recursive=recursive)

        if self.namespace is not None:
            result["namespace"] = self.namespace
        if self.database is not None:
            result["database"] = self.database
        if self.storage_type is not None:
            result["storage_type"] = self.storage_type.value if recursive else self.storage_type
        if self.path is not None:
            result["path"] = self.path

        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LocalSurrealDbOptions":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "LocalSurrealDbOptions":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
