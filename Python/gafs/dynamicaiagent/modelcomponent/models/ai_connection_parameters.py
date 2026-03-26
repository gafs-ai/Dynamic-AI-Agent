from __future__ import annotations

import json
from abc import ABC
from typing import Any

from .ai_deployment_type import AiDeploymentType
from .ai_provider_type import AiProviderType
from gafs.dynamicaiagent.cloudaicomponent.models.cloud_ai_provider_type import CloudAiProviderType
from .ai_operation_type import AiOperationType

class AiConnectionParameters(ABC):
    """Base connection-parameter class for AI providers.

    - `deployment_type` selects the deployment family (CLOUD, LOCAL, REMOTE, ...).
    - Arbitrary provider-specific parameters are stored in `custom_parameters`.
    """

    def __init__(self, operation_type: AiOperationType|str, deployment_type: AiDeploymentType | str, provider_type: AiProviderType | str) -> None:
        if isinstance(operation_type, AiOperationType):
            object.__setattr__(self, "operation_type", operation_type)
        elif isinstance(operation_type, str):
            object.__setattr__(self, "operation_type", AiOperationType(operation_type))
        else:
            raise ValueError

        if isinstance(deployment_type, AiDeploymentType):
            object.__setattr__(self, "deployment_type", deployment_type)
        elif isinstance(deployment_type, str):
            object.__setattr__(self, "deployment_type", AiDeploymentType(deployment_type))
        else:
            raise ValueError

        if self.deployment_type == AiDeploymentType.CLOUD:
            if isinstance(provider_type, CloudAiProviderType):
                object.__setattr__(self, "provider_type", provider_type)
            elif isinstance(provider_type, str):
                try:
                    object.__setattr__(self, "provider_type", CloudAiProviderType(provider_type))
                except ValueError:
                    object.__setattr__(self, "provider_type", provider_type)
            else:
                raise ValueError
        elif self.deployment_type == AiDeploymentType.REMOE:
            raise NotImplementedError("Remote deployment is not supported yet.")
        elif self.deployment_type == AiDeploymentType.LOCAL:
            raise NotImplementedError("Local deployment is not supported yet.")
        else:
            raise ValueError

        object.__setattr__(self, "parameters", dict[str, Any]())

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "operation_type":
            raise AttributeError("operation_type is read-only.")
        if name == "deployment_type":
            raise AttributeError("deployment_type is read-only.")
        elif name == "provider_type":
            raise AttributeError("provider_type is read-only.")
        elif name == "parameters":
            if isinstance(value, dict):
                for key, value in value.items():
                    self.parameters[key] = value
            else:
                raise ValueError
        else:
            self.parameters[name] = value

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert to a dictionary.

        Args:
            recursive: If True, convert Enum fields to their string values.

        Returns:
            Dictionary representation of this instance.
        """
        result: dict[str, Any] = {}

        if self.operation_type is not None:
            if recursive:
                result["operation_type"] = self.operation_type.value
            else:
                result["operation_type"] = self.operation_type

        if self.deployment_type is not None:
            if recursive:
                result["deployment_type"] = self.deployment_type.value
            else:
                result["deployment_type"] = self.deployment_type

        if isinstance(self.provider_type, AiProviderType):
            if recursive:
                result["provider_type"] = self.provider_type.value
            else:
                result["provider_type"] = self.provider_type
        elif isinstance(self.provider_type, str):
            result["provider_type"] = self.provider_type

        if self.parameters is not None:
            result["parameters"] = self.parameters

        return result

    def to_json(self) -> str:
        """Serialize to a JSON string.

        Returns:
            JSON string representation. Nested objects are converted to primitives.
        """
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AiConnectionParameters":
        if "operation_type" in data:
            if isinstance(data["operation_type"], AiOperationType):
                operation_type = data.pop("operation_type")
            elif isinstance(data["operation_type"], str):
                operation_type = AiOperationType(data.pop("operation_type"))
            else:
                raise ValueError
        else:
            raise ValueError("operation_type is required.")
        
        if "deployment_type" in data:
            if isinstance(data["deployment_type"], AiDeploymentType):
                deployment_type = data.pop("deployment_type")
            elif isinstance(data["deployment_type"], str):
                deployment_type = AiDeploymentType(data.pop("deployment_type"))
            else:
                raise ValueError
        else:
            raise ValueError("deployment_type is required.")

        if "provider_type" in data:
            if isinstance(data["provider_type"], AiProviderType):
                provider_type = data.pop("provider_type")
            elif isinstance(data["provider_type"], str):
                try:
                    provider_type = AiProviderType(data["provider_type"])
                except ValueError:
                    provider_type = data["provider_type"]
                data.pop("provider_type", None)
            else:
                raise ValueError
        else:
            raise ValueError("provider_type is required.")

        entity = cls(deployment_type=deployment_type, provider_type=provider_type)

        for key, value in data.items():
            setattr(entity, key, value)

        return entity


    @classmethod
    def from_json(cls, json_str: str) -> "AiConnectionParameters":
        converted: Any = json.loads(json_str)
        if isinstance(converted, dict):
            return cls.from_dict(converted)
        else:
            raise ValueError("json_str is not a valid dictionary.")


