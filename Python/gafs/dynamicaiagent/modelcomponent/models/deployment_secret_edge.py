"""deployment_secret_edge.py - Edge class for model_deployments → references_secret → Secrets."""

from __future__ import annotations

import json
from typing import Any


class DeploymentSecretEdge:
    """Represents a ``references_secret`` relation edge in SurrealDB.

    Links a ``ModelDeployment`` (source) to a ``Secret`` (target).

    The edge is created and deleted via SurrealQL ``RELATE`` / ``DELETE`` queries.
    It is not directly exposed to external callers; ``ModelDeployment.secrets``
    contains the resolved secret IDs.

    Attributes:
        id: Edge record ID (auto-assigned by SurrealDB on RELATE).
        source: Record ID of the source ``ModelDeployment`` (without table prefix).
        target: Record ID of the target ``Secret`` (without table prefix).
    """

    @staticmethod
    def EDGE_TYPE() -> str:  # noqa: N802
        """SurrealDB edge collection name."""
        return "references_secret"

    def __init__(self) -> None:
        object.__setattr__(self, "id", None)      # str | None
        object.__setattr__(self, "source", None)  # str
        object.__setattr__(self, "target", None)  # str

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("id", "$id"):
            if value is None:
                object.__setattr__(self, "id", None)
            elif isinstance(value, str):
                object.__setattr__(self, "id", value)
            else:
                raise ValueError(f"id must be str or None, got {type(value)}")
        elif name == "source":
            if isinstance(value, str):
                object.__setattr__(self, "source", value.rsplit(":", 1)[-1])
            else:
                raise ValueError(f"source must be str, got {type(value)}")
        elif name == "target":
            if isinstance(value, str):
                object.__setattr__(self, "target", value.rsplit(":", 1)[-1])
            else:
                raise ValueError(f"target must be str, got {type(value)}")
        else:
            pass  # Ignore unknown fields.

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False, exclude_id: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if not exclude_id and self.id is not None:
            result["id"] = self.id
        if self.source is not None:
            result["source"] = self.source
        if self.target is not None:
            result["target"] = self.target
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeploymentSecretEdge":
        if not isinstance(data, dict):
            raise ValueError("data must be a dict")
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        return entity
