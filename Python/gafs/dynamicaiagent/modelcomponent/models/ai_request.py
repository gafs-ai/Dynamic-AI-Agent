"""AiRequest — value object that describes a single AI model invocation."""

from __future__ import annotations

import json
from typing import Any

from .ai_deployment_type import AiDeploymentType
from .ai_operation_type import AiOperationType
from .ai_payload import AiPayload, ChatCompletionPayload, EmbeddingPayload, TextCompletionPayload


class AiRequest:
    """A request to an AI model: operation type, payload, and optional inference parameters."""

    def __init__(
        self,
        operation_type: AiOperationType | str,
        payload: AiPayload | dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        # Set operation_type (read-only after construction)
        if isinstance(operation_type, AiOperationType):
            object.__setattr__(self, "operation_type", operation_type)
        elif isinstance(operation_type, str):
            object.__setattr__(self, "operation_type", AiOperationType(operation_type))
        else:
            raise ValueError

        # Set payload, auto-selecting the correct subclass based on operation_type
        if isinstance(payload, AiPayload):
            object.__setattr__(self, "payload", payload)
        elif payload is None:
            object.__setattr__(self, "payload", None)
        else:
            dict_payload: dict[str, Any] = {}
            if isinstance(payload, dict):
                dict_payload = payload
            elif isinstance(payload, str):
                parsed = json.loads(payload)
                if not isinstance(parsed, dict):
                    raise ValueError
                dict_payload = parsed
            else:
                raise ValueError
            object.__setattr__(self, "payload", AiRequest._build_payload(self.operation_type, dict_payload))

        # Set parameters (defaults to empty dict)
        if isinstance(parameters, dict):
            object.__setattr__(self, "parameters", parameters)
        elif parameters is None:
            object.__setattr__(self, "parameters", {})
        elif isinstance(parameters, str):
            parsed_params = json.loads(parameters)
            if not isinstance(parsed_params, dict):
                raise ValueError
            object.__setattr__(self, "parameters", parsed_params)
        else:
            raise ValueError

    @staticmethod
    def _build_payload(operation_type: AiOperationType, data: dict[str, Any]) -> AiPayload:
        """Select and instantiate the correct payload subclass for the given operation type."""
        if operation_type == AiOperationType.CHAT_COMPLETION:
            return ChatCompletionPayload.from_dict(data)
        if operation_type == AiOperationType.TEXT_COMPLETION:
            return TextCompletionPayload.from_dict(data)
        if operation_type == AiOperationType.EMBEDDING:
            return EmbeddingPayload.from_dict(data)
        raise NotImplementedError(f"Payload construction not implemented for: {operation_type}")

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "operation_type":
            raise AttributeError("operation_type is read-only.")
        elif name == "payload":
            if isinstance(value, AiPayload):
                object.__setattr__(self, "payload", value)
            elif isinstance(value, dict):
                object.__setattr__(self, "payload", AiRequest._build_payload(self.operation_type, value))
            elif isinstance(value, str):
                parsed = json.loads(value)
                if not isinstance(parsed, dict):
                    raise ValueError
                object.__setattr__(self, "payload", AiRequest._build_payload(self.operation_type, parsed))
            else:
                raise ValueError
        elif name == "parameters":
            if isinstance(value, dict):
                object.__setattr__(self, "parameters", value)
            elif isinstance(value, str):
                parsed = json.loads(value)
                if not isinstance(parsed, dict):
                    raise ValueError
                object.__setattr__(self, "parameters", parsed)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.operation_type is not None:
            if recursive:
                result["operation_type"] = self.operation_type.value
            else:
                result["operation_type"] = self.operation_type
        if self.payload is not None:
            result["payload"] = self.payload.to_dict(recursive=recursive)
        if self.parameters is not None:
            result["parameters"] = self.parameters
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AiRequest":
        # Extract operation_type first (required)
        if "operation_type" not in data:
            raise ValueError("operation_type is required.")
        operation_type_raw = data["operation_type"]
        if isinstance(operation_type_raw, AiOperationType):
            operation_type = operation_type_raw
        elif isinstance(operation_type_raw, str):
            operation_type = AiOperationType(operation_type_raw)
        else:
            raise ValueError

        # Extract payload
        payload_raw = data.get("payload")
        payload: AiPayload | None = None
        if payload_raw is not None:
            if isinstance(payload_raw, AiPayload):
                payload = payload_raw
            elif isinstance(payload_raw, dict):
                payload = cls._build_payload(operation_type, payload_raw)
            else:
                raise ValueError

        # Extract parameters
        parameters_raw = data.get("parameters")
        if isinstance(parameters_raw, dict):
            parameters = parameters_raw
        elif parameters_raw is None:
            parameters = {}
        else:
            raise ValueError

        return cls(operation_type=operation_type, payload=payload, parameters=parameters)

    @classmethod
    def from_json(cls, json_str: str) -> "AiRequest":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
