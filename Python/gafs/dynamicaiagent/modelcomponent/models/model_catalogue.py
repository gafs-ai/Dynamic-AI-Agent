"""Model catalogue data model and deployment types.

Defines ModelCatalogue (metadata for AI models), deployment variants
(Local, Remote, Cloud), and related enums used by the model catalogue service.
"""
from __future__ import annotations

import json
from enum import Enum
from typing import Any, cast

from surrealdb import RecordID

from .ai_connection_parameters import AiConnectionParameters
from .ai_operation_type import AiOperationType
from .ai_provider_type import AiProviderType
from gafs.dynamicaiagent.cloudaicomponent.models.cloud_ai_provider_type import CloudAiProviderType

from .ai_deployment_type import AiDeploymentType

class ModelStatus(Enum):
    """Lifecycle status of a model in the catalogue."""

    RECOMMENDED = "recommended"
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class DeploymentStatus(Enum):
    """Status of a deployment."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class ParameterType(Enum):
    """Type of a parameter."""
    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"

class _BooleanConversionHelper:
    @staticmethod
    def _str_to_bool(value: str) -> bool:
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        else:
            raise ValueError


class AvailableInferenceParameters:
    @staticmethod
    def _normalize_min_max_for_type(
        value: Any,
        parameter_type: ParameterType,
    ) -> int | float:
        match parameter_type:
            case ParameterType.INT:
                if isinstance(value, int):
                    return value
                if isinstance(value, float):
                    return int(value)
                raise ValueError
            case ParameterType.FLOAT:
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
        parameter_type: ParameterType,
    ) -> list[Any]:
        match parameter_type:
            case ParameterType.STR:
                if all(isinstance(item, str) for item in values):
                    return values
                raise ValueError
            case ParameterType.INT:
                if all(isinstance(item, int) for item in values):
                    return values
                raise ValueError
            case ParameterType.FLOAT:
                if all(isinstance(item, float) for item in values):
                    return values
                raise ValueError
            case _:
                raise ValueError

    def __init__(self) -> None:
        object.__setattr__(self, "key", None) # str
        object.__setattr__(self, "type", None) # ParameterType
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
            converted_type: ParameterType
            if isinstance(value, ParameterType):
                converted_type = value
            elif isinstance(value, str):
                converted_type = ParameterType(value)
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
                object.__setattr__(self, "required", _BooleanConversionHelper._str_to_bool(value))
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
                        case ParameterType.INT:
                            if isinstance(value, int):
                                object.__setattr__(self, "min", value)
                            elif isinstance(value, float):
                                object.__setattr__(self, "min", int(value))
                            else:
                                raise ValueError
                        case ParameterType.FLOAT:
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
                        case ParameterType.INT:
                            if isinstance(value, int):
                                object.__setattr__(self, "max", value)
                            elif isinstance(value, float):
                                object.__setattr__(self, "max", int(value))
                            else:
                                raise ValueError
                        case ParameterType.FLOAT:
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
                        case ParameterType.STR:
                            if all(isinstance(item, str) for item in value):
                                object.__setattr__(self, "allowed_values", value)
                            else:
                                raise ValueError
                        case ParameterType.INT:
                            if all(isinstance(item, int) for item in value):
                                object.__setattr__(self, "allowed_values", value)
                            else:
                                raise ValueError
                        case ParameterType.FLOAT:
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
    def from_dict(cls, data: dict[str, Any]) -> "AvailableInferenceParameters":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity
    
    @classmethod
    def from_json(cls, json_str: str) -> "AvailableInferenceParameters":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class ModelDeployment:
    """Base deployment descriptor for an AI model.

    Attributes:
        deployment_type: Where the model runs (local, remote, cloud).
        priority: Deployment priority; larger value means higher priority.
        max_confidence_level: Maximum input confidence level this deployment
            accepts (e.g. 0: unclassified, 1: restricted, 2: confidential,
            3: secret, 4: top secret). Users may define their own levels.
        secrets: Optional list of links to secret resources managed by the secret manager.
    """

    def __init__(self):
        object.__setattr__(self, "id", None) # str
        object.__setattr__(self, "name", None) # str
        object.__setattr__(self, "description", None) # str
        object.__setattr__(self, "tags", None) # list[str]
        object.__setattr__(self, "secrets", None) # list[str] IDs of linked secrets
        object.__setattr__(self, "deployment_type", None) # AiDeploymentType
        object.__setattr__(self, "provider_type", None) # AiProviderType
        object.__setattr__(self, "connection_parameters", None) # dict[str, Any]
        object.__setattr__(self, "priority", None) # int
        object.__setattr__(self, "max_confidence_level", None) # int
        object.__setattr__(self, "status", None) # ModelStatus
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name == "id" or name == "$id":
            if value is None:
                object.__setattr__(self, "id", None)
            elif isinstance(value, str):
                # Normalize SurrealDB record IDs (e.g. "table:id") into the document ID only.
                object.__setattr__(self, "id", value.rsplit(":", 1)[-1])
            elif isinstance(value, RecordID):
                normalized = cast(str, value.id).rsplit(":", 1)[-1]
                object.__setattr__(self, "id", normalized)
            else:
                raise ValueError
        elif name == "name":
            if isinstance(value, str):
                object.__setattr__(self, "name", value)
            else:
                raise ValueError
        elif name == "description":
            if isinstance(value, str):
                object.__setattr__(self, "description", value)
            else:
                raise ValueError
        elif name == "tags":
            if isinstance(value, list) and all(isinstance(tag, str) for tag in value):
                object.__setattr__(self, "tags", value)
            else:
                raise ValueError
        elif name == "secrets":
            if isinstance(value, list) and all(isinstance(link, str) for link in value):
                object.__setattr__(self, "secrets", value)
            else:
                raise ValueError
        elif name == "deployment_type":
            if isinstance(value, AiDeploymentType):
                object.__setattr__(self, "deployment_type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "deployment_type", AiDeploymentType(value))
            else:
                raise ValueError
        elif name == "provider_type":
            match self.deployment_type:
                case AiDeploymentType.CLOUD:
                    if isinstance(value, CloudAiProviderType):
                        object.__setattr__(self, "provider_type", value)
                    elif isinstance(value, str):
                        object.__setattr__(self, "provider_type", CloudAiProviderType(value))
                    else:
                        raise ValueError
                case AiDeploymentType.REMOTE:
                    # TODO: Implement remote deployment
                    raise NotImplementedError
                case AiDeploymentType.LOCAL:
                    # TODO: Implement local deployment
                    raise NotImplementedError
                case _:
                    raise ValueError
        elif name == "connection_parameters":
            if isinstance(value, dict):
                object.__setattr__(self, "connection_parameters", value)
            else:
                raise ValueError
        elif name == "priority":
            if isinstance(value, int):
                object.__setattr__(self, "priority", value)
            else:
                raise ValueError
        elif name == "max_confidence_level":
            if isinstance(value, int):
                object.__setattr__(self, "max_confidence_level", value)
            else:
                raise ValueError
        elif name == "status":
            if isinstance(value, DeploymentStatus):
                object.__setattr__(self, "status", value)
            elif isinstance(value, str):
                object.__setattr__(self, "status", DeploymentStatus(value))
            else:
                raise ValueError
        else:
            pass

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(
        self,
        recursive: bool = False,
        exclude_id: bool = False,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if not exclude_id:
            if self.id is not None:
                result["id"] = self.id
        if self.name is not None:
            result["name"] = self.name
        if self.description is not None:
            result["description"] = self.description
        if self.tags is not None:
            result["tags"] = self.tags
        if self.secrets is not None:
            result["secrets"] = self.secrets
        if self.deployment_type is not None:
            if recursive:
                result["deployment_type"] = self.deployment_type.value
            else:
                result["deployment_type"] = self.deployment_type
        if self.provider_type is not None:
            if recursive:
                result["provider_type"] = self.provider_type.value
            else:
                result["provider_type"] = self.provider_type
        if self.connection_parameters is not None:
            result["connection_parameters"] = self.connection_parameters
        if self.priority is not None:
            result["priority"] = self.priority
        if self.max_confidence_level is not None:
            result["max_confidence_level"] = self.max_confidence_level
        if self.status is not None:
            if recursive:
                result["status"] = self.status.value
            else:
                result["status"] = self.status
        return result
    
    def to_json(self, exclude_id: bool = False) -> str:
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelDeployment":
        if not isinstance(data, dict):
            raise ValueError
        
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity
    
    @classmethod
    def from_json(cls, json_str: str) -> "ModelDeployment":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class ModelCatalogue:
    """Metadata record for an AI model in the catalogue.

    Stored in the model catalogue store (e.g. SurrealDB). Supports
    optional description, vector, tags, and multiple deployments.

    This base entity represents the record as it is stored in the
    catalogue. It does *not* include search-specific fields such as
    the distance from a query vector.

    Attributes:
        id: Unique identifier (record ID in the store).
        name: Human-readable model name.
        type: Type of model (embedding, completion, chat).
        status: Lifecycle status; defaults to ACTIVE.
        description: Optional text description.
        description_vector: Optional embedding vector for similarity search.
        priority: Model priority; larger value means higher priority.
        tags: Optional list of tags for filtering.
        deployments: Optional list of deployment descriptors (local, remote,
            or cloud).
    """

    def __init__(self):
        object.__setattr__(self, "id", None)
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "type", None)
        object.__setattr__(self, "status", None)
        object.__setattr__(self, "description", None)
        object.__setattr__(self, "description_vector", None)
        object.__setattr__(self, "priority", None)
        object.__setattr__(self, "tags", None)
        object.__setattr__(self, "deployments", None)
        object.__setattr__(self, "default_inference_parameters", None)
        object.__setattr__(self, "available_inference_parameters", None)


    def __setattr__(self, name: str, value: Any) -> None:
        if name == "id" or name == "$id":
            if value is None:
                object.__setattr__(self, "id", None)
            elif isinstance(value, str):
                # Normalize SurrealDB record IDs (e.g. "table:id") into the document ID only.
                object.__setattr__(self, "id", value.rsplit(":", 1)[-1])
            elif isinstance(value, RecordID):
                normalized = cast(str, value.id).rsplit(":", 1)[-1]
                object.__setattr__(self, "id", normalized)
            else:
                raise ValueError

        elif name == "name":
            if isinstance(value, str):
                object.__setattr__(self, "name", value)
            else:
                raise ValueError

        elif name == "type":
            if isinstance(value, AiOperationType):
                object.__setattr__(self, "type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "type", AiOperationType(value))
            else:
                raise ValueError
        
        elif name == "status":
            if isinstance(value, ModelStatus):
                object.__setattr__(self, "status", value)
            elif isinstance(value, str):
                object.__setattr__(self, "status", ModelStatus(value))
            else:
                raise ValueError
        
        elif name == "description":
            if isinstance(value, str):
                object.__setattr__(self, "description", value)
            else:
                raise ValueError
        
        elif name == "description_vector":
            if isinstance(value, list):
                object.__setattr__(self, "description_vector", value)
            else:
                raise ValueError
        
        elif name == "priority":
            if isinstance(value, int):
                object.__setattr__(self, "priority", value)
            else:
                raise ValueError
        
        elif name == "tags":
            if isinstance(value, list):
                object.__setattr__(self, "tags", value)
            else:
                raise ValueError
        
        elif name == "deployments":
            if isinstance(value, list):
                if all(isinstance(item, str) for item in value):
                    object.__setattr__(self, "deployments", value)
                else:
                    raise ValueError
            else:
                raise ValueError
        
        elif name == "default_inference_parameters":
            if isinstance(value, dict):
                object.__setattr__(self, "default_inference_parameters", value)
            else:
                raise ValueError
        elif name == "available_inference_parameters":
            if isinstance(value, list):
                if len(value) > 0:
                    if isinstance(value[0], AvailableInferenceParameters):
                        object.__setattr__(self, "available_inference_parameters", value)
                    elif isinstance(value[0], dict):
                        converted: list[AvailableInferenceParameters] = []
                        for item in value:
                            converted.append(AvailableInferenceParameters.from_dict(item))
                        object.__setattr__(self, "available_inference_parameters", converted)
                    else:
                        raise ValueError
                else:
                    object.__setattr__(self, "available_inference_parameters", value)
            else:
                raise ValueError
        else:
            pass


    def __repr__(self) -> str:
        return self.to_json()


    def to_dict(self, recursive: bool = False, exclude_id: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}

        if not exclude_id:
            if self.id is not None:
                result["id"] = self.id
        if self.name is not None:
            result["name"] = self.name
        if self.type is not None:
            if recursive:
                result["type"] = self.type.value
            else:
                result["type"] = self.type
        if self.status is not None:
            if recursive:
                result["status"] = self.status.value
            else:
                result["status"] = self.status
        if self.description is not None:
            result["description"] = self.description
        if self.description_vector is not None:
            result["description_vector"] = self.description_vector
        if self.priority is not None:
            result["priority"] = self.priority
        if self.tags is not None:
            result["tags"] = self.tags
        if self.deployments is not None:
            result["deployments"] = self.deployments
        if self.default_inference_parameters is not None:
            result["default_inference_parameters"] = self.default_inference_parameters
        if self.available_inference_parameters is not None:
            if recursive:
                result["available_inference_parameters"] = [item.to_dict(recursive=True) for item in self.available_inference_parameters]
            else:
                result["available_inference_parameters"] = self.available_inference_parameters
        return result


    def to_json(self, exclude_id: bool = False) -> str:
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))


    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelCatalogue":
        if not isinstance(data, dict):
            raise ValueError

        entity = cls()
        
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity


    @classmethod
    def from_json(cls, json_str: str) -> "ModelCatalogue":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class ModelCatalogueSearchResultEntry(ModelCatalogue):
    """Search result entry for a model catalogue."""

    def __init__(self):
        super().__init__()
        object.__setattr__(self, "distance", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "distance" or name == "dist": # dist as an alias for distance
            if isinstance(value, float):
                object.__setattr__(self, "distance", value)
            elif isinstance(value, int):
                object.__setattr__(self, "distance", float(value))
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = super().to_dict(recursive=recursive)
        if self.distance is not None:
            result["distance"] = self.distance
        return result
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))
