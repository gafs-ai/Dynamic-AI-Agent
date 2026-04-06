from __future__ import annotations

import json
from abc import ABC
from typing import Any

from .message import Message


class AiOutput(ABC):
    """Abstract base class for AI operation output (text, chat, embedding).

    Subclasses must implement to_dict and provide concrete output structures.
    """

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
    """Output for text completion operations. Contains the generated text."""

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
    
    def __repr__(self) -> str:
        return self.to_json()
    
    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a dictionary.

        Args:
            recursive: Unused; kept for interface consistency.

        Returns:
            Dictionary with text field.
        """
        result: dict[str, Any] = {}
        if self.text is not None:
            result["text"] = self.text
        return result

    def to_json(self) -> str:
        """Serialize to a JSON string (nested objects converted to primitives)."""
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TextCompletionOutput:
        """Create an instance from a dictionary. None values are skipped.

        Args:
            data: Dictionary containing output fields.

        Returns:
            New TextCompletionOutput instance.

        Raises:
            ValueError: When a field value has an invalid type.
        """
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> TextCompletionOutput:
        """Create an instance from a JSON string.

        Args:
            json_str: JSON string that parses to a dictionary.

        Returns:
            New TextCompletionOutput instance.

        Raises:
            ValueError: When json_str does not parse to a dict or a field is invalid.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class ChatCompletionOutput(AiOutput):
    """Output for chat completion operations. Contains a list of Message objects."""

    def __init__(self) -> None:
        object.__setattr__(self, "messages", None)
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name == "messages":
            converted: list[Message] = []

            if isinstance(value, list):
                if len(value) > 0:
                    if isinstance(value[0], Message):
                        for item in value:
                            converted.append(item)
                    elif isinstance(value[0], dict):
                        for item in value:
                            converted.append(Message.from_dict(item))
                    elif isinstance(value[0], str):
                        for item in value:
                            converted.append(Message.from_json(item))
                    else:
                        raise ValueError
            else:
                if isinstance(value, Message):
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

    def __repr__(self) -> str:
        return self.to_json()
    
    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a dictionary.

        Args:
            recursive: If True, convert each Message to a dict.

        Returns:
            Dictionary with messages field.
        """
        result: dict[str, Any] = {}
        if self.messages is not None:
            if recursive:
                result["messages"] = [message.to_dict(recursive=True) for message in self.messages]
            else:
                result["messages"] = self.messages
        return result

    def to_json(self) -> str:
        """Serialize to a JSON string (nested objects converted to primitives)."""
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatCompletionOutput:
        """Create an instance from a dictionary. None values are skipped.

        Args:
            data: Dictionary containing output fields. messages may be list of dict/str.

        Returns:
            New ChatCompletionOutput instance.

        Raises:
            ValueError: When a field value has an invalid type.
        """
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> ChatCompletionOutput:
        """Create an instance from a JSON string.

        Args:
            json_str: JSON string that parses to a dictionary.

        Returns:
            New ChatCompletionOutput instance.

        Raises:
            ValueError: When json_str does not parse to a dict or a field is invalid.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class EmbeddingOutput(AiOutput):
    """Output for embedding operations. Contains a list of float values."""

    def __init__(self) -> None:
        object.__setattr__(self, "embedding", None)
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name == "embedding":
            if isinstance(value, list):
                if len(value) > 0:
                    if isinstance(value[0], (float, int)):
                        object.__setattr__(self, "embedding", value)
                    else:
                        raise ValueError
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)
    
    def __repr__(self) -> str:
        return self.to_json()
    
    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a dictionary.

        Args:
            recursive: Unused; kept for interface consistency.

        Returns:
            Dictionary with embedding field.
        """
        result: dict[str, Any] = {}
        if self.embedding is not None:
            result["embedding"] = self.embedding
        return result

    def to_json(self) -> str:
        """Serialize to a JSON string (nested objects converted to primitives)."""
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EmbeddingOutput:
        """Create an instance from a dictionary. None values are skipped.

        Args:
            data: Dictionary containing output fields.

        Returns:
            New EmbeddingOutput instance.

        Raises:
            ValueError: When a field value has an invalid type.
        """
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> EmbeddingOutput:
        """Create an instance from a JSON string.

        Args:
            json_str: JSON string that parses to a dictionary.

        Returns:
            New EmbeddingOutput instance.

        Raises:
            ValueError: When json_str does not parse to a dict or a field is invalid.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


