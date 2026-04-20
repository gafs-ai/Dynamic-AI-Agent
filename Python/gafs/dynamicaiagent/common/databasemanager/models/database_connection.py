"""database_connection.py - DatabaseConnection data class.

Stores configuration for a database connection entry in the DatabaseConnections collection.
"""

from __future__ import annotations

import json
from typing import Any

from surrealdb import RecordID

from gafs.dynamicaiagent.utils.databaseprovider import DatabaseProviderType


class DatabaseConnection:
    """Represents a database connection configuration entry.

    This entry is stored in the DatabaseConnections collection of the default database.
    The raw_secret field is transient — it is NEVER written to the database.

    Attributes:
        id: Record ID. Normalized by stripping the SurrealDB table prefix.
        name: Unique human-readable name for the connection.
        description: Optional description.
        database_type: Database provider type.
        secret: ID of the associated Secret record containing credentials.
        raw_secret: Raw credential dict. Transient — never persisted or returned to callers.
        parameters: Non-secret connection parameters (e.g. endpoint, namespace).
    """

    @staticmethod
    def COLLECTION_NAME() -> str:
        """Name of the SurrealDB collection for DatabaseConnection entries."""
        return "DatabaseConnections"

    def __init__(self) -> None:
        object.__setattr__(self, "id", None)
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "description", None)
        object.__setattr__(self, "database_type", None)
        object.__setattr__(self, "secret", None)
        object.__setattr__(self, "raw_secret", None)
        object.__setattr__(self, "parameters", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "id" or name == "$id":
            # Normalize SurrealDB RecordID: strip table prefix (e.g. "table:abc" -> "abc")
            if value is None:
                object.__setattr__(self, "id", None)
            elif isinstance(value, str):
                object.__setattr__(self, "id", value.split(":", 1)[-1] if ":" in value else value)
            elif isinstance(value, RecordID):
                # RecordID.id holds the raw id part
                raw = str(value.id)
                object.__setattr__(self, "id", raw.split(":", 1)[-1] if ":" in raw else raw)
            else:
                raise ValueError(f"DatabaseConnection.id must be str or RecordID, got {type(value)}")
        elif name == "name":
            if value is None:
                object.__setattr__(self, "name", None)
            elif isinstance(value, str):
                object.__setattr__(self, "name", value)
            else:
                raise ValueError(f"DatabaseConnection.name must be str, got {type(value)}")
        elif name == "description":
            if value is None:
                object.__setattr__(self, "description", None)
            elif isinstance(value, str):
                object.__setattr__(self, "description", value)
            else:
                raise ValueError(f"DatabaseConnection.description must be str, got {type(value)}")
        elif name == "database_type":
            if value is None:
                object.__setattr__(self, "database_type", None)
            elif isinstance(value, DatabaseProviderType):
                object.__setattr__(self, "database_type", value)
            elif isinstance(value, str):
                # Auto-convert string to enum
                object.__setattr__(self, "database_type", DatabaseProviderType(value))
            else:
                raise ValueError(
                    f"DatabaseConnection.database_type must be DatabaseProviderType or str, got {type(value)}"
                )
        elif name == "secret":
            # Normalize SurrealDB RecordID for secret as well
            if value is None:
                object.__setattr__(self, "secret", None)
            elif isinstance(value, str):
                object.__setattr__(self, "secret", value.split(":", 1)[-1] if ":" in value else value)
            elif isinstance(value, RecordID):
                raw = str(value.id)
                object.__setattr__(self, "secret", raw.split(":", 1)[-1] if ":" in raw else raw)
            else:
                raise ValueError(f"DatabaseConnection.secret must be str or RecordID, got {type(value)}")
        elif name == "raw_secret":
            # raw_secret is transient and must be a dict
            if value is None:
                object.__setattr__(self, "raw_secret", None)
            elif isinstance(value, dict):
                object.__setattr__(self, "raw_secret", value)
            else:
                raise ValueError(f"DatabaseConnection.raw_secret must be dict, got {type(value)}")
        elif name == "parameters":
            if value is None:
                object.__setattr__(self, "parameters", None)
            elif isinstance(value, dict):
                object.__setattr__(self, "parameters", value)
            else:
                raise ValueError(f"DatabaseConnection.parameters must be dict, got {type(value)}")
        else:
            raise ValueError(f"Unknown attribute: {name}")

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False, exclude_id: bool = False) -> dict[str, Any]:
        """Serialize to dict. raw_secret is always excluded.

        Args:
            recursive: If True, convert enum values to strings.
            exclude_id: If True, exclude the id field.

        Returns:
            Dict representation without raw_secret.
        """
        result: dict[str, Any] = {}

        if not exclude_id and self.id is not None:
            result["id"] = self.id

        if self.name is not None:
            result["name"] = self.name

        if self.description is not None:
            result["description"] = self.description

        if self.database_type is not None:
            result["database_type"] = self.database_type.value if recursive else self.database_type

        if self.secret is not None:
            result["secret"] = self.secret

        # raw_secret is intentionally excluded from all serialization

        if self.parameters is not None:
            result["parameters"] = self.parameters

        return result

    def to_json(self, exclude_id: bool = False) -> str:
        """Serialize to JSON string. raw_secret is always excluded.

        Args:
            exclude_id: If True, exclude the id field.

        Returns:
            JSON representation.
        """
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DatabaseConnection":
        """Deserialize from dict.

        Args:
            data: Dict with connection data.

        Returns:
            DatabaseConnection instance.
        """
        obj = cls()
        for key, value in data.items():
            if value is not None and hasattr(obj, key):
                setattr(obj, key, value)
        return obj

    @classmethod
    def from_json(cls, json_str: str) -> "DatabaseConnection":
        """Deserialize from JSON string.

        Args:
            json_str: JSON string.

        Returns:
            DatabaseConnection instance.

        Raises:
            ValueError: If json_str is not a JSON object.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError("JSON must be an object")
        return cls.from_dict(converted)
