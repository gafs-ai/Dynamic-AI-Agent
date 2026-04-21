"""AiResponse — value object returned by AI model invocations, containing output and status metadata."""

from __future__ import annotations

import json
from typing import Any

from .ai_operation_status import AiOperationStatus
from .ai_output import AiOutput


class AiResponse:
    """The response from an AI model operation, containing the output and status metadata."""

    def __init__(self) -> None:
        object.__setattr__(self, "output", None)
        object.__setattr__(self, "status", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "output":
            if isinstance(value, AiOutput):
                object.__setattr__(self, "output", value)
            else:
                raise ValueError
        elif name == "status":
            if isinstance(value, AiOperationStatus):
                object.__setattr__(self, "status", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.output is not None:
            if recursive:
                result["output"] = self.output.to_dict(recursive=True)
            else:
                result["output"] = self.output
        if self.status is not None:
            if recursive:
                result["status"] = self.status.to_dict(recursive=True)
            else:
                result["status"] = self.status
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AiResponse":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "AiResponse":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
