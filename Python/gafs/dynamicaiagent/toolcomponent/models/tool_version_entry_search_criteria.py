"""tool_version_entry_search_criteria.py - Search criteria for ToolVersions collection."""

from __future__ import annotations

import json
from typing import Any

from .tool_catalogue import ToolVersionStatus


class ToolVersionEntrySearchCriteria:
    """Search criteria for ToolVersions records.

    Attributes:
        tool_id: Filter by tool ID.
        status: Filter by tool version status (OR).
        limit: Maximum number of version records returned.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "tool_id", None)
        object.__setattr__(self, "status", [ToolVersionStatus.LATEST, ToolVersionStatus.ACTIVE])
        object.__setattr__(self, "limit", 100)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "tool_id":
            if isinstance(value, str):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "status":
            if isinstance(value, list):
                converted = []
                for item in value:
                    if isinstance(item, ToolVersionStatus):
                        converted.append(item)
                    elif isinstance(item, str):
                        converted.append(ToolVersionStatus(item))
                    else:
                        raise ValueError
                object.__setattr__(self, name, converted)
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
        return json.dumps({"tool_id": self.tool_id, "limit": self.limit})
