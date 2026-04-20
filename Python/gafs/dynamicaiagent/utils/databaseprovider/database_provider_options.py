import json
from abc import ABC
from typing import Any

from .database_provider_type import DatabaseProviderType
from .retry_options import RetryOptions


class DatabaseProviderOptions(ABC):
    """Abstract base class for database provider configuration.

    All concrete provider option classes must inherit from this class and
    extend it with provider-specific attributes such as connection strings
    and credentials.  Every attribute assignment is validated via
    ``__setattr__``, so invalid types raise ``ValueError``.

    NOTE: ``database_type`` accepts both ``DatabaseProviderType`` enum
    instances and their string values; other values raise ``ValueError``.
    """

    def __init__(self) -> None:
        # Initialize all base fields to None per data-class coding rules.
        object.__setattr__(self, "database_type", None)
        object.__setattr__(self, "database_name", None)
        object.__setattr__(self, "retry_options", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "database_type":
            # Accept either a DatabaseProviderType enum or its string value.
            if isinstance(value, DatabaseProviderType):
                object.__setattr__(self, "database_type", value)
            elif isinstance(value, str):
                # Automatic conversion from string to enum.
                object.__setattr__(self, "database_type", DatabaseProviderType(value))
            else:
                raise ValueError
        elif name == "database_name":
            if isinstance(value, str):
                object.__setattr__(self, "database_name", value)
            else:
                raise ValueError
        elif name == "retry_options":
            # retry_options is optional; None is also accepted.
            if isinstance(value, RetryOptions) or value is None:
                object.__setattr__(self, "retry_options", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Serialize the base fields to a dictionary.

        Subclasses should call ``super().to_dict(recursive=recursive)`` and
        then add their own fields to the returned dictionary.

        Args:
            recursive: When True, convert enum values to their string
                representation and nested objects to dicts.

        Returns:
            Dictionary representation of the base configuration fields.
        """
        result: dict[str, Any] = {}

        if self.database_type is not None:
            if recursive:
                result["database_type"] = self.database_type.value
            else:
                result["database_type"] = self.database_type

        if self.database_name is not None:
            result["database_name"] = self.database_name

        if self.retry_options is not None:
            if recursive:
                result["retry_options"] = self.retry_options.to_dict(recursive=True)
            else:
                result["retry_options"] = self.retry_options

        return result

    def to_json(self) -> str:
        """Serialize the options to a JSON string.

        Returns:
            JSON string representation of these options.
        """
        return json.dumps(self.to_dict(recursive=True))
