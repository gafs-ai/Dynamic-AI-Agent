"""
field_attribute_type.py - Enum of field attribute types used in collection and schema definitions.

Covers all scalar types and their list/set collection variants supported by the
underlying data store.
"""

from enum import Enum


class FieldAttributeType(Enum):
    """Represents the data type of a field in a collection schema.

    In addition to plain scalar types, list and set variants are provided for
    multi-value fields.  The string values match the type identifiers used by
    the underlying data store.
    """

    # --- Boolean ---

    BOOL = "bool"
    """Boolean value."""

    LIST_BOOL = "list[bool]"
    """Ordered list of boolean values."""

    # --- Integer ---

    INT = "int"
    """64-bit signed integer."""

    LIST_INT = "list[int]"
    """Ordered list of integers."""

    SET_INT = "set[int]"
    """Unordered unique set of integers."""

    # --- Float ---

    FLOAT = "float"
    """64-bit floating-point number."""

    LIST_FLOAT = "list[float]"
    """Ordered list of floats."""

    SET_FLOAT = "set[float]"
    """Unordered unique set of floats."""

    # --- String ---

    STR = "str"
    """UTF-8 string."""

    LIST_STR = "list[str]"
    """Ordered list of strings."""

    SET_STR = "set[str]"
    """Unordered unique set of strings."""

    # --- Bytes ---

    BYTES = "bytes"
    """Raw binary data."""

    # --- Datetime ---

    DATETIME = "datetime"
    """UTC datetime with timezone information."""

    LIST_DATETIME = "list[datetime]"
    """Ordered list of datetimes."""

    SET_DATETIME = "set[datetime]"
    """Unordered unique set of datetimes."""

    # --- Duration ---

    DURATION = "duration"
    """Time duration."""

    LIST_DURATION = "list[duration]"
    """Ordered list of durations."""

    SET_DURATION = "set[duration]"
    """Unordered unique set of durations."""

    # --- Geometries ---

    GEOMETRIES = "geometries"
    """Geospatial geometry value."""

    LIST_GEOMETRIES = "list[geometries]"
    """Ordered list of geometry values."""

    # --- Object (dictionary) ---

    OBJECT = "dict"
    """Arbitrary key-value object (dictionary)."""

    LIST_OBJECT = "list[dict]"
    """Ordered list of objects."""

    SET_OBJECT = "set[dict]"
    """Unordered unique set of objects."""
