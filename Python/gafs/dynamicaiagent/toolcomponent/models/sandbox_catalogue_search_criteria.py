"""sandbox_catalogue_search_criteria.py - Search criteria for SandboxCatalogue collection."""

from __future__ import annotations

import json
from typing import Any

from .sandbox_catalogue import SandboxStatus
from .tool_catalogue_search_criteria import TagsSearchCriteria


class SandboxCatalogueSearchCriteria:
    """Search criteria for SandboxCatalogue records.

    Attributes:
        name: Filter by exact sandbox name.
        status: Filter by sandbox status (OR).
        tags: Tag filter supporting AND/OR matching.
        limit: Maximum number of sandbox records returned.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "name", None)
        object.__setattr__(self, "status", [SandboxStatus.ACTIVE])
        object.__setattr__(self, "tags", None)
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
                    if isinstance(item, SandboxStatus):
                        converted.append(item)
                    elif isinstance(item, str):
                        converted.append(SandboxStatus(item))
                    else:
                        raise ValueError
                object.__setattr__(self, name, converted)
            else:
                raise ValueError
        elif name == "tags":
            if isinstance(value, TagsSearchCriteria):
                object.__setattr__(self, name, value)
            elif isinstance(value, dict):
                object.__setattr__(self, name, TagsSearchCriteria.from_dict(value))
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
        return json.dumps({"name": self.name, "limit": self.limit})
