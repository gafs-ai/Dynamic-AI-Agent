import json
from typing import Any

from ..database_provider_options import DatabaseProviderOptions
from ..database_provider_type import DatabaseProviderType
from ..retry_options import RetryOptions


class RemoteSurrealDbOptions(DatabaseProviderOptions):
    """Configuration for the remote SurrealDB provider (WebSocket connection).

    Inherits base fields (``database_type``, ``database_name``,
    ``retry_options``) from ``DatabaseProviderOptions`` and adds
    SurrealDB-specific connection and authentication fields.

    NOTE: ``database_type`` is fixed to ``SURREALDB_REMOTE``; setting it to
    any other value raises ``ValueError``.
    NOTE: ``password`` must never be logged or stored in plaintext outside
    of this options object.
    """

    def __init__(self) -> None:
        # Initialize parent class fields first.
        super().__init__()

        # Initialize child class specific fields.
        object.__setattr__(self, "endpoint", None)
        object.__setattr__(self, "namespace", None)
        object.__setattr__(self, "database", None)
        object.__setattr__(self, "username", None)
        object.__setattr__(self, "password", None)
        object.__setattr__(self, "auth_level", None)

        # Fix database_type to SURREALDB_REMOTE and set auth_level default.
        object.__setattr__(self, "database_type", DatabaseProviderType.SURREALDB_REMOTE)
        object.__setattr__(self, "auth_level", "database")

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
            # database_type must always be SURREALDB_REMOTE.
            if isinstance(value, DatabaseProviderType):
                if value != DatabaseProviderType.SURREALDB_REMOTE:
                    raise ValueError
                object.__setattr__(self, "database_type", value)
            elif isinstance(value, str):
                converted = DatabaseProviderType(value)
                if converted != DatabaseProviderType.SURREALDB_REMOTE:
                    raise ValueError
                object.__setattr__(self, "database_type", converted)
            else:
                raise ValueError
        else:
            # Delegate all other attributes (database_name, retry_options) to parent.
            super().__setattr__(name, value)

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Serialize all fields to a dictionary.

        NOTE: The ``password`` field is intentionally included in the
        serialized output so that options can be reconstructed from the dict.
        Callers should treat the result carefully and avoid logging it.

        Args:
            recursive: When True, convert enums to their string values and
                nested objects to dicts.

        Returns:
            Dictionary representation of these options.
        """
        # Start with the base class fields.
        result: dict[str, Any] = super().to_dict(recursive=recursive)

        if self.endpoint is not None:
            result["endpoint"] = self.endpoint

        if self.namespace is not None:
            result["namespace"] = self.namespace

        if self.database is not None:
            result["database"] = self.database

        if self.username is not None:
            result["username"] = self.username

        # NOTE: password is included for round-trip serialization.
        # Never log the result of to_dict / to_json.
        if self.password is not None:
            result["password"] = self.password

        if self.auth_level is not None:
            result["auth_level"] = self.auth_level

        return result

    def to_json(self) -> str:
        """Serialize these options to a JSON string.

        NOTE: The resulting string contains the password.  Never log it.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RemoteSurrealDbOptions":
        """Create a RemoteSurrealDbOptions instance from a dictionary.

        Args:
            data: Dictionary with option field values.

        Returns:
            A new RemoteSurrealDbOptions instance.
        """
        entity = cls()

        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)

        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "RemoteSurrealDbOptions":
        """Create a RemoteSurrealDbOptions instance from a JSON string.

        Args:
            json_str: JSON string representation.

        Returns:
            A new RemoteSurrealDbOptions instance.

        Raises:
            ValueError: If the JSON does not represent a dictionary.
        """
        converted: Any = json.loads(json_str)

        if not isinstance(converted, dict):
            raise ValueError

        return cls.from_dict(converted)
