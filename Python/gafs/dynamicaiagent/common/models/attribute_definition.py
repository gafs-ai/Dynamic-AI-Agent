"""
attribute_definition.py - Data class representing the schema and validation rules
for a single attribute (inference parameter) in a model or collection definition.
"""

from __future__ import annotations

import json
from typing import Any

from .field_attribute_type import FieldAttributeType


class AttributeDefinition:
    """Defines the schema and validation constraints for a single attribute.

    An ``AttributeDefinition`` describes one field within a broader schema – for
    example, a single inference parameter accepted by a model deployment.  It
    captures the field's name, its expected data type, and optional constraints
    such as an allowed-values set, numeric bounds, and a custom validator.

    NOTE: ``type`` accepts both ``FieldAttributeType`` enum instances and their
    raw string values; a string is automatically converted to the enum member.
    ``allowed_values`` accepts both ``set`` and ``list`` inputs and is stored
    internally as a ``set``; it is serialized as a sorted ``list`` so that
    ``to_dict`` / ``to_json`` output is deterministic.
    """

    # --- Constructor ---

    def __init__(self) -> None:
        """Initialize all fields to ``None``.

        ``object.__setattr__`` is used directly here to bypass the custom
        validation logic in ``__setattr__``, which would reject ``None``.
        """
        object.__setattr__(self, "key", None)            # str
        object.__setattr__(self, "description", None)    # str | None
        object.__setattr__(self, "type", None)           # FieldAttributeType
        object.__setattr__(self, "allowed_values", None) # set[int] | set[float] | set[str] | None
        object.__setattr__(self, "min", None)            # int | float | None
        object.__setattr__(self, "max", None)            # int | float | None
        object.__setattr__(self, "custom_validator", None) # str | None

    # --- Attribute assignment with validation ---

    def __setattr__(self, name: str, value: Any) -> None:
        """Set an attribute with type validation and automatic conversion.

        Supports:
        - ``str`` → ``FieldAttributeType`` conversion for the ``type`` field.
        - ``list`` → ``set`` conversion for ``allowed_values``.

        Args:
            name:  Name of the attribute to set.
            value: Value to assign.

        Raises:
            ValueError: When *value* has an incompatible type for *name*, or
                when *name* is not a recognised attribute.
        """
        if name == "key":
            # key must be a non-None string.
            if isinstance(value, str):
                object.__setattr__(self, "key", value)
            else:
                raise ValueError

        elif name == "description":
            # description is an optional free-text string.
            if isinstance(value, str):
                object.__setattr__(self, "description", value)
            else:
                raise ValueError

        elif name == "type":
            # Accept the enum directly, or convert from its string value.
            if isinstance(value, FieldAttributeType):
                new_type = value
            elif isinstance(value, str):
                # FieldAttributeType(value) raises ValueError for unknown strings.
                new_type = FieldAttributeType(value)
            else:
                raise ValueError

            # Re-cast min/max to the new type when they are already set.
            # Only INT and FLOAT support numeric bounds; any other type with
            # a pre-existing bound is an error.
            if self.min is not None:
                if new_type == FieldAttributeType.INT:
                    if isinstance(self.min, (int, float)):
                        object.__setattr__(self, "min", int(self.min))
                    else:
                        raise ValueError
                elif new_type == FieldAttributeType.FLOAT:
                    if isinstance(self.min, (int, float)):
                        object.__setattr__(self, "min", float(self.min))
                    else:
                        raise ValueError
            if self.max is not None:
                if new_type == FieldAttributeType.INT:
                    object.__setattr__(self, "max", int(self.max))
                elif new_type == FieldAttributeType.FLOAT:
                    object.__setattr__(self, "max", float(self.max))
                else:
                    raise ValueError

            # Re-cast allowed_values elements to the new type when already set.
            if self.allowed_values is not None:
                object.__setattr__(
                    self, "allowed_values",
                    _cast_allowed_values(self.allowed_values, new_type),
                )

            object.__setattr__(self, "type", new_type)

        elif name == "allowed_values":
            # Accept both set and list; store as set for O(1) membership tests.
            if isinstance(value, (set, list)):
                cast_values: set = set(value)
                # Cast elements to the current type when type is already set.
                if self.type is not None:
                    cast_values = _cast_allowed_values(cast_values, self.type)
                object.__setattr__(self, "allowed_values", cast_values)
            else:
                raise ValueError

        elif name == "min":
            # Numeric lower bound; applicable to INT and FLOAT types.
            if isinstance(value, (int, float)):
                # Cast to the appropriate numeric type when type is already set.
                if self.type == FieldAttributeType.INT:
                    value = int(value)
                elif self.type == FieldAttributeType.FLOAT:
                    value = float(value)
                elif self.type is not None:
                    # type is set but is not a numeric scalar type.
                    raise ValueError
                object.__setattr__(self, "min", value)
            else:
                raise ValueError

        elif name == "max":
            # Numeric upper bound; applicable to INT and FLOAT types.
            if isinstance(value, (int, float)):
                # Cast to the appropriate numeric type when type is already set.
                if self.type == FieldAttributeType.INT:
                    value = int(value)
                elif self.type == FieldAttributeType.FLOAT:
                    value = float(value)
                elif self.type is not None:
                    # type is set but is not a numeric scalar type.
                    raise ValueError
                object.__setattr__(self, "max", value)
            else:
                raise ValueError

        elif name == "custom_validator":
            # Holds the function_id string referencing a ToolCatalogue entry.
            if isinstance(value, str):
                object.__setattr__(self, "custom_validator", value)
            else:
                raise ValueError

        else:
            raise ValueError

    # --- String representation ---

    def __repr__(self) -> str:
        """Return a JSON representation of this instance.

        Returns:
            A JSON string produced by ``to_json()``.
        """
        return self.to_json()

    # --- Serialization ---

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert this instance to a plain dictionary.

        Args:
            recursive: When ``True``, nested objects (``FieldAttributeType``,
                ``set``) are converted to JSON-compatible primitives.  When
                ``False``, they are kept as-is.

        Returns:
            A dictionary containing only the fields that have been set
            (i.e. are not ``None``).
        """
        result: dict[str, Any] = {}

        if self.key is not None:
            result["key"] = self.key

        if self.description is not None:
            result["description"] = self.description

        if self.type is not None:
            # Convert enum to its string value when recursive serialization is requested.
            if recursive:
                result["type"] = self.type.value
            else:
                result["type"] = self.type

        if self.allowed_values is not None:
            # Sets are not JSON-serializable; convert to a sorted list for
            # deterministic output.  Sorting works because the set is
            # homogeneous (all int, all float, or all str).
            result["allowed_values"] = sorted(self.allowed_values)

        if self.min is not None:
            result["min"] = self.min

        if self.max is not None:
            result["max"] = self.max

        if self.custom_validator is not None:
            result["custom_validator"] = self.custom_validator

        return result

    def to_json(self) -> str:
        """Serialize this instance to a JSON string.

        Returns:
            A JSON string with all non-``None`` fields serialized to
            primitive types (``recursive=True`` is always used so that
            ``FieldAttributeType`` values and sets are properly converted).
        """
        return json.dumps(self.to_dict(recursive=True))

    # --- Deserialization ---

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AttributeDefinition":
        """Create an ``AttributeDefinition`` from a plain dictionary.

        Unknown keys are silently ignored.  Fields with ``None`` values are
        skipped so that ``__init__``'s ``None`` defaults are preserved (this
        avoids ``ValueError`` from the validation logic in ``__setattr__``).

        Args:
            data: Dictionary containing attribute field values.  Typically
                produced by ``to_dict(recursive=True)`` or deserialized from
                a database record.

        Returns:
            A new ``AttributeDefinition`` instance populated from *data*.
        """
        entity = cls()

        for key, value in data.items():
            # Only set fields that belong to this class.
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                # Silently skip unknown keys (forward/backward compatibility).
                continue

        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "AttributeDefinition":
        """Create an ``AttributeDefinition`` from a JSON string.

        Args:
            json_str: A JSON string representing an ``AttributeDefinition``
                (must deserialize to a ``dict``).

        Returns:
            A new ``AttributeDefinition`` instance.

        Raises:
            ValueError: When *json_str* does not deserialize to a dictionary.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


# ---------------------------------------------------------------------------
# Module-private helpers
# ---------------------------------------------------------------------------

def _cast_allowed_values(values: set, field_type: FieldAttributeType) -> set:
    """Cast the elements of *values* to the scalar base type of *field_type*.

    Casting rules:
    - ``STR``   – every element is converted to ``str``.
    - ``INT``   – ``float`` elements are truncated to ``int``; ``str`` raises
                  ``ValueError``.
    - ``FLOAT`` – ``int`` elements are widened to ``float``; ``str`` raises
                  ``ValueError``.
    - Other types – the set is returned unchanged.

    Args:
        values:     The set of allowed values to cast.
        field_type: The target ``FieldAttributeType``.

    Returns:
        A new ``set`` with elements cast to the appropriate type.

    Raises:
        ValueError: When an element cannot be cast to the target type.
    """
    if field_type == FieldAttributeType.STR:
        # Cast int and float to str; str stays as-is.
        return {str(v) for v in values}

    elif field_type == FieldAttributeType.INT:
        # float is truncated to int; str is not allowed.
        result: set = set()
        for v in values:
            if isinstance(v, int):
                result.add(v)
            elif isinstance(v, float):
                result.add(int(v))
            else:
                raise ValueError
        return result

    elif field_type == FieldAttributeType.FLOAT:
        # int is widened to float; str is not allowed.
        result = set()
        for v in values:
            if isinstance(v, float):
                result.add(v)
            elif isinstance(v, int):
                result.add(float(v))
            else:
                raise ValueError
        return result

    else:
        # For types other than STR / INT / FLOAT, return the values unchanged.
        return values
