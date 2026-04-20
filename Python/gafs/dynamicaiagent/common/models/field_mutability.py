"""
field_mutability.py - Enum describing who is allowed to modify a field's value.
"""

from enum import Enum


class FieldMutability(Enum):
    """Defines the mutability policy for a field in a data model.

    Controls whether a field value can be changed after the record is created,
    and who is permitted to perform the change.
    """

    IMMUTABLE = "immutable"
    """The field value is fixed at creation time and cannot be changed afterwards."""

    MUTABLE = "mutable"
    """The field value can be updated freely by users or the system."""

    SYSTEM = "system"
    """Only the system is allowed to update the field value; user writes are rejected."""

    SET_ONLY = "set_only"
    """The field value can be written only when it is currently null or empty.
    Once a non-null value is stored, further writes are rejected."""
