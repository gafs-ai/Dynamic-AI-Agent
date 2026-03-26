from typing import override, cast
from logging import Logger
from gafs.dynamicaiagent.utils.databaseprovider import DatabaseProviderOptions
from .i_database_manager import IDatabaseManager
from gafs.dynamicaiagent.utils.databaseprovider import DatabaseType
from gafs.dynamicaiagent.utils.databaseprovider import SurrealDbRemoteProvider
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider
from gafs.dynamicaiagent.utils.databaseprovider.surrealdb_remote_provider import RemoteSurrealDbOptions
from .exceptions.database_manager_exception import DatabaseManagerException
from .exceptions.database_manager_exceptions import (
    DatabaseManagerConfigurationException,
    DatabaseManagerProviderCloseException,
    DatabaseManagerProviderInitializationException,
)

class DatabaseManager(IDatabaseManager):
    """
    Database manager implementation.
    Manages multiple database providers and provides methods to add, get, and remove them.
    """

    def __init__(self, logger: Logger):
        self._logger: Logger = logger
        self._providers: dict[str, IDatabaseProvider] = {}
        self._default_database_provider: IDatabaseProvider | None = None

    @override
    async def add_provider(self, options: DatabaseProviderOptions, overwrite: bool = False) -> bool:
        """Add a database provider.
        
        Args:
            options: Database provider options.
            overwrite: If True, overwrite existing provider with the same name.
        
        Returns:
            True if the provider was added successfully, False if it already exists and overwrite is False.
        
        Raises:
            DatabaseManagerException: If provider configuration, initialization, or
                overwrite close operation fails.
        """
        self._logger.debug(f"Adding database provider {options.database_name}...")

        if options.database_name in self._providers:
            if overwrite:
                self._logger.debug(f"Database provider {options.database_name} already exists. Overwriting...")
                provider_to_remove: IDatabaseProvider = self._providers[options.database_name]
                try:
                    await provider_to_remove.close()
                except DatabaseManagerException:
                    raise
                except Exception as ex:
                    raise DatabaseManagerProviderCloseException(
                        message=(
                            "Failed to close existing database provider during overwrite."
                        ),
                        cause=ex,
                    ) from ex
                del self._providers[options.database_name]
            else:
                message: str = f"Database provider {options.database_name} already exists"
                self._logger.info(message)
                return False

        provider: IDatabaseProvider = None

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
                        details={
                            "database_type": options.database_type.value
                        },
                        cause=ex,
                    ) from ex
            case _:
                raise DatabaseManagerConfigurationException(
                    message=f"Unsupported database type: {options.database_type}",
                    details={
                        "database_type": options.database_type.value,
                    },
                )
        
        self._providers[options.database_name] = provider
        if options.database_name == self.DEFAULT_DATABASE_NAME():
            self._default_database_provider = provider
            self._logger.debug(
                f"Database provider {options.database_name} is set as the default."
            )
        self._logger.debug(f"Database provider {options.database_name} added successfully")
        return True

    @override
    def get_provider(self, database_name: str) -> IDatabaseProvider | None:
        """Get a database provider by name.
        
        Args:
            database_name: Name of the database provider.
        
        Returns:
            Database provider instance if found, None otherwise.
        """
        return self._providers.get(database_name, None)

    @override
    def get_default_database_provider(self) -> IDatabaseProvider | None:
        """Get the default database provider.
        
        Returns:
            Default database provider instance if found, None otherwise.
        """
        return self._default_database_provider
    
    @override
    async def remove_provider(self, database_name: str) -> bool:
        """Remove a database provider.
        
        Args:
            database_name: Name of the database provider to remove.
        
        Returns:
            True if the provider was removed successfully, False if it was not found.
        """
        self._logger.debug(f"Removing database provider {database_name}...")

        if database_name not in self._providers:
            self._logger.info(f"Database provider {database_name} not found")
            return False

        provider: IDatabaseProvider = self._providers[database_name]
        try:
            await provider.close()
        except DatabaseManagerException:
            raise
        except Exception as ex:
            raise DatabaseManagerProviderCloseException(
                message="Failed to close database provider while removing it.",
                cause=ex
            ) from ex
        del self._providers[database_name]
        if self._default_database_provider is provider:
            self._default_database_provider = None
        self._logger.debug(f"Database provider {database_name} removed successfully")
        return True
