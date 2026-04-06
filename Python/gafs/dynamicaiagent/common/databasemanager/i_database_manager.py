from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider

from .database_connection import DatabaseConnection

if TYPE_CHECKING:
    from gafs.dynamicaiagent.common.secretmanager.i_secret_manager import ISecretManager


class IDatabaseManager(ABC):
    """Interface for database manager.

    The database manager is responsible for two concerns:

    1. **Provider registry** – creating, caching, and disposing
       :py:class:`IDatabaseProvider` instances.
    2. **Connection catalogue** – persisting
       :py:class:`DatabaseConnection` configuration entries in the
       ``databases`` collection of the default database.

    Initialisation sequence
    -----------------------
    Because :py:class:`ISecretManager` depends on
    :py:class:`IDatabaseManager` and vice-versa, the two-phase
    initialisation below must be followed::

        # Phase 1 – database-only initialisation
        await database_manager.initialize_default_connection(config)

        # Phase 2 – secret manager setup
        secret_manager.initialize(database_manager, ...)

        # Phase 3 – complete database manager setup
        await database_manager.initialize(secret_manager)

    After phase 3 all public methods are available.  Methods that
    interact with non-default databases or secrets can only be called
    after phase 3.
    """

    @staticmethod
    def DEFAULT_DATABASE_NAME() -> str:
        """Name used as both the provider key and the record id for the
        default database entry in the ``databases`` collection."""
        return "default"

    @staticmethod
    def COLLECTION_NAME() -> str:
        """SurrealDB collection that stores :py:class:`DatabaseConnection`
        configuration entries."""
        return "databases"

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    @abstractmethod
    async def initialize_default_connection(
        self, config: DatabaseConnection
    ) -> None:
        """Phase-1 initialisation: connect to the default database.

        Steps performed:

        1. Establish a connection to the default database using *config*.
        2. Register the resulting :py:class:`IDatabaseProvider` internally.
        3. Create a placeholder entry in the ``databases`` collection with
           ``id = "default"`` and ``name = "default"`` (no secret stored).
        4. Ensure a unique index exists on the ``name`` field of the
           ``databases`` collection (``DEFINE INDEX IF NOT EXISTS``).

        Args:
            config: Configuration containing the
                :py:class:`DatabaseProviderOptions` for the default database.
        """
        pass

    @abstractmethod
    async def initialize(self, secret_manager: ISecretManager) -> None:
        """Phase-3 initialisation: register the :py:class:`ISecretManager`.

        Must be called after :py:meth:`initialize_default_connection` **and**
        after :py:class:`ISecretManager` has been fully initialised.

        Methods that require secret management (e.g.
        :py:meth:`add_connection`, :py:meth:`get_provider` for non-default
        providers) will raise
        :py:exc:`DatabaseManagerNotInitializedException` until this method
        has been called.

        Args:
            secret_manager: The already-initialised secret manager instance.
        """
        pass

    # ------------------------------------------------------------------
    # Connection catalogue (CRUD)
    # ------------------------------------------------------------------

    @abstractmethod
    async def add_connection(
        self, connection_configurations: DatabaseConnection
    ) -> DatabaseConnection:
        """Create a new :py:class:`DatabaseConnection` entry.

        Exactly one of ``raw_secret`` or ``secret`` may be set (or neither).
        Having both set simultaneously is an error.

        **Case A – ``raw_secret`` is provided:**

        1. Create a :py:class:`Secret` via :py:class:`ISecretManager` from
           the ``raw_secret`` dict; record the generated secret id.
        2. Clear ``raw_secret`` on *connection_configurations* and set
           ``secret`` to the new secret id.
        3. Persist the modified entry to the ``databases`` collection.

        **Case B – ``secret`` (an id) is provided:**

        1. Verify the referenced secret exists; raise
           :py:exc:`DatabaseManagerSecretNotFoundException` if not.
        2. Persist the entry to the ``databases`` collection.

        Args:
            connection_configurations: Connection data to store.

        Returns:
            The persisted :py:class:`DatabaseConnection` as returned by the
            database (includes the generated or specified ``id``).

        Raises:
            DatabaseManagerNotInitializedException: Phase-3 init not done.
            DatabaseManagerInvalidOperationException: Both ``raw_secret`` and
                ``secret`` are set simultaneously.
            DatabaseManagerSecretNotFoundException: The ``secret`` id does
                not reference an existing secret.
        """
        pass

    @abstractmethod
    async def update_connection(
        self, database_connection: DatabaseConnection
    ) -> DatabaseConnection:
        """Merge-update an existing :py:class:`DatabaseConnection` entry.

        Validation rules:

        * Updates to the ``default`` connection (by id **or** name) are
          rejected.
        * ``raw_secret`` must **not** be set; to rotate credentials use
          :py:class:`ISecretManager` directly and then call this method
          with the new secret id.
        * ``database_connection.id`` must be set and must reference an
          existing record.

        The method performs a MERGE update so only the non-``None`` fields
        supplied in *database_connection* are written.

        If a :py:class:`IDatabaseProvider` for the same id is already
        registered in the cache, it is replaced with a newly created
        provider that uses the updated configuration.

        Args:
            database_connection: Updated connection data. ``id`` is required.

        Returns:
            The updated :py:class:`DatabaseConnection` as returned by the
            database.

        Raises:
            DatabaseManagerNotInitializedException: Phase-3 init not done.
            DatabaseManagerInvalidOperationException: Target is the default
                connection, or ``raw_secret`` is present.
            DatabaseManagerConnectionNotFoundException: No record exists
                for the given id.
            DatabaseManagerSecretNotFoundException: The ``secret`` id does
                not reference an existing secret.
        """
        pass

    @abstractmethod
    async def get_connection(self, id: str) -> DatabaseConnection | None:
        """Retrieve a :py:class:`DatabaseConnection` entry by its record id.

        Args:
            id: Record id to look up.

        Returns:
            The matching :py:class:`DatabaseConnection`, or ``None`` if the
            record does not exist.
        """
        pass

    @abstractmethod
    async def get_connection_by_name(self, name: str) -> DatabaseConnection | None:
        """Retrieve a :py:class:`DatabaseConnection` entry by its ``name``.

        Args:
            name: The unique name to search for.

        Returns:
            The matching :py:class:`DatabaseConnection`, or ``None`` if no
            record has that name.
        """
        pass

    @abstractmethod
    async def delete_connection(self, id: str) -> None:
        """Delete a :py:class:`DatabaseConnection` entry.

        If a :py:class:`IDatabaseProvider` for the specified id is cached,
        it is closed and removed from the registry before the database
        record is deleted.

        Args:
            id: Record id of the connection to delete.

        Raises:
            DatabaseManagerInvalidOperationException: *id* is ``"default"``.
            DatabaseManagerConnectionNotFoundException: No record exists
                for the given id.
        """
        pass

    # ------------------------------------------------------------------
    # Provider access
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_provider(self, id: str) -> IDatabaseProvider:
        """Return the :py:class:`IDatabaseProvider` for a connection id.

        If the provider is already cached it is returned immediately.
        If *id* is ``"default"``, :py:meth:`get_default_provider` is
        called internally.

        Otherwise the provider is created on demand:

        1. Load the :py:class:`DatabaseConnection` from the ``databases``
           collection; raise
           :py:exc:`DatabaseManagerConnectionNotFoundException` if absent.
        2. If the connection has a ``secret``, retrieve it via
           :py:class:`ISecretManager`; raise
           :py:exc:`DatabaseManagerSecretNotFoundException` if absent.
        3. Build connection parameters by merging
           ``parameters`` with the secret's ``secret`` dict
           (secret values take precedence).
        4. Construct a :py:class:`DatabaseProviderOptions` subclass from
           the merged dict using the ``database_type`` value.
        5. Initialise a new :py:class:`IDatabaseProvider`, cache it, and
           return it.

        Args:
            id: Record id of the :py:class:`DatabaseConnection`.

        Returns:
            The corresponding :py:class:`IDatabaseProvider` instance.

        Raises:
            DatabaseManagerNotInitializedException: Phase-3 init not done
                (for non-default providers).
            DatabaseManagerConnectionNotFoundException: No connection record
                for the given id, or the default provider is not registered.
            DatabaseManagerSecretNotFoundException: The required secret does
                not exist.
        """
        pass

    @abstractmethod
    def get_default_provider(self) -> IDatabaseProvider:
        """Return the default :py:class:`IDatabaseProvider` synchronously.

        The default provider is registered during
        :py:meth:`initialize_default_connection`. This method exists as a
        synchronous shortcut to avoid ``await`` in callers that only need
        the default database.

        Returns:
            The default :py:class:`IDatabaseProvider` instance.

        Raises:
            DatabaseManagerConnectionNotFoundException: The default provider
                has not been registered (phase-1 init not done).
        """
        pass

