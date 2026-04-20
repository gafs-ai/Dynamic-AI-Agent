"""Data models used in database provider tests.

NOTE: This module is NOT a test module.  It defines test-only data classes
that are used across multiple test files.  The ``__test__ = False`` flag
prevents pytest from treating ``TestRecord`` as a test class.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from surrealdb import RecordID


class TestRecord:
    """A simple data class used as a dummy record in database provider tests.

    Conforms to DataClassCodingRulesPython.md.

    NOTE: pytest will not collect this class as a test because ``__test__``
    is set to ``False``.
    """

    __test__ = False  # Tell pytest not to collect this as a test class.

    def __init__(self) -> None:
        object.__setattr__(self, "id", None)
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "description", None)
        object.__setattr__(self, "created_at", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("id", "$id"):
            # Normalize SurrealDB RecordID and "table:id" strings to just the id part.
            if value is None:
                object.__setattr__(self, "id", None)
            elif isinstance(value, str):
                object.__setattr__(self, "id", value.rsplit(":", 1)[-1])
            elif isinstance(value, RecordID):
                object.__setattr__(self, "id", str(value.id))
            else:
                object.__setattr__(self, "id", str(value))
        elif name == "name":
            if value is None or isinstance(value, str):
                object.__setattr__(self, "name", value)
            else:
                raise ValueError
        elif name == "description":
            if value is None or isinstance(value, str):
                object.__setattr__(self, "description", value)
            else:
                raise ValueError
        elif name == "created_at":
            if value is None:
                object.__setattr__(self, "created_at", None)
            elif isinstance(value, datetime):
                object.__setattr__(self, "created_at", value)
            elif isinstance(value, str):
                object.__setattr__(
                    self,
                    "created_at",
                    datetime.fromisoformat(value.replace("Z", "+00:00")),
                )
            elif isinstance(value, (int, float)):
                object.__setattr__(self, "created_at", datetime.fromtimestamp(value))
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(
        self,
        recursive: bool = False,
        exclude_id: bool = False,
    ) -> dict[str, Any]:
        """Serialize this record to a dictionary.

        Args:
            recursive: When True, convert datetime to ISO string.
            exclude_id: When True, omit the ``id`` field.

        Returns:
            Dictionary representation of this record.
        """
        result: dict[str, Any] = {}

        if not exclude_id:
            if self.id is not None:
                result["id"] = self.id

        if self.name is not None:
            result["name"] = self.name

        if self.description is not None:
            result["description"] = self.description

        if self.created_at is not None:
            if recursive:
                result["created_at"] = self.created_at.isoformat()
            else:
                result["created_at"] = self.created_at

        return result

    def to_json(self, exclude_id: bool = False) -> str:
        """Serialize this record to a JSON string.

        Args:
            exclude_id: When True, omit the ``id`` field.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestRecord":
        """Create a TestRecord from a dictionary.

        Args:
            data: Dictionary with record field values.

        Returns:
            A new TestRecord instance.
        """
        entity = cls()

        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)

        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "TestRecord":
        """Create a TestRecord from a JSON string.

        Args:
            json_str: JSON string representation.

        Returns:
            A new TestRecord instance.

        Raises:
            ValueError: If the JSON does not represent a dictionary.
        """
        converted: Any = json.loads(json_str)

        if not isinstance(converted, dict):
            raise ValueError

        return cls.from_dict(converted)
