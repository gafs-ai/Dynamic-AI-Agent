"""secret_key.py - SecretKey value object for cryptographic key pairs."""

from __future__ import annotations

import json
from typing import Any


class SecretKey:
    """Value object that holds a pair of cryptographic keys for a specific algorithm.

    For symmetric algorithms (e.g. AES-256-GCM), ``encryption_key`` and
    ``decryption_key`` hold the same shared key value.  For asymmetric algorithms,
    ``encryption_key`` is the public key and ``decryption_key`` is the private key.

    SecretKey entries are persisted in ``secret_keys.json`` under the application
    data folder when keys are auto-generated.

    NOTE: ``decryption_key`` must never be logged or stored in plaintext in a
    location that is not protected.
    """

    def __init__(self) -> None:
        """Initialize SecretKey with all fields set to None.

        NOTE: Uses object.__setattr__ to bypass the custom setter, which rejects None.
        """
        object.__setattr__(self, "name", None)
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
        if name == "name":
            # name must be a non-empty string matching a CryptoType.value
            if isinstance(value, str):
                object.__setattr__(self, "name", value)
            else:
                raise ValueError
        elif name == "encryption_key":
            # encryption_key must be a non-empty string (base64-encoded key)
            if isinstance(value, str):
                object.__setattr__(self, "encryption_key", value)
            else:
                raise ValueError
        elif name == "decryption_key":
            # decryption_key must be a non-empty string (base64-encoded key)
            if isinstance(value, str):
                object.__setattr__(self, "decryption_key", value)
            else:
                raise ValueError
        else:
            raise ValueError

    def __repr__(self) -> str:
        """Return a JSON string representation of this SecretKey.

        NOTE: Both keys are included in the output. Handle with care.
        """
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert this SecretKey to a plain dictionary.

        Args:
            recursive: Unused; included for interface consistency with other models.

        Returns:
            Dictionary containing name, encryption_key, and decryption_key.
        """
        result: dict[str, Any] = {}

        # Include each field only if it has been set
        if self.name is not None:
            result["name"] = self.name
        if self.encryption_key is not None:
            result["encryption_key"] = self.encryption_key
        if self.decryption_key is not None:
            result["decryption_key"] = self.decryption_key

        return result

    def to_json(self) -> str:
        """Serialize this SecretKey to a JSON string.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SecretKey":
        """Create a SecretKey instance from a dictionary.

        Args:
            data: Dictionary with keys ``name``, ``encryption_key``, ``decryption_key``.

        Returns:
            A new SecretKey instance.
        """
        entity = cls()

        # Set each known field, skipping None values to avoid __setattr__ rejection
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)

        return entity

    @classmethod
    def from_json(cls, json_str: str) -> "SecretKey":
        """Create a SecretKey instance from a JSON string.

        Args:
            json_str: JSON string representation of a SecretKey.

        Returns:
            A new SecretKey instance.

        Raises:
            ValueError: If the JSON is not a dictionary.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)
