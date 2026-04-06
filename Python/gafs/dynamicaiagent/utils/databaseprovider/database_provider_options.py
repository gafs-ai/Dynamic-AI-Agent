from __future__ import annotations

import json
from abc import ABC
from typing import Any

from .database_provider_type import DatabaseProviderType


class DatabaseProviderOptions(ABC):
    """Base class for database provider options.

    The actual option class should inherit this and be implemented for each database provider.
    Each implementation should define the following attributes:
        database_type: DatabaseProviderType
        database_name: str
        support_vector_search: bool
        vector_graph_search_max_depth: int
        support_full_text_search: bool
        max_limit: int
    """

    def __init__(self):
        object.__setattr__(self, "database_type", None)
        object.__setattr__(self, "database_name", None)
        object.__setattr__(self, "support_vector_search", False)
        object.__setattr__(self, "vector_graph_search_max_depth", 0)
        object.__setattr__(self, "support_full_text_search", False)
        object.__setattr__(self, "max_limit", 100)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "database_type":
            if isinstance(value, DatabaseProviderType):
                object.__setattr__(self, "database_type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "database_type", DatabaseProviderType(value))
            else:
                raise ValueError
        elif name == "database_name":
            if isinstance(value, str):
                object.__setattr__(self, "database_name", value)
            else:
                raise ValueError
        elif name == "support_vector_search":
            if isinstance(value, bool):
                object.__setattr__(self, "support_vector_search", value)
            else:
                raise ValueError
        elif name == "vector_graph_search_max_depth":
            if isinstance(value, int):
                object.__setattr__(self, "vector_graph_search_max_depth", value)
            else:
                raise ValueError
        elif name == "support_full_text_search":
            if isinstance(value, bool):
                object.__setattr__(self, "support_full_text_search", value)
            else:
                raise ValueError
        elif name == "max_limit":
            if isinstance(value, int):
                object.__setattr__(self, "max_limit", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Serialize options to a dictionary.

        Args:
            recursive: When True, enum values are serialized to their raw string value.

        Returns:
            Dictionary representation of these options.
        """
        result: dict[str, Any] = {}
        if self.database_type is not None:
            if recursive:
                result["database_type"] = self.database_type.value
            else:
                result["database_type"] = self.database_type
        if self.database_name is not None:
            result["database_name"] = self.database_name
        if self.support_vector_search is not None:
            result["support_vector_search"] = self.support_vector_search
        if self.vector_graph_search_max_depth is not None:
            result["vector_graph_search_max_depth"] = self.vector_graph_search_max_depth
        if self.support_full_text_search is not None:
            result["support_full_text_search"] = self.support_full_text_search
        if self.max_limit is not None:
            result["max_limit"] = self.max_limit
        return result

    def to_json(self) -> str:
        """Serialize options to a JSON string.

        Returns:
            JSON string representation of these options.
        """
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DatabaseProviderOptions":
        """Deserialize options from a dictionary.

        Unknown keys are silently ignored.

        Args:
            data: Dictionary to deserialize from.

        Returns:
            New instance populated from the dictionary.
        """
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "DatabaseProviderOptions":
        """Deserialize options from a JSON string.

        Args:
            json_str: JSON string to deserialize from.

        Returns:
            New instance populated from the JSON string.

        Raises:
            ValueError: When the JSON string does not represent a valid dictionary.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
