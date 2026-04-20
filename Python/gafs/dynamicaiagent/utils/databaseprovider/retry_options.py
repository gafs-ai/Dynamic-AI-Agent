import json
from typing import Any


class RetryOptions:
    """Configuration for retry behaviour on connection errors.

    Controls how many times and how long to wait between retry attempts when
    a database operation fails due to a connection problem.  Retry is only
    applied to connection errors; query errors and authentication errors are
    never retried.

    NOTE: All attributes are initialized to None in __init__.  When an
    attribute is None the provider falls back to the class-level defaults
    (timeout=60, max_retry=2, retry_interval=10).  Use the module-level
    constants DEFAULT_TIMEOUT, DEFAULT_MAX_RETRY, DEFAULT_RETRY_INTERVAL if
    you need to reference the defaults explicitly.
    """

    # Default values applied when an attribute is None.
    DEFAULT_TIMEOUT: int = 60
    DEFAULT_MAX_RETRY: int = 2
    DEFAULT_RETRY_INTERVAL: int = 10

    def __init__(self) -> None:
        # Initialize all fields to None per data-class coding rules.
        # Actual defaults are applied at the point of use (provider resolution).
        object.__setattr__(self, "timeout", None)
        object.__setattr__(self, "max_retry", None)
        object.__setattr__(self, "retry_interval", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "timeout":
            # Request timeout in seconds; must be a positive integer.
            if isinstance(value, int):
                object.__setattr__(self, "timeout", value)
            else:
                raise ValueError
        elif name == "max_retry":
            # Maximum number of retry attempts; 0 means no retries.
            if isinstance(value, int):
                object.__setattr__(self, "max_retry", value)
            else:
                raise ValueError
        elif name == "retry_interval":
            # Base retry interval in seconds; actual wait = retry_interval * n (1-based).
            if isinstance(value, int):
                object.__setattr__(self, "retry_interval", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Serialize this object to a dictionary.

        Args:
            recursive: Unused for this class (all fields are primitives),
                kept for consistency with the project data-class convention.

        Returns:
            Dictionary containing only the non-None fields.
        """
        result: dict[str, Any] = {}

        if self.timeout is not None:
            result["timeout"] = self.timeout
        if self.max_retry is not None:
            result["max_retry"] = self.max_retry
        if self.retry_interval is not None:
            result["retry_interval"] = self.retry_interval

        return result

    def to_json(self) -> str:
        """Serialize this object to a JSON string.

        Returns:
            JSON representation of this object.
        """
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RetryOptions":
        """Create a RetryOptions instance from a dictionary.

        Args:
            data: Dictionary with optional keys 'timeout', 'max_retry',
                'retry_interval'.

        Returns:
            A new RetryOptions instance with the given values.
        """
        entity = cls()

        for key, value in data.items():
            if hasattr(entity, key):
                # Skip None values to preserve the __init__ default (None).
                if value is not None:
                    setattr(entity, key, value)

        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "RetryOptions":
        """Create a RetryOptions instance from a JSON string.

        Args:
            json_str: JSON string representation.

        Returns:
            A new RetryOptions instance.

        Raises:
            ValueError: If the JSON does not represent a dictionary.
        """
        converted: Any = json.loads(json_str)

        if not isinstance(converted, dict):
            raise ValueError

        return cls.from_dict(converted)
