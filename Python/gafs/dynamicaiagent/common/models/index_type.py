"""
index_type.py - Enum of index types available for fields in a collection schema.
"""

from enum import Enum


class IndexType(Enum):
    """Represents the type of index to build on a field.

    The index type determines how data is stored and queried in the underlying
    data store, and which query operators are available for that field.
    """

    STANDARD = "standard"
    """Standard B-tree-style index suitable for equality and range queries."""

    FULL_TEXT = "full_text"
    """Full-text search index that tokenises string values and supports
    natural-language keyword searches."""
