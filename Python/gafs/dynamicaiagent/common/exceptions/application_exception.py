"""
application_exception.py - Base exception class for the entire application.

All exceptions raised within this application should extend ApplicationException so that
error context (timing, origin component, cause chain) is consistently captured.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from random import randbytes
from typing import Any


class ApplicationException(Exception):
    """Base exception for the entire application.

    All component-specific exceptions extend this class.  When an exception is
    created, the following context is automatically recorded inside ``details``:

    - ``datetime`` – UTC datetime at which the exception was detected.
    - ``id``       – Unique identifier in the format ``"{timestamp}-{6 random
                     uppercase letters}"``.
    - ``component`` – Name of the component that raised the exception (defaults
                      to ``DEFAULT_COMPONENT_NAME``; subclasses should override
                      to their own component name).
    - ``message``  – Copy of the human-readable error message for downstream
                     structured handling.
    - ``causes``   – (Only when *cause* is also an ``ApplicationException``)
                     Ordered list of ancestor exception IDs, enabling full cause
                     chain tracing.

    Additional context-specific keys (e.g. ``"model_id"``, ``"db_query"``) may
    be inserted into ``details`` by callers or subclasses as needed.

    NOTE: Subclasses should override ``ERROR_NAME`` and ``DEFAULT_COMPONENT_NAME``
    to reflect the name of their own component.
    """

    # --- Class-level constants ---

    ERROR_NAME: str = "ApplicationException"
    """Identifies the exception type in string representations."""

    DEFAULT_MESSAGE: str = "Unexpected Exception in Application"
    """Fallback message used when the caller does not supply one."""

    DEFAULT_COMPONENT_NAME: str = "Unknown"
    """Fallback component name used when not overridden by a subclass."""

    # --- Constructor ---

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        """Initialize ApplicationException.

        Args:
            message: Human-readable description of the error.  Defaults to
                ``DEFAULT_MESSAGE``.
            details: Optional dictionary of additional context to attach.
                Any auto-set keys (``datetime``, ``id``, ``component``,
                ``message``) are only inserted when they are not already
                present in the provided dictionary.
            cause: The original exception that triggered this one, if any.
                When *cause* is itself an ``ApplicationException``, its ``id``
                and the ids of its own ancestors are propagated into
                ``details["causes"]``.
        """
        super().__init__(message)

        # Store the human-readable message as an instance attribute.
        self.message: str = message

        # Use the provided details dict or start with an empty one.
        self.details: dict[str, Any] = details if isinstance(details, dict) else {}

        # --- Auto-populate standard detail fields ---

        # Record the UTC moment the exception was detected.
        current: datetime = datetime.now(tz=timezone.utc)
        self.details.setdefault("datetime", current)

        # Build a unique ID: "<unix-timestamp>-<6 random uppercase letters>".
        random_suffix: str = "".join(chr(65 + b % 26) for b in randbytes(6))
        self.details.setdefault(
            "id", f"{datetime.timestamp(current):.0f}-{random_suffix}"
        )

        # Record which component raised the exception.
        self.details.setdefault("component", self.DEFAULT_COMPONENT_NAME)

        # Mirror the message into details so downstream handlers can inspect it
        # without needing the exception object itself.
        self.details.setdefault("message", self.message)

        # --- Propagate cause chain when applicable ---

        if cause is not None and isinstance(cause, ApplicationException):
            # Collect the immediate cause id.
            cause_id: str | None = cause.details.get("id", None)
            if cause_id is not None:
                # Start the causes list with the immediate cause.
                causes: list[str] = [cause_id]

                # Append ancestor ids already stored on the causing exception.
                ancestor_ids: list[str] | None = cause.details.get("causes", None)
                if ancestor_ids is not None:
                    causes.extend(ancestor_ids)

                self.details["causes"] = causes

        # Store the raw cause for programmatic inspection.
        self.cause: BaseException | None = cause

    # --- String representations ---

    def __str__(self) -> str:
        """Return a concise human-readable representation of the exception.

        Returns:
            A string in the format ``"{ERROR_NAME}: {message}"``.
        """
        return f"{self.ERROR_NAME}: {self.message}"

    def __repr__(self) -> str:
        """Return a JSON-serializable representation of the full details dict.

        Returns:
            A JSON string containing all fields in ``details``.  ``datetime``
            objects are serialized to ISO 8601 strings.
        """
        return json.dumps(self.details, default=_json_default)


# ---------------------------------------------------------------------------
# Module-private helpers
# ---------------------------------------------------------------------------

def _json_default(obj: Any) -> Any:
    """Custom JSON serializer for types not natively supported by ``json.dumps``.

    Args:
        obj: The object that ``json.dumps`` could not serialize.

    Returns:
        A JSON-compatible representation of *obj*.

    Raises:
        TypeError: When *obj* cannot be serialized.
    """
    if isinstance(obj, datetime):
        # Serialize datetime to ISO 8601 string (includes timezone info).
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
