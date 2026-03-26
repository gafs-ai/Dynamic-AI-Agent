"""Data models for database provider tests (not pytest tests)."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from surrealdb import RecordID
from typing import cast


class TestRecord:
    """Test record data class with id field for database provider tests.

    Conforms to DataClassCodingRulesPython.md.
    """

    __test__ = False  # Tell pytest not to collect this as a test class

    def __init__(self) -> None:
        object.__setattr__(self, "id", None)
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "description", None)
        object.__setattr__(self, "created_at", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "id" or name == "$id":
            if value is None:
                object.__setattr__(self, "id", None)
            elif isinstance(value, str):
                # Normalize SurrealDB record IDs (e.g. "table:id") into the document ID only.
                object.__setattr__(self, "id", value.rsplit(":", 1)[-1])
            elif isinstance(value, RecordID):
                normalized = cast(str, value.id).rsplit(":", 1)[-1]
                object.__setattr__(self, "id", normalized)
            else:
                object.__setattr__(self, "id", str(value).rsplit(":", 1)[-1])
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
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TestRecord:
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> TestRecord:
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
