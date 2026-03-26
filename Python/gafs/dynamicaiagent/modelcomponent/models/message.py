"""Message and message part models for chat/completion APIs."""

import base64
import json
from abc import ABC
from enum import Enum
from typing import Any


class Role(Enum):
    """Enum that represents the role of the message."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ContentType(Enum):
    """Enum that represents the type of the message part."""

    TEXT = "text"
    IMAGE_URL = "image_url"
    AUDIO = "audio"
    FILE = "file"
    REFUSAL = "refusal"


class MessagePart(ABC):
    """Base class for message part content (text, image_url, audio, file, refusal)."""

    def __init__(self, type: ContentType|str) -> None:
        if isinstance(type, ContentType):
            object.__setattr__(self, "type", type)
        elif isinstance(type, str):
            object.__setattr__(self, "type", ContentType(type))
        else:
            raise ValueError
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
        """Convert to a dictionary.

        Args:
            recursive: If True, convert Enum fields to their string values.

        Returns:
            Dictionary representation of this message part.
        """
        result: dict[str, Any] = {}
        if self.type is not None:
            if recursive:
                result["type"] = self.type.value
            else:
                result["type"] = self.type
        return result

    def to_json(self) -> str:
        """Serialize to a JSON string (nested objects converted to primitives)."""
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessagePart":
        """Build a MessagePart subclass from a dictionary using the type field.

        Args:
            data: Dictionary containing type and part-specific fields.

        Returns:
            Concrete MessagePart subclass (TextMessagePart, ImageUrlMessagePart, etc.).

        Raises:
            ValueError: When type is missing or invalid.
        """
        type: ContentType = None

        if "type" in data:
            if isinstance(data["type"], ContentType):
                type = data["type"]
            elif isinstance(data["type"], str):
                type = ContentType(data["type"])
            else:
                raise ValueError
        else:
            raise ValueError

        match (type):
            case ContentType.TEXT:
                return TextMessagePart.from_dict(data)
            case ContentType.IMAGE_URL:
                return ImageUrlMessagePart.from_dict(data)
            case ContentType.AUDIO:
                return AudioDataMessagePart.from_dict(data)
            case ContentType.FILE:
                return FileMessagePart.from_dict(data)
            case ContentType.REFUSAL:
                return RefusalMessagePart.from_dict(data)
            case _:
                raise ValueError


    @classmethod
    def from_json(cls, json_str: str) -> "MessagePart":
        """Build a MessagePart subclass from a JSON string.

        Args:
            json_str: JSON string that parses to a dictionary.

        Returns:
            Concrete MessagePart subclass instance.

        Raises:
            ValueError: When json_str does not parse to a dict or type is invalid.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class TextMessagePart(MessagePart):
    """Message part that contains text."""

    def __init__(self) -> None:
        super().__init__(ContentType.TEXT)
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
        """Convert to a dictionary including type and text."""
        result: dict[str, Any] = super().to_dict(recursive=recursive)
        if self.text is not None:
            result["text"] = self.text
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TextMessagePart":
        """Create an instance from a dictionary. None values and unknown keys are skipped."""
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "TextMessagePart":
        """Create an instance from a JSON string."""
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class ImageUrlMessagePart(MessagePart):
    """Message part that contains image URL."""

    def __init__(self) -> None:
        super().__init__(ContentType.IMAGE_URL)
        object.__setattr__(self, "url", None)
        object.__setattr__(self, "detail", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "url":
            if isinstance(value, str):
                object.__setattr__(self, "url", value)
            else:
                raise ValueError
        elif name == "detail":
            if isinstance(value, str):
                v = value.lower()
                if v in ("auto", "high", "low"):
                    object.__setattr__(self, "detail", v)
                else:
                    object.__setattr__(self, "detail", "auto")
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a dictionary including type, url, and detail."""
        result: dict[str, Any] = super().to_dict(recursive=recursive)
        if self.url is not None:
            result["url"] = self.url
        if self.detail is not None:
            result["detail"] = self.detail
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImageUrlMessagePart":
        """Create an instance from a dictionary. None values and unknown keys are skipped."""
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "ImageUrlMessagePart":
        """Create an instance from a JSON string."""
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class AudioData:
    """Holds base64 audio data and format (e.g. for input_audio)."""

    def __init__(self) -> None:
        object.__setattr__(self, "data", None)
        object.__setattr__(self, "format", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "data":
            if isinstance(value, str):
                object.__setattr__(self, "data", value)
            elif isinstance(value, bytes):
                object.__setattr__(self, "data", base64.b64encode(value).decode())
            else:
                raise ValueError
        elif name == "format":
            if isinstance(value, str):
                object.__setattr__(self, "format", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a dictionary with data and format fields."""
        result: dict[str, Any] = {}
        if self.data is not None:
            result["data"] = self.data
        if self.format is not None:
            result["format"] = self.format
        return result

    def to_json(self) -> str:
        """Serialize to a JSON string (nested objects converted to primitives)."""
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AudioData":
        """Create an instance from a dictionary. None values and unknown keys are skipped."""
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "AudioData":
        """Create an instance from a JSON string."""
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class AudioDataMessagePart(MessagePart):
    """Message part that contains audio data (base64)."""

    def __init__(self) -> None:
        super().__init__(ContentType.AUDIO)
        object.__setattr__(self, "input_audio", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "input_audio":
            if isinstance(value, AudioData):
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
        """Convert to a dictionary including type and input_audio."""
        result: dict[str, Any] = super().to_dict(recursive=recursive)
        if self.input_audio is not None:
            result["input_audio"] = self.input_audio.to_dict(recursive=recursive)
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AudioDataMessagePart":
        """Create an instance from a dictionary. None values and unknown keys are skipped."""
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "AudioDataMessagePart":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class FileData:
    """Holds base64 file data, file_id, and filename."""

    def __init__(self) -> None:
        object.__setattr__(self, "data", None)
        object.__setattr__(self, "file_id", None)
        object.__setattr__(self, "filename", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "data":
            if isinstance(value, str):
                object.__setattr__(self, "data", value)
            elif isinstance(value, bytes):
                object.__setattr__(self, "data", base64.b64encode(value).decode())
            else:
                raise ValueError
        elif name == "file_id":
            if isinstance(value, str):
                object.__setattr__(self, "file_id", value)
            else:
                raise ValueError
        elif name == "filename":
            if isinstance(value, str):
                object.__setattr__(self, "filename", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a dictionary with data, file_id, and filename."""
        result: dict[str, Any] = {}
        if self.data is not None:
            result["data"] = self.data
        if self.file_id is not None:
            result["file_id"] = self.file_id
        if self.filename is not None:
            result["filename"] = self.filename
        return result

    def to_json(self) -> str:
        """Serialize to a JSON string (nested objects converted to primitives)."""
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileData":
        """Create an instance from a dictionary. None values and unknown keys are skipped."""
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "FileData":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
    

class FileMessagePart(MessagePart):
    """Message part that contains file data (base64)."""

    def __init__(self) -> None:
        super().__init__(ContentType.FILE)
        object.__setattr__(self, "file", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "file":
            if isinstance(value, FileData):
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
        """Convert to a dictionary including type and file."""
        result: dict[str, Any] = super().to_dict(recursive=recursive)
        if self.file is not None:
            result["file"] = self.file.to_dict(recursive=recursive)
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileMessagePart":
        """Create an instance from a dictionary. None values and unknown keys are skipped."""
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "FileMessagePart":
        """Create an instance from a JSON string."""
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class RefusalMessagePart(MessagePart):
    """Message part that contains refusal text."""

    def __init__(self) -> None:
        super().__init__(ContentType.REFUSAL)
        object.__setattr__(self, "refusal", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "refusal":
            if isinstance(value, str):
                object.__setattr__(self, "refusal", value)
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = super().to_dict(recursive=recursive)
        if self.refusal is not None:
            result["refusal"] = self.refusal
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RefusalMessagePart":
        """Create an instance from a dictionary. None values and unknown keys are skipped."""
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "RefusalMessagePart":
        """Create an instance from a JSON string."""
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class Message:
    """Chat/completion message with role, optional name, and content (text or list of parts)."""

    def __init__(self) -> None:
        object.__setattr__(self, "role", None)
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "content", None)

    @staticmethod
    def _content_part_from_dict(data: dict[str, Any]) -> MessagePart:
        """Build a MessagePart subclass from a dict using the \"type\" field."""
        part_type = data.get("type")
        if isinstance(part_type, ContentType):
            ct = part_type
        elif isinstance(part_type, str):
            ct = ContentType(part_type)
        else:
            raise ValueError
        if ct == ContentType.TEXT:
            return TextMessagePart.from_dict(data)
        if ct == ContentType.IMAGE_URL:
            return ImageUrlMessagePart.from_dict(data)
        if ct == ContentType.AUDIO:
            return AudioDataMessagePart.from_dict(data)
        if ct == ContentType.FILE:
            return FileMessagePart.from_dict(data)
        if ct == ContentType.REFUSAL:
            return RefusalMessagePart.from_dict(data)
        raise ValueError

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "role":
            if isinstance(value, Role):
                object.__setattr__(self, "role", value)
            elif isinstance(value, str):
                object.__setattr__(self, "role", Role(value))
            else:
                raise ValueError
        elif name == "name":
            if isinstance(value, str):
                object.__setattr__(self, "name", value)
            else:
                raise ValueError
        elif name == "content":
            if isinstance(value, str):
                object.__setattr__(self, "content", value)
            elif isinstance(value, list):
                if len(value) > 0 and isinstance(value[0], dict):
                    converted: list[MessagePart] = [
                        self._content_part_from_dict(item) for item in value
                    ]
                    object.__setattr__(self, "content", converted)
                else:
                    object.__setattr__(self, "content", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a dictionary.

        Args:
            recursive: If True, convert role Enum and content MessageParts to primitives.

        Returns:
            Dictionary with role, name, and content.
        """
        result: dict[str, Any] = {}
        if self.role is not None:
            if recursive and isinstance(self.role, Role):
                result["role"] = self.role.value
            else:
                result["role"] = self.role
        if self.name is not None:
            result["name"] = self.name
        if self.content is not None:
            if recursive and isinstance(self.content, list):
                result["content"] = [
                    p.to_dict(recursive=True) for p in self.content
                ]
            else:
                result["content"] = self.content
        return result

    def to_json(self) -> str:
        """Serialize to a JSON string. Role and content are converted to primitives."""
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create an instance from a dictionary.

        Args:
            data: Dictionary containing role, name, and content. content may be
                a string or list of dicts (MessageParts). None values and unknown keys are skipped.

        Returns:
            New Message instance.

        Raises:
            ValueError: When a field value has an invalid type.
        """
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """Create an instance from a JSON string.

        Args:
            json_str: JSON string that parses to a dictionary.

        Returns:
            New Message instance.

        Raises:
            ValueError: When json_str does not parse to a dict or a field is invalid.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
