import json
from datetime import datetime
from typing import Any, cast
from surrealdb.types import RecordID

class Secret:
    """Secret entity used to store secret values.

    The `secret` field is a dictionary of key-value pairs.

    - Keys starting with ``raw_`` represent raw (plain text) values.
    - Keys starting with ``encrypted_`` represent encrypted values.

    NOTE: Encryption and decryption of these values are handled by `SecretManager`.
    """

    def __init__(self) -> None:
        """Initialize all fields to None."""
        object.__setattr__(self, "id", None) # str
        object.__setattr__(self, "name", None) # str
        object.__setattr__(self, "secret", None) # dict[str, Any]
        object.__setattr__(self, "description", None) # str
        object.__setattr__(self, "created_at", None) # datetime
        object.__setattr__(self, "updated_at", None) # datetime
        object.__setattr__(self, "valid_until", None) # datetime

    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute with type validation and conversion.

        Args:
            name: The name of the attribute to set.
            value: The value to set.

        Raises:
            ValueError: If the value type is invalid.
        """
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
        elif name == "secret":
            if isinstance(value, dict):
                object.__setattr__(self, "secret", value)
            else:
                raise ValueError
        elif name == "description":
            if isinstance(value, str):
                object.__setattr__(self, "description", value)
            else:
                raise ValueError
        elif name == "created_at":
            if isinstance(value, datetime):
                object.__setattr__(self, "created_at", value)
            elif isinstance(value, str):
                object.__setattr__(self, "created_at", datetime.fromisoformat(value))
            elif isinstance(value, int):
                object.__setattr__(self, "created_at", datetime.fromtimestamp(value))
            else:
                raise ValueError
        elif name == "updated_at":
            if isinstance(value, datetime):
                object.__setattr__(self, "updated_at", value)
            elif isinstance(value, str):
                object.__setattr__(self, "updated_at", datetime.fromisoformat(value))
            elif isinstance(value, int):
                object.__setattr__(self, "updated_at", datetime.fromtimestamp(value))
            else:
                raise ValueError
        elif name == "valid_until":
            if isinstance(value, datetime):
                object.__setattr__(self, "valid_until", value)
            elif isinstance(value, str):
                object.__setattr__(self, "valid_until", datetime.fromisoformat(value))
            elif isinstance(value, int):
                object.__setattr__(self, "valid_until", datetime.fromtimestamp(value))
            else:
                raise ValueError
        else:
            object.__setattr__(self, name, value)

    def to_dict(self, recursive: bool = False, exclude_id: bool = False) -> dict[str, Any]:
        """Convert the Secret instance to a dictionary.

        Args:
            recursive: If True, convert nested objects to primitive types.
            exclude_id: If True, exclude the id field from the result.

        Returns:
            A dictionary representation of the Secret instance.
        """
        result: dict[str, Any] = {}

        if not exclude_id:
            if self.id is not None:
                result["id"] = self.id

        if self.name is not None:
            result["name"] = self.name

        if self.secret is not None:
            result["secret"] = self.secret

        if self.description is not None:
            result["description"] = self.description

        if self.created_at is not None:
            if recursive:
                result["created_at"] = self.created_at.isoformat()
            else:
                result["created_at"] = self.created_at

        if self.updated_at is not None:
            if recursive:
                result["updated_at"] = self.updated_at.isoformat()
            else:
                result["updated_at"] = self.updated_at

        if self.valid_until is not None:
            if recursive:
                result["valid_until"] = self.valid_until.isoformat()
            else:
                result["valid_until"] = self.valid_until

        return result

    def to_json(self, exclude_id: bool = False) -> str:
        """Convert the Secret instance to a JSON string.

        Args:
            exclude_id: If True, exclude the id field from the result.

        Returns:
            A JSON string representation of the Secret instance.
        """
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Secret":
        """Create a Secret instance from a dictionary.

        Args:
            data: A dictionary containing Secret data.

        Returns:
            A new Secret instance.
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
    def from_json(cls, json_str: str) -> "Secret":
        """Create a Secret instance from a JSON string.

        Args:
            json_str: A JSON string containing Secret data.

        Returns:
            A new Secret instance.

        Raises:
            ValueError: If the JSON string is not a dictionary.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
