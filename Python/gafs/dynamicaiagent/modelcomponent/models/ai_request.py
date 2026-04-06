from __future__ import annotations

import json
from typing import Any

from .ai_operation_type import AiOperationType
from .ai_payload import (
    AiPayload,
    ChatCompletionPayload,
    EmbeddingPayload,
    TextCompletionPayload,
)


class AiRequest:
    """Request to an AI model: operation type, provider options, and payload.

    Combines operation_type (e.g., chat_completion, embedding), provider-specific
    options, and payload (input data) for a single AI operation.
    """

    def __init__(
        self,
        operation_type: AiOperationType|str,
        payload: AiPayload|dict[str, Any]|str|None = None,
        parameters: dict[str, Any]|str|None = None,
    ) -> None:
        if isinstance(operation_type, AiOperationType):
            object.__setattr__(self, "operation_type", operation_type)
        elif isinstance(operation_type, str):
            object.__setattr__(self, "operation_type", AiOperationType(operation_type))
        else:
            raise ValueError
        
        if isinstance(payload, AiPayload):
            object.__setattr__(self, "payload", payload)
        else:
            dict_payload: dict[str, Any]|None = None
            if isinstance(payload, dict):
                dict_payload = payload
            elif isinstance(payload, str):
                dict_payload = json.loads(payload)
                if not isinstance(dict_payload, dict):
                    raise ValueError
            
            match self.operation_type:
                case AiOperationType.CHAT_COMPLETION:
                    object.__setattr__(self, "payload", ChatCompletionPayload.from_dict(dict_payload))
                case AiOperationType.TEXT_COMPLETION:
                    object.__setattr__(self, "payload", TextCompletionPayload.from_dict(dict_payload))
                case AiOperationType.EMBEDDING:
                    object.__setattr__(self, "payload", EmbeddingPayload.from_dict(dict_payload))
                case _:
                    raise NotImplementedError
        
        if isinstance(parameters, dict):
            object.__setattr__(self, "parameters", parameters)
        elif isinstance(parameters, str):
            converted: Any = json.loads(parameters)
            if isinstance(converted, dict):
                object.__setattr__(self, "parameters", converted)
            else:
                raise ValueError
        elif parameters is None:
            object.__setattr__(self, "parameters", dict[str, Any]())
        else:
            raise ValueError
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name == "operation_type":
            raise AttributeError("operation_type is read-only.")
        elif name == "payload":
            if isinstance(value, AiPayload):
                object.__setattr__(self, "payload", value)
            else:
                dict_payload: dict[str, Any]|None = None
                if isinstance(value, dict):
                    dict_payload = value
                elif isinstance(value, str):
                    dict_payload = json.loads(value)
                    if not isinstance(dict_payload, dict):
                        raise ValueError
                else:
                    raise ValueError
            
            match self.operation_type:
                case AiOperationType.CHAT_COMPLETION:
                    object.__setattr__(self, "payload", ChatCompletionPayload.from_dict(dict_payload))
                case AiOperationType.TEXT_COMPLETION:
                    object.__setattr__(self, "payload", TextCompletionPayload.from_dict(dict_payload))
                case AiOperationType.EMBEDDING:
                    object.__setattr__(self, "payload", EmbeddingPayload.from_dict(dict_payload))
                case _:
                    # TODO: Implement other payload types
                    raise NotImplementedError

        elif name == "parameters":
            if isinstance(value, dict):
                object.__setattr__(self, "parameters", value)
            elif isinstance(value, str):
                converted: Any = json.loads(value)
                if isinstance(converted, dict):
                    object.__setattr__(self, "parameters", converted)
                else:
                    raise ValueError
            else:
                raise ValueError
        else:
            pass # Ignore unknown attributes
    
    def __repr__(self) -> str:
        return self.to_json()


    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a dictionary.

        Args:
            recursive: If True, convert Enum and nested objects to primitives.

        Returns:
            Dictionary with operation_type, options, and payload.
        """
        result: dict[str, Any] = {}
        if self.operation_type is not None:
            if recursive:
                result["operation_type"] = self.operation_type.value
            else:
                result["operation_type"] = self.operation_type
        if self.payload is not None:
            if recursive:
                result["payload"] = self.payload.to_dict(recursive=recursive)
            else:
                result["payload"] = self.payload.to_dict(recursive=False)
        if self.parameters is not None:
            result["parameters"] = self.parameters
        return result
    
    def to_json(self) -> str:
        """Serialize to a JSON string (nested objects converted to primitives)."""
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AiRequest":
        """Create an instance from a dictionary.

        Payload and options are deserialized based on operation_type and provider_type.

        Args:
            data: Dictionary containing operation_type, options, and payload.

        Returns:
            New AiRequest instance.

        Raises:
            ValueError: When a field has an invalid type or operation_type is unsupported.
            NotImplementedError: When operation_type is IMAGE_GENERATION, SPEECH_TO_TEXT, or TEXT_TO_SPEECH.
        """
        if "operation_type" in data:
            if isinstance(data["operation_type"], AiOperationType):
                operation_type = data["operation_type"]
            elif isinstance(data["operation_type"], str):
                operation_type = AiOperationType(data["operation_type"])
            else:
                raise ValueError
        else:
            raise ValueError
        
        if "payload" in data:
            if isinstance(data["payload"], AiPayload):
                payload = data["payload"]
            elif isinstance(data["payload"], dict):
                match (operation_type):
                    case AiOperationType.CHAT_COMPLETION:
                        payload = ChatCompletionPayload.from_dict(data["payload"])
                    case AiOperationType.TEXT_COMPLETION:
                        payload = TextCompletionPayload.from_dict(data["payload"])
                    case AiOperationType.EMBEDDING:
                        payload = EmbeddingPayload.from_dict(data["payload"])
                    case AiOperationType.IMAGE_GENERATION:
                        raise NotImplementedError
                    case AiOperationType.SPEECH_TO_TEXT:
                        raise NotImplementedError
                    case AiOperationType.TEXT_TO_SPEECH:
                        raise NotImplementedError
                    case _:
                        raise ValueError
            elif isinstance(data["payload"], str):
                match (operation_type):
                    case AiOperationType.CHAT_COMPLETION:
                        payload = ChatCompletionPayload.from_json(data["payload"])
                    case AiOperationType.TEXT_COMPLETION:
                        payload = TextCompletionPayload.from_json(data["payload"])
                    case AiOperationType.EMBEDDING:
                        payload = EmbeddingPayload.from_json(data["payload"])
                    case AiOperationType.IMAGE_GENERATION:
                        raise NotImplementedError
                    case AiOperationType.SPEECH_TO_TEXT:
                        raise NotImplementedError
                    case AiOperationType.TEXT_TO_SPEECH:
                        raise NotImplementedError
                    case _:
                        raise ValueError
            else:
                raise ValueError

        if "parameters" in data:
            if isinstance(data["parameters"], dict):
                parameters: dict[str, Any] = data["parameters"]
            elif isinstance(data["parameters"], str):
                parameters = json.loads(data["parameters"])
                if not isinstance(parameters, dict):
                    raise ValueError
            else:
                raise ValueError
        else:
            parameters = dict[str, Any]()
        
        return cls(operation_type=operation_type, payload=payload, parameters=parameters)
    
    @classmethod
    def from_json(cls, json_str: str) -> "AiRequest":
        """Create an instance from a JSON string.

        Args:
            json_str: JSON string that parses to a dictionary.

        Returns:
            New AiRequest instance.

        Raises:
            ValueError: When json_str does not parse to a dict or a field is invalid.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
