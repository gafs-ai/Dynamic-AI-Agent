"""i_database_manager.py - Abstract base class (interface) for DatabaseManager."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider

from .models import DatabaseConnection, FullTextAnalyzer

if TYPE_CHECKING:
    # ISecretManager is in a separate component that may not yet exist.
    # Use TYPE_CHECKING to avoid circular / missing imports at runtime.
    from gafs.dynamicaiagent.common.secretmanager import ISecretManager


class IDatabaseManager(ABC):
    """Interface for the DatabaseManager component.

    Responsibilities:
        - Provider registry: create, cache, and dispose IDatabaseProvider instances.
        - Connection catalogue: persist and manage DatabaseConnection entries in
          the DatabaseConnections collection.
        - Analyzer catalogue: persist and manage FullTextAnalyzer entries in
          the FullTextAnalyzers collection.

    Initialization sequence:
        Due to the mutual dependency between DatabaseManager and SecretManager,
        initialization must follow this three-phase sequence:

            # Phase 1 — database-only initialization
            await database_manager.initialize_default_connection(config)

            # Phase 2 — SecretManager initialization (uses the DatabaseManager)
            await secret_manager.initialize(database_manager, ...)

            # Phase 3 — complete DatabaseManager setup
            await database_manager.initialize(secret_manager)

        After phase 3, all public methods are available.
        Methods with requires_phase=1 are available after phase 1.
        Methods with requires_phase=3 require phase 3 to be complete.
    """

    @staticmethod
    def DEFAULT_DATABASE_NAME() -> str:
        """Key and record id used for the default database entry in DatabaseConnections."""
        return "default"

    # ---------------------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------------------

    @abstractmethod
    async def initialize_default_connection(self, config: DatabaseConnection) -> bool:
        """Phase-1 initialization: connect to the default database.

        Validates the given config, creates the default IDatabaseProvider, ensures
        the 'default' entry exists in DatabaseConnections, and sets up all required
        indexes and default analyzers.

        Args:
            config: Configuration for the default database connection.

        Returns:
            True on success.

        Raises:
            DatabaseManagerInitializationException: If connection or setup fails.
        """
        ...

    @abstractmethod
    async def initialize(self, secret_manager: "ISecretManager") -> bool:
        """Phase-3 initialization: register the ISecretManager.

        Must be called after phase-1 and after ISecretManager is fully initialized.

        Args:
            secret_manager: Already-initialized SecretManager instance.

        Returns:
            True on success.

        Raises:
            DatabaseManagerInitializationException: If initialization fails.
        """
        ...

    # ---------------------------------------------------------------------------
    # Connection catalogue
    # ---------------------------------------------------------------------------

    @abstractmethod
    async def create_connection(
        self, connection_configurations: DatabaseConnection
    ) -> DatabaseConnection:
        """Create a new DatabaseConnection entry in the DatabaseConnections collection.

        Args:
            connection_configurations: Connection data. Set either secret or raw_secret, not both.

        Returns:
            Persisted entry (raw_secret excluded).

        Raises:
            DatabaseManagerNotInitializedException: DatabaseManager is not fully initialized.
            DatabaseManagerInvalidDatabaseConnectionEntryException: Entry is invalid.
            DatabaseManagerConflictingConnectionException: Specified id conflicts with existing.
            DatabaseManagerSecretNotFoundException: secret id does not reference an existing secret.
            DatabaseManagerOperationException: Database query or connection failure.
        """
        ...

    @abstractmethod
    async def update_connection(
        self, database_connection: DatabaseConnection
    ) -> DatabaseConnection:
        """Merge-update an existing DatabaseConnection entry.

        Only non-None fields are written. Updates to the 'default' connection are rejected.
        If a provider for the same id is cached, it is replaced with a newly created one.

        Args:
            database_connection: Updated connection data. id is required. raw_secret must not be set.

        Returns:
            Updated entry as returned by the database.

        Raises:
            DatabaseManagerNotInitializedException: DatabaseManager is not fully initialized.
            DatabaseManagerInvalidDatabaseConnectionEntryException: Entry is invalid.
            DatabaseManagerInvalidOperationException: Target is the default connection.
            DatabaseManagerConnectionNotFoundException: No record exists for the given id.
            DatabaseManagerSecretNotFoundException: secret id does not reference an existing secret.
            DatabaseManagerOperationException: Database query or connection failure.
        """
        ...

    @abstractmethod
    async def get_connection(self, id: str) -> DatabaseConnection | None:
        """Retrieve a DatabaseConnection entry by record id.

        Args:
            id: Record id to look up.

        Returns:
            Matching entry, or None if not found.

        Raises:
            DatabaseManagerNotInitializedException: DatabaseManager is not fully initialized.
            DatabaseManagerOperationException: Database query failure.
        """
        ...

    @abstractmethod
    async def get_all_connections(self) -> list[DatabaseConnection]:
        """Retrieve all DatabaseConnection entries.

        Returns:
            All entries as a list (empty list if none found).

        Raises:
            DatabaseManagerNotInitializedException: DatabaseManager is not fully initialized.
            DatabaseManagerOperationException: Database query failure.
        """
        ...

    @abstractmethod
    async def get_connections_by_name(
        self, name: str, ambiguous: bool = False
    ) -> list[DatabaseConnection]:
        """Retrieve DatabaseConnection entries by name.

        Args:
            name: Connection name to search for.
            ambiguous: If True, use partial (contains) match. If False, use exact match.

        Returns:
            Matching entries as a list (empty list if none found).

        Raises:
            DatabaseManagerNotInitializedException: DatabaseManager is not fully initialized.
            DatabaseManagerOperationException: Database query failure.
        """
        ...

    @abstractmethod
    async def delete_connection(self, id: str) -> None:
        """Delete a DatabaseConnection entry and close any cached provider for the same id.

        Deletion of the 'default' connection is rejected. If the provider for the specified
        id is cached, it is closed and removed before the record is deleted.

        Args:
            id: Record id of the connection to delete.

        Raises:
            DatabaseManagerNotInitializedException: DatabaseManager is not fully initialized.
            DatabaseManagerInvalidOperationException: id is 'default'.
            DatabaseManagerConnectionNotFoundException: No record exists for the given id.
            DatabaseManagerOperationException: Database query failure.
        """
        ...

    # ---------------------------------------------------------------------------
    # Analyzer catalogue
    # ---------------------------------------------------------------------------

    @abstractmethod
    async def create_analyzer(self, analyzer: FullTextAnalyzer) -> FullTextAnalyzer:
        """Create a new FullTextAnalyzer entry and define the analyzer on the default database.

        Args:
            analyzer: Analyzer definition to create.

        Returns:
            Created entry.

        Raises:
            DatabaseManagerNotInitializedException: DatabaseManager is not fully initialized.
            DatabaseManagerConflictingAnalyzerException: name or id conflicts with existing.
            DatabaseManagerInvalidAnalyzerException: Validation failure.
            DatabaseManagerAnalyzerOperationException: Creation or definition query fails.
        """
        ...

    @abstractmethod
    async def update_analyzer(self, analyzer: FullTextAnalyzer) -> FullTextAnalyzer:
        """Update an existing FullTextAnalyzer entry and alter the analyzer on the default database.

        Uses ALTER ANALYZER to update. If tokenizers or filters changed, rebuilds all indexes
        that reference the updated analyzer.

        Args:
            analyzer: Updated analyzer definition. id is required.

        Returns:
            Updated entry.

        Raises:
            DatabaseManagerNotInitializedException: DatabaseManager is not fully initialized.
            DatabaseManagerAnalyzerNotFoundException: Update target does not exist.
            DatabaseManagerInvalidAnalyzerException: Validation failure or id is empty.
            DatabaseManagerAnalyzerOperationException: Query failure.
        """
        ...

    @abstractmethod
    async def get_analyzer(self, id: str) -> FullTextAnalyzer | None:
        """Retrieve a FullTextAnalyzer entry by record id.

        Args:
            id: Record id to look up.

        Returns:
            Matching entry, or None if not found.

        Raises:
            DatabaseManagerNotInitializedException: DatabaseManager is not fully initialized.
            DatabaseManagerAnalyzerOperationException: Query failure.
        """
        ...

    @abstractmethod
    async def get_all_analyzers(self) -> list[FullTextAnalyzer]:
        """Retrieve all FullTextAnalyzer entries.

        Returns:
            All entries as a list (empty list if none found).

        Raises:
            DatabaseManagerNotInitializedException: DatabaseManager is not fully initialized.
            DatabaseManagerAnalyzerOperationException: Query failure.
        """
        ...

    @abstractmethod
    async def get_analyzers_by_name(
        self, name: str, ambiguous: bool = False
    ) -> list[FullTextAnalyzer]:
        """Retrieve FullTextAnalyzer entries by name.

        Args:
            name: Analyzer name to search for.
            ambiguous: If True, use partial (contains) match. If False, use exact match.

        Returns:
            Matching entries as a list (empty list if none found).

        Raises:
            DatabaseManagerNotInitializedException: DatabaseManager is not fully initialized.
            DatabaseManagerAnalyzerOperationException: Query failure.
        """
        ...

    @abstractmethod
    async def delete_analyzer(self, id: str) -> None:
        """Delete a FullTextAnalyzer entry and remove the analyzer from the default database.

        The FullTextAnalyzers collection entry and the actual database analyzer are kept consistent.

        Args:
            id: Record id of the analyzer to delete.

        Raises:
            DatabaseManagerNotInitializedException: DatabaseManager is not fully initialized.
            DatabaseManagerAnalyzerNotFoundException: Target does not exist.
            DatabaseManagerAnalyzerOperationException: Query failure.
        """
        ...

    # ---------------------------------------------------------------------------
    # Provider getters
    # ---------------------------------------------------------------------------

    @abstractmethod
    async def get_provider(self, id: str) -> IDatabaseProvider:
        """Return the IDatabaseProvider for a connection id.

        If already cached, return immediately. For 'default', delegates to
        get_default_provider(). Non-default providers are created on demand.

        Active providers are cached in the DatabaseManager instance.

        Args:
            id: Record id of the DatabaseConnection.

        Returns:
            Corresponding provider instance.

        Raises:
            DatabaseManagerNotInitializedException: Phase-3 not completed (for non-default).
            DatabaseManagerConnectionNotFoundException: No connection record for the given id.
            DatabaseManagerSecretNotFoundException: Required secret does not exist.
            DatabaseManagerOperationException: Query failure.
        """
        ...

    @abstractmethod
    def get_default_provider(self) -> IDatabaseProvider:
        """Return the default IDatabaseProvider synchronously.

        NOTE: This is a synchronous method (not async).

        Returns:
            Default provider instance.

        Raises:
            DatabaseManagerNotInitializedException: Default provider is not registered.
        """
        ...
