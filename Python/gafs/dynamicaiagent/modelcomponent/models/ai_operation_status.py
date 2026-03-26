from __future__ import annotations

import json
from enum import Enum
from typing import Any


class AiOperationStatus:
    """Status of an AI operation (e.g., token usage, operation ID).

    Holds metadata about an AI request/response such as completion status,
    operation identifier, and token counts.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "status", None)
        object.__setattr__(self, "operation_id", None)
        object.__setattr__(self, "input_tokens", None)
        object.__setattr__(self, "output_tokens", None)
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name == "status":
            if isinstance(value, AiOperationStatusEnum):
                object.__setattr__(self, "status", value)
            elif isinstance(value, str):
                object.__setattr__(self, "status", AiOperationStatusEnum(value))
            else:
                raise ValueError
        elif name == "operation_id":
            if isinstance(value, str):
                object.__setattr__(self, "operation_id", value)
            else:
                raise ValueError
        elif name == "input_tokens":
            if isinstance(value, int):
                object.__setattr__(self, "input_tokens", value)
            else:
                raise ValueError
        elif name == "output_tokens":
            if isinstance(value, int):
                object.__setattr__(self, "output_tokens", value)
            else:
                raise ValueError
        else:
            raise ValueError
    
    def __repr__(self) -> str:
        return self.to_json()
    
    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a dictionary.

        Args:
            recursive: If True, convert Enum fields to their string values.

        Returns:
            Dictionary representation of this instance.
        """
        result: dict[str, Any] = {}
        if self.status is not None:
            if recursive:
                result["status"] = self.status.value
            else:
                result["status"] = self.status
        if self.operation_id is not None:
            result["operation_id"] = self.operation_id
        if self.input_tokens is not None:
            result["input_tokens"] = self.input_tokens
        if self.output_tokens is not None:
            result["output_tokens"] = self.output_tokens
        return result
    
    def to_json(self) -> str:
        """Serialize to a JSON string.

        Returns:
            JSON string representation. Nested objects are converted to primitives.
        """
        return json.dumps(self.to_dict(recursive=True))
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AiOperationStatus":
        """Create an instance from a dictionary.

        Args:
            data: Dictionary containing status fields. None values are skipped.

        Returns:
            New AiOperationStatus instance.

        Raises:
            ValueError: When a field value has an invalid type.
        """
        entity: AiOperationStatus = cls()
        for key, value in data.items():
            setattr(entity, key, value)
        return entity
    
    @classmethod
    def from_json(cls, json_str: str) -> "AiOperationStatus":
        """Create an instance from a JSON string.

        Args:
            json_str: JSON string that parses to a dictionary.

        Returns:
            New AiOperationStatus instance.

        Raises:
            ValueError: When json_str does not parse to a dict or a field is invalid.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class AiOperationStatusEnum(Enum):
    """Enum for AI operation lifecycle status."""

    COMPLETED = "completed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    CANCELLED = "cancelled"
    QUEUED = "queued"
    INCOMPLETE = "incomplete"
