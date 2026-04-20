from __future__ import annotations

import json
from typing import Any


class KeyPair:
    """Value object that holds a pair of cryptographic keys.

    For symmetric algorithms, ``encryption_key`` and ``decryption_key`` hold the
    same shared key value.  For asymmetric algorithms, ``encryption_key`` is the
    public key and ``decryption_key`` is the private key.

    Both keys are base64-encoded strings.

    NOTE: ``decryption_key`` must never be logged, serialized to external systems,
    or stored in plaintext.  ``to_dict`` and ``to_json`` intentionally omit
    ``decryption_key`` for this reason.
    """

    def __init__(self) -> None:
        """Initialize KeyPair with all fields set to None.

        NOTE: Use object.__setattr__ to bypass the custom __setattr__ validator,
        which would reject None values.
        """
        object.__setattr__(self, "encryption_key", None)
        object.__setattr__(self, "decryption_key", None)

    def __setattr__(self, name: str, value: Any) -> None:
        """Validate and set an attribute.

        Args:
            name: Attribute name.
            value: Attribute value.

        Raises:
            ValueError: If the value is not of the expected type.
        """
        if name == "encryption_key":
            # encryption_key must always be a non-empty string.
            if isinstance(value, str):
                object.__setattr__(self, "encryption_key", value)
            else:
                raise ValueError
        elif name == "decryption_key":
            # decryption_key must always be a non-empty string.
            if isinstance(value, str):
                object.__setattr__(self, "decryption_key", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        # Use to_json for the canonical string representation.
        # NOTE: decryption_key is intentionally excluded from the output.
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert this KeyPair to a dictionary.

        Args:
            recursive: Unused; included for interface consistency.

        Returns:
            Dictionary containing only ``encryption_key``.
            ``decryption_key`` is intentionally excluded for security.

        NOTE: ``decryption_key`` is never included in the serialized output.
        """
        result: dict[str, Any] = {}

        # Only include the public-facing encryption key.
        # The decryption key (private key) is never serialized.
        if self.encryption_key is not None:
            result["encryption_key"] = self.encryption_key

        return result

    def to_json(self) -> str:
        """Serialize this KeyPair to a JSON string.

        Returns:
            JSON string containing only ``encryption_key``.
            ``decryption_key`` is intentionally excluded for security.
        """
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KeyPair":
        """Create a KeyPair from a dictionary.

        Args:
            data: Dictionary with ``encryption_key`` and optionally
                  ``decryption_key``.

        Returns:
            A new KeyPair instance populated from ``data``.
        """
        entity = cls()

        # Set each field that is present in the data and has a non-None value.
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)

        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "KeyPair":
        """Create a KeyPair from a JSON string.

        Args:
            json_str: JSON string produced by ``to_json`` or equivalent.

        Returns:
            A new KeyPair instance populated from the JSON data.

        Raises:
            ValueError: If ``json_str`` is not a JSON object.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
