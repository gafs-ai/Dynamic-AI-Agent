"""deployment_selection_options.py - Options for filtering deployment selection at invocation time."""

from __future__ import annotations

import json
from typing import Any

from .ai_deployment_type import AiDeploymentType


class DeploymentSelectionOptions:
    """Runtime options for filtering which deployment is selected during invoke.

    Both attributes default to ``None`` (no filter applied).

    Attributes:
        deployment_type: Preferred deployment type. When set, only deployments
            of this type are eligible.
        confidence: Caller's data confidence level. Only deployments whose
            ``max_confidence_level`` is ``>= confidence`` are eligible.
    """

    def __init__(self) -> None:
        # Initialize all fields to None, bypassing validation.
        object.__setattr__(self, "deployment_type", None)  # AiDeploymentType | None
        object.__setattr__(self, "confidence", None)       # int | None

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "deployment_type":
            if value is None:
                object.__setattr__(self, "deployment_type", None)
            elif isinstance(value, AiDeploymentType):
                object.__setattr__(self, "deployment_type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "deployment_type", AiDeploymentType(value))
            else:
                raise ValueError(f"deployment_type must be AiDeploymentType or str, got {type(value)}")
        elif name == "confidence":
            if value is None:
                object.__setattr__(self, "confidence", None)
            elif isinstance(value, int):
                object.__setattr__(self, "confidence", value)
            else:
                raise ValueError(f"confidence must be int or None, got {type(value)}")
        else:
            raise ValueError(f"Unknown attribute: {name}")

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False, exclude_id: bool = False) -> dict[str, Any]:
        """Convert to a plain dictionary.

        Args:
            recursive: When ``True``, enum values are serialized as their string values.
            exclude_id: Unused; present for API consistency.

        Returns:
            Dictionary representation of this object.
        """
        result: dict[str, Any] = {}
        if self.deployment_type is not None:
            result["deployment_type"] = (
                self.deployment_type.value if recursive else self.deployment_type
            )
        if self.confidence is not None:
            result["confidence"] = self.confidence
        return result

    def to_json(self) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeploymentSelectionOptions":
        """Create a ``DeploymentSelectionOptions`` from a dictionary.

        Args:
            data: Dictionary with optional ``deployment_type`` and ``confidence`` keys.

        Returns:
            New instance with the supplied values.
        """
        if not isinstance(data, dict):
            raise ValueError("data must be a dict")
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "DeploymentSelectionOptions":
        """Create a ``DeploymentSelectionOptions`` from a JSON string.

        Args:
            json_str: JSON-encoded dictionary.

        Returns:
            New instance.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError("JSON must represent an object")
        return cls.from_dict(converted)
