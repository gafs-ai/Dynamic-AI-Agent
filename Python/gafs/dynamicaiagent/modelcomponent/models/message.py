"""Message model — Role, ContentType, MessagePart subtypes, and the top-level Message data class."""

from __future__ import annotations

import base64
import json
from abc import ABC
from enum import Enum
from typing import Any


class Role(Enum):
    """Enum for the sender role in a conversation message."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ContentType(Enum):
    """Enum for the type of content in a message part."""

    TEXT = "text"
    IMAGE_URL = "image_url"
    AUDIO = "audio"
    FILE = "file"
    REFUSAL = "refusal"


class MessagePart(ABC):
    """Abstract base class for typed message content parts.

    Dispatches to the appropriate subclass via from_dict based on the 'type' field.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "type", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "type":
            if isinstance(value, ContentType):
                object.__setattr__(self, "type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "type", ContentType(value))
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.type is not None:
            if recursive:
                result["type"] = self.type.value
            else:
                result["type"] = self.type
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessagePart":
        """Factory method: dispatches to the correct subclass based on 'type'."""
        if cls is not MessagePart:
            # Called directly on a concrete subclass — construct it
            entity = cls()
            for key, value in data.items():
                if hasattr(entity, key) and value is not None:
                    setattr(entity, key, value)
            return entity

        # Dispatch based on 'type' discriminator
        type_value = data.get("type")
        if type_value is None:
            raise ValueError("MessagePart.from_dict requires 'type' field.")
        if isinstance(type_value, ContentType):
            content_type = type_value
        else:
            content_type = ContentType(str(type_value))

        if content_type == ContentType.TEXT:
            return TextMessagePart.from_dict(data)
        if content_type == ContentType.IMAGE_URL:
            return ImageUrlMessagePart.from_dict(data)
        if content_type == ContentType.AUDIO:
            return AudioDataMessagePart.from_dict(data)
        if content_type == ContentType.FILE:
            return FileMessagePart.from_dict(data)
        if content_type == ContentType.REFUSAL:
            return RefusalMessagePart.from_dict(data)
        raise ValueError(f"Unknown ContentType: {content_type}")

    @classmethod
    def from_json(cls, json_str: str) -> "MessagePart":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class TextMessagePart(MessagePart):
    """A plain-text message content part."""

    def __init__(self) -> None:
        super().__init__()
        # Set type directly via object.__setattr__ to bypass parent validation
        object.__setattr__(self, "type", ContentType.TEXT)
        object.__setattr__(self, "text", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "text":
            if isinstance(value, str) or value is None:
                object.__setattr__(self, "text", value)
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result = super().to_dict(recursive=recursive)
        if self.text is not None:
            result["text"] = self.text
        return result


class ImageUrlMessagePart(MessagePart):
    """An image URL message content part."""

    # Detail values accepted by the OpenAI API
    _VALID_DETAILS = frozenset({"auto", "high", "low"})

    def __init__(self) -> None:
        super().__init__()
        object.__setattr__(self, "type", ContentType.IMAGE_URL)
        object.__setattr__(self, "url", None)
        object.__setattr__(self, "detail", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "url":
            if isinstance(value, str) or value is None:
                object.__setattr__(self, "url", value)
            else:
                raise ValueError
        elif name == "detail":
            if value is None:
                object.__setattr__(self, "detail", None)
            elif isinstance(value, str):
                # Normalize unknown values to "auto" per design doc
                normalized = value if value in self._VALID_DETAILS else "auto"
                object.__setattr__(self, "detail", normalized)
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result = super().to_dict(recursive=recursive)
        if self.url is not None:
            result["url"] = self.url
        if self.detail is not None:
            result["detail"] = self.detail
        return result


class AudioData:
    """Helper class holding base64-encoded audio and its format."""

    def __init__(self) -> None:
        object.__setattr__(self, "data", None)
        object.__setattr__(self, "format", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "data":
            if isinstance(value, bytes):
                # Auto-encode bytes to base64 string
                object.__setattr__(self, "data", base64.b64encode(value).decode("ascii"))
            elif isinstance(value, str) or value is None:
                object.__setattr__(self, "data", value)
            else:
                raise ValueError
        elif name == "format":
            if isinstance(value, str) or value is None:
                object.__setattr__(self, "format", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.data is not None:
            result["data"] = self.data
        if self.format is not None:
            result["format"] = self.format
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AudioData":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "AudioData":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class AudioDataMessagePart(MessagePart):
    """An audio data message content part."""

    def __init__(self) -> None:
        super().__init__()
        object.__setattr__(self, "type", ContentType.AUDIO)
        object.__setattr__(self, "input_audio", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "input_audio":
            if isinstance(value, AudioData) or value is None:
                object.__setattr__(self, "input_audio", value)
            elif isinstance(value, dict):
                object.__setattr__(self, "input_audio", AudioData.from_dict(value))
            elif isinstance(value, str):
                object.__setattr__(self, "input_audio", AudioData.from_json(value))
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result = super().to_dict(recursive=recursive)
        if self.input_audio is not None:
            if recursive:
                result["input_audio"] = self.input_audio.to_dict(recursive=True)
            else:
                result["input_audio"] = self.input_audio
        return result


class FileData:
    """Helper class holding base64-encoded file content and its metadata."""

    def __init__(self) -> None:
        object.__setattr__(self, "data", None)
        object.__setattr__(self, "file_id", None)
        object.__setattr__(self, "filename", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "data":
            if isinstance(value, bytes):
                # Auto-encode bytes to base64 string
                object.__setattr__(self, "data", base64.b64encode(value).decode("ascii"))
            elif isinstance(value, str) or value is None:
                object.__setattr__(self, "data", value)
            else:
                raise ValueError
        elif name in ("file_id", "filename"):
            if isinstance(value, str) or value is None:
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.data is not None:
            result["data"] = self.data
        if self.file_id is not None:
            result["file_id"] = self.file_id
        if self.filename is not None:
            result["filename"] = self.filename
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileData":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "FileData":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class FileMessagePart(MessagePart):
    """A file data message content part."""

    def __init__(self) -> None:
        super().__init__()
        object.__setattr__(self, "type", ContentType.FILE)
        object.__setattr__(self, "file", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "file":
            if isinstance(value, FileData) or value is None:
                object.__setattr__(self, "file", value)
            elif isinstance(value, dict):
                object.__setattr__(self, "file", FileData.from_dict(value))
            elif isinstance(value, str):
                object.__setattr__(self, "file", FileData.from_json(value))
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result = super().to_dict(recursive=recursive)
        if self.file is not None:
            if recursive:
                result["file"] = self.file.to_dict(recursive=True)
            else:
                result["file"] = self.file
        return result


class RefusalMessagePart(MessagePart):
    """A refusal message content part returned by the model."""

    def __init__(self) -> None:
        super().__init__()
        object.__setattr__(self, "type", ContentType.REFUSAL)
        object.__setattr__(self, "refusal", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "refusal":
            if isinstance(value, str) or value is None:
                object.__setattr__(self, "refusal", value)
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result = super().to_dict(recursive=recursive)
        if self.refusal is not None:
            result["refusal"] = self.refusal
        return result


class Message:
    """A single message in a conversation, with role, optional name, and content."""

    def __init__(self) -> None:
        object.__setattr__(self, "role", None)
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "content", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "role":
            if isinstance(value, Role):
                object.__setattr__(self, "role", value)
            elif isinstance(value, str):
                object.__setattr__(self, "role", Role(value))
            else:
                raise ValueError
        elif name == "name":
            if isinstance(value, str) or value is None:
                object.__setattr__(self, "name", value)
            else:
                raise ValueError
        elif name == "content":
            if value is None or isinstance(value, str):
                object.__setattr__(self, "content", value)
            elif isinstance(value, list):
                # Convert list[dict] to list[MessagePart] if needed
                if len(value) > 0 and isinstance(value[0], dict):
                    converted: list[MessagePart] = [MessagePart.from_dict(item) for item in value]
                    object.__setattr__(self, "content", converted)
                else:
                    # Assume already list[MessagePart]
                    object.__setattr__(self, "content", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.role is not None:
            if recursive:
                result["role"] = self.role.value
            else:
                result["role"] = self.role
        if self.name is not None:
            result["name"] = self.name
        if self.content is not None:
            if isinstance(self.content, str):
                result["content"] = self.content
            elif isinstance(self.content, list):
                if recursive:
                    result["content"] = [part.to_dict(recursive=True) for part in self.content]
                else:
                    result["content"] = self.content
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        entity = cls()
        for key, value in data.items():
            if value is None:
                continue
            if key == "role":
                setattr(entity, "role", value)
            elif key == "name":
                setattr(entity, "name", value)
            elif key == "content":
                setattr(entity, "content", value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
