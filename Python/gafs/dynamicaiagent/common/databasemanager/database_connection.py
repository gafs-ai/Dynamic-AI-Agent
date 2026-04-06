import json
from typing import Any, cast
from surrealdb import RecordID

from gafs.dynamicaiagent.utils.databaseprovider import DatabaseProviderType


class DatabaseConnection:
    """Represents a database connection configuration entry.

    Stored in the ``databases`` collection of the default database.

    Attributes:
        id: Record identifier (normalized from SurrealDB RecordID).
        name: Unique human-readable name for the connection.
        description: Optional description.
        database_type: Database provider type (e.g.
            :py:attr:`DatabaseProviderType.SURREALDB_REMOTE`). Accepts both
            the enum value and its string representation for convenience.
        secret: ID of the associated Secret record containing credentials.
        raw_secret: Transient field for raw credential data used during
            :py:meth:`add_connection`. Never persisted to the database as raw data.
        parameters: Non-secret connection parameters (e.g. endpoint,
            namespace, database name).
    """

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
            if isinstance(value, str):
                # Normalize SurrealDB record IDs (e.g. "table:id") into the document ID only.
                object.__setattr__(self, "id", value.rsplit(":", 1)[-1])
            elif isinstance(value, RecordID):
                normalized = cast(str, value.id).rsplit(":", 1)[-1]
                object.__setattr__(self, "id", normalized)
            else:
                raise ValueError
        elif name == "name":
            if isinstance(value, str):
                object.__setattr__(self, "name", value)
            else:
                raise ValueError
        elif name == "description":
            if isinstance(value, str):
                object.__setattr__(self, "description", value)
            else:
                raise ValueError
        elif name == "database_type":
            if isinstance(value, DatabaseProviderType):
                object.__setattr__(self, "database_type", value)
            elif isinstance(value, str):
                # Automatic conversion from string to enum.
                object.__setattr__(self, "database_type", DatabaseProviderType(value))
            else:
                raise ValueError
        elif name == "secret":
            if isinstance(value, str):
                # Normalize SurrealDB record IDs (e.g. "table:id") into the document ID only.
                object.__setattr__(self, "secret", value.rsplit(":", 1)[-1])
            elif isinstance(value, RecordID):
                normalized = cast(str, value.id).rsplit(":", 1)[-1]
                object.__setattr__(self, "secret", normalized)
            else:
                raise ValueError
        elif name == "raw_secret":
            if isinstance(value, dict):
                object.__setattr__(self, "raw_secret", value)
            else:
                raise ValueError
        elif name == "parameters":
            if isinstance(value, dict):
                object.__setattr__(self, "parameters", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False, exclude_id: bool = False) -> dict[str, Any]:
        """Convert to a dictionary suitable for JSON serialization or database writes.

        The ``raw_secret`` field is intentionally excluded because it is
        transient and must never be persisted.

        Args:
            recursive: When ``True``, enum values (e.g. ``database_type``) are
                serialized to their string ``.value`` form. When ``False``, enum
                objects are kept as-is.
            exclude_id: When ``True`` the ``id`` field is omitted from the
                result (useful for CREATE queries).

        Returns:
            Dictionary representation of this instance.
        """
        result: dict[str, Any] = {}
        if not exclude_id:
            if self.id is not None:
                result["id"] = self.id
        if self.name is not None:
            result["name"] = self.name
        if self.description is not None:
            result["description"] = self.description
        if self.database_type is not None:
            if recursive:
                result["database_type"] = self.database_type.value
            else:
                result["database_type"] = self.database_type
        if self.secret is not None:
            result["secret"] = self.secret
        # raw_secret is intentionally excluded — transient field, never stored.
        if self.parameters is not None:
            result["parameters"] = self.parameters
        return result

    def to_json(self, exclude_id: bool = False) -> str:
        """Convert to a JSON string.

        Args:
            exclude_id: When ``True`` the ``id`` field is omitted.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DatabaseConnection":
        """Create an instance from a dictionary.

        Args:
            data: Dictionary containing field data. Unknown keys are ignored.
                Fields with ``None`` values are skipped to preserve the
                ``None`` defaults set by ``__init__``.

        Returns:
            New ``DatabaseConnection`` instance populated from *data*.
        """
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "DatabaseConnection":
        """Create an instance from a JSON string.

        Args:
            json_str: JSON-encoded dictionary.

        Returns:
            New ``DatabaseConnection`` instance.

        Raises:
            ValueError: If the JSON does not represent a dictionary.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
