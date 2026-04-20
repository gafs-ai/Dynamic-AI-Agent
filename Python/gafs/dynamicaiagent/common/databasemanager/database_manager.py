"""database_manager.py - Concrete implementation of IDatabaseManager."""

from __future__ import annotations

import logging
from logging import Logger
from typing import TYPE_CHECKING, Any

from gafs.dynamicaiagent.utils.databaseprovider import (
    DatabaseProviderType,
    IDatabaseProvider,
    SurrealDbLocalProvider,
    SurrealDbRemoteProvider,
)
from gafs.dynamicaiagent.utils.databaseprovider import LocalSurrealDbOptions, RemoteSurrealDbOptions
from gafs.dynamicaiagent.utils.databaseprovider.exceptions import DatabaseRecordNotFoundException

from .exceptions import (
    DatabaseManagerAnalyzerNotFoundException,
    DatabaseManagerAnalyzerOperationException,
    DatabaseManagerConflictingAnalyzerException,
    DatabaseManagerConflictingConnectionException,
    DatabaseManagerConnectionNotFoundException,
    DatabaseManagerInitializationException,
    DatabaseManagerInvalidAnalyzerException,
    DatabaseManagerInvalidDatabaseConnectionEntryException,
    DatabaseManagerInvalidOperationException,
    DatabaseManagerNotInitializedException,
    DatabaseManagerOperationException,
    DatabaseManagerSecretNotFoundException,
)
from .i_database_manager import IDatabaseManager
from .models import DatabaseConnection, FullTextAnalyzer

if TYPE_CHECKING:
    from gafs.dynamicaiagent.common.secretmanager import ISecretManager


class DatabaseManager(IDatabaseManager):
    """Concrete implementation of IDatabaseManager.

    Manages database providers, connection configurations, and full-text analyzer definitions.
    Follows a three-phase initialization sequence to handle the mutual dependency with
    SecretManager.

    Phase 1 (initialize_default_connection): establishes the default DB connection.
    Phase 2: SecretManager initializes using this DatabaseManager.
    Phase 3 (initialize): registers the SecretManager to enable secret-aware operations.
    """

    def __init__(self, logger: Logger) -> None:
        """Initialize DatabaseManager with a logger.

        All internal state starts as None/empty. Call initialize_default_connection()
        to begin the initialization sequence.

        Args:
            logger: Logger instance for this component.
        """
        # Logger for this instance
        self._logger: Logger = logger

        # The default database provider, set during phase-1 initialization
        self._default_provider: IDatabaseProvider | None = None

        # Cache of non-default providers keyed by connection id
        self._providers: dict[str, IDatabaseProvider] = {}

        # SecretManager reference, set during phase-3 initialization
        self._secret_manager: Any | None = None

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    def _get_default_provider_or_raise(self) -> IDatabaseProvider:
        """Return the default provider, raising if not yet initialized.

        Returns:
            The default IDatabaseProvider instance.

        Raises:
            DatabaseManagerNotInitializedException: If phase-1 has not been completed.
        """
        if self._default_provider is None:
            raise DatabaseManagerNotInitializedException(
                "Default database provider is not initialized. "
                "Call initialize_default_connection() first."
            )
        return self._default_provider

    def _check_phase3_or_raise(self) -> None:
        """Raise if phase-3 initialization has not been completed.

        Raises:
            DatabaseManagerNotInitializedException: If _secret_manager is None.
        """
        if self._secret_manager is None:
            raise DatabaseManagerNotInitializedException(
                "DatabaseManager is not fully initialized (phase-3 incomplete). "
                "Call initialize(secret_manager) first."
            )

    async def _create_provider(
        self, config: DatabaseConnection
    ) -> IDatabaseProvider:
        """Build and initialize an IDatabaseProvider from a DatabaseConnection config.

        Merges parameters with raw_secret (if present) to construct the options.
        For non-default connections with a secret reference, use _create_provider_from_connection
        instead to load the secret via ISecretManager.

        Args:
            config: DatabaseConnection with database_type, parameters, and optionally raw_secret.

        Returns:
            Initialized IDatabaseProvider.

        Raises:
            DatabaseManagerInitializationException: If options construction or initialization fails.
        """
        # Merge parameters with raw_secret credentials
        params: dict[str, Any] = dict(config.parameters or {})
        if config.raw_secret:
            # raw_secret values take precedence over parameters
            params.update(config.raw_secret)

        try:
            # Construct the appropriate options class from the merged parameter dict
            if config.database_type == DatabaseProviderType.SURREALDB_REMOTE:
                options = RemoteSurrealDbOptions.from_dict(params)
                provider: IDatabaseProvider = SurrealDbRemoteProvider(self._logger)
            elif config.database_type == DatabaseProviderType.SURREALDB_LOCAL:
                options = LocalSurrealDbOptions.from_dict(params)
                provider = SurrealDbLocalProvider(self._logger)
            else:
                raise DatabaseManagerInitializationException(
                    f"Unsupported database_type: {config.database_type}"
                )
        except DatabaseManagerInitializationException:
            raise
        except Exception as e:
            self._logger.error(f"Failed to build provider options: {e}")
            raise DatabaseManagerInitializationException(
                f"Failed to build database provider options: {e}", cause=e
            )

        try:
            await provider.initialize(options)
        except Exception as e:
            self._logger.error(f"Failed to initialize database provider: {e}")
            raise DatabaseManagerInitializationException(
                f"Failed to initialize database provider: {e}", cause=e
            )

        return provider

    async def _create_provider_from_connection(
        self, connection: DatabaseConnection
    ) -> IDatabaseProvider:
        """Build and initialize an IDatabaseProvider for a non-default connection.

        Loads the secret from ISecretManager if a secret id is set, then merges
        the secret credentials into the connection parameters.

        Args:
            connection: DatabaseConnection entry (loaded from database).

        Returns:
            Initialized IDatabaseProvider.

        Raises:
            DatabaseManagerSecretNotFoundException: If the referenced secret is not found.
            DatabaseManagerOperationException: If secret retrieval or provider creation fails.
        """
        params: dict[str, Any] = dict(connection.parameters or {})

        # Load secret credentials from SecretManager if a secret is referenced
        if connection.secret and self._secret_manager is not None:
            try:
                secret = await self._secret_manager.get_secret(connection.secret)
                # Merge secret's raw credentials dict — secret values take precedence
                secret_data: dict[str, Any] = {}
                if hasattr(secret, "secret") and isinstance(secret.secret, dict):
                    secret_data = secret.secret
                elif hasattr(secret, "raw_secret") and isinstance(secret.raw_secret, dict):
                    secret_data = secret.raw_secret
                params.update(secret_data)
            except DatabaseRecordNotFoundException as e:
                raise DatabaseManagerSecretNotFoundException(
                    f"Secret '{connection.secret}' referenced by connection not found.",
                    cause=e,
                )
            except DatabaseManagerSecretNotFoundException:
                raise
            except Exception as e:
                self._logger.error(f"Failed to retrieve secret '{connection.secret}': {e}")
                raise DatabaseManagerOperationException(
                    f"Failed to retrieve secret for connection: {e}", cause=e
                )

        # Build the options and initialize the provider
        try:
            if connection.database_type == DatabaseProviderType.SURREALDB_REMOTE:
                options = RemoteSurrealDbOptions.from_dict(params)
                provider: IDatabaseProvider = SurrealDbRemoteProvider(self._logger)
            elif connection.database_type == DatabaseProviderType.SURREALDB_LOCAL:
                options = LocalSurrealDbOptions.from_dict(params)
                provider = SurrealDbLocalProvider(self._logger)
            else:
                raise DatabaseManagerOperationException(
                    f"Unsupported database_type: {connection.database_type}"
                )
        except (DatabaseManagerOperationException, DatabaseManagerSecretNotFoundException):
            raise
        except Exception as e:
            self._logger.error(f"Failed to build provider options for connection '{connection.id}': {e}")
            raise DatabaseManagerOperationException(
                f"Failed to build provider options: {e}", cause=e
            )

        try:
            await provider.initialize(options)
        except Exception as e:
            self._logger.error(f"Failed to initialize provider for connection '{connection.id}': {e}")
            raise DatabaseManagerOperationException(
                f"Failed to initialize database provider: {e}", cause=e
            )

        return provider

    async def _close_and_deregister_provider(self, provider_id: str) -> None:
        """Close and remove a provider from the cache.

        If closing fails, the failure is logged at WARNING level but no exception is raised.

        Args:
            provider_id: The connection id whose provider should be removed.
        """
        provider = self._providers.pop(provider_id, None)
        if provider is not None:
            try:
                await provider.close()
            except Exception as e:
                # Log at WARNING level — closing failure must not propagate
                self._logger.warning(
                    f"Failed to close provider for connection '{provider_id}': {e}"
                )

    async def _rebuild_indexes_for_analyzer(self, analyzer_name: str) -> None:
        """Rebuild all full-text search indexes that reference the given analyzer.

        Queries SurrealDB's INFO FOR DB and INFO FOR TABLE to find all indexes
        referencing the analyzer, then issues REBUILD INDEX for each one.

        If rebuilding fails for any index, it is logged at WARNING level but no exception is raised.

        Args:
            analyzer_name: Name of the analyzer whose referencing indexes should be rebuilt.
        """
        provider = self._get_default_provider_or_raise()

        try:
            # Retrieve database-level info to get all table names
            db_info = await provider.query_raw("INFO FOR DB;")
            if not db_info or not isinstance(db_info, dict):
                return

            tables = db_info.get("tables", {})
            if not tables:
                return

            # Check each table's indexes for references to the analyzer
            for table_name in list(tables.keys()):
                try:
                    table_info = await provider.query_raw(f"INFO FOR TABLE `{table_name}`;")
                    if not table_info or not isinstance(table_info, dict):
                        continue

                    indexes = table_info.get("indexes", {})
                    for index_name, index_def in indexes.items():
                        # Check if the index definition references this analyzer
                        if isinstance(index_def, str) and f"ANALYZER {analyzer_name}" in index_def:
                            try:
                                await provider.query_raw(
                                    f"REBUILD INDEX IF EXISTS `{index_name}` ON `{table_name}`;"
                                )
                                self._logger.info(
                                    f"Rebuilt index '{index_name}' on '{table_name}' "
                                    f"for analyzer '{analyzer_name}'."
                                )
                            except Exception as rebuild_err:
                                self._logger.warning(
                                    f"Failed to rebuild index '{index_name}' on '{table_name}': {rebuild_err}"
                                )
                except Exception as table_err:
                    self._logger.warning(
                        f"Failed to get info for table '{table_name}': {table_err}"
                    )
        except Exception as e:
            self._logger.warning(f"Failed to query DB info for analyzer rebuild: {e}")

    def _build_default_connection_entry(self, config: DatabaseConnection) -> DatabaseConnection:
        """Build the stripped-down default DatabaseConnection entry for persistence.

        Only id, name, description, and database_type are kept — secrets and
        connection parameters are never saved.

        Args:
            config: Full connection configuration.

        Returns:
            A DatabaseConnection with only the safe fields set.
        """
        entry = DatabaseConnection()
        entry.id = IDatabaseManager.DEFAULT_DATABASE_NAME()
        entry.name = IDatabaseManager.DEFAULT_DATABASE_NAME()
        if config.description is not None:
            entry.description = config.description
        if config.database_type is not None:
            entry.database_type = config.database_type
        return entry

    # ---------------------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------------------

    async def initialize_default_connection(self, config: DatabaseConnection) -> bool:
        """Phase-1 initialization: connect to the default database.

        Steps:
            1. Validate and normalize the config.
            2. Create the default IDatabaseProvider.
            3. Define default full-text analyzers (default_ngram_analyzer, default_english_analyzer).
            4. Set up the FullTextAnalyzers collection indexes.
            5. Upsert the 'default' entry in DatabaseConnections (only safe fields saved).
            6. Set up the DatabaseConnections collection indexes.

        Args:
            config: Configuration for the default database connection.

        Returns:
            True on success.

        Raises:
            DatabaseManagerInitializationException: If any step fails.
        """
        # --- Step 1: Validate the config ---
        if config.database_type is None:
            raise DatabaseManagerInitializationException(
                "initialize_default_connection: database_type is required."
            )
        if not config.parameters and not config.raw_secret:
            raise DatabaseManagerInitializationException(
                "initialize_default_connection: parameters or raw_secret must be provided."
            )

        # --- Step 2: Create the default provider and register it ---
        self._logger.info("Initializing default database connection...")
        try:
            provider = await self._create_provider(config)
        except DatabaseManagerInitializationException:
            raise
        except Exception as e:
            raise DatabaseManagerInitializationException(
                f"Failed to create default provider: {e}", cause=e
            )

        # Register the default provider before any database operations
        self._default_provider = provider
        self._logger.info("Default database provider initialized.")

        # --- Step 3: Define default analyzers (required before FULL TEXT indexes) ---
        try:
            ngram = FullTextAnalyzer.DEFAULT_ANALYZER()
            english = FullTextAnalyzer.DEFAULT_ENGLISH_ANALYZER()

            # Define each default analyzer using IF NOT EXISTS to be idempotent
            await provider.query_raw(ngram.get_define_analyzer_statement(overwrite=False))
            await provider.query_raw(english.get_define_analyzer_statement(overwrite=False))
            self._logger.info("Default analyzers defined (or already exist).")
        except Exception as e:
            self._logger.error(f"Failed to define default analyzers: {e}")
            raise DatabaseManagerInitializationException(
                f"Failed to define default analyzers: {e}", cause=e
            )

        # --- Step 4: Set up FullTextAnalyzers collection (index on name) ---
        try:
            coll_fa = FullTextAnalyzer.COLLECTION_NAME()
            await provider.query_raw(
                f"DEFINE INDEX IF NOT EXISTS fa_name_unique "
                f"ON {coll_fa} FIELDS name UNIQUE;"
            )
            await provider.query_raw(
                f"DEFINE INDEX IF NOT EXISTS fa_name_search "
                f"ON {coll_fa} FIELDS name "
                f"SEARCH ANALYZER {FullTextAnalyzer.DEFAULT_ANALYZER().name} BM25 HIGHLIGHTS;"
            )
            self._logger.info("FullTextAnalyzers indexes ensured.")
        except Exception as e:
            self._logger.error(f"Failed to set up FullTextAnalyzers indexes: {e}")
            raise DatabaseManagerInitializationException(
                f"Failed to set up FullTextAnalyzers indexes: {e}", cause=e
            )

        # Also upsert the default analyzer entries into the FullTextAnalyzers collection
        try:
            await self._upsert_default_analyzer_entries(provider)
        except Exception as e:
            # Non-fatal — log and continue; catalog entries are informational
            self._logger.warning(f"Failed to upsert default analyzer catalog entries: {e}")

        # --- Step 5: Upsert the 'default' entry in DatabaseConnections ---
        try:
            coll_dc = DatabaseConnection.COLLECTION_NAME()
            default_id = IDatabaseManager.DEFAULT_DATABASE_NAME()
            entry = self._build_default_connection_entry(config)

            # Try to read existing entry
            existing = await provider.query_raw(
                f"SELECT * FROM {coll_dc}:{default_id};"
            )
            existing_entry: dict[str, Any] | None = None
            if isinstance(existing, list) and existing:
                existing_entry = existing[0] if isinstance(existing[0], dict) else None
            elif isinstance(existing, dict):
                existing_entry = existing

            if existing_entry is None:
                # First run — create the entry using inline JSON content
                content_json = entry.to_json()
                await provider.query_raw(
                    f"CREATE {coll_dc}:{default_id} CONTENT {content_json};"
                )
                self._logger.info("Created default DatabaseConnections entry.")
            else:
                # Entry exists — overwrite with current safe fields
                import json as _json_init
                update_dict = entry.to_dict(recursive=True, exclude_id=True)
                update_json = _json_init.dumps(update_dict)
                await provider.query_raw(
                    f"UPDATE {coll_dc}:{default_id} MERGE {update_json};"
                )
                self._logger.info("Updated default DatabaseConnections entry.")
        except Exception as e:
            self._logger.error(f"Failed to upsert default DatabaseConnections entry: {e}")
            raise DatabaseManagerInitializationException(
                f"Failed to upsert default DatabaseConnections entry: {e}", cause=e
            )

        # --- Step 6: Set up DatabaseConnections collection indexes ---
        try:
            coll_dc = DatabaseConnection.COLLECTION_NAME()
            ngram_name = FullTextAnalyzer.DEFAULT_ANALYZER().name
            english_name = FullTextAnalyzer.DEFAULT_ENGLISH_ANALYZER().name

            await provider.query_raw(
                f"DEFINE INDEX IF NOT EXISTS dc_name_unique "
                f"ON {coll_dc} FIELDS name UNIQUE;"
            )
            await provider.query_raw(
                f"DEFINE INDEX IF NOT EXISTS dc_name_search "
                f"ON {coll_dc} FIELDS name "
                f"SEARCH ANALYZER {ngram_name} BM25 HIGHLIGHTS;"
            )
            await provider.query_raw(
                f"DEFINE INDEX IF NOT EXISTS dc_description_search "
                f"ON {coll_dc} FIELDS description "
                f"SEARCH ANALYZER {english_name} BM25 HIGHLIGHTS;"
            )
            self._logger.info("DatabaseConnections indexes ensured.")
        except Exception as e:
            self._logger.error(f"Failed to set up DatabaseConnections indexes: {e}")
            raise DatabaseManagerInitializationException(
                f"Failed to set up DatabaseConnections indexes: {e}", cause=e
            )

        self._logger.info("Phase-1 initialization completed.")
        return True

    async def _upsert_default_analyzer_entries(self, provider: IDatabaseProvider) -> None:
        """Insert default analyzer catalog entries if they don't already exist.

        Args:
            provider: The default database provider to use.
        """
        coll = FullTextAnalyzer.COLLECTION_NAME()
        for analyzer in [FullTextAnalyzer.DEFAULT_ANALYZER(), FullTextAnalyzer.DEFAULT_ENGLISH_ANALYZER()]:
            existing = await provider.query_raw(f"SELECT * FROM {coll}:{analyzer.id};")
            entry_exists = (
                isinstance(existing, list) and bool(existing)
            ) or (
                isinstance(existing, dict) and bool(existing)
            )
            if not entry_exists:
                content_json = analyzer.to_json(recursive=True, exclude_id=True)
                await provider.query_raw(
                    f"CREATE {coll}:{analyzer.id} CONTENT {content_json};"
                )

    async def initialize(self, secret_manager: "ISecretManager") -> bool:
        """Phase-3 initialization: register the ISecretManager.

        Args:
            secret_manager: Already-initialized SecretManager instance.

        Returns:
            True on success.

        Raises:
            DatabaseManagerInitializationException: If initialization fails.
        """
        if secret_manager is None:
            raise DatabaseManagerInitializationException(
                "initialize: secret_manager must not be None."
            )

        # Store the ISecretManager reference for later use
        self._secret_manager = secret_manager
        self._logger.info("Phase-3 initialization completed (SecretManager registered).")
        return True

    # ---------------------------------------------------------------------------
    # Connection catalogue
    # ---------------------------------------------------------------------------

    async def create_connection(
        self, connection_configurations: DatabaseConnection
    ) -> DatabaseConnection:
        """Create a new DatabaseConnection entry in the DatabaseConnections collection.

        Args:
            connection_configurations: Connection data. Set either secret or raw_secret, not both.

        Returns:
            Persisted entry (raw_secret excluded).

        Raises:
            DatabaseManagerNotInitializedException: Not fully initialized.
            DatabaseManagerInvalidDatabaseConnectionEntryException: Entry is invalid.
            DatabaseManagerConflictingConnectionException: id already exists.
            DatabaseManagerSecretNotFoundException: secret id not found.
            DatabaseManagerOperationException: Database failure.
        """
        # --- Step 1: Validate the connection entry ---
        if not connection_configurations.name:
            raise DatabaseManagerInvalidDatabaseConnectionEntryException(
                "DatabaseConnection.name is required."
            )
        if connection_configurations.database_type is None:
            raise DatabaseManagerInvalidDatabaseConnectionEntryException(
                "DatabaseConnection.database_type is required."
            )
        if connection_configurations.secret and connection_configurations.raw_secret:
            raise DatabaseManagerInvalidDatabaseConnectionEntryException(
                "DatabaseConnection must not have both secret and raw_secret set simultaneously."
            )

        # --- Step 2: Get the default provider (requires phase 3 check) ---
        self._check_phase3_or_raise()
        provider = self._get_default_provider_or_raise()
        coll = DatabaseConnection.COLLECTION_NAME()

        # --- Step 3: Check for id conflict if id is provided ---
        if connection_configurations.id:
            try:
                existing = await self.get_connection(connection_configurations.id)
                if existing is not None:
                    raise DatabaseManagerConflictingConnectionException(
                        f"A DatabaseConnection with id '{connection_configurations.id}' already exists."
                    )
            except DatabaseManagerConflictingConnectionException:
                raise
            except DatabaseManagerOperationException:
                raise
            except Exception as e:
                raise DatabaseManagerOperationException(
                    f"Failed to check id conflict: {e}", cause=e
                )

        # --- Step 4/5: Handle secret or raw_secret ---
        if connection_configurations.secret:
            # Verify the referenced secret exists
            try:
                await self._secret_manager.get_secret(connection_configurations.secret)
            except DatabaseRecordNotFoundException as e:
                raise DatabaseManagerSecretNotFoundException(
                    f"Secret '{connection_configurations.secret}' not found.", cause=e
                )
            except Exception as e:
                self._logger.error(f"Failed to verify secret existence: {e}")
                raise DatabaseManagerSecretNotFoundException(
                    f"Secret '{connection_configurations.secret}' not found or inaccessible.",
                    cause=e,
                )
        elif connection_configurations.raw_secret:
            # Create a new Secret entry via SecretManager
            try:
                # Build a minimal Secret object with the raw credentials
                secret_obj = self._build_secret_for_connection(connection_configurations.raw_secret)
                created_secret = await self._secret_manager.create_secret(secret_obj)
                # Store the secret id and clear raw_secret
                object.__setattr__(connection_configurations, "secret", created_secret.id)
                object.__setattr__(connection_configurations, "raw_secret", None)
            except Exception as e:
                self._logger.error(f"Failed to create secret for connection: {e}")
                raise DatabaseManagerOperationException(
                    f"Failed to create secret for connection: {e}", cause=e
                )

        # --- Step 6: Save the connection entry to the database ---
        try:
            # Serialize without raw_secret (always excluded by to_dict)
            entry_dict = connection_configurations.to_dict(recursive=True)
            entry_json = connection_configurations.to_json()

            if connection_configurations.id:
                # Use the specified id
                result = await provider.query_raw(
                    f"CREATE {coll}:{connection_configurations.id} CONTENT {entry_json};"
                )
            else:
                # Let the database assign the id
                result = await provider.query_raw(
                    f"CREATE {coll} CONTENT {entry_json};"
                )

            # Parse the result and return the created entry
            created = self._parse_single_result(result)
            if created is None:
                raise DatabaseManagerOperationException(
                    "CREATE returned no result."
                )
            return DatabaseConnection.from_dict(created)
        except (DatabaseManagerOperationException, DatabaseManagerConflictingConnectionException):
            raise
        except Exception as e:
            self._logger.error(f"Failed to create DatabaseConnection entry: {e}")
            raise DatabaseManagerOperationException(
                f"Failed to create DatabaseConnection entry: {e}", cause=e
            )

    def _build_secret_for_connection(self, raw_secret: dict[str, Any]) -> Any:
        """Build a Secret object from a raw credentials dict.

        Attempts to import the Secret class from the secretmanager package.
        Falls back to a simple namespace object if the package is not available.

        Args:
            raw_secret: Raw credential key-value pairs.

        Returns:
            A Secret-compatible object with the credentials set.
        """
        try:
            # Try to import the actual Secret model
            from gafs.dynamicaiagent.common.secretmanager import Secret as SecretModel
            s = SecretModel()
            # Set the secret field (or raw_secret depending on the Secret model design)
            if hasattr(s, "secret"):
                s.secret = raw_secret
            elif hasattr(s, "raw_secret"):
                s.raw_secret = raw_secret
            return s
        except ImportError:
            # Fallback: create a simple namespace object with the right attributes
            class _SimpleSecret:
                def __init__(self, credentials: dict[str, Any]) -> None:
                    self.secret = credentials
                    self.raw_secret = credentials
            return _SimpleSecret(raw_secret)

    def _parse_single_result(self, result: Any) -> dict[str, Any] | None:
        """Extract a single record dict from a SurrealDB query result.

        Args:
            result: Raw query result from IDatabaseProvider.query_raw.

        Returns:
            The first record dict, or None if no records.
        """
        if isinstance(result, list):
            return result[0] if result and isinstance(result[0], dict) else None
        if isinstance(result, dict):
            return result
        return None

    def _parse_list_result(self, result: Any) -> list[dict[str, Any]]:
        """Extract a list of record dicts from a SurrealDB query result.

        Args:
            result: Raw query result from IDatabaseProvider.query_raw.

        Returns:
            List of record dicts (empty list if no records).
        """
        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict)]
        if isinstance(result, dict):
            return [result]
        return []

    async def update_connection(
        self, database_connection: DatabaseConnection
    ) -> DatabaseConnection:
        """Merge-update an existing DatabaseConnection entry.

        Only non-None fields are written. Updates to the 'default' connection are rejected.
        If a cached provider exists for the same id, it is replaced.

        Args:
            database_connection: Updated connection data. id is required. raw_secret must not be set.

        Returns:
            Updated entry.

        Raises:
            DatabaseManagerNotInitializedException: Not fully initialized.
            DatabaseManagerInvalidDatabaseConnectionEntryException: Entry is invalid.
            DatabaseManagerInvalidOperationException: Target is the default connection.
            DatabaseManagerConnectionNotFoundException: No record for the given id.
            DatabaseManagerSecretNotFoundException: secret id not found.
            DatabaseManagerOperationException: Database failure.
        """
        default_name = IDatabaseManager.DEFAULT_DATABASE_NAME()

        # --- Step 1: Validate ---
        if not database_connection.id:
            raise DatabaseManagerInvalidDatabaseConnectionEntryException(
                "DatabaseConnection.id is required for update."
            )
        if database_connection.id == default_name or database_connection.name == default_name:
            raise DatabaseManagerInvalidOperationException(
                "Updating the 'default' connection is not allowed."
            )
        if database_connection.raw_secret:
            raise DatabaseManagerInvalidDatabaseConnectionEntryException(
                "DatabaseConnection.raw_secret must not be set during update. "
                "Update the Secret entry directly via SecretManager instead."
            )

        # --- Step 2: Get the default provider ---
        self._check_phase3_or_raise()
        provider = self._get_default_provider_or_raise()
        coll = DatabaseConnection.COLLECTION_NAME()
        conn_id = database_connection.id

        # --- Step 3: Verify the original entry exists ---
        try:
            original = await self.get_connection(conn_id)
        except DatabaseManagerOperationException:
            raise
        except Exception as e:
            raise DatabaseManagerOperationException(
                f"Failed to retrieve original connection '{conn_id}': {e}", cause=e
            )
        if original is None:
            raise DatabaseManagerConnectionNotFoundException(
                f"DatabaseConnection '{conn_id}' not found."
            )

        # --- Step 4: Validate new secret if updating secret reference ---
        if database_connection.secret is not None and database_connection.secret != original.secret:
            try:
                await self._secret_manager.get_secret(database_connection.secret)
            except DatabaseRecordNotFoundException as e:
                raise DatabaseManagerSecretNotFoundException(
                    f"Secret '{database_connection.secret}' not found.", cause=e
                )
            except Exception as e:
                raise DatabaseManagerSecretNotFoundException(
                    f"Secret '{database_connection.secret}' not found or inaccessible.", cause=e
                )

        # --- Step 5: Update the DatabaseConnection entry ---
        try:
            # Build the update payload — only include non-None fields, never raw_secret
            update_dict = database_connection.to_dict(recursive=True, exclude_id=True)
            import json as _json
            update_json = _json.dumps(update_dict)
            result = await provider.query_raw(
                f"UPDATE {coll}:{conn_id} MERGE {update_json} RETURN AFTER;"
            )
            updated_data = self._parse_single_result(result)
            if updated_data is None:
                raise DatabaseManagerOperationException(
                    "UPDATE returned no result."
                )
            updated = DatabaseConnection.from_dict(updated_data)
        except (DatabaseManagerOperationException, DatabaseManagerInvalidOperationException):
            raise
        except Exception as e:
            self._logger.error(f"Failed to update DatabaseConnection '{conn_id}': {e}")
            raise DatabaseManagerOperationException(
                f"Failed to update DatabaseConnection '{conn_id}': {e}", cause=e
            )

        # --- Step 6: Replace the cached provider if one exists for this id ---
        if conn_id in self._providers:
            old_provider = self._providers.pop(conn_id)
            try:
                # Attempt to create a new provider with updated configuration
                new_provider = await self._create_provider_from_connection(updated)
                self._providers[conn_id] = new_provider
                self._logger.info(
                    f"Provider for connection '{conn_id}' replaced after update."
                )
            except Exception as e:
                self._logger.warning(
                    f"Failed to create new provider for '{conn_id}' after update: {e}. "
                    f"Provider deregistered."
                )
            # Close the old provider regardless
            try:
                await old_provider.close()
            except Exception as e:
                self._logger.warning(
                    f"Failed to close old provider for '{conn_id}': {e}"
                )

        return updated

    async def get_connection(self, id: str) -> DatabaseConnection | None:
        """Retrieve a DatabaseConnection entry by record id.

        Args:
            id: Record id to look up.

        Returns:
            Matching entry, or None if not found.

        Raises:
            DatabaseManagerNotInitializedException: Not fully initialized.
            DatabaseManagerOperationException: Database query failure.
        """
        self._check_phase3_or_raise()
        provider = self._get_default_provider_or_raise()
        coll = DatabaseConnection.COLLECTION_NAME()

        try:
            result = await provider.query_raw(f"SELECT * FROM {coll}:{id};")
            data = self._parse_single_result(result)
            if data is None:
                return None
            return DatabaseConnection.from_dict(data)
        except Exception as e:
            self._logger.error(f"Failed to get DatabaseConnection '{id}': {e}")
            raise DatabaseManagerOperationException(
                f"Failed to get DatabaseConnection '{id}': {e}", cause=e
            )

    async def get_all_connections(self) -> list[DatabaseConnection]:
        """Retrieve all DatabaseConnection entries.

        Returns:
            All entries as a list (empty list if none found).

        Raises:
            DatabaseManagerNotInitializedException: Not fully initialized.
            DatabaseManagerOperationException: Database query failure.
        """
        self._check_phase3_or_raise()
        provider = self._get_default_provider_or_raise()
        coll = DatabaseConnection.COLLECTION_NAME()

        try:
            result = await provider.query_raw(f"SELECT * FROM {coll};")
            records = self._parse_list_result(result)
            return [DatabaseConnection.from_dict(r) for r in records]
        except Exception as e:
            self._logger.error(f"Failed to get all DatabaseConnections: {e}")
            raise DatabaseManagerOperationException(
                f"Failed to get all DatabaseConnections: {e}", cause=e
            )

    async def get_connections_by_name(
        self, name: str, ambiguous: bool = False
    ) -> list[DatabaseConnection]:
        """Retrieve DatabaseConnection entries by name.

        Args:
            name: Connection name to search for.
            ambiguous: If True, use full-text (contains) search. If False, use exact match.

        Returns:
            Matching entries as a list (empty list if none found).

        Raises:
            DatabaseManagerNotInitializedException: Not fully initialized.
            DatabaseManagerOperationException: Database query failure.
        """
        self._check_phase3_or_raise()
        provider = self._get_default_provider_or_raise()
        coll = DatabaseConnection.COLLECTION_NAME()

        try:
            if ambiguous:
                # Use full-text search (@@) for partial name matching
                import json as _json
                query = f"SELECT * FROM {coll} WHERE name @@ {_json.dumps(name)};"
            else:
                # Use exact name match
                import json as _json
                query = f"SELECT * FROM {coll} WHERE name = {_json.dumps(name)};"

            result = await provider.query_raw(query)
            records = self._parse_list_result(result)
            return [DatabaseConnection.from_dict(r) for r in records]
        except Exception as e:
            self._logger.error(f"Failed to get DatabaseConnections by name '{name}': {e}")
            raise DatabaseManagerOperationException(
                f"Failed to get DatabaseConnections by name: {e}", cause=e
            )

    async def delete_connection(self, id: str) -> None:
        """Delete a DatabaseConnection entry and close any cached provider.

        Deletion of the 'default' connection is rejected.

        Args:
            id: Record id of the connection to delete.

        Raises:
            DatabaseManagerNotInitializedException: Not fully initialized.
            DatabaseManagerInvalidOperationException: id is 'default'.
            DatabaseManagerConnectionNotFoundException: No record for the given id.
            DatabaseManagerOperationException: Database query failure.
        """
        # Reject deletion of the default connection
        if id == IDatabaseManager.DEFAULT_DATABASE_NAME():
            raise DatabaseManagerInvalidOperationException(
                "Deletion of the 'default' connection is not allowed."
            )

        self._check_phase3_or_raise()
        provider = self._get_default_provider_or_raise()
        coll = DatabaseConnection.COLLECTION_NAME()

        # Verify the entry exists before deletion
        try:
            existing = await self.get_connection(id)
        except DatabaseManagerOperationException:
            raise
        except Exception as e:
            raise DatabaseManagerOperationException(
                f"Failed to check existence of connection '{id}': {e}", cause=e
            )
        if existing is None:
            raise DatabaseManagerConnectionNotFoundException(
                f"DatabaseConnection '{id}' not found."
            )

        # Close and deregister the cached provider (if any)
        if id in self._providers:
            await self._close_and_deregister_provider(id)

        # Delete the database record
        try:
            await provider.query_raw(f"DELETE {coll}:{id};")
            self._logger.info(f"DatabaseConnection '{id}' deleted.")
        except Exception as e:
            self._logger.error(f"Failed to delete DatabaseConnection '{id}': {e}")
            raise DatabaseManagerOperationException(
                f"Failed to delete DatabaseConnection '{id}': {e}", cause=e
            )

    # ---------------------------------------------------------------------------
    # Analyzer catalogue
    # ---------------------------------------------------------------------------

    async def create_analyzer(self, analyzer: FullTextAnalyzer) -> FullTextAnalyzer:
        """Create a new FullTextAnalyzer entry and define the analyzer on the database.

        Args:
            analyzer: Analyzer definition to create.

        Returns:
            Created entry.

        Raises:
            DatabaseManagerNotInitializedException: Not initialized.
            DatabaseManagerConflictingAnalyzerException: name or id conflicts.
            DatabaseManagerInvalidAnalyzerException: Validation failure.
            DatabaseManagerAnalyzerOperationException: DB operation fails.
        """
        # --- Step 1: Validate ---
        try:
            analyzer.validate_and_normalize()
        except DatabaseManagerInvalidAnalyzerException:
            raise
        except Exception as e:
            raise DatabaseManagerInvalidAnalyzerException(
                f"Analyzer validation failed: {e}", cause=e
            )

        # --- Step 2: Get default provider ---
        provider = self._get_default_provider_or_raise()
        coll = FullTextAnalyzer.COLLECTION_NAME()

        # --- Check for id conflict if id is provided ---
        if analyzer.id:
            try:
                existing_id = await self.get_analyzer(analyzer.id)
                if existing_id is not None:
                    raise DatabaseManagerConflictingAnalyzerException(
                        f"A FullTextAnalyzer with id '{analyzer.id}' already exists."
                    )
            except DatabaseManagerConflictingAnalyzerException:
                raise
            except DatabaseManagerAnalyzerOperationException:
                raise
            except Exception as e:
                raise DatabaseManagerAnalyzerOperationException(
                    f"Failed to check analyzer id conflict: {e}", cause=e
                )

        # --- Check for name conflict ---
        try:
            existing_name = await self.get_analyzers_by_name(analyzer.name, ambiguous=False)
            if existing_name:
                raise DatabaseManagerConflictingAnalyzerException(
                    f"A FullTextAnalyzer with name '{analyzer.name}' already exists."
                )
        except DatabaseManagerConflictingAnalyzerException:
            raise
        except DatabaseManagerAnalyzerOperationException:
            raise
        except Exception as e:
            raise DatabaseManagerAnalyzerOperationException(
                f"Failed to check analyzer name conflict: {e}", cause=e
            )

        # --- Define the analyzer in SurrealDB ---
        try:
            define_stmt = analyzer.get_define_analyzer_statement(overwrite=False)
            await provider.query_raw(define_stmt)
            self._logger.info(f"Analyzer '{analyzer.name}' defined in SurrealDB.")
        except Exception as e:
            self._logger.error(f"Failed to define analyzer '{analyzer.name}': {e}")
            raise DatabaseManagerAnalyzerOperationException(
                f"Failed to define analyzer '{analyzer.name}' in SurrealDB: {e}", cause=e
            )

        # --- Create the collection entry ---
        try:
            entry_json = analyzer.to_json(recursive=True, exclude_id=True)
            if analyzer.id:
                result = await provider.query_raw(
                    f"CREATE {coll}:{analyzer.id} CONTENT {entry_json};"
                )
            else:
                result = await provider.query_raw(
                    f"CREATE {coll} CONTENT {entry_json};"
                )
            created = self._parse_single_result(result)
            if created is None:
                raise DatabaseManagerAnalyzerOperationException(
                    "CREATE FullTextAnalyzer returned no result."
                )
            return FullTextAnalyzer.from_dict(created)
        except DatabaseManagerAnalyzerOperationException:
            raise
        except Exception as e:
            self._logger.error(f"Failed to create FullTextAnalyzer entry '{analyzer.name}': {e}")
            raise DatabaseManagerAnalyzerOperationException(
                f"Failed to create FullTextAnalyzer catalog entry: {e}", cause=e
            )

    async def update_analyzer(self, analyzer: FullTextAnalyzer) -> FullTextAnalyzer:
        """Update an existing FullTextAnalyzer entry and alter the analyzer on the database.

        Uses ALTER ANALYZER. Rebuilds referencing indexes if tokenizers or filters changed.

        Args:
            analyzer: Updated analyzer definition. id is required.

        Returns:
            Updated entry.

        Raises:
            DatabaseManagerNotInitializedException: Not initialized.
            DatabaseManagerAnalyzerNotFoundException: Target does not exist.
            DatabaseManagerInvalidAnalyzerException: Validation failure or id is empty.
            DatabaseManagerAnalyzerOperationException: Query failure.
        """
        # --- Validate ---
        if not analyzer.id:
            raise DatabaseManagerInvalidAnalyzerException(
                "FullTextAnalyzer.id is required for update."
            )
        if not analyzer.name:
            raise DatabaseManagerInvalidAnalyzerException(
                "FullTextAnalyzer.name is required."
            )
        try:
            analyzer.validate_and_normalize()
        except DatabaseManagerInvalidAnalyzerException:
            raise
        except Exception as e:
            raise DatabaseManagerInvalidAnalyzerException(
                f"Analyzer validation failed: {e}", cause=e
            )

        provider = self._get_default_provider_or_raise()
        coll = FullTextAnalyzer.COLLECTION_NAME()
        analyzer_id = analyzer.id

        # --- Verify the entry exists and get the original ---
        try:
            original = await self.get_analyzer(analyzer_id)
        except DatabaseManagerAnalyzerOperationException:
            raise
        except Exception as e:
            raise DatabaseManagerAnalyzerOperationException(
                f"Failed to retrieve analyzer '{analyzer_id}': {e}", cause=e
            )
        if original is None:
            raise DatabaseManagerAnalyzerNotFoundException(
                f"FullTextAnalyzer '{analyzer_id}' not found."
            )

        # --- Determine if functionality changed (for index rebuild decision) ---
        def _tokens_str(a: FullTextAnalyzer) -> str:
            tokens = a.tokenizers or []
            return ",".join(sorted(t.tokenizer.value for t in tokens if t.tokenizer))

        def _filters_str(a: FullTextAnalyzer) -> str:
            filters = a.filters or []
            return ",".join(sorted(f.to_surreal_filter_str() for f in filters if f.filter))

        original_tokens = _tokens_str(original)
        original_filters = _filters_str(original)
        new_tokens = _tokens_str(analyzer)
        new_filters = _filters_str(analyzer)
        functionality_changed = (
            original_tokens != new_tokens or original_filters != new_filters
        )

        # The original analyzer name (needed for ALTER ANALYZER and index rebuild)
        original_name = original.name

        # --- Execute ALTER ANALYZER ---
        try:
            alter_stmt = analyzer.get_alter_analyzer_statement()
            await provider.query_raw(alter_stmt)
            self._logger.info(f"Analyzer '{original_name}' altered in SurrealDB.")
        except Exception as e:
            self._logger.error(f"Failed to alter analyzer '{original_name}': {e}")
            raise DatabaseManagerAnalyzerOperationException(
                f"Failed to alter analyzer '{original_name}': {e}", cause=e
            )

        # --- Update the catalog entry ---
        try:
            import json as _json
            update_dict = analyzer.to_dict(recursive=True, exclude_id=True)
            update_json = _json.dumps(update_dict)
            result = await provider.query_raw(
                f"UPDATE {coll}:{analyzer_id} MERGE {update_json} RETURN AFTER;"
            )
            updated_data = self._parse_single_result(result)
            if updated_data is None:
                raise DatabaseManagerAnalyzerOperationException(
                    "UPDATE FullTextAnalyzer returned no result."
                )
            updated = FullTextAnalyzer.from_dict(updated_data)
        except DatabaseManagerAnalyzerOperationException:
            raise
        except Exception as e:
            self._logger.error(f"Failed to update FullTextAnalyzer catalog entry '{analyzer_id}': {e}")
            raise DatabaseManagerAnalyzerOperationException(
                f"Failed to update FullTextAnalyzer catalog entry: {e}", cause=e
            )

        # --- Rebuild indexes if functionality changed ---
        if functionality_changed:
            self._logger.info(
                f"Analyzer '{original_name}' functionality changed — rebuilding referencing indexes."
            )
            # Rebuild using the original name (the analyzer definition keeps its name)
            await self._rebuild_indexes_for_analyzer(original_name)

        return updated

    async def get_analyzer(self, id: str) -> FullTextAnalyzer | None:
        """Retrieve a FullTextAnalyzer entry by record id.

        Args:
            id: Record id to look up.

        Returns:
            Matching entry, or None if not found.

        Raises:
            DatabaseManagerNotInitializedException: Not initialized.
            DatabaseManagerAnalyzerOperationException: Query failure.
        """
        provider = self._get_default_provider_or_raise()
        coll = FullTextAnalyzer.COLLECTION_NAME()

        try:
            result = await provider.query_raw(f"SELECT * FROM {coll}:{id};")
            data = self._parse_single_result(result)
            if data is None:
                return None
            return FullTextAnalyzer.from_dict(data)
        except Exception as e:
            self._logger.error(f"Failed to get FullTextAnalyzer '{id}': {e}")
            raise DatabaseManagerAnalyzerOperationException(
                f"Failed to get FullTextAnalyzer '{id}': {e}", cause=e
            )

    async def get_all_analyzers(self) -> list[FullTextAnalyzer]:
        """Retrieve all FullTextAnalyzer entries.

        Returns:
            All entries as a list (empty list if none found).

        Raises:
            DatabaseManagerNotInitializedException: Not initialized.
            DatabaseManagerAnalyzerOperationException: Query failure.
        """
        provider = self._get_default_provider_or_raise()
        coll = FullTextAnalyzer.COLLECTION_NAME()

        try:
            result = await provider.query_raw(f"SELECT * FROM {coll};")
            records = self._parse_list_result(result)
            return [FullTextAnalyzer.from_dict(r) for r in records]
        except Exception as e:
            self._logger.error(f"Failed to get all FullTextAnalyzers: {e}")
            raise DatabaseManagerAnalyzerOperationException(
                f"Failed to get all FullTextAnalyzers: {e}", cause=e
            )

    async def get_analyzers_by_name(
        self, name: str, ambiguous: bool = False
    ) -> list[FullTextAnalyzer]:
        """Retrieve FullTextAnalyzer entries by name.

        Args:
            name: Analyzer name to search for.
            ambiguous: If True, use full-text (contains) search. If False, use exact match.

        Returns:
            Matching entries (empty list if none found).

        Raises:
            DatabaseManagerNotInitializedException: Not initialized.
            DatabaseManagerAnalyzerOperationException: Query failure.
        """
        provider = self._get_default_provider_or_raise()
        coll = FullTextAnalyzer.COLLECTION_NAME()

        try:
            import json as _json
            if ambiguous:
                query = f"SELECT * FROM {coll} WHERE name @@ {_json.dumps(name)};"
            else:
                query = f"SELECT * FROM {coll} WHERE name = {_json.dumps(name)};"

            result = await provider.query_raw(query)
            records = self._parse_list_result(result)
            return [FullTextAnalyzer.from_dict(r) for r in records]
        except Exception as e:
            self._logger.error(f"Failed to get FullTextAnalyzers by name '{name}': {e}")
            raise DatabaseManagerAnalyzerOperationException(
                f"Failed to get FullTextAnalyzers by name: {e}", cause=e
            )

    async def delete_analyzer(self, id: str) -> None:
        """Delete a FullTextAnalyzer entry and remove the analyzer from the database.

        Args:
            id: Record id of the analyzer to delete.

        Raises:
            DatabaseManagerNotInitializedException: Not initialized.
            DatabaseManagerAnalyzerNotFoundException: Target does not exist.
            DatabaseManagerAnalyzerOperationException: Query failure.
        """
        provider = self._get_default_provider_or_raise()
        coll = FullTextAnalyzer.COLLECTION_NAME()

        # Verify the entry exists
        try:
            existing = await self.get_analyzer(id)
        except DatabaseManagerAnalyzerOperationException:
            raise
        except Exception as e:
            raise DatabaseManagerAnalyzerOperationException(
                f"Failed to check existence of analyzer '{id}': {e}", cause=e
            )
        if existing is None:
            raise DatabaseManagerAnalyzerNotFoundException(
                f"FullTextAnalyzer '{id}' not found."
            )

        # Remove the analyzer from SurrealDB first
        try:
            drop_stmt = existing.get_drop_analyzer_statement()
            await provider.query_raw(drop_stmt)
            self._logger.info(f"Analyzer '{existing.name}' removed from SurrealDB.")
        except Exception as e:
            self._logger.error(f"Failed to remove analyzer '{existing.name}' from SurrealDB: {e}")
            raise DatabaseManagerAnalyzerOperationException(
                f"Failed to remove analyzer '{existing.name}' from SurrealDB: {e}", cause=e
            )

        # Delete the collection entry
        try:
            await provider.query_raw(f"DELETE {coll}:{id};")
            self._logger.info(f"FullTextAnalyzer '{id}' deleted from catalog.")
        except Exception as e:
            self._logger.error(f"Failed to delete FullTextAnalyzer catalog entry '{id}': {e}")
            raise DatabaseManagerAnalyzerOperationException(
                f"Failed to delete FullTextAnalyzer catalog entry '{id}': {e}", cause=e
            )

    # ---------------------------------------------------------------------------
    # Provider getters
    # ---------------------------------------------------------------------------

    async def get_provider(self, id: str) -> IDatabaseProvider:
        """Return the IDatabaseProvider for a connection id.

        Returns cached provider immediately. Creates on demand for uncached providers.

        Args:
            id: Record id of the DatabaseConnection.

        Returns:
            Corresponding provider instance.

        Raises:
            DatabaseManagerNotInitializedException: Phase-3 not completed for non-default.
            DatabaseManagerConnectionNotFoundException: No connection record for the given id.
            DatabaseManagerSecretNotFoundException: Required secret does not exist.
            DatabaseManagerOperationException: Query failure.
        """
        # Return cached provider immediately if available
        if id in self._providers:
            return self._providers[id]

        # Delegate to synchronous method for the default connection
        if id == IDatabaseManager.DEFAULT_DATABASE_NAME():
            return self.get_default_provider()

        # Non-default providers require phase-3 (need ISecretManager for secrets)
        self._check_phase3_or_raise()
        provider = self._get_default_provider_or_raise()

        # Load connection config from the database
        try:
            connection = await self.get_connection(id)
        except DatabaseManagerOperationException:
            raise
        except Exception as e:
            raise DatabaseManagerOperationException(
                f"Failed to load connection config for '{id}': {e}", cause=e
            )
        if connection is None:
            raise DatabaseManagerConnectionNotFoundException(
                f"No DatabaseConnection record found for id '{id}'."
            )

        # Create the provider using the connection config and secret
        new_provider = await self._create_provider_from_connection(connection)

        # Cache and return the new provider
        self._providers[id] = new_provider
        self._logger.info(f"Provider for connection '{id}' created and cached.")
        return new_provider

    def get_default_provider(self) -> IDatabaseProvider:
        """Return the default IDatabaseProvider synchronously.

        NOTE: This is a synchronous method (not async).

        Returns:
            Default provider instance.

        Raises:
            DatabaseManagerNotInitializedException: Default provider is not registered.
        """
        return self._get_default_provider_or_raise()
