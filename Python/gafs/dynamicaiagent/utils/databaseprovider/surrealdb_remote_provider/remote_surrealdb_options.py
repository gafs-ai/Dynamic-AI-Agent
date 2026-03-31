from __future__ import annotations

import json
from typing import Any

from ..database_provider_options import DatabaseProviderOptions
from ..database_provider_type import DatabaseProviderType


class RemoteSurrealDbOptions(DatabaseProviderOptions):
    """Options for Remote SurrealDB provider.

    Attributes:
        endpoint: SurrealDB server endpoint URL.
        namespace: SurrealDB namespace.
        database: SurrealDB database name.
        username: Authentication username.
        password: Authentication password.
        database_type: Database type (should be SURREALDB_REMOTE).
        database_name: Logical database name for the provider.
        auth_level: Authentication level (default: "database").
        support_vector_search: Whether vector search is supported (default: True).
        vector_graph_search_max_depth: Maximum depth for vector graph search (default: 5).
        support_full_text_search: Whether full-text search is supported (default: True).
        max_limit: Maximum query result limit (default: 100).
    """

    def __init__(self) -> None:
        """Initialize all fields to None or appropriate default values."""
        # Initialize parent class fields first
        super().__init__()

        # Initialize child class specific fields
        object.__setattr__(self, "endpoint", None)
        object.__setattr__(self, "namespace", None)
        object.__setattr__(self, "database", None)
        object.__setattr__(self, "username", None)
        object.__setattr__(self, "password", None)
        object.__setattr__(self, "auth_level", "database")

        # Override parent class defaults with child class specific values
        object.__setattr__(self, "database_type", DatabaseProviderType.SURREALDB_REMOTE)
        object.__setattr__(self, "support_vector_search", True)
        object.__setattr__(self, "vector_graph_search_max_depth", 5)
        object.__setattr__(self, "support_full_text_search", True)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "endpoint":
            if isinstance(value, str):
                object.__setattr__(self, "endpoint", value)
            else:
                raise ValueError
        elif name == "namespace":
            if isinstance(value, str):
                object.__setattr__(self, "namespace", value)
            else:
                raise ValueError
        elif name == "database":
            if isinstance(value, str):
                object.__setattr__(self, "database", value)
            else:
                raise ValueError
        elif name == "username":
            if isinstance(value, str):
                object.__setattr__(self, "username", value)
            else:
                raise ValueError
        elif name == "password":
            if isinstance(value, str):
                object.__setattr__(self, "password", value)
            else:
                raise ValueError
        elif name == "auth_level":
            if isinstance(value, str):
                object.__setattr__(self, "auth_level", value)
            else:
                raise ValueError
        elif name == "database_type":
            if isinstance(value, DatabaseProviderType):
                if value != DatabaseProviderType.SURREALDB_REMOTE:
                    raise ValueError
            elif isinstance(value, str):
                converted_type = DatabaseProviderType(value)
                if converted_type != DatabaseProviderType.SURREALDB_REMOTE:
                    raise ValueError
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        # Get parent class fields
        result: dict[str, Any] = super().to_dict(recursive=recursive)

        # Add child class specific fields
        if self.endpoint is not None:
            result["endpoint"] = self.endpoint
        if self.namespace is not None:
            result["namespace"] = self.namespace
        if self.database is not None:
            result["database"] = self.database
        if self.username is not None:
            result["username"] = self.username
        if self.password is not None:
            result["password"] = self.password
        if self.auth_level is not None:
            result["auth_level"] = self.auth_level

        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RemoteSurrealDbOptions":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "RemoteSurrealDbOptions":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
