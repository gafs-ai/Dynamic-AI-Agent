"""tool_catalogue_search_result_entry.py - Search result wrapper for tool catalogue search."""

from __future__ import annotations

from typing import Any

from .tool_catalogue import ToolCatalogueEntry, ToolVersionEntry


class ToolCatalogueSearchResultEntry:
    """Single result record from IToolCatalogueService.search_tool_catalogue_entries.

    Combines a matched ToolCatalogueEntry with the subset of its ToolVersionEntry
    records that satisfied the version_status filter.

    Attributes:
        catalogue: The matched tool catalogue entry.
        versions: Version entries whose status matched the search criteria.
    """

    def __init__(self) -> None:
        object.__setattr__(self, "catalogue", None)
        object.__setattr__(self, "versions", [])

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "catalogue":
            if isinstance(value, ToolCatalogueEntry):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        elif name == "versions":
            if isinstance(value, list):
                object.__setattr__(self, name, value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return f"ToolCatalogueSearchResultEntry(catalogue={self.catalogue}, versions_count={len(self.versions)})"
