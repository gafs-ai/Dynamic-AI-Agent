from __future__ import annotations

import json
from typing import Any

from .attribute_type import AttributeType


class AttributeDefinition:
    @staticmethod
    def _normalize_min_max_for_type(
        value: Any,
        parameter_type: AttributeType,
    ) -> int | float:
        match parameter_type:
            case AttributeType.INT:
                if isinstance(value, int):
                    return value
                if isinstance(value, float):
                    return int(value)
                raise ValueError
            case AttributeType.FLOAT:
                if isinstance(value, float):
                    return value
                if isinstance(value, int):
                    return float(value)
                raise ValueError
            case _:
                raise ValueError

    @staticmethod
    def _validate_allowed_values_for_type(
        values: list[Any],
        parameter_type: AttributeType,
    ) -> list[Any]:
        match parameter_type:
            case AttributeType.STR:
                if all(isinstance(item, str) for item in values):
                    return values
                raise ValueError
            case AttributeType.INT:
                if all(isinstance(item, int) for item in values):
                    return values
                raise ValueError
            case AttributeType.FLOAT:
                if all(isinstance(item, float) for item in values):
                    return values
                raise ValueError
            case _:
                raise ValueError

    def __init__(self) -> None:
        object.__setattr__(self, "key", None) # str
        object.__setattr__(self, "type", None) # AttributeType
        object.__setattr__(self, "required", None) # bool
        object.__setattr__(self, "description", None) # str
        object.__setattr__(self, "min", None) # int|float
        object.__setattr__(self, "max", None) # int|float
        object.__setattr__(self, "allowed_values", None) # list[str]

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "key":
            if isinstance(value, str):
                object.__setattr__(self, "key", value)
            else:
                raise ValueError
        elif name == "type":
            converted_type: AttributeType
            if isinstance(value, AttributeType):
                converted_type = value
            elif isinstance(value, str):
                converted_type = AttributeType(value)
            else:
                raise ValueError

            if self.min is not None:
                normalized_min = self._normalize_min_max_for_type(self.min, converted_type)
                object.__setattr__(self, "min", normalized_min)
            if self.max is not None:
                normalized_max = self._normalize_min_max_for_type(self.max, converted_type)
                object.__setattr__(self, "max", normalized_max)
            if self.allowed_values is not None:
                if isinstance(self.allowed_values, list):
                    normalized_allowed_values = self._validate_allowed_values_for_type(self.allowed_values, converted_type)
                    object.__setattr__(self, "allowed_values", normalized_allowed_values)
                else:
                    raise ValueError
        elif name == "required":
            if isinstance(value, bool):
                object.__setattr__(self, "required", value)
            elif isinstance(value, str):
                object.__setattr__(self, "required", self._str_to_bool(value))
            else:
                raise ValueError
        elif name == "description":
            if isinstance(value, str):
                object.__setattr__(self, "description", value)
            else:
                raise ValueError
        elif name == "min":
            if isinstance(value, (int, float)):
                if self.type is None:
                    object.__setattr__(self, "min", value)
                else:
                    match self.type:
                        case AttributeType.INT:
                            if isinstance(value, int):
                                object.__setattr__(self, "min", value)
                            elif isinstance(value, float):
                                object.__setattr__(self, "min", int(value))
                            else:
                                raise ValueError
                        case AttributeType.FLOAT:
                            if isinstance(value, float):
                                object.__setattr__(self, "min", value)
                            elif isinstance(value, int):
                                object.__setattr__(self, "min", float(value))
                            else:
                                raise ValueError
                        case _:
                            raise ValueError
            else:
                raise ValueError
        elif name == "max":
            if isinstance(value, (int, float)):
                if self.type is None:
                    object.__setattr__(self, "max", value)
                else:
                    match self.type:
                        case AttributeType.INT:
                            if isinstance(value, int):
                                object.__setattr__(self, "max", value)
                            elif isinstance(value, float):
                                object.__setattr__(self, "max", int(value))
                            else:
                                raise ValueError
                        case AttributeType.FLOAT:
                            if isinstance(value, float):
                                object.__setattr__(self, "max", value)
                            elif isinstance(value, int):
                                object.__setattr__(self, "max", float(value))
                            else:
                                raise ValueError
                        case _:
                            raise ValueError
            else:
                raise ValueError
        elif name == "allowed_values":
            if isinstance(value, list):
                if self.type is None:
                    object.__setattr__(self, "allowed_values", value)
                else:
                    match self.type:
                        case AttributeType.STR:
                            if all(isinstance(item, str) for item in value):
                                object.__setattr__(self, "allowed_values", value)
                            else:
                                raise ValueError
                        case AttributeType.INT:
                            if all(isinstance(item, int) for item in value):
                                object.__setattr__(self, "allowed_values", value)
                            else:
                                raise ValueError
                        case AttributeType.FLOAT:
                            if all(isinstance(item, float) for item in value):
                                object.__setattr__(self, "allowed_values", value)
                            else:
                                raise ValueError
                        case _:
                            raise ValueError
            else:
                raise ValueError
        else:
            pass
    
    def __repr__(self) -> str:
        return self.to_json()
    
    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.key is not None:
            result["key"] = self.key
        if self.type is not None:
            if recursive:
                result["type"] = self.type.value
            else:
                result["type"] = self.type
        if self.required is not None:
            result["required"] = self.required
        if self.description is not None:
            result["description"] = self.description
        if self.min is not None:
            result["min"] = self.min
        if self.max is not None:
            result["max"] = self.max
        if self.allowed_values is not None:
            result["allowed_values"] = self.allowed_values
        return result
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AttributeDefinition":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity
    
    @classmethod
    def from_json(cls, json_str: str) -> "AttributeDefinition":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
    
    @staticmethod
    def _str_to_bool(value: str) -> bool:
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        raise ValueError
