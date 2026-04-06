from __future__ import annotations

import json
from typing import Any

from .ai_operation_status import AiOperationStatus
from .ai_output import AiOutput


class AiResponse:
    """Response from an AI operation: output and status metadata.

    Holds the operation result (AiOutput subclass) and optional AiOperationStatus
    (e.g., token usage, operation ID).
    """

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
            pass # Drop unknown attributes
    
    def __repr__(self) -> str:
        return self.to_json()
    
    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a dictionary.

        Args:
            recursive: If True, convert nested objects (output, status) to primitives.

        Returns:
            Dictionary with output and status fields.
        """
        result: dict[str, Any] = {}
        if self.output is not None:
            result["output"] = self.output.to_dict(recursive=recursive)
        if self.status is not None:
            result["status"] = self.status.to_dict(recursive=recursive)
        return result
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AiResponse:
        """Create an instance from a dictionary. None values are skipped.

        Args:
            data: Dictionary containing output and status. output must be deserializable
                to an AiOutput subclass (e.g., TextCompletionOutput, ChatCompletionOutput).

        Returns:
            New AiResponse instance.

        Raises:
            ValueError: When a field value has an invalid type.
        """
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity
    
    @classmethod
    def from_json(cls, json_str: str) -> AiResponse:
        """Create an instance from a JSON string.

        Args:
            json_str: JSON string that parses to a dictionary.

        Returns:
            New AiResponse instance.

        Raises:
            ValueError: When json_str does not parse to a dict or a field is invalid.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
