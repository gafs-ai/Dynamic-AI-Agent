"""AiConnectionParameters — value object that identifies the AI backend and carries provider-specific configuration."""

from __future__ import annotations

import json
from typing import Any

from .ai_deployment_type import AiDeploymentType
from .ai_operation_type import AiOperationType
from .ai_provider_type import AiProviderType


class AiConnectionParameters:
    """Connection parameters for an AI provider.

    Holds the operation type, deployment family, provider type, and provider-specific
    parameters (endpoint, api_key, model, etc.).

    NOTE: operation_type, deployment_type, and provider_type are read-only after construction.
    Assigning a dict to parameters MERGES it into the existing dict (does not replace).
    Setting an unknown attribute is equivalent to setting parameters[key] = value.

    NOTE: CloudAiProviderType is imported lazily inside __init__ to avoid a circular import
    between modelcomponent and cloudaicomponent.
    """

    def __init__(
        self,
        operation_type: AiOperationType | str,
        deployment_type: AiDeploymentType | str,
        provider_type: AiProviderType | str,
    ) -> None:
        # Resolve operation_type
        if isinstance(operation_type, AiOperationType):
            object.__setattr__(self, "operation_type", operation_type)
        elif isinstance(operation_type, str):
            object.__setattr__(self, "operation_type", AiOperationType(operation_type))
        else:
            raise ValueError

        # Resolve deployment_type
        if isinstance(deployment_type, AiDeploymentType):
            object.__setattr__(self, "deployment_type", deployment_type)
        elif isinstance(deployment_type, str):
            object.__setattr__(self, "deployment_type", AiDeploymentType(deployment_type))
        else:
            raise ValueError

        # Resolve provider_type based on deployment_type
        resolved_deployment = self.deployment_type
        if resolved_deployment == AiDeploymentType.CLOUD:
            # Lazy import to avoid circular dependency: cloudaicomponent -> modelcomponent -> cloudaicomponent
            from gafs.dynamicaiagent.cloudaicomponent.models.cloud_ai_provider_type import CloudAiProviderType
            if isinstance(provider_type, CloudAiProviderType):
                object.__setattr__(self, "provider_type", provider_type)
            elif isinstance(provider_type, str):
                try:
                    object.__setattr__(self, "provider_type", CloudAiProviderType(provider_type))
                except ValueError:
                    # Store as custom string provider
                    object.__setattr__(self, "provider_type", provider_type)
            else:
                raise ValueError
        elif resolved_deployment == AiDeploymentType.REMOTE:
            raise NotImplementedError("Remote deployment is not supported yet.")
        elif resolved_deployment == AiDeploymentType.LOCAL:
            raise NotImplementedError("Local deployment is not supported yet.")
        else:
            raise ValueError

        # Initialize parameters as empty dict
        object.__setattr__(self, "parameters", {})

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "operation_type":
            raise AttributeError("operation_type is read-only.")
        elif name == "deployment_type":
            raise AttributeError("deployment_type is read-only.")
        elif name == "provider_type":
            raise AttributeError("provider_type is read-only.")
        elif name == "parameters":
            if isinstance(value, dict):
                # Merge into the existing parameters dict (do not replace)
                for k, v in value.items():
                    self.parameters[k] = v
            else:
                raise ValueError
        else:
            # Setting any unknown attribute is equivalent to parameters[name] = value
            self.parameters[name] = value

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
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
        if self.provider_type is not None:
            if isinstance(self.provider_type, AiProviderType):
                if recursive:
                    result["provider_type"] = self.provider_type.value
                else:
                    result["provider_type"] = self.provider_type
            else:
                # Custom string provider
                result["provider_type"] = self.provider_type
        if self.parameters:
            result["parameters"] = self.parameters
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AiConnectionParameters":
        # All three key fields are required
        if "operation_type" not in data:
            raise ValueError("operation_type is required.")
        if "deployment_type" not in data:
            raise ValueError("deployment_type is required.")
        if "provider_type" not in data:
            raise ValueError("provider_type is required.")

        operation_type = data["operation_type"]
        deployment_type = data["deployment_type"]
        provider_type = data["provider_type"]

        entity = cls(
            operation_type=operation_type,
            deployment_type=deployment_type,
            provider_type=provider_type,
        )

        # Merge any remaining keys as parameters
        for key, value in data.items():
            if key in ("operation_type", "deployment_type", "provider_type"):
                continue
            if key == "parameters" and isinstance(value, dict):
                entity.parameters = value
            elif value is not None:
                entity.parameters[key] = value

        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "AiConnectionParameters":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
