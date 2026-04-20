import json
from enum import Enum
from typing import Any

from ..database_provider_options import DatabaseProviderOptions
from ..database_provider_type import DatabaseProviderType
from ..retry_options import RetryOptions


class LocalSurrealDbStorageType(Enum):
    """Storage backend options for the embedded SurrealDB provider.

    MEM: In-memory storage. No persistence; data is lost on shutdown.
    FILE: File-based persistent storage.
    SURREALKV: SurrealKV persistent storage (default).
    ROCKSDB: RocksDB persistent storage.
    """

    MEM = "mem"
    FILE = "file"
    SURREALKV = "surrealkv"
    ROCKSDB = "rocksdb"


class LocalSurrealDbOptions(DatabaseProviderOptions):
    """Configuration for the embedded (local) SurrealDB provider.

    Inherits base fields (``database_type``, ``database_name``,
    ``retry_options``) from ``DatabaseProviderOptions`` and adds
    SurrealDB-specific fields.

    NOTE: ``database_type`` is fixed to ``SURREALDB_LOCAL``; setting it to
    any other value raises ``ValueError``.
    NOTE: When ``storage_type`` is ``MEM``, the ``path`` attribute is
    ignored.
    """

    def __init__(self) -> None:
        # Initialize parent class fields first.
        super().__init__()

        # Initialize child class specific fields.
        object.__setattr__(self, "namespace", None)
        object.__setattr__(self, "database", None)
        object.__setattr__(self, "storage_type", None)
        object.__setattr__(self, "path", None)

        # Fix database_type to SURREALDB_LOCAL and set storage_type default.
        object.__setattr__(self, "database_type", DatabaseProviderType.SURREALDB_LOCAL)
        object.__setattr__(self, "storage_type", LocalSurrealDbStorageType.SURREALKV)

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
            # Accept either a LocalSurrealDbStorageType enum or its string value.
            if isinstance(value, LocalSurrealDbStorageType):
                object.__setattr__(self, "storage_type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "storage_type", LocalSurrealDbStorageType(value))
            else:
                raise ValueError
        elif name == "path":
            if isinstance(value, str) or value is None:
                object.__setattr__(self, "path", value)
            else:
                raise ValueError
        elif name == "database_type":
            # database_type must always be SURREALDB_LOCAL.
            if isinstance(value, DatabaseProviderType):
                if value != DatabaseProviderType.SURREALDB_LOCAL:
                    raise ValueError
                object.__setattr__(self, "database_type", value)
            elif isinstance(value, str):
                converted = DatabaseProviderType(value)
                if converted != DatabaseProviderType.SURREALDB_LOCAL:
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

        Args:
            recursive: When True, convert enums to their string values and
                nested objects to dicts.

        Returns:
            Dictionary representation of these options.
        """
        # Start with the base class fields.
        result: dict[str, Any] = super().to_dict(recursive=recursive)

        if self.namespace is not None:
            result["namespace"] = self.namespace

        if self.database is not None:
            result["database"] = self.database

        if self.storage_type is not None:
            if recursive:
                result["storage_type"] = self.storage_type.value
            else:
                result["storage_type"] = self.storage_type

        if self.path is not None:
            result["path"] = self.path

        return result

    def to_json(self) -> str:
        """Serialize these options to a JSON string.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LocalSurrealDbOptions":
        """Create a LocalSurrealDbOptions instance from a dictionary.

        Args:
            data: Dictionary with option field values.

        Returns:
            A new LocalSurrealDbOptions instance.
        """
        entity = cls()

        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)

        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "LocalSurrealDbOptions":
        """Create a LocalSurrealDbOptions instance from a JSON string.

        Args:
            json_str: JSON string representation.

        Returns:
            A new LocalSurrealDbOptions instance.

        Raises:
            ValueError: If the JSON does not represent a dictionary.
        """
        converted: Any = json.loads(json_str)

        if not isinstance(converted, dict):
            raise ValueError

        return cls.from_dict(converted)
