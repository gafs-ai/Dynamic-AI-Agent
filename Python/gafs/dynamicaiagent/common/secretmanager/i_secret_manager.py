"""i_secret_manager.py - Abstract base class (interface) for SecretManager."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from gafs.dynamicaiagent.utils.cryptoutil import CryptoType, CryptoUtil
from gafs.dynamicaiagent.utils.databaseprovider import (
    IDatabaseProvider,
    SurrealDbLocalProvider,
    SurrealDbRemoteProvider,
)

from .exceptions import (
    SecretManagerCryptoException,
    SecretManagerInitializationException,
    SecretManagerInvalidSecretEntryException,
    SecretManagerKeyNotFoundException,
    SecretManagerNotInitializedException,
    SecretManagerOperationException,
    SecretManagerSecretNotFoundException,
)
from .models import Secret, SecretKey


class SecretSearchCriteria:
    """Criteria for searching ``Secret`` entries in the database.

    All fields are optional.  Only fields that are set (non-None) are included
    in the generated query.

    NOTE: ``to_query()`` currently supports only SurrealDB providers
          (``SurrealDbRemoteProvider`` and ``SurrealDbLocalProvider``).
          Passing any other provider type raises ``NotImplementedError``.

    Attributes:
        name: Substring to search for within the ``name`` field.
        description_keywords: List of keywords to search within ``description`` (OR condition).
        created_at_from: Lower bound (inclusive) for ``created_at``.
        created_at_to: Upper bound (inclusive) for ``created_at``.
        updated_at_from: Lower bound (inclusive) for ``updated_at``.
        updated_at_to: Upper bound (inclusive) for ``updated_at``.
        valid_until_from: Lower bound (inclusive) for ``valid_until``.
        valid_until_to: Upper bound (inclusive) for ``valid_until``.
        limit: Maximum number of results to return. No LIMIT clause when ``<= 0``.
    """

    def __init__(
        self,
        name: str | None = None,
        description_keywords: list[str] | None = None,
        created_at_from: datetime | str | int | None = None,
        created_at_to: datetime | str | int | None = None,
        updated_at_from: datetime | str | int | None = None,
        updated_at_to: datetime | str | int | None = None,
        valid_until_from: datetime | str | int | None = None,
        valid_until_to: datetime | str | int | None = None,
        limit: int = 100,
    ) -> None:
        """Initialize search criteria.

        Args:
            name: Substring to match against the ``name`` field.
            description_keywords: Keywords for full-text search on ``description``.
            created_at_from: Lower bound for ``created_at`` (datetime, ISO string, or epoch int).
            created_at_to: Upper bound for ``created_at`` (datetime, ISO string, or epoch int).
            updated_at_from: Lower bound for ``updated_at`` (datetime, ISO string, or epoch int).
            updated_at_to: Upper bound for ``updated_at`` (datetime, ISO string, or epoch int).
            valid_until_from: Lower bound for ``valid_until`` (datetime, ISO string, or epoch int).
            valid_until_to: Upper bound for ``valid_until`` (datetime, ISO string, or epoch int).
            limit: Maximum result count. 0 or negative means no limit.
        """
        self.name = name
        self.description_keywords = description_keywords
        self.created_at_from = created_at_from
        self.created_at_to = created_at_to
        self.updated_at_from = updated_at_from
        self.updated_at_to = updated_at_to
        self.valid_until_from = valid_until_from
        self.valid_until_to = valid_until_to
        self.limit = limit

    def __setattr__(self, name: str, value: Any) -> None:
        """Validate and set an attribute with type conversion.

        Datetime fields accept ``datetime``, ISO-8601 string, or Unix epoch int.

        Args:
            name: Attribute name.
            value: Attribute value.

        Raises:
            ValueError: If the value type is invalid.
        """
        if name == "name":
            # name accepts str or None
            if value is not None and not isinstance(value, str):
                raise ValueError("name must be str | None")
            object.__setattr__(self, "name", value)

        elif name == "description_keywords":
            # description_keywords must be a list of strings or None
            if value is not None:
                if not isinstance(value, list):
                    raise ValueError("description_keywords must be list[str] | None")
            object.__setattr__(self, "description_keywords", value)

        elif name in (
            "created_at_from",
            "created_at_to",
            "updated_at_from",
            "updated_at_to",
            "valid_until_from",
            "valid_until_to",
        ):
            # Datetime fields: accept datetime, ISO string, or epoch int
            if value is None:
                object.__setattr__(self, name, None)
            elif isinstance(value, datetime):
                object.__setattr__(self, name, value)
            elif isinstance(value, str):
                try:
                    object.__setattr__(self, name, datetime.fromisoformat(value))
                except ValueError as e:
                    raise ValueError(
                        f"{name} must be a valid ISO datetime string"
                    ) from e
            elif isinstance(value, int):
                object.__setattr__(self, name, datetime.fromtimestamp(value))
            else:
                raise ValueError(
                    f"{name} must be datetime | str | int | None, got {type(value)}"
                )

        elif name == "limit":
            # limit must be a non-negative integer
            if not isinstance(value, int):
                raise ValueError("limit must be int")
            if value < 0:
                raise ValueError("limit must be >= 0")
            object.__setattr__(self, "limit", value)

        else:
            object.__setattr__(self, name, value)

    def to_query(
        self,
        database_provider: IDatabaseProvider,
        collection_name: str = "Secrets",
    ) -> str:
        """Build a SurrealQL SELECT query string from the set criteria.

        Args:
            database_provider: The database provider to use. Must be SurrealDbRemoteProvider.
            collection_name: Target SurrealDB table name. Defaults to ``"Secrets"``.

        Returns:
            A SurrealQL SELECT query string.

        Raises:
            NotImplementedError: If a provider other than SurrealDbRemoteProvider is passed.
        """
        # Both SurrealDB remote and local (embedded) providers use the same SurrealQL syntax.
        # Other provider types are not supported.
        if not isinstance(database_provider, (SurrealDbRemoteProvider, SurrealDbLocalProvider)):
            raise NotImplementedError(
                f"Database provider {type(database_provider)} is not supported "
                "for Secret search."
            )

        # Start building the query
        query: str = f"SELECT * FROM {collection_name} WHERE"
        conditions: list[str] = []

        # Name substring match
        if self.name is not None:
            conditions.append(f" string::contains(name, '{self.name}')")

        # Description keyword search (OR between keywords)
        if self.description_keywords:
            if len(self.description_keywords) == 1:
                conditions.append(f" string::contains(description, '{self.description_keywords[0]}')")
            else:
                or_part = " OR ".join(
                    f"string::contains(description, '{kw}')" for kw in self.description_keywords
                )
                conditions.append(f" ({or_part})")

        def _fmt(dt: datetime) -> str:
            """Format a datetime for use in a SurrealQL string literal."""
            return dt.isoformat()

        # Date-range conditions
        if self.created_at_from is not None:
            conditions.append(f" created_at >= '{_fmt(self.created_at_from)}'")
        if self.created_at_to is not None:
            conditions.append(f" created_at <= '{_fmt(self.created_at_to)}'")
        if self.updated_at_from is not None:
            conditions.append(f" updated_at >= '{_fmt(self.updated_at_from)}'")
        if self.updated_at_to is not None:
            conditions.append(f" updated_at <= '{_fmt(self.updated_at_to)}'")
        if self.valid_until_from is not None:
            conditions.append(f" valid_until >= '{_fmt(self.valid_until_from)}'")
        if self.valid_until_to is not None:
            conditions.append(f" valid_until <= '{_fmt(self.valid_until_to)}'")

        # Join conditions with AND, or use a tautology if no conditions are set
        if conditions:
            query += " AND".join(conditions)
        else:
            query += " true"

        # Apply result limit if set
        if self.limit > 0:
            query += f" LIMIT {self.limit}"

        return query


class ISecretManager(ABC):
    """Abstract interface for the SecretManager component.

    SecretManager is responsible for:
        - Key registry: loading, storing, and generating ``SecretKey`` entries per ``CryptoType``.
        - Secret catalogue: persisting encrypted ``Secret`` entries in the ``Secrets`` collection.
        - Crypto: transparently encrypting values on write and decrypting on read.

    Initialization sequence:
        SecretManager.initialize() is Phase-2 of the application startup sequence.

        # Phase 1
        await database_manager.initialize_default_connection(config)
        # Phase 2 (this component)
        secret_manager.initialize(database_manager, crypto_util, config)
        # Phase 3
        await database_manager.initialize(secret_manager)
    """

    @abstractmethod
    def initialize(
        self,
        database_manager: Any,
        crypto_util: CryptoUtil,
        config: dict[str, Any],
    ) -> bool:
        """Phase-2 initialization: register dependencies and load cryptographic keys.

        Must be called after Phase-1 (``DatabaseManager.initialize_default_connection``).

        Args:
            database_manager: Already Phase-1-initialized ``DatabaseManager`` instance.
            crypto_util: Utility used to perform encryption and decryption.
            config: Component configuration dict. If ``config["secret_keys"]`` is present
                and non-empty, keys are loaded from there (priority A). Otherwise, keys
                are loaded from ``secret_keys.json`` in the application data folder (B),
                or auto-generated and persisted (C).

        Returns:
            True on successful initialization.

        Raises:
            SecretManagerInitializationException: If initialization fails (e.g. default
                database provider not available).
        """
        ...

    @abstractmethod
    def add_key(self, key: SecretKey) -> None:
        """Register a ``SecretKey`` entry in the internal key store.

        Args:
            key: Key entry to register. ``key.name`` must match a valid ``CryptoType.value``.

        Raises:
            SecretManagerInvalidSecretEntryException: A key for ``key.name`` is already registered.
        """
        ...

    @abstractmethod
    def get_key(self, crypto_type: CryptoType) -> SecretKey:
        """Retrieve the registered ``SecretKey`` for the specified crypto type.

        Args:
            crypto_type: Crypto type to look up.

        Returns:
            Registered ``SecretKey`` entry.

        Raises:
            SecretManagerKeyNotFoundException: No key is registered for the specified crypto type.
        """
        ...

    @abstractmethod
    def generate_key(self, crypto_type: CryptoType) -> SecretKey:
        """Generate a new ``SecretKey``, register it, and persist all keys to disk.

        Args:
            crypto_type: Crypto type for which to generate a key.

        Returns:
            The newly generated and registered ``SecretKey``.

        Raises:
            SecretManagerNotInitializedException: SecretManager is not initialized.
            SecretManagerInvalidSecretEntryException: A key for the crypto type is already registered.
        """
        ...

    @abstractmethod
    async def create_secret(self, secret: Secret) -> Secret:
        """Encrypt and persist a new ``Secret`` entry in the ``Secrets`` collection.

        Each key-value pair in ``secret.raw_secret`` is encrypted and stored in
        ``secret.secret`` before persistence.  The returned entry has ``raw_secret``
        populated with the original plaintext and ``secret`` set to ``None``.

        Args:
            secret: Secret entry to create. ``raw_secret`` must be populated with
                the plaintext credentials. If ``id`` is not set, the database assigns one.

        Returns:
            Created entry with ``raw_secret`` populated (plaintext) and ``secret`` = None.

        Raises:
            SecretManagerNotInitializedException: SecretManager is not initialized.
            SecretManagerInvalidSecretEntryException: ``secret`` entry data is invalid.
            SecretManagerCryptoException: Encryption of a value fails.
            SecretManagerOperationException: Database persistence fails.
        """
        ...

    @abstractmethod
    async def update_secret(self, secret: Secret) -> Secret:
        """Encrypt and merge-update an existing ``Secret`` entry.

        Args:
            secret: Updated entry. ``id`` is required. ``raw_secret`` must be populated
                with the plaintext credentials.

        Returns:
            Updated entry with ``raw_secret`` populated (plaintext) and ``secret`` = None.

        Raises:
            SecretManagerNotInitializedException: SecretManager is not initialized.
            SecretManagerInvalidSecretEntryException: Entry data is invalid (e.g. ``id`` missing).
            SecretManagerCryptoException: Encryption of a value fails.
            SecretManagerSecretNotFoundException: Target record does not exist.
            SecretManagerOperationException: Database operation fails.
        """
        ...

    @abstractmethod
    async def get_secret(self, secret_id: str, decrypt: bool = False) -> Secret | None:
        """Retrieve a ``Secret`` entry by record id.

        Args:
            secret_id: Record id to look up.
            decrypt: If True, decrypt the stored values and return them in ``raw_secret``.
                If False, mask all values in ``secret`` with ``"******"``.

        Returns:
            Matching ``Secret`` entry, or ``None`` if not found.

        Raises:
            SecretManagerNotInitializedException: SecretManager is not initialized.
            SecretManagerCryptoException: Decryption fails (only when ``decrypt=True``).
            SecretManagerOperationException: Database query fails.
        """
        ...

    @abstractmethod
    async def search_secrets(
        self, criteria: SecretSearchCriteria, decrypt: bool = False
    ) -> list[Secret]:
        """Search for ``Secret`` entries matching the given criteria.

        Args:
            criteria: Search criteria.
            decrypt: If True, decrypt the stored values in the results.

        Returns:
            List of matching ``Secret`` entries. Empty list if nothing matches.

        Raises:
            SecretManagerNotInitializedException: SecretManager is not initialized.
            SecretManagerCryptoException: Decryption fails (only when ``decrypt=True``).
            SecretManagerOperationException: Database query fails.
        """
        ...

    @abstractmethod
    async def delete_secret(self, secret_id: str) -> None:
        """Delete a ``Secret`` entry by record id.

        Args:
            secret_id: Record id of the entry to delete.

        Raises:
            SecretManagerNotInitializedException: SecretManager is not initialized.
            SecretManagerSecretNotFoundException: No record with the given id exists.
            SecretManagerOperationException: Database operation fails.
        """
        ...
