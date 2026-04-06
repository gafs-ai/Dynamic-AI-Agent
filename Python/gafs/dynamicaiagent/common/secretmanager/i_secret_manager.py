from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager
from gafs.dynamicaiagent.common.secretmanager.secret import Secret
from gafs.dynamicaiagent.utils.databaseprovider import (
    IDatabaseProvider,
    SurrealDbRemoteProvider,
)
from gafs.dynamicaiagent.utils.symmetriccryptoutil import (
    SymmetricCryptoType,
    SymmetricCryptoUtil,
)


class ISecretManager(ABC):
    """Interface for secret manager.

    Implementations of this interface must be able to:

    - manage symmetric keys for specific cryptographic algorithms
      (for example AES-256-GCM)
    - create, update, retrieve and delete secrets stored in the database.
    """

    @abstractmethod
    def initialize(
        self,
        database_manager: IDatabaseManager,
        crypto_util: SymmetricCryptoUtil,
        keys: dict[str, str],
    ) -> bool:
        """Initialize secret manager with database provider, crypto util and keys.

        Args:
            database_manager: Database manager used to access the underlying database.
            crypto_util: Utility used to perform symmetric encryption and decryption.
            keys: Mapping from crypto type value to symmetric key string.

        Returns:
            True if the initialization succeeded, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def add_symmetric_key(self, crypto_type: SymmetricCryptoType, key: str) -> bool:
        """Register a symmetric key for the specified crypto type.

        Args:
            crypto_type: The crypto type to register the key for.
            key: The key to register.

        Returns:
            True if the key was registered successfully, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def get_symmetric_key(self, crypto_type: SymmetricCryptoType) -> str | None:
        """Get a symmetric key for the specified crypto type.

        Args:
            crypto_type: The crypto type to get the key for.

        Returns:
            The key for the specified crypto type.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_symmetric_key(self, crypto_type: SymmetricCryptoType) -> str:
        """Generate and register a symmetric key for the specified crypto type.

        Args:
            crypto_type: The crypto type for which a key will be generated.

        Returns:
            The generated symmetric key.
        """
        raise NotImplementedError

    @abstractmethod
    async def create_secret(self, secret: Secret) -> Secret:
        """Create a new secret.

        Args:
            secret: The secret entity to be created. If id is not specified,
                a new id will be generated.

        Returns:
            The created secret.
        """
        raise NotImplementedError

    @abstractmethod
    async def update_secret(self, secret: Secret) -> Secret:
        """Update an existing secret.

        Args:
            secret: The secret entity with updated values.

        Returns:
            The updated secret.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_secret(self, secret_id: str) -> Secret:
        """Get a secret by id.

        If the secret is encrypted, the secret will be decrypted before returning.

        Args:
            secret_id: The identifier of the secret to retrieve.

        Returns:
            The retrieved secret with decrypted values.
        """
        raise NotImplementedError

    @abstractmethod
    async def search_secrets(
        self, secret_search_criteria: "SecretSearchCriteria"
    ) -> list[Secret]:
        """Search secrets by criteria.

        Args:
            secret_search_criteria: The criteria to search for secrets.

        Returns:
            A list of secrets matching the criteria.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_secret(self, secret_id: str) -> bool:
        """Delete a secret by id.

        Args:
            secret_id: The identifier of the secret to delete.

        Returns:
            True if the secret was deleted successfully, False otherwise.
        """
        raise NotImplementedError


class SecretSearchCriteria:
    """Search criteria for querying `Secret` records.

    Currently only SurrealDB queries are supported.

    Attributes:
        name: String for partial match search on secret name.
        description_keywords: Keywords for description (OR condition).
        created_at_from: Lower bound for created_at.
        created_at_to: Upper bound for created_at.
        updated_at_from: Lower bound for updated_at.
        updated_at_to: Upper bound for updated_at.
        valid_until_from: Lower bound for valid_until.
        valid_until_to: Upper bound for valid_until.
        limit: Maximum number of results. No LIMIT clause when <= 0.
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
        # Initialize all fields like a data class, listing all possible values
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
        """Setter with validation.

        - String fields accept `str | None`
        - Datetime fields accept `datetime | str(ISO) | int(epoch seconds) | None`
        - List fields accept `list[str] | None`
        - limit must be int >= 0
        """

        if name == "name":
            if value is not None and not isinstance(value, str):
                raise ValueError("name must be str | None")
            object.__setattr__(self, name, value)
            return

        if name == "description_keywords":
            if value is not None:
                if not isinstance(value, list) or not all(
                    isinstance(v, str) for v in value
                ):
                    raise ValueError("description_keywords must be list[str] | None")
            object.__setattr__(self, name, value)
            return

        datetime_fields = {
            "created_at_from",
            "created_at_to",
            "updated_at_from",
            "updated_at_to",
            "valid_until_from",
            "valid_until_to",
        }
        if name in datetime_fields:
            if value is None:
                object.__setattr__(self, name, None)
                return
            if isinstance(value, datetime):
                object.__setattr__(self, name, value)
                return
            if isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value)
                except ValueError as exc:  # noqa: TRY003
                    raise ValueError(
                        f"{name} must be a valid ISO datetime string"
                    ) from exc
                object.__setattr__(self, name, dt)
                return
            if isinstance(value, int):
                object.__setattr__(self, name, datetime.fromtimestamp(value))
                return
            raise ValueError(
                f"{name} must be datetime | str | int | None, got {type(value)}"
            )

        if name == "limit":
            if not isinstance(value, int):
                raise ValueError("limit must be int")
            if value < 0:
                raise ValueError("limit must be >= 0")
            object.__setattr__(self, name, value)
            return

        # Set other attributes as-is
        object.__setattr__(self, name, value)

    def to_query(
        self,
        database_provider: IDatabaseProvider,
        collection_name: str = "secret",
    ) -> str:
        """Build a SurrealDB SELECT query string.

        Args:
            database_provider: The database provider to use.
            collection_name: Target table name. Default is `secret`.

        Returns:
            A SurrealQL SELECT query string.

        Raises:
            NotImplementedError: When a provider other than SurrealDbRemoteProvider is passed.
        """
        if not isinstance(database_provider, SurrealDbRemoteProvider):
            raise NotImplementedError(
                f"Database provider {type(database_provider)} is not supported "
                "for Secret search."
            )

        query: str = f"SELECT * FROM {collection_name} WHERE"
        conditions: list[str] = []

        if self.name is not None:
            conditions.append(f" name ∋ '{self.name}'")

        if self.description_keywords:
            if len(self.description_keywords) == 1:
                conditions.append(
                    f" description ∋ '{self.description_keywords[0]}'"
                )
            else:
                or_part = " OR ".join(
                    f"description ∋ '{keyword}'"
                    for keyword in self.description_keywords
                )
                conditions.append(f" ({or_part})")

        def _format_dt(dt: datetime) -> str:
            # SurrealDB can compare ISO8601 datetime strings directly
            return dt.isoformat()

        if self.created_at_from is not None:
            conditions.append(
                f" created_at >= '{_format_dt(self.created_at_from)}'"
            )
        if self.created_at_to is not None:
            conditions.append(
                f" created_at <= '{_format_dt(self.created_at_to)}'"
            )

        if self.updated_at_from is not None:
            conditions.append(
                f" updated_at >= '{_format_dt(self.updated_at_from)}'"
            )
        if self.updated_at_to is not None:
            conditions.append(
                f" updated_at <= '{_format_dt(self.updated_at_to)}'"
            )

        if self.valid_until_from is not None:
            conditions.append(
                f" valid_until >= '{_format_dt(self.valid_until_from)}'"
            )
        if self.valid_until_to is not None:
            conditions.append(
                f" valid_until <= '{_format_dt(self.valid_until_to)}'"
            )

        if conditions:
            query += " AND".join(conditions)
        else:
            query += " true"

        if self.limit > 0:
            query += f" LIMIT {self.limit}"

        return query