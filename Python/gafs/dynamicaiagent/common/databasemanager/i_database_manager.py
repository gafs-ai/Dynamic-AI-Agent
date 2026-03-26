from __future__ import annotations

from abc import ABC, abstractmethod

from gafs.dynamicaiagent.utils.databaseprovider import DatabaseProviderOptions
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider

class IDatabaseManager(ABC):
    """
    Interface for database manager.
    Database manager manages multiple database providers.
    """

    @staticmethod
    def DEFAULT_DATABASE_NAME() -> str:
        """Get the default database name.
        
        Returns:
            Default database name.
        """
        return "default"

    @abstractmethod
    async def add_provider(self, options: DatabaseProviderOptions, overwrite: bool = False) -> bool:
        """Add a database provider.
        
        Args:
            options: Database provider options.
            overwrite: If True, overwrite existing provider with the same name.
        
        Returns:
            True if the provider was added successfully, False if it already exists and overwrite is False.
        """
        pass

    @abstractmethod
    def get_provider(self, database_name: str) -> IDatabaseProvider | None:
        """Get a database provider by name.
        
        Args:
            database_name: Name of the database provider.
        
        Returns:
            Database provider instance if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_default_database_provider(self) -> IDatabaseProvider | None:
        """Get the default database provider.
        
        Returns:
            Default database provider instance if found, None otherwise.
        """
        pass

    @abstractmethod
    async def remove_provider(self, database_name: str) -> bool:
        """Remove a database provider.
        
        Args:
            database_name: Name of the database provider to remove.
        
        Returns:
            True if the provider was removed successfully, False if it was not found.
        """
        pass
