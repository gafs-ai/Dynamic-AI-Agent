"""sandbox_catalogue_service.py - Concrete implementation of ISandboxCatalogueService.

Provides CRUD and search operations on SandboxCatalogueEntry records stored in
a SurrealDB database, with polymorphic (de)serialization for Host and Docker subtypes.
"""

from __future__ import annotations

import logging
from typing import Any

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider

from .exceptions import (
    ConflictingSandboxCatalogueEntryException,
    FullTextAnalyzerNotExistException,
    InvalidSandboxCatalogueEntryException,
    InvalidSandboxCatalogueSearchCriteriaException,
    SandboxCatalogueEntryNotFoundException,
    ToolComponentInitializationException,
    ToolComponentNotInitializedException,
    ToolComponentOperationException,
)
from .i_sandbox_catalogue_service import ISandboxCatalogueService
from .models import (
    SandboxCatalogueDockerEntry,
    SandboxCatalogueEntry,
    SandboxCatalogueHostEntry,
    SandboxCatalogueSearchCriteria,
    ToolComponentConfigurations,
)
from .models.sandbox_catalogue import SandboxType
from .models.tool_catalogue_search_criteria import LogicalOperator


class SandboxCatalogueService(ISandboxCatalogueService):
    """CRUD and search operations on SandboxCatalogueEntry records.

    Uses SurrealDB as the underlying data store. Supports polymorphic
    serialization via the sandbox_type discriminator field.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the service.

        Args:
            logger: Logger instance for operational messages.
        """
        self._logger: logging.Logger = logger
        self._database_manager: IDatabaseManager | None = None
        self._database_provider: IDatabaseProvider | None = None
        self._configurations: ToolComponentConfigurations | None = None

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _thing_ref(table: str, record_key: str) -> str:
        """Return a safe SurrealQL record reference: type::thing('table', 'key')."""
        t = table.replace("'", "''")
        k = record_key.replace("'", "''")
        return f"type::thing('{t}', '{k}')"

    @staticmethod
    def _escape_string(value: str) -> str:
        """Escape a string value for safe inclusion in a SurrealQL query."""
        return value.replace("\\", "\\\\").replace("'", "\\'")

    def _provider(self) -> IDatabaseProvider:
        """Return the cached database provider.

        Raises:
            ToolComponentNotInitializedException: Service is not initialized.
        """
        if self._database_provider is not None:
            return self._database_provider
        if self._database_manager is None:
            raise ToolComponentNotInitializedException(
                "SandboxCatalogueService is not initialized (no IDatabaseManager)."
            )
        provider = self._database_manager.get_default_provider()
        if provider is None:
            raise ToolComponentNotInitializedException(
                "Default database provider is not available."
            )
        return provider

    def _unwrap_result(self, raw: Any) -> Any:
        """Unwrap the raw SurrealDB query result."""
        if isinstance(raw, list) and len(raw) > 0:
            first = raw[0]
            if isinstance(first, dict) and "result" in first:
                return first["result"]
        return raw

    def _unwrap_record(self, item: Any) -> dict[str, Any]:
        """Unwrap a single record to a plain dict."""
        if isinstance(item, dict):
            return item
        if hasattr(item, "__dict__"):
            return item.__dict__
        return {}

    def _deserialize_entry(self, data: dict[str, Any]) -> SandboxCatalogueEntry:
        """Deserialize a database record to the correct SandboxCatalogueEntry subtype.

        Args:
            data: Raw record dict from the database.

        Returns:
            SandboxCatalogueDockerEntry or SandboxCatalogueHostEntry.

        Raises:
            ToolComponentOperationException: sandbox_type is missing or unrecognized.
        """
        sandbox_type_raw = data.get("sandbox_type")
        if sandbox_type_raw is None:
            raise ToolComponentOperationException(
                "SandboxCatalogueEntry record is missing 'sandbox_type' field."
            )
        try:
            sandbox_type = SandboxType(sandbox_type_raw)
        except ValueError:
            raise ToolComponentOperationException(
                f"Unrecognized sandbox_type value: '{sandbox_type_raw}'."
            )

        if sandbox_type == SandboxType.DOCKER:
            return SandboxCatalogueDockerEntry.from_dict(data)
        elif sandbox_type == SandboxType.HOST:
            return SandboxCatalogueHostEntry.from_dict(data)
        else:
            raise ToolComponentOperationException(
                f"Unsupported sandbox_type: '{sandbox_type_raw}'."
            )

    def _serialize_entry(self, entry: SandboxCatalogueEntry) -> dict[str, Any]:
        """Serialize an entry to a dict including the sandbox_type discriminator.

        Args:
            entry: SandboxCatalogueEntry to serialize.

        Returns:
            Dict with sandbox_type field included.
        """
        return entry.to_dict(recursive=True, exclude_id=True)

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    async def initialize(
        self,
        database_manager: IDatabaseManager,
        component_configurations: ToolComponentConfigurations,
    ) -> bool:
        """Initialize the sandbox catalogue service and create required indexes.

        Args:
            database_manager: Provides the default IDatabaseProvider.
            component_configurations: Index and analyzer settings.

        Returns:
            True on success.

        Raises:
            ToolComponentInitializationException: Any failure during initialization.
        """
        self._logger.debug("Initializing SandboxCatalogueService...")
        try:
            self._database_manager = database_manager
            self._configurations = component_configurations
            self._database_provider = database_manager.get_default_provider()
            await self.ensure_indexes(component_configurations, overwrite=False)
        except ToolComponentInitializationException:
            raise
        except Exception as exc:
            raise ToolComponentInitializationException(
                "Failed to initialize SandboxCatalogueService.",
                cause=exc,
            ) from exc
        self._logger.info("SandboxCatalogueService initialized.")
        return True

    async def ensure_indexes(
        self,
        configurations: ToolComponentConfigurations,
        overwrite: bool = False,
    ) -> bool:
        """Create or update all required database indexes.

        Args:
            configurations: Analyzer names and settings.
            overwrite: When True, use OVERWRITE to force-update existing indexes.

        Returns:
            True on success.

        Raises:
            ToolComponentNotInitializedException: Service is not initialized.
            FullTextAnalyzerNotExistException: A referenced analyzer does not exist.
            ToolComponentOperationException: Index creation failures.
        """
        self._logger.debug("Ensuring SandboxCatalogue indexes (overwrite=%s)...", overwrite)
        provider = self._provider()

        # Verify the name_analyzer exists
        if self._database_manager is not None:
            try:
                matches = await self._database_manager.get_analyzers_by_name(
                    configurations.name_analyzer
                )
            except Exception as exc:
                raise FullTextAnalyzerNotExistException(
                    f"Failed to check for analyzer '{configurations.name_analyzer}'.",
                    cause=exc,
                ) from exc
            if not matches:
                raise FullTextAnalyzerNotExistException(
                    f"Full-text analyzer '{configurations.name_analyzer}' does not exist."
                )

        sandbox = SandboxCatalogueEntry.CollectionName()
        if_kw = "OVERWRITE" if overwrite else "IF NOT EXISTS"
        name_a = configurations.name_analyzer

        indexes: list[tuple[str, str]] = [
            (
                "idx_sandbox_catalogue_name_ft",
                f"DEFINE INDEX {if_kw} idx_sandbox_catalogue_name_ft ON TABLE {sandbox} "
                f"FIELDS name SEARCH ANALYZER {name_a} BM25 CONCURRENTLY;",
            ),
            (
                "idx_sandbox_catalogue_status",
                f"DEFINE INDEX {if_kw} idx_sandbox_catalogue_status ON TABLE {sandbox} "
                f"FIELDS status CONCURRENTLY;",
            ),
            (
                "idx_sandbox_catalogue_tags",
                f"DEFINE INDEX {if_kw} idx_sandbox_catalogue_tags ON TABLE {sandbox} "
                f"FIELDS tags CONCURRENTLY;",
            ),
        ]

        for index_name, query in indexes:
            try:
                await provider.query_raw(query)
                self._logger.debug("Index ensured: %s", index_name)
            except Exception as exc:
                raise ToolComponentOperationException(
                    f"Failed to ensure index '{index_name}'.",
                    cause=exc,
                ) from exc

        self._logger.info("All SandboxCatalogue indexes ensured.")
        return True

    # -------------------------------------------------------------------------
    # SandboxCatalogueEntry CRUD
    # -------------------------------------------------------------------------

    async def create_catalogue_entry(
        self, catalogue: SandboxCatalogueEntry
    ) -> SandboxCatalogueEntry:
        """Persist a new sandbox catalogue record.

        Args:
            catalogue: Sandbox catalogue entry to create.

        Returns:
            The created SandboxCatalogueEntry with the assigned ID.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidSandboxCatalogueEntryException: Validation failure.
            ConflictingSandboxCatalogueEntryException: Duplicate name.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()

        # Validate required fields
        if not catalogue.name:
            raise InvalidSandboxCatalogueEntryException(
                "SandboxCatalogueEntry name must not be empty."
            )
        if catalogue.status is None:
            raise InvalidSandboxCatalogueEntryException(
                "SandboxCatalogueEntry status must not be None."
            )

        # Check for duplicate name
        name_escaped = self._escape_string(catalogue.name)
        sandbox = SandboxCatalogueEntry.CollectionName()
        check_q = f"SELECT id FROM {sandbox} WHERE name = '{name_escaped}';"
        try:
            raw_check = await provider.query_raw(check_q)
            raw_check = self._unwrap_result(raw_check)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to check for duplicate sandbox name.", cause=exc
            ) from exc
        if raw_check and isinstance(raw_check, list) and len(raw_check) > 0:
            raise ConflictingSandboxCatalogueEntryException(
                f"A SandboxCatalogueEntry with name '{catalogue.name}' already exists."
            )

        # Serialize entry with sandbox_type discriminator
        entry_dict = self._serialize_entry(catalogue)
        import json as _json
        entry_json = _json.dumps(entry_dict)

        if not catalogue.id:
            create_q = f"CREATE {sandbox} CONTENT {entry_json};"
        else:
            create_q = (
                f"CREATE {self._thing_ref(sandbox, catalogue.id)} "
                f"CONTENT {entry_json};"
            )

        try:
            raw = await provider.query_raw(create_q)
            raw = self._unwrap_result(raw)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to create SandboxCatalogueEntry.", cause=exc
            ) from exc

        if not raw:
            raise ToolComponentOperationException("Create SandboxCatalogueEntry returned no result.")

        record_data = raw[0] if isinstance(raw, list) else raw
        record_data = self._unwrap_record(record_data)
        created = self._deserialize_entry(record_data)
        self._logger.info(
            "Created SandboxCatalogueEntry: id=%s name=%s", created.id, created.name
        )
        return created

    async def update_catalogue_entry(
        self, catalogue: SandboxCatalogueEntry
    ) -> SandboxCatalogueEntry:
        """Update an existing sandbox catalogue record.

        Args:
            catalogue: Sandbox catalogue entry with updated fields. id must be set.

        Returns:
            The updated SandboxCatalogueEntry.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidSandboxCatalogueEntryException: Validation failure or empty id.
            SandboxCatalogueEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()

        if not catalogue.id:
            raise InvalidSandboxCatalogueEntryException(
                "SandboxCatalogueEntry id must not be empty for update."
            )

        # Verify existing record
        await self.get_catalogue_entry(catalogue.id)

        sandbox = SandboxCatalogueEntry.CollectionName()
        entry_dict = self._serialize_entry(catalogue)
        import json as _json
        entry_json = _json.dumps(entry_dict)

        update_q = f"UPDATE {self._thing_ref(sandbox, catalogue.id)} MERGE {entry_json};"
        try:
            raw = await provider.query_raw(update_q)
            raw = self._unwrap_result(raw)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to update SandboxCatalogueEntry.", cause=exc
            ) from exc

        if not raw:
            raise ToolComponentOperationException("Update SandboxCatalogueEntry returned no result.")

        record_data = raw[0] if isinstance(raw, list) else raw
        record_data = self._unwrap_record(record_data)
        updated = self._deserialize_entry(record_data)
        self._logger.info("Updated SandboxCatalogueEntry: id=%s", updated.id)
        return updated

    async def delete_catalogue_entry(self, catalogue_id: str) -> None:
        """Delete a sandbox catalogue record.

        Args:
            catalogue_id: ID of the sandbox catalogue entry to delete.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            SandboxCatalogueEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()
        sandbox = SandboxCatalogueEntry.CollectionName()
        delete_q = f"DELETE {self._thing_ref(sandbox, catalogue_id)} RETURN BEFORE;"
        try:
            raw = await provider.query_raw(delete_q)
            raw = self._unwrap_result(raw)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to delete SandboxCatalogueEntry.", cause=exc
            ) from exc

        if not raw or (isinstance(raw, list) and len(raw) == 0):
            raise SandboxCatalogueEntryNotFoundException(
                f"SandboxCatalogueEntry '{catalogue_id}' not found.",
                details={"catalogue_id": catalogue_id},
            )
        self._logger.info("Deleted SandboxCatalogueEntry: id=%s", catalogue_id)

    async def get_catalogue_entry(self, catalogue_id: str) -> SandboxCatalogueEntry:
        """Retrieve a single sandbox catalogue record by its id.

        Args:
            catalogue_id: ID of the sandbox catalogue entry.

        Returns:
            The matching SandboxCatalogueEntry.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            SandboxCatalogueEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()
        sandbox = SandboxCatalogueEntry.CollectionName()
        query = f"SELECT * FROM {self._thing_ref(sandbox, catalogue_id)};"
        try:
            raw = await provider.query_raw(query)
            raw = self._unwrap_result(raw)
        except Exception as exc:
            raise ToolComponentOperationException(
                f"Failed to get SandboxCatalogueEntry '{catalogue_id}'.", cause=exc
            ) from exc

        if not raw or (isinstance(raw, list) and len(raw) == 0):
            raise SandboxCatalogueEntryNotFoundException(
                f"SandboxCatalogueEntry '{catalogue_id}' not found.",
                details={"catalogue_id": catalogue_id},
            )

        record_data = raw[0] if isinstance(raw, list) else raw
        record_data = self._unwrap_record(record_data)
        return self._deserialize_entry(record_data)

    async def get_all_catalogue_entries(self) -> list[SandboxCatalogueEntry]:
        """Return all sandbox catalogue records.

        Returns:
            List of all SandboxCatalogueEntry records.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()
        sandbox = SandboxCatalogueEntry.CollectionName()
        query = f"SELECT * FROM {sandbox};"
        try:
            raw = await provider.query_raw(query)
            raw = self._unwrap_result(raw)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to get all SandboxCatalogueEntries.", cause=exc
            ) from exc

        if not raw:
            return []
        if isinstance(raw, list):
            results = []
            for item in raw:
                item_dict = self._unwrap_record(item)
                results.append(self._deserialize_entry(item_dict))
            return results
        return []

    async def search_catalogue_entries(
        self, search_criteria: SandboxCatalogueSearchCriteria
    ) -> list[SandboxCatalogueEntry]:
        """Search sandbox catalogue records using search_criteria.

        Args:
            search_criteria: Filter and search parameters.

        Returns:
            List of matching SandboxCatalogueEntry records.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidSandboxCatalogueSearchCriteriaException: Invalid criteria.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()

        if search_criteria is None:
            raise InvalidSandboxCatalogueSearchCriteriaException(
                "Search criteria must not be None."
            )
        if search_criteria.limit is not None and search_criteria.limit <= 0:
            raise InvalidSandboxCatalogueSearchCriteriaException("Limit must be positive.")

        sandbox = SandboxCatalogueEntry.CollectionName()
        where_clauses: list[str] = []

        if search_criteria.name is not None:
            name_esc = self._escape_string(search_criteria.name)
            where_clauses.append(f"name = '{name_esc}'")

        if search_criteria.status is not None and len(search_criteria.status) > 0:
            status_list = ", ".join(f"'{s.value}'" for s in search_criteria.status)
            where_clauses.append(f"status IN [{status_list}]")

        if search_criteria.tags is not None:
            tags_crit = search_criteria.tags
            if tags_crit.tags and len(tags_crit.tags) > 0:
                if tags_crit.operator == LogicalOperator.AND:
                    for tag in tags_crit.tags:
                        tag_esc = self._escape_string(tag)
                        where_clauses.append(f"'{tag_esc}' IN tags")
                else:
                    tag_conditions = " OR ".join(
                        f"'{self._escape_string(t)}' IN tags" for t in tags_crit.tags
                    )
                    where_clauses.append(f"({tag_conditions})")

        limit_val = search_criteria.limit or 100
        if where_clauses:
            where_str = " AND ".join(where_clauses)
            query = f"SELECT * FROM {sandbox} WHERE {where_str} LIMIT {limit_val};"
        else:
            query = f"SELECT * FROM {sandbox} LIMIT {limit_val};"

        try:
            raw = await provider.query_raw(query)
            raw = self._unwrap_result(raw)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to search SandboxCatalogueEntries.", cause=exc
            ) from exc

        if not raw:
            return []
        if isinstance(raw, list):
            results = []
            for item in raw:
                item_dict = self._unwrap_record(item)
                results.append(self._deserialize_entry(item_dict))
            return results
        return []
