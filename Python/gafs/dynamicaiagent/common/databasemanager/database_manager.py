from __future__ import annotations

import json
from logging import Logger
from typing import TYPE_CHECKING, cast, override

from gafs.dynamicaiagent.utils.databaseprovider import (
    DatabaseProviderOptions,
    DatabaseProviderType,
    DatabaseType,
    IDatabaseProvider,
    SurrealDbRemoteProvider,
)
from gafs.dynamicaiagent.utils.databaseprovider.surrealdb_remote_provider import (
    RemoteSurrealDbOptions,
)

from .database_connection import DatabaseConnection
from .i_database_manager import IDatabaseManager
from .exceptions.database_manager_exception import DatabaseManagerException
from .exceptions.database_manager_exceptions import (
    DatabaseManagerConfigurationException,
    DatabaseManagerProviderCloseException,
    DatabaseManagerProviderInitializationException,
    DatabaseManagerNotInitializedException,
    DatabaseManagerConnectionNotFoundException,
    DatabaseManagerSecretNotFoundException,
    DatabaseManagerInvalidOperationException,
)

if TYPE_CHECKING:
    from gafs.dynamicaiagent.common.secretmanager.i_secret_manager import ISecretManager
    from gafs.dynamicaiagent.common.secretmanager.secret import Secret


class DatabaseManager(IDatabaseManager):
    """Concrete implementation of :py:class:`IDatabaseManager`.

    Manages a registry of :py:class:`IDatabaseProvider` instances and
    persists :py:class:`DatabaseConnection` configuration entries in the
    ``databases`` collection of the default database.

    See :py:class:`IDatabaseManager` for the required initialisation
    sequence.
    """

    def __init__(self, logger: Logger) -> None:
        self._logger: Logger = logger
        # Provider registry: keyed by DatabaseConnection.id (or "default").
        self._providers: dict[str, IDatabaseProvider] = {}
        self._secret_manager: ISecretManager | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _add_provider(
        self,
        options: DatabaseProviderOptions,
        provider_id: str,
        overwrite: bool = False,
    ) -> IDatabaseProvider:
        """Create and register a database provider.

        Args:
            options: Provider options used to create the provider.
            provider_id: Key under which the provider is registered.
            overwrite: When ``True``, close the existing provider first.

        Returns:
            The newly created and registered :py:class:`IDatabaseProvider`.

        Raises:
            DatabaseManagerProviderCloseException: Closing the existing
                provider failed.
            DatabaseManagerProviderInitializationException: Creating or
                initialising the new provider failed.
            DatabaseManagerConfigurationException: Unsupported
                ``database_type``.
        """
        self._logger.debug("Adding database provider '%s'...", provider_id)

        if provider_id in self._providers:
            if overwrite:
                self._logger.debug(
                    "Provider '%s' already exists. Overwriting...", provider_id
                )
                existing: IDatabaseProvider = self._providers[provider_id]
                try:
                    await existing.close()
                except DatabaseManagerException:
                    raise
                except Exception as ex:
                    raise DatabaseManagerProviderCloseException(
                        message="Failed to close existing provider during overwrite.",
                        cause=ex,
                    ) from ex
                del self._providers[provider_id]
            else:
                self._logger.debug(
                    "Provider '%s' already registered, returning existing instance.",
                    provider_id,
                )
                return self._providers[provider_id]

        provider: IDatabaseProvider

        match options.database_type:
            case DatabaseType.SURREALDB_REMOTE:
                try:
                    provider = SurrealDbRemoteProvider(self._logger)
                    await provider.initialize(cast(RemoteSurrealDbOptions, options))
                except DatabaseManagerException:
                    raise
                except Exception as ex:
                    raise DatabaseManagerProviderInitializationException(
                        message="Failed to initialize database provider.",
                        details={"database_type": options.database_type.value},
                        cause=ex,
                    ) from ex
            case _:
                raise DatabaseManagerConfigurationException(
                    message=f"Unsupported database type: {options.database_type}",
                    details={"database_type": options.database_type.value},
                )

        self._providers[provider_id] = provider
        self._logger.debug("Database provider '%s' registered.", provider_id)
        return provider

    async def _remove_provider(self, provider_id: str) -> bool:
        """Close and deregister a provider.

        Args:
            provider_id: Key of the provider to remove.

        Returns:
            ``True`` if removed; ``False`` if the key was not registered.

        Raises:
            DatabaseManagerProviderCloseException: Close operation failed.
        """
        if provider_id not in self._providers:
            return False
        provider: IDatabaseProvider = self._providers[provider_id]
        try:
            await provider.close()
        except DatabaseManagerException:
            raise
        except Exception as ex:
            raise DatabaseManagerProviderCloseException(
                message="Failed to close database provider while removing it.",
                cause=ex,
            ) from ex
        del self._providers[provider_id]
        self._logger.debug("Database provider '%s' removed.", provider_id)
        return True

    def _check_initialized(self) -> None:
        """Raise if phase-3 initialisation has not been completed."""
        if self._secret_manager is None:
            raise DatabaseManagerNotInitializedException()

    async def _build_provider_options(
        self, connection: DatabaseConnection
    ) -> DatabaseProviderOptions:
        """Construct :py:class:`DatabaseProviderOptions` from a connection record.

        Merges ``connection.parameters`` with decrypted secret
        values (secret values take precedence). Then creates the appropriate
        :py:class:`DatabaseProviderOptions` subclass from the merged dict.

        Args:
            connection: The :py:class:`DatabaseConnection` to build from.

        Returns:
            Populated :py:class:`DatabaseProviderOptions` instance.

        Raises:
            DatabaseManagerSecretNotFoundException: The referenced secret
                does not exist.
            DatabaseManagerConfigurationException: Unsupported
                ``database_type`` or ``database_type`` is ``None``.
        """
        if connection.database_type is None:
            raise DatabaseManagerConfigurationException(
                message="DatabaseConnection.database_type is required to build provider options.",
                details={"id": connection.id},
            )

        conn_params: dict = dict(connection.parameters or {})

        if connection.secret is not None:
            secret: Secret | None = await self._secret_manager.get_secret(  # type: ignore[union-attr]
                connection.secret
            )
            if secret is None:
                raise DatabaseManagerSecretNotFoundException(
                    message=f"Secret not found: {connection.secret}",
                    details={"secret_id": connection.secret},
                )
            if secret.secret is not None:
                conn_params = {**conn_params, **secret.secret}

        match connection.database_type:
            case DatabaseProviderType.SURREALDB_REMOTE:
                options = RemoteSurrealDbOptions()
                for key, value in conn_params.items():
                    if hasattr(options, key) and value is not None:
                        setattr(options, key, value)
                options.database_type = DatabaseType.SURREALDB_REMOTE
                options.database_name = connection.id
                return options
            case _:
                raise DatabaseManagerConfigurationException(
                    message=f"Unsupported database type: {connection.database_type}",
                    details={"database_type": connection.database_type.value},
                )

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    @override
    async def initialize_default_connection(
        self, config: DatabaseConnection
    ) -> None:
        """Phase-1 initialisation: connect to the default database.

        1. Build :py:class:`DatabaseProviderOptions` from *config* by merging
           ``config.parameters`` with ``config.raw_secret`` (credentials are
           supplied as plain-text at this stage because
           :py:class:`ISecretManager` is not yet available).
        2. Create and register the default :py:class:`IDatabaseProvider`.
        3. Upsert a placeholder record
           ``{ id: "default", name: "default" }`` into the ``databases``
           collection (no secret stored).
        4. Ensure a unique index on the ``name`` field exists.
        """
        self._logger.debug("Initializing default database connection...")

        # Build provider options directly from DatabaseConnection.
        # At this point SecretManager is unavailable, so raw_secret is merged
        # into connection parameters as plain-text credentials.
        if config.database_type is None:
            raise DatabaseManagerConfigurationException(
                message="config.database_type is required for default connection."
            )

        conn_params: dict = dict(config.parameters or {})
        if config.raw_secret is not None:
            conn_params = {**conn_params, **config.raw_secret}

        match config.database_type:
            case DatabaseProviderType.SURREALDB_REMOTE:
                options = RemoteSurrealDbOptions()
                for key, value in conn_params.items():
                    if hasattr(options, key) and value is not None:
                        setattr(options, key, value)
                options.database_type = DatabaseType.SURREALDB_REMOTE
                options.database_name = self.DEFAULT_DATABASE_NAME()
            case _:
                raise DatabaseManagerConfigurationException(
                    message=f"Unsupported database type: {config.database_type}",
                    details={"database_type": config.database_type.value},
                )

        # [1] & [2]: connect and register default provider
        await self._add_provider(options, self.DEFAULT_DATABASE_NAME())

        default_provider = self.get_default_provider()

        # [3]: create the placeholder default entry (idempotent)
        collection = self.COLLECTION_NAME()
        default_id = self.DEFAULT_DATABASE_NAME()
        insert_query = (
            f"INSERT IGNORE INTO {collection} "
            f"{{ id: {collection}:{default_id}, name: {json.dumps(default_id)} }}"
        )
        await default_provider.query_raw(insert_query)

        # [4]: guarantee a unique index on the "name" field
        index_query = (
            f"DEFINE INDEX IF NOT EXISTS "
            f"idx_{collection}_name_unique "
            f"ON {collection} FIELDS name UNIQUE"
        )
        await default_provider.query_raw(index_query)

        self._logger.info("Default database connection initialized.")

    @override
    async def initialize(self, secret_manager: ISecretManager) -> None:
        """Phase-3 initialisation: register the SecretManager."""
        self._logger.debug("Registering SecretManager with DatabaseManager...")
        self._secret_manager = secret_manager
        self._logger.info("DatabaseManager fully initialized.")

    # ------------------------------------------------------------------
    # Connection catalogue (CRUD)
    # ------------------------------------------------------------------

    @override
    async def add_connection(
        self, connection_configurations: DatabaseConnection
    ) -> DatabaseConnection:
        """Create a new DatabaseConnection entry in the database."""
        self._check_initialized()

        has_raw_secret = connection_configurations.raw_secret is not None
        has_secret = connection_configurations.secret is not None

        if has_raw_secret and has_secret:
            raise DatabaseManagerInvalidOperationException(
                message=(
                    "Cannot specify both raw_secret and secret simultaneously. "
                    "Provide only one."
                )
            )

        default_provider = self.get_default_provider()

        if has_raw_secret:
            # Case A: create a Secret from raw_secret, then link by id
            from gafs.dynamicaiagent.common.secretmanager.secret import Secret  # noqa: PLC0415

            secret_entity: Secret = Secret()
            secret_entity.secret = connection_configurations.raw_secret

            created_secret: Secret = await self._secret_manager.create_secret(  # type: ignore[union-attr]
                secret_entity
            )

            # Clear the transient field and record the new secret id.
            object.__setattr__(connection_configurations, "raw_secret", None)
            connection_configurations.secret = created_secret.id

        elif has_secret:
            # Case B: verify the referenced secret exists
            existing_secret = await self._secret_manager.get_secret(  # type: ignore[union-attr]
                connection_configurations.secret
            )
            if existing_secret is None:
                raise DatabaseManagerSecretNotFoundException(
                    message=f"Secret not found: {connection_configurations.secret}",
                    details={"secret_id": connection_configurations.secret},
                )

        content_json = connection_configurations.to_json(exclude_id=True)
        if connection_configurations.id is not None:
            query = (
                f"CREATE {self.COLLECTION_NAME()}:{connection_configurations.id} "
                f"CONTENT {content_json}"
            )
        else:
            query = f"CREATE {self.COLLECTION_NAME()} CONTENT {content_json}"

        created: DatabaseConnection = await default_provider.query(
            query, DatabaseConnection
        )
        self._logger.info("DatabaseConnection created: %s", created.id)
        return created

    @override
    async def update_connection(
        self, database_connection: DatabaseConnection
    ) -> DatabaseConnection:
        """Merge-update an existing DatabaseConnection entry."""
        self._check_initialized()

        # Reject updates to the default connection.
        if (
            database_connection.id == self.DEFAULT_DATABASE_NAME()
            or database_connection.name == self.DEFAULT_DATABASE_NAME()
        ):
            raise DatabaseManagerInvalidOperationException(
                message="Cannot update the default database connection.",
                details={
                    "id": database_connection.id,
                    "name": database_connection.name,
                },
            )

        # raw_secret is not permitted in updates – rotate via SecretManager instead.
        if database_connection.raw_secret is not None:
            raise DatabaseManagerInvalidOperationException(
                message=(
                    "raw_secret is not permitted in update_connection. "
                    "Update the secret through SecretManager directly, "
                    "then call update_connection with the new secret id."
                )
            )

        # id must be present; verify the record exists.
        if database_connection.id is None:
            raise DatabaseManagerInvalidOperationException(
                message="database_connection.id must be set for an update operation."
            )

        existing = await self.get_connection(database_connection.id)
        if existing is None:
            raise DatabaseManagerConnectionNotFoundException(
                message=f"DatabaseConnection not found: {database_connection.id}",
                details={"id": database_connection.id},
            )

        # Verify the referenced secret exists if a new one is supplied.
        if database_connection.secret is not None:
            referenced_secret = await self._secret_manager.get_secret(  # type: ignore[union-attr]
                database_connection.secret
            )
            if referenced_secret is None:
                raise DatabaseManagerSecretNotFoundException(
                    message=f"Secret not found: {database_connection.secret}",
                    details={"secret_id": database_connection.secret},
                )

        # Merge-update the record in the databases collection.
        default_provider = self.get_default_provider()
        content_json = database_connection.to_json(exclude_id=True)
        query = (
            f"UPDATE {self.COLLECTION_NAME()}:{database_connection.id} "
            f"MERGE {content_json}"
        )

        updated: DatabaseConnection | None = await default_provider.query(
            query, DatabaseConnection
        )
        if updated is None:
            raise DatabaseManagerConnectionNotFoundException(
                message=(
                    f"DatabaseConnection not found after update: "
                    f"{database_connection.id}"
                ),
                details={"id": database_connection.id},
            )

        # Replace the cached provider if one was already registered.
        if database_connection.id in self._providers:
            self._logger.debug(
                "Replacing cached provider for '%s' with updated configuration.",
                database_connection.id,
            )
            refreshed = await self.get_connection(database_connection.id)
            if refreshed is not None and refreshed.database_type is not None:
                new_options = await self._build_provider_options(refreshed)
                await self._add_provider(
                    new_options, database_connection.id, overwrite=True
                )

        self._logger.info("DatabaseConnection updated: %s", database_connection.id)
        return updated

    @override
    async def get_connection(self, id: str) -> DatabaseConnection | None:
        """Retrieve a DatabaseConnection entry by id from the database."""
        default_provider = self.get_default_provider()
        query = f"SELECT * FROM {self.COLLECTION_NAME()}:{id}"
        result: DatabaseConnection | None = await default_provider.query(
            query, DatabaseConnection
        )
        return result

    @override
    async def get_connection_by_name(self, name: str) -> DatabaseConnection | None:
        """Retrieve a DatabaseConnection entry by name from the database."""
        default_provider = self.get_default_provider()
        # Use json.dumps to produce a properly quoted and escaped string literal.
        safe_name = json.dumps(name)
        query = (
            f"SELECT * FROM {self.COLLECTION_NAME()} "
            f"WHERE name = {safe_name}"
        )
        result: DatabaseConnection | None = await default_provider.query(
            query, DatabaseConnection
        )
        return result

    @override
    async def delete_connection(self, id: str) -> None:
        """Delete a DatabaseConnection entry."""
        # Reject deletion of the default connection.
        if id == self.DEFAULT_DATABASE_NAME():
            raise DatabaseManagerInvalidOperationException(
                message="Cannot delete the default database connection."
            )

        # Verify the record exists before proceeding.
        existing = await self.get_connection(id)
        if existing is None:
            raise DatabaseManagerConnectionNotFoundException(
                message=f"DatabaseConnection not found: {id}",
                details={"id": id},
            )

        # Remove the cached provider if one is registered.
        await self._remove_provider(id)

        # Delete the record from the database.
        default_provider = self.get_default_provider()
        query = f"DELETE {self.COLLECTION_NAME()}:{id}"
        await default_provider.query_raw(query)

        self._logger.info("DatabaseConnection deleted: %s", id)

    # ------------------------------------------------------------------
    # Provider access
    # ------------------------------------------------------------------

    @override
    async def get_provider(self, id: str) -> IDatabaseProvider:
        """Return or lazily create the provider for a connection id."""
        if id == self.DEFAULT_DATABASE_NAME():
            return self.get_default_provider()

        # Return cached provider immediately if available
        if id in self._providers:
            return self._providers[id]

        # Provider not cached – must load connection config from the database.
        self._check_initialized()

        # Load the connection configuration record.
        connection = await self.get_connection(id)
        if connection is None:
            raise DatabaseManagerConnectionNotFoundException(
                message=f"DatabaseConnection not found: {id}",
                details={"id": id},
            )

        # Build provider options (merges secret values if the connection has one).
        options = await self._build_provider_options(connection)

        # Create, cache, and return the new provider.
        provider = await self._add_provider(options, id)
        return provider

    @override
    def get_default_provider(self) -> IDatabaseProvider:
        """Return the default provider synchronously."""
        provider = self._providers.get(self.DEFAULT_DATABASE_NAME())
        if provider is None:
            raise DatabaseManagerConnectionNotFoundException(
                message=(
                    "Default database provider is not registered. "
                    "Call initialize_default_connection() first."
                )
            )
        return provider

