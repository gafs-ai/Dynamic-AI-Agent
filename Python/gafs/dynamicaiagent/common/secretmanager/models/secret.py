"""secret.py - Secret data class for storing encrypted credentials."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from surrealdb import RecordID


class Secret:
    """Represents an encrypted credential entry stored in the ``Secrets`` collection.

    The ``secret`` field holds encrypted values (persisted to the database).
    The ``raw_secret`` field holds plaintext values and is **never** persisted.

    When returned from SecretManager operations:
        - If decryption was performed: ``raw_secret`` is populated, ``secret`` is None.
        - If decryption was not performed: ``secret`` values are masked with ``"******"``,
          ``raw_secret`` is None.

    NOTE: ``raw_secret`` is a transient field — it must never be written to the database
    under any circumstances.
    """

    @staticmethod
    def COLLECTION_NAME() -> str:
        """Name of the SurrealDB collection for Secret entries."""
        return "Secrets"

    def __init__(self) -> None:
        """Initialize Secret with all fields set to None.

        NOTE: Uses object.__setattr__ to bypass the custom setter, which rejects None.
        """
        object.__setattr__(self, "id", None)           # str | None
        object.__setattr__(self, "name", None)         # str | None
        object.__setattr__(self, "secret", None)       # dict[str, Any] | None  (encrypted, persisted)
        object.__setattr__(self, "raw_secret", None)   # dict[str, Any] | None  (plaintext, transient)
        object.__setattr__(self, "description", None)  # str | None
        object.__setattr__(self, "tags", None)         # list[str] | None
        object.__setattr__(self, "created_at", None)   # datetime | None
        object.__setattr__(self, "updated_at", None)   # datetime | None
        object.__setattr__(self, "valid_until", None)  # datetime | None

    def __setattr__(self, name: str, value: Any) -> None:
        """Validate and set an attribute with type conversion support.

        Handles:
            - ``id``/``$id``: strips the SurrealDB table prefix from RecordID or string.
            - Datetime fields: accept datetime, ISO string, or epoch int.
            - Dict fields: accept dict only.
            - List fields: accept list only.

        Args:
            name: Attribute name.
            value: Attribute value.

        Raises:
            ValueError: If the value is not of the expected type.
        """
        if name == "id" or name == "$id":
            # Normalize SurrealDB RecordID: strip the table prefix (e.g. "Secrets:abc" -> "abc")
            if value is None:
                object.__setattr__(self, "id", None)
            elif isinstance(value, str):
                # Strip the table prefix if present
                object.__setattr__(self, "id", value.split(":", 1)[-1] if ":" in value else value)
            elif isinstance(value, RecordID):
                # RecordID.id holds the raw identifier part
                raw = str(value.id)
                object.__setattr__(self, "id", raw.split(":", 1)[-1] if ":" in raw else raw)
            else:
                raise ValueError

        elif name == "name":
            if value is None:
                object.__setattr__(self, "name", None)
            elif isinstance(value, str):
                object.__setattr__(self, "name", value)
            else:
                raise ValueError

        elif name == "secret":
            # Encrypted values dict — persisted to the database
            if value is None:
                object.__setattr__(self, "secret", None)
            elif isinstance(value, dict):
                object.__setattr__(self, "secret", value)
            else:
                raise ValueError

        elif name == "raw_secret":
            # Plaintext values dict — transient, never persisted
            if value is None:
                object.__setattr__(self, "raw_secret", None)
            elif isinstance(value, dict):
                object.__setattr__(self, "raw_secret", value)
            else:
                raise ValueError

        elif name == "description":
            if value is None:
                object.__setattr__(self, "description", None)
            elif isinstance(value, str):
                object.__setattr__(self, "description", value)
            else:
                raise ValueError

        elif name == "tags":
            if value is None:
                object.__setattr__(self, "tags", None)
            elif isinstance(value, list):
                object.__setattr__(self, "tags", value)
            else:
                raise ValueError

        elif name == "created_at":
            # Accept datetime, ISO string, or epoch int
            if value is None:
                object.__setattr__(self, "created_at", None)
            elif isinstance(value, datetime):
                object.__setattr__(self, "created_at", value)
            elif isinstance(value, str):
                object.__setattr__(self, "created_at", datetime.fromisoformat(value))
            elif isinstance(value, int):
                object.__setattr__(self, "created_at", datetime.fromtimestamp(value))
            else:
                raise ValueError

        elif name == "updated_at":
            if value is None:
                object.__setattr__(self, "updated_at", None)
            elif isinstance(value, datetime):
                object.__setattr__(self, "updated_at", value)
            elif isinstance(value, str):
                object.__setattr__(self, "updated_at", datetime.fromisoformat(value))
            elif isinstance(value, int):
                object.__setattr__(self, "updated_at", datetime.fromtimestamp(value))
            else:
                raise ValueError

        elif name == "valid_until":
            if value is None:
                object.__setattr__(self, "valid_until", None)
            elif isinstance(value, datetime):
                object.__setattr__(self, "valid_until", value)
            elif isinstance(value, str):
                object.__setattr__(self, "valid_until", datetime.fromisoformat(value))
            elif isinstance(value, int):
                object.__setattr__(self, "valid_until", datetime.fromtimestamp(value))
            else:
                raise ValueError

        else:
            # Pass through unknown attributes (e.g. SurrealDB metadata fields)
            object.__setattr__(self, name, value)

    def __repr__(self) -> str:
        """Return a JSON representation of this Secret (excludes raw_secret)."""
        return self.to_json()

    def to_dict(self, recursive: bool = False, exclude_id: bool = False) -> dict[str, Any]:
        """Convert this Secret to a dictionary suitable for database persistence.

        NOTE: ``raw_secret`` is NEVER included in the output — it is a transient field.

        Args:
            recursive: If True, convert nested objects (datetimes) to primitive types.
            exclude_id: If True, exclude the ``id`` field from the result.

        Returns:
            Dictionary containing only the persisted fields.
        """
        result: dict[str, Any] = {}

        # Include id unless explicitly excluded
        if not exclude_id and self.id is not None:
            result["id"] = self.id

        if self.name is not None:
            result["name"] = self.name

        # Include the encrypted secret dict (persisted field)
        # raw_secret is intentionally excluded — it is transient and never persisted
        if self.secret is not None:
            result["secret"] = self.secret

        if self.description is not None:
            result["description"] = self.description

        if self.tags is not None:
            result["tags"] = self.tags

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
        """Serialize this Secret to a JSON string (excludes raw_secret).

        Args:
            exclude_id: If True, exclude the ``id`` field from the output.

        Returns:
            JSON string representation of the persisted fields.
        """
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Secret":
        """Create a Secret instance from a dictionary.

        Typically used to deserialize records returned from the database.
        Unknown keys are ignored.  Fields set to None in data are skipped
        (the field retains its default None from ``__init__``).

        Args:
            data: Dictionary containing Secret field values.

        Returns:
            A new Secret instance.
        """
        entity = cls()

        for key, value in data.items():
            if hasattr(entity, key):
                # Skip None values — field stays at its initialized default (None)
                if value is not None:
                    setattr(entity, key, value)
            # Unknown fields are silently ignored

        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "Secret":
        """Create a Secret instance from a JSON string.

        Args:
            json_str: JSON string representation of a Secret.

        Returns:
            A new Secret instance.

        Raises:
            ValueError: If the JSON does not represent a dictionary.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
