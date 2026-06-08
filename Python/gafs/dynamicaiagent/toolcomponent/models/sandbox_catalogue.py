"""sandbox_catalogue.py - Data models for sandbox catalogue entries.

Defines the persisted data models for sandbox catalogue entries, including
abstract base class and Docker/Host concrete subtypes.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from surrealdb import RecordID


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SandboxType(Enum):
    """Type discriminator for sandbox catalogue entries."""

    HOST = "host"
    """Code runs directly on the host OS."""

    DOCKER = "docker"
    """Code runs inside a Docker container."""


class SandboxStatus(Enum):
    """Lifecycle status of a sandbox."""

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


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class SandboxCatalogueEntry:
    """Abstract base class for sandbox catalogue records.

    Attributes:
        id: Record ID (stripped of table prefix).
        status: Lifecycle status of the sandbox.
        name: Unique sandbox name.
        description: Optional description.
        tags: Optional list of string tags.
    """

    @staticmethod
    def CollectionName() -> str:
        """SurrealDB collection name for sandbox catalogue records."""
        return "SandboxCatalogue"

    def __init__(self) -> None:
        object.__setattr__(self, "id", None)
        object.__setattr__(self, "status", None)
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "description", None)
        object.__setattr__(self, "tags", None)

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
        elif name == "status":
            if isinstance(value, SandboxStatus):
                object.__setattr__(self, name, value)
            elif isinstance(value, str):
                object.__setattr__(self, name, SandboxStatus(value))
            else:
                raise ValueError
        elif name in ("name", "description"):
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "tags":
            if isinstance(value, list):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        else:
            raise ValueError(f"Unknown attribute: {name}")

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
        if self.tags is not None:
            result["tags"] = self.tags
        return result

    def to_json(self, exclude_id: bool = False) -> str:
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SandboxCatalogueEntry":
        entity = cls()
        for key, value in data.items():
            if value is not None:
                try:
                    setattr(entity, key, value)
                except (ValueError, AttributeError):
                    continue
        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "SandboxCatalogueEntry":
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


# ---------------------------------------------------------------------------
# SandboxCatalogueHostEntry
# ---------------------------------------------------------------------------

class SandboxCatalogueHostEntry(SandboxCatalogueEntry):
    """Sandbox catalogue entry for host-based execution.

    No additional attributes beyond the base class.
    """

    def __init__(self) -> None:
        super().__init__()

    def __setattr__(self, name: str, value: Any) -> None:
        # No additional attributes; delegate to parent
        super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False, exclude_id: bool = False) -> dict[str, Any]:
        result = super().to_dict(recursive=recursive, exclude_id=exclude_id)
        if recursive:
            result["sandbox_type"] = SandboxType.HOST.value
        else:
            result["sandbox_type"] = SandboxType.HOST
        return result

    def to_json(self, exclude_id: bool = False) -> str:
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SandboxCatalogueHostEntry":
        entity = cls()
        for key, value in data.items():
            if key == "sandbox_type":
                continue
            if value is not None:
                try:
                    setattr(entity, key, value)
                except (ValueError, AttributeError):
                    continue
        return entity


# ---------------------------------------------------------------------------
# SandboxCatalogueDockerEntry
# ---------------------------------------------------------------------------

class SandboxCatalogueDockerEntry(SandboxCatalogueEntry):
    """Sandbox catalogue entry for Docker-based execution.

    Attributes:
        docker_file: Dockerfile content for image creation.
        run_options: Additional docker run options (e.g. --memory 512m).
    """

    def __init__(self) -> None:
        super().__init__()
        object.__setattr__(self, "docker_file", None)
        object.__setattr__(self, "run_options", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("docker_file", "run_options"):
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def to_dict(self, recursive: bool = False, exclude_id: bool = False) -> dict[str, Any]:
        result = super().to_dict(recursive=recursive, exclude_id=exclude_id)
        if recursive:
            result["sandbox_type"] = SandboxType.DOCKER.value
        else:
            result["sandbox_type"] = SandboxType.DOCKER
        if self.docker_file is not None:
            result["docker_file"] = self.docker_file
        if self.run_options is not None:
            result["run_options"] = self.run_options
        return result

    def to_json(self, exclude_id: bool = False) -> str:
        return json.dumps(self.to_dict(recursive=True, exclude_id=exclude_id))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SandboxCatalogueDockerEntry":
        entity = cls()
        for key, value in data.items():
            if key == "sandbox_type":
                continue
            if value is not None:
                try:
                    setattr(entity, key, value)
                except (ValueError, AttributeError):
                    continue
        return entity
