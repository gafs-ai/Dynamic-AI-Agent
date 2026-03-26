from __future__ import annotations

import json
from abc import ABC
from typing import Any

from .message import Message


class AiPayload(ABC):
    """Base payload class for model requests.

    Implements custom serialization according to project data class rules.
    """

    def __init__(self) -> None:
        pass

    def __setattr__(self, name: str, value: Any) -> None:
        pass

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        return {}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AiPayload:
        return cls()

    @classmethod
    def from_json(cls, json_str: str) -> AiPayload:
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class TextCompletionPayload(AiPayload):
    """Payload for text completion style models."""

    def __init__(self) -> None:
        super().__init__()
        object.__setattr__(self, "text", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "text":
            if isinstance(value, str):
                object.__setattr__(self, "text", value)
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a dictionary including text and parent fields."""
        result = super().to_dict(recursive=recursive)
        if self.text is not None:
            result["text"] = self.text
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TextCompletionPayload":
        """Create an instance from a dictionary. None values are skipped."""
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "TextCompletionPayload":
        """Create an instance from a JSON string."""
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class ChatCompletionPayload(AiPayload):
    """Payload for chat completion style models."""

    def __init__(self) -> None:
        super().__init__()
        object.__setattr__(self, "messages", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "messages":
            if isinstance(value, list):
                converted: list[Message] = []
                if len(value) > 0:
                    if isinstance(value[0], Message):
                        for item in value:
                            converted.append(item)
                    elif isinstance(value[0], dict):
                        for item in value:
                            converted.append(Message.from_dict(item))
                    else:
                        raise ValueError
                object.__setattr__(self, "messages", converted)
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a dictionary. If recursive, each Message is serialized to dict."""
        result = super().to_dict(recursive=recursive)
        if self.messages is not None:
            if recursive:
                result["messages"] = [m.to_dict(recursive=True) for m in self.messages]
            else:
                result["messages"] = self.messages
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatCompletionPayload":
        """Create an instance from a dictionary. None values are skipped."""
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "ChatCompletionPayload":
        """Create an instance from a JSON string."""
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class EmbeddingPayload(AiPayload):
    """Payload for embedding models."""

    def __init__(self) -> None:
        super().__init__()
        object.__setattr__(self, "input", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "input":
            if isinstance(value, str) or isinstance(value, list):
                object.__setattr__(self, "input", value)
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a dictionary including input and parent fields."""
        result = super().to_dict(recursive=recursive)
        if self.input is not None:
            result["input"] = self.input
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmbeddingPayload":
        """Create an instance from a dictionary. None values are skipped."""
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "EmbeddingPayload":
        """Create an instance from a JSON string."""
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
