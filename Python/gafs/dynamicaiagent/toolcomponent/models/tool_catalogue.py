"""tool_catalogue.py - Data models for ToolCatalogueEntry and ToolVersionEntry.

Defines the persisted data models for tool catalogue entries and their version
records, along with supporting enums and parameter definition sub-classes.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from surrealdb import RecordID

from gafs.dynamicaiagent.common.models import FieldAttributeType


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ToolStatus(Enum):
    """Lifecycle status of a tool in the catalogue."""

    DEVELOPMENT = "development"
    """Under development."""

    EARLY = "early_access"
    """Early access / beta release."""

    ACTIVE = "active"
    """Available for use."""

    DEPRECATED = "deprecated"
    """Scheduled for retirement; avoid new usage."""

    RETIRED = "retired"
    """No longer available."""


class ToolVersionStatus(Enum):
    """Lifecycle status of a tool version."""

    DEVELOPMENT = "development"
    """Under development."""

    EARLY = "early_access"
    """Early access / beta release."""

    LATEST = "latest"
    """Latest version recommended for use."""

    ACTIVE = "active"
    """Available for use (but not the latest version)."""

    DEPRECATED = "deprecated"
    """Scheduled for retirement; avoid new usage."""

    RETIRED = "retired"
    """No longer available."""


# ---------------------------------------------------------------------------
# Parameter definition sub-classes
# ---------------------------------------------------------------------------

class InputParameterDefinition:
    """Definition of a single input parameter for a tool version.

    Attributes:
        name: Name of the parameter.
        description: Optional description.
        type: Type of the value.
        required: Whether the value is required.
        default: Default value string.
        allowed_values: Set of allowed values.
        min_value: Minimum value (inclusive boundary).
        max_value: Maximum value (exclusive boundary).
    """

    def __init__(self) -> None:
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "description", None)
        object.__setattr__(self, "type", None)
        object.__setattr__(self, "required", None)
        object.__setattr__(self, "default", None)
        object.__setattr__(self, "allowed_values", None)
        object.__setattr__(self, "min_value", None)
        object.__setattr__(self, "max_value", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "name":
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "description":
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "type":
            if isinstance(value, FieldAttributeType):
                object.__setattr__(self, name, value)
            elif isinstance(value, str):
                object.__setattr__(self, name, FieldAttributeType(value))
            else:
                raise ValueError
        elif name == "required":
            if isinstance(value, bool):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "default":
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "allowed_values":
            if isinstance(value, (set, list)):
                object.__setattr__(self, name, set(value) if isinstance(value, list) else value)
            else:
                raise ValueError
        elif name in ("min_value", "max_value"):
            # Accept any value for min/max since type depends on the parameter type
            object.__setattr__(self, name, value)
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.name is not None:
            result["name"] = self.name
        if self.description is not None:
            result["description"] = self.description
        if self.type is not None:
            result["type"] = self.type.value if recursive else self.type
        if self.required is not None:
            result["required"] = self.required
        if self.default is not None:
            result["default"] = self.default
        if self.allowed_values is not None:
            result["allowed_values"] = list(self.allowed_values) if recursive else self.allowed_values
        if self.min_value is not None:
            result["min_value"] = self.min_value
        if self.max_value is not None:
            result["max_value"] = self.max_value
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InputParameterDefinition":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "InputParameterDefinition":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class OutputParameterDefinition:
    """Definition of a single output parameter for a tool version.

    Attributes:
        name: Name of the parameter.
        description: Optional description.
        type: Type of the value.
        nullable: Whether the value is nullable.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "description", None)
        object.__setattr__(self, "type", None)
        object.__setattr__(self, "nullable", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "name":
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "description":
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "type":
            if isinstance(value, FieldAttributeType):
                object.__setattr__(self, name, value)
            elif isinstance(value, str):
                object.__setattr__(self, name, FieldAttributeType(value))
            else:
                raise ValueError
        elif name == "nullable":
            if isinstance(value, bool):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.name is not None:
            result["name"] = self.name
        if self.description is not None:
            result["description"] = self.description
        if self.type is not None:
            result["type"] = self.type.value if recursive else self.type
        if self.nullable is not None:
            result["nullable"] = self.nullable
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OutputParameterDefinition":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "OutputParameterDefinition":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class InputFileDefinition:
    """Definition of a single input file parameter for a tool version.

    Attributes:
        name: Name of the parameter.
        description: Optional description.
        min: Minimum number of files (inclusive).
        max: Maximum number of files (exclusive).
        max_size: Size limit of a single file in bytes.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "description", None)
        object.__setattr__(self, "min", None)
        object.__setattr__(self, "max", None)
        object.__setattr__(self, "max_size", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "name":
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "description":
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name in ("min", "max", "max_size"):
            if isinstance(value, int):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.name is not None:
            result["name"] = self.name
        if self.description is not None:
            result["description"] = self.description
        if self.min is not None:
            result["min"] = self.min
        if self.max is not None:
            result["max"] = self.max
        if self.max_size is not None:
            result["max_size"] = self.max_size
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InputFileDefinition":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "InputFileDefinition":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class OutputFileDefinition:
    """Definition of a single output file parameter for a tool version.

    Attributes:
        name: Name of the parameter.
        description: Optional description.
        min: Minimum number of files (inclusive).
        max: Maximum number of files (exclusive).
    """

    def __init__(self) -> None:
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "description", None)
        object.__setattr__(self, "min", None)
        object.__setattr__(self, "max", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "name":
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "description":
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name in ("min", "max"):
            if isinstance(value, int):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.name is not None:
            result["name"] = self.name
        if self.description is not None:
            result["description"] = self.description
        if self.min is not None:
            result["min"] = self.min
        if self.max is not None:
            result["max"] = self.max
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OutputFileDefinition":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "OutputFileDefinition":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


# ---------------------------------------------------------------------------
# ToolCatalogueEntry
# ---------------------------------------------------------------------------

class ToolCatalogueEntry:
    """Persisted record for a tool in the tool catalogue.

    Attributes:
        id: Record ID (stripped of table prefix).
        status: Lifecycle status of the tool.
        name: Unique tool name.
        description: Optional description of the tool.
        description_vector: Embedding vector for similarity search.
        tags: Optional list of string tags.
    """

    @staticmethod
    def CollectionName() -> str:
        """SurrealDB collection name for tool catalogue records."""
        return "ToolCatalogue"

    def __init__(self) -> None:
        object.__setattr__(self, "id", None)
        object.__setattr__(self, "status", None)
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "description", None)
        object.__setattr__(self, "description_vector", None)
        object.__setattr__(self, "tags", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("id", "$id"):
            # Normalize SurrealDB RecordID to bare string id
            if value is None:
                object.__setattr__(self, "id", None)
            elif isinstance(value, RecordID):
                object.__setattr__(self, "id", str(value.id))
            elif isinstance(value, str):
                # Strip table prefix if present (e.g. "ToolCatalogue:abc" -> "abc")
                object.__setattr__(self, "id", value.rsplit(":", 1)[-1] if ":" in value else value)
            elif isinstance(value, dict):
                raw = value.get("id") or value.get("$id")
                if raw is not None:
                    setattr(self, "id", raw)
                else:
                    raise ValueError
            else:
                object.__setattr__(self, "id", str(value))
        elif name == "status":
            if isinstance(value, ToolStatus):
                object.__setattr__(self, name, value)
            elif isinstance(value, str):
                object.__setattr__(self, name, ToolStatus(value))
            else:
                raise ValueError
        elif name == "name":
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "description":
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "description_vector":
            if isinstance(value, list):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "tags":
            if isinstance(value, list):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False, exclude_id: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if not exclude_id:
            if self.id is not None:
                result["id"] = self.id
        if self.status is not None:
            result["status"] = self.status.value if recursive else self.status
        if self.name is not None:
            result["name"] = self.name
        if self.description is not None:
            result["description"] = self.description
        if self.description_vector is not None:
            result["description_vector"] = self.description_vector
        if self.tags is not None:
            result["tags"] = self.tags
        return result

    def to_json(self, exclude_id: bool = False) -> str:
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolCatalogueEntry":
        entity = cls()
        for key, value in data.items():
            if value is not None:
                try:
                    setattr(entity, key, value)
                except (ValueError, AttributeError):
                    continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "ToolCatalogueEntry":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


# ---------------------------------------------------------------------------
# ToolVersionEntry
# ---------------------------------------------------------------------------

class ToolVersionEntry:
    """Persisted record for a specific version of a tool.

    Attributes:
        id: Record ID (stripped of table prefix).
        tool_id: ID referencing the parent ToolCatalogueEntry.
        status: Lifecycle status of this version.
        description: Optional description of this version.
        language: Programming language (e.g. 'Python', 'Python3.12').
        sandbox_id: ID of a specific sandbox to use for execution.
        sandbox_selection_tags: Tags used to auto-select a sandbox.
        code: Program code stored directly in the database.
        code_link: Link to the code repository.
        input_parameters: List of input parameter definitions.
        input_files: List of input file definitions.
        output_parameters: List of output parameter definitions.
        output_files: List of output file definitions.
    """

    @staticmethod
    def CollectionName() -> str:
        """SurrealDB collection name for tool version records."""
        return "ToolVersions"

    def __init__(self) -> None:
        object.__setattr__(self, "id", None)
        object.__setattr__(self, "tool_id", None)
        object.__setattr__(self, "status", None)
        object.__setattr__(self, "description", None)
        object.__setattr__(self, "language", None)
        object.__setattr__(self, "sandbox_id", None)
        object.__setattr__(self, "sandbox_selection_tags", None)
        object.__setattr__(self, "code", None)
        object.__setattr__(self, "code_link", None)
        object.__setattr__(self, "input_parameters", None)
        object.__setattr__(self, "input_files", None)
        object.__setattr__(self, "output_parameters", None)
        object.__setattr__(self, "output_files", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("id", "$id"):
            if value is None:
                object.__setattr__(self, "id", None)
            elif isinstance(value, RecordID):
                object.__setattr__(self, "id", str(value.id))
            elif isinstance(value, str):
                object.__setattr__(self, "id", value.rsplit(":", 1)[-1] if ":" in value else value)
            elif isinstance(value, dict):
                raw = value.get("id") or value.get("$id")
                if raw is not None:
                    setattr(self, "id", raw)
                else:
                    raise ValueError
            else:
                object.__setattr__(self, "id", str(value))
        elif name == "tool_id":
            if isinstance(value, str):
                # Strip table prefix if present
                object.__setattr__(self, name, value.rsplit(":", 1)[-1] if ":" in value else value)
            elif isinstance(value, RecordID):
                object.__setattr__(self, name, str(value.id))
            else:
                raise ValueError
        elif name == "status":
            if isinstance(value, ToolVersionStatus):
                object.__setattr__(self, name, value)
            elif isinstance(value, str):
                object.__setattr__(self, name, ToolVersionStatus(value))
            else:
                raise ValueError
        elif name in ("description", "language", "sandbox_id", "code", "code_link"):
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "sandbox_selection_tags":
            if isinstance(value, list):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "input_parameters":
            if isinstance(value, list):
                if len(value) > 0 and isinstance(value[0], dict):
                    converted_list: list[InputParameterDefinition] = [
                        InputParameterDefinition.from_dict(item) for item in value
                    ]
                    object.__setattr__(self, name, converted_list)
                else:
                    object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "input_files":
            if isinstance(value, list):
                if len(value) > 0 and isinstance(value[0], dict):
                    converted_list2: list[InputFileDefinition] = [
                        InputFileDefinition.from_dict(item) for item in value
                    ]
                    object.__setattr__(self, name, converted_list2)
                else:
                    object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "output_parameters":
            if isinstance(value, list):
                if len(value) > 0 and isinstance(value[0], dict):
                    converted_list3: list[OutputParameterDefinition] = [
                        OutputParameterDefinition.from_dict(item) for item in value
                    ]
                    object.__setattr__(self, name, converted_list3)
                else:
                    object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "output_files":
            if isinstance(value, list):
                if len(value) > 0 and isinstance(value[0], dict):
                    converted_list4: list[OutputFileDefinition] = [
                        OutputFileDefinition.from_dict(item) for item in value
                    ]
                    object.__setattr__(self, name, converted_list4)
                else:
                    object.__setattr__(self, name, value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    @staticmethod
    def _param_def_to_dict(p: Any, recursive: bool) -> Any:
        """Convert a parameter definition to dict if recursive."""
        if recursive and hasattr(p, "to_dict"):
            return p.to_dict(recursive=True)
        return p

    def to_dict(self, recursive: bool = False, exclude_id: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if not exclude_id:
            if self.id is not None:
                result["id"] = self.id
        if self.tool_id is not None:
            result["tool_id"] = self.tool_id
        if self.status is not None:
            result["status"] = self.status.value if recursive else self.status
        if self.description is not None:
            result["description"] = self.description
        if self.language is not None:
            result["language"] = self.language
        if self.sandbox_id is not None:
            result["sandbox_id"] = self.sandbox_id
        if self.sandbox_selection_tags is not None:
            result["sandbox_selection_tags"] = self.sandbox_selection_tags
        if self.code is not None:
            result["code"] = self.code
        if self.code_link is not None:
            result["code_link"] = self.code_link
        if self.input_parameters is not None:
            result["input_parameters"] = [
                self._param_def_to_dict(p, recursive) for p in self.input_parameters
            ]
        if self.input_files is not None:
            result["input_files"] = [
                self._param_def_to_dict(p, recursive) for p in self.input_files
            ]
        if self.output_parameters is not None:
            result["output_parameters"] = [
                self._param_def_to_dict(p, recursive) for p in self.output_parameters
            ]
        if self.output_files is not None:
            result["output_files"] = [
                self._param_def_to_dict(p, recursive) for p in self.output_files
            ]
        return result

    def to_json(self, exclude_id: bool = False) -> str:
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolVersionEntry":
        entity = cls()
        for key, value in data.items():
            if value is not None:
                try:
                    setattr(entity, key, value)
                except (ValueError, AttributeError):
                    continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "ToolVersionEntry":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
