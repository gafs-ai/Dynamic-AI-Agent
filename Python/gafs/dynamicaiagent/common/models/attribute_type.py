"""
attribute_type.py - Enum of scalar attribute types used in data model definitions.
"""

from enum import Enum


class AttributeType(Enum):
    """Represents the scalar data type of a single attribute (field).

    These types are used to describe the type of an attribute in a data model
    definition, and drive validation, serialization, and storage behaviour.
    """

    BOOL = "bool"
    """Boolean value (``True`` / ``False``)."""

    INT = "int"
    """64-bit signed integer."""

    FLOAT = "float"
    """64-bit floating-point number."""

    STR = "str"
    """UTF-8 string."""

    BYTES = "bytes"
    """Raw binary data."""

    DATETIME = "datetime"
    """UTC datetime with timezone information."""

    DURATION = "duration"
    """Time duration (e.g. ISO 8601 duration string)."""

    GEOMETRIES = "geometries"
    """Geospatial geometry value (e.g. GeoJSON)."""
