from __future__ import annotations
from typing import Any
import json
from datetime import datetime, timezone
from random import randbytes

class ApplicationException(Exception):
    ERROR_NAME: str = "ApplicationException"
    DEFAULT_MESSAGE: str = "Unexpected Error in Application."
    DEFAULT_COMPONENT_NAME: str = "Unknown"

    def __init__(self, message: str = DEFAULT_MESSAGE, details: dict[str, Any] | None = None, cause: BaseException = None):
        super().__init__(message)
        self.message: str = message
        self.details: dict[str, Any] = details if isinstance(details, dict) else {}
        current: datetime = datetime.now(tz=timezone.utc)
        self.details.setdefault("datetime", current.isoformat())
        self.details.setdefault("id", f"{datetime.timestamp(current):.0f}-{''.join(chr(65 + b % 26) for b in randbytes(6))}")
        self.details.setdefault("component", self.DEFAULT_COMPONENT_NAME)
        self.details.setdefault("message", self.message)
        if cause is not None:
            if isinstance(cause, ApplicationException):
                cause_id: str|None = cause.details.get("id", None)
                if cause_id is not None:
                    causes: list[str] = [cause_id]
                    cause_ids: list[str]|None = cause.details.get("causes", None)
                    if cause_ids is not None:
                        causes.extend(cause_ids)
                    self.details["causes"] = causes
        self.cause: Exception = cause

    def __str__(self) -> str:
        return f"{self.ERROR_NAME}: {self.message}"

    def __repr__(self) -> str:
        return json.dumps(self.details)
