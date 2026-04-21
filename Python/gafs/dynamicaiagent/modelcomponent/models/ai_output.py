"""AI output classes — typed containers for the data returned by AI model operations."""

from __future__ import annotations

import json
from abc import ABC
from typing import Any

from .message import Message


class AiOutput(ABC):
    """Abstract base class for all AI operation response outputs."""

    def __init__(self) -> None:
        pass

    def __setattr__(self, name: str, value: Any) -> None:
        raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        raise NotImplementedError

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))


class TextCompletionOutput(AiOutput):
    """Output for TEXT_COMPLETION operations. Contains the generated text."""

    def __init__(self) -> None:
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
        result: dict[str, Any] = {}
        if self.text is not None:
            result["text"] = self.text
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TextCompletionOutput":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "TextCompletionOutput":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class ChatCompletionOutput(AiOutput):
    """Output for CHAT_COMPLETION operations. Contains response messages."""

    def __init__(self) -> None:
        object.__setattr__(self, "messages", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "messages":
            converted: list[Message] = []
            if isinstance(value, list):
                if len(value) > 0:
                    if isinstance(value[0], Message):
                        converted = list(value)
                    elif isinstance(value[0], dict):
                        for item in value:
                            converted.append(Message.from_dict(item))
                    elif isinstance(value[0], str):
                        for item in value:
                            converted.append(Message.from_json(item))
                    else:
                        raise ValueError
            elif isinstance(value, Message):
                converted.append(value)
            elif isinstance(value, dict):
                converted.append(Message.from_dict(value))
            elif isinstance(value, str):
                converted.append(Message.from_json(value))
            else:
                raise ValueError
            object.__setattr__(self, "messages", converted)
        else:
            super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.messages is not None:
            if recursive:
                result["messages"] = [m.to_dict(recursive=True) for m in self.messages]
            else:
                result["messages"] = self.messages
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatCompletionOutput":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "ChatCompletionOutput":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class EmbeddingOutput(AiOutput):
    """Output for EMBEDDING operations. Contains the embedding vector."""

    def __init__(self) -> None:
        object.__setattr__(self, "vector", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "vector":
            if isinstance(value, list):
                object.__setattr__(self, "vector", value)
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.vector is not None:
            result["vector"] = self.vector
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmbeddingOutput":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "EmbeddingOutput":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
