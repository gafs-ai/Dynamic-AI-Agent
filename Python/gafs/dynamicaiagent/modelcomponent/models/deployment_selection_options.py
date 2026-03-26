import json
from typing import Any
from .ai_deployment_type import AiDeploymentType

class DeploymentSelectionOptions:
    def __init__(self):
        object.__setattr__(self, "deployment_type", None)
        object.__setattr__(self, "confidence", None)
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name == "deployment_type":
            if isinstance(value, AiDeploymentType):
                object.__setattr__(self, "deployment_type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "deployment_type", AiDeploymentType(value))
            else:
                raise ValueError
        elif name == "confidence":
            if isinstance(value, int):
                object.__setattr__(self, "confidence", value)
            else:
                raise ValueError
        else:
            raise ValueError
    
    def __repr__(self) -> str:
        return self.to_json()
    
    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        converted: dict[str, Any] = {}
        if self.deployment_type is not None:
            if recursive:
                converted["deployment_type"] = self.deployment_type.value
            else:
                converted["deployment_type"] = self.deployment_type
        if self.confidence is not None:
            converted["confidence"] = self.confidence
        return converted
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeploymentSelectionOptions":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "DeploymentSelectionOptions":
        return cls.from_dict(json.loads(json_str))
