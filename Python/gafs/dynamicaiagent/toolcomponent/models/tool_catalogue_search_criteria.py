"""tool_catalogue_search_criteria.py - Search criteria for ToolCatalogue and ToolVersions.

Provides criteria classes and supporting types for building SurrealQL queries
against the tool catalogue and version collections.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from .tool_catalogue import ToolStatus, ToolVersionStatus


# ---------------------------------------------------------------------------
# Supporting types
# ---------------------------------------------------------------------------

class LogicalOperator(Enum):
    """Logical operator for combining multiple tag conditions."""

    AND = "AND"
    OR = "OR"


class TagsSearchCriteria:
    """Criteria for tag-based filtering.

    Attributes:
        tags: List of tag values to match.
        operator: AND or OR for combining tag conditions.
    """

    def __init__(
        self,
        tags: list[str] | None = None,
        operator: LogicalOperator = LogicalOperator.OR,
    ) -> None:
        object.__setattr__(self, "tags", tags if tags is not None else [])
        object.__setattr__(self, "operator", operator)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "tags":
            if isinstance(value, list):
                object.__setattr__(self, "tags", value)
            else:
                raise ValueError("tags must be list[str]")
        elif name == "operator":
            if isinstance(value, LogicalOperator):
                object.__setattr__(self, "operator", value)
            elif isinstance(value, str):
                object.__setattr__(self, "operator", LogicalOperator[value.upper()])
            else:
                raise ValueError
        else:
            raise ValueError(f"Unknown attribute: {name}")

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        return {
            "tags": self.tags,
            "operator": self.operator.value if recursive else self.operator,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TagsSearchCriteria":
        tags = data.get("tags", [])
        operator = data.get("operator", LogicalOperator.OR)
        return cls(tags=tags, operator=operator)


# ---------------------------------------------------------------------------
# ToolCatalogueSearchCriteria
# ---------------------------------------------------------------------------

class ToolCatalogueSearchCriteria:
    """Search criteria for ToolCatalogue records.

    Attributes:
        name: Filter by exact tool name.
        status: Filter by tool status (OR).
        description_keywords: Full-text search keywords for description.
        description_vector: Query vector for vector similarity search.
        tags: Tag filter supporting AND/OR matching.
        version_status: Filter versions by status and include in response.
        limit: Maximum number of tool records returned.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "status", [ToolStatus.ACTIVE])
        object.__setattr__(self, "description_keywords", None)
        object.__setattr__(self, "description_vector", None)
        object.__setattr__(self, "tags", None)
        object.__setattr__(self, "version_status", [ToolVersionStatus.LATEST, ToolVersionStatus.ACTIVE])
        object.__setattr__(self, "limit", 100)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "name":
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "status":
            if isinstance(value, list):
                converted = []
                for item in value:
                    if isinstance(item, ToolStatus):
                        converted.append(item)
                    elif isinstance(item, str):
                        converted.append(ToolStatus(item))
                    else:
                        raise ValueError
                object.__setattr__(self, name, converted)
            else:
                raise ValueError
        elif name == "description_keywords":
            if isinstance(value, list):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "description_vector":
            if isinstance(value, list):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "tags":
            if isinstance(value, TagsSearchCriteria):
                object.__setattr__(self, name, value)
            elif isinstance(value, dict):
                object.__setattr__(self, name, TagsSearchCriteria.from_dict(value))
            else:
                raise ValueError
        elif name == "version_status":
            if isinstance(value, list):
                converted2 = []
                for item in value:
                    if isinstance(item, ToolVersionStatus):
                        converted2.append(item)
                    elif isinstance(item, str):
                        converted2.append(ToolVersionStatus(item))
                    else:
                        raise ValueError
                object.__setattr__(self, name, converted2)
            else:
                raise ValueError
        elif name == "limit":
            if isinstance(value, int):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return json.dumps({
            "name": self.name,
            "limit": self.limit,
        })
