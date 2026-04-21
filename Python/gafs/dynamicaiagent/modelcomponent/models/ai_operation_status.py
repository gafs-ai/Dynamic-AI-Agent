"""AiOperationStatus — records the outcome and token usage of an AI operation."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any


class AiOperationStatusEnum(Enum):
    """Enum for the completion state of an AI operation."""

    COMPLETED = "completed"
    ERROR = "error"
    IN_PROGRESS = "in_progress"


class AiOperationStatus:
    """Metadata about a completed AI operation (token usage, status, etc.)."""

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
            elif value is None:
                object.__setattr__(self, "status", None)
            else:
                raise ValueError
        elif name == "operation_id":
            if isinstance(value, str) or value is None:
                object.__setattr__(self, "operation_id", value)
            else:
                raise ValueError
        elif name == "input_tokens":
            if isinstance(value, int) or value is None:
                object.__setattr__(self, "input_tokens", value)
            else:
                raise ValueError
        elif name == "output_tokens":
            if isinstance(value, int) or value is None:
                object.__setattr__(self, "output_tokens", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
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
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AiOperationStatus":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "AiOperationStatus":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
