"""tool_catalogue_service.py - Concrete implementation of IToolCatalogueService.

Provides CRUD and search operations on ToolCatalogueEntry and ToolVersionEntry
records stored in a SurrealDB database, along with index management and
filesystem synchronization of tool code.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from typing import Any

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider

from .exceptions import (
    ConflictingToolCatalogueEntryException,
    FullTextAnalyzerNotExistException,
    InvalidToolCatalogueEntryException,
    InvalidToolCatalogueSearchCriteriaException,
    InvalidToolVersionEntryException,
    InvalidToolVersionSearchCriteriaException,
    ToolCatalogueEntryNotFoundException,
    ToolComponentInitializationException,
    ToolComponentNotInitializedException,
    ToolComponentOperationException,
    ToolVersionEntryNotFoundException,
)
from .i_tool_catalogue_service import IToolCatalogueService
from .models import (
    ToolCatalogueEntry,
    ToolCatalogueSearchCriteria,
    ToolCatalogueSearchResultEntry,
    ToolComponentConfigurations,
    ToolVersionEntry,
    ToolVersionEntrySearchCriteria,
)
from .models.tool_catalogue_search_criteria import LogicalOperator


class ToolCatalogueService(IToolCatalogueService):
    """CRUD and search operations on ToolCatalogueEntry and ToolVersionEntry records.

    Uses SurrealDB as the underlying data store. Also synchronises tool code
    to the filesystem under {app_data_folder}/tools/codes/ when versions are
    created or updated.
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
                "ToolCatalogueService is not initialized (no IDatabaseManager)."
            )
        provider = self._database_manager.get_default_provider()
        if provider is None:
            raise ToolComponentNotInitializedException(
                "Default database provider is not available."
            )
        return provider

    def _unwrap_result(self, raw: Any) -> Any:
        """Unwrap the raw SurrealDB query result.

        SurrealDB wraps multi-statement results in a list of statement dicts.
        For single-statement results, extract the inner result payload.
        """
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

    async def _sync_code_to_filesystem(self, version: ToolVersionEntry) -> None:
        """Sync the tool code from the database record to the filesystem.

        Creates the code directory and writes code or clones from code_link.

        Args:
            version: Tool version entry with code or code_link.

        Raises:
            ToolComponentOperationException: Filesystem or clone operation failure.
        """
        if self._configurations is None or self._configurations.app_data_folder is None:
            raise ToolComponentOperationException("App data folder is not configured.")

        # Build the target code directory path
        code_dir = os.path.join(
            self._configurations.app_data_folder,
            "tools", "codes",
            f"{version.tool_id}_{version.id}"
        )
        try:
            os.makedirs(code_dir, exist_ok=True)
        except OSError as exc:
            raise ToolComponentOperationException(
                f"Failed to create code directory '{code_dir}'.",
                cause=exc,
            ) from exc

        if version.code is not None:
            # Write code directly to main.py
            main_py_path = os.path.join(code_dir, "main.py")
            try:
                with open(main_py_path, "w", encoding="utf-8") as f:
                    f.write(version.code)
                self._logger.debug("Wrote tool code to '%s'.", main_py_path)
            except OSError as exc:
                raise ToolComponentOperationException(
                    f"Failed to write tool code to '{main_py_path}'.",
                    cause=exc,
                ) from exc

        elif version.code_link is not None:
            # Clone or download code from the repository link
            # Clear existing files first
            try:
                for entry in os.scandir(code_dir):
                    if entry.is_file():
                        os.remove(entry.path)
                    elif entry.is_dir():
                        shutil.rmtree(entry.path)
            except OSError as exc:
                raise ToolComponentOperationException(
                    f"Failed to clear code directory '{code_dir}'.",
                    cause=exc,
                ) from exc
            # Clone the repository
            import subprocess
            result = subprocess.run(
                ["git", "clone", version.code_link, code_dir],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                raise ToolComponentOperationException(
                    f"Failed to clone repository '{version.code_link}': {result.stderr}",
                )

    def _delete_code_from_filesystem(self, tool_id: str, version_id: str) -> None:
        """Delete the code directory for a tool version (best-effort).

        Args:
            tool_id: Tool catalogue entry ID.
            version_id: Tool version entry ID.
        """
        if self._configurations is None or self._configurations.app_data_folder is None:
            return
        code_dir = os.path.join(
            self._configurations.app_data_folder,
            "tools", "codes",
            f"{tool_id}_{version_id}"
        )
        if os.path.exists(code_dir):
            try:
                shutil.rmtree(code_dir)
                self._logger.debug("Deleted code directory '%s'.", code_dir)
            except OSError as exc:
                self._logger.warning("Failed to delete code directory '%s': %s", code_dir, exc)

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    async def initialize(
        self,
        database_manager: IDatabaseManager,
        component_configurations: ToolComponentConfigurations,
    ) -> bool:
        """Initialize the catalogue service and create required indexes.

        Args:
            database_manager: Provides the default IDatabaseProvider.
            component_configurations: Index and analyzer settings.

        Returns:
            True on success.

        Raises:
            ToolComponentInitializationException: Any failure during initialization.
        """
        self._logger.debug("Initializing ToolCatalogueService...")
        try:
            self._database_manager = database_manager
            self._configurations = component_configurations
            self._database_provider = database_manager.get_default_provider()
            await self.ensure_indexes(component_configurations, overwrite=False)
        except ToolComponentInitializationException:
            raise
        except Exception as exc:
            raise ToolComponentInitializationException(
                "Failed to initialize ToolCatalogueService.",
                cause=exc,
            ) from exc
        self._logger.info("ToolCatalogueService initialized.")
        return True

    async def ensure_indexes(
        self,
        configurations: ToolComponentConfigurations,
        overwrite: bool = False,
    ) -> bool:
        """Create or update all required database indexes.

        Args:
            configurations: Analyzer names and HNSW settings.
            overwrite: When True, use OVERWRITE to force-update existing indexes.

        Returns:
            True on success.

        Raises:
            ToolComponentNotInitializedException: Service is not initialized.
            FullTextAnalyzerNotExistException: A referenced analyzer does not exist.
            ToolComponentOperationException: Index creation failures.
        """
        self._logger.debug("Ensuring indexes (overwrite=%s)...", overwrite)
        provider = self._provider()

        # Verify the referenced analyzers exist via DatabaseManager
        if self._database_manager is not None:
            for analyzer_name in (
                configurations.name_analyzer,
                configurations.description_analyzer,
            ):
                try:
                    matches = await self._database_manager.get_analyzers_by_name(analyzer_name)
                except Exception as exc:
                    raise FullTextAnalyzerNotExistException(
                        f"Failed to check for analyzer '{analyzer_name}'.",
                        cause=exc,
                    ) from exc
                if not matches:
                    raise FullTextAnalyzerNotExistException(
                        f"Full-text analyzer '{analyzer_name}' does not exist. "
                        "Create it via DatabaseManager before initializing ToolComponent."
                    )

        cat = ToolCatalogueEntry.CollectionName()
        ver = ToolVersionEntry.CollectionName()
        if_kw = "OVERWRITE" if overwrite else "IF NOT EXISTS"
        name_a = configurations.name_analyzer
        desc_a = configurations.description_analyzer

        indexes: list[tuple[str, str]] = [
            # --- ToolCatalogue indexes ---
            (
                "idx_tool_catalogue_name_ft",
                f"DEFINE INDEX {if_kw} idx_tool_catalogue_name_ft ON TABLE {cat} "
                f"FIELDS name SEARCH ANALYZER {name_a} BM25 CONCURRENTLY;",
            ),
            (
                "idx_tool_catalogue_status",
                f"DEFINE INDEX {if_kw} idx_tool_catalogue_status ON TABLE {cat} "
                f"FIELDS status CONCURRENTLY;",
            ),
            (
                "idx_tool_catalogue_description_ft",
                f"DEFINE INDEX {if_kw} idx_tool_catalogue_description_ft ON TABLE {cat} "
                f"FIELDS description SEARCH ANALYZER {desc_a} BM25 CONCURRENTLY;",
            ),
            (
                "idx_tool_catalogue_description_vector",
                f"DEFINE INDEX {if_kw} idx_tool_catalogue_description_vector ON TABLE {cat} "
                f"FIELDS description_vector HNSW "
                f"DIMENSION {configurations.vector_dimensions} "
                f"TYPE {configurations.vector_data_type.value} "
                f"DIST {configurations.vector_search_method.value} "
                f"EFC {configurations.vector_exploration_factor} "
                f"M {configurations.vector_max_connections} CONCURRENTLY;",
            ),
            (
                "idx_tool_catalogue_tags",
                f"DEFINE INDEX {if_kw} idx_tool_catalogue_tags ON TABLE {cat} "
                f"FIELDS tags CONCURRENTLY;",
            ),
            # --- ToolVersions indexes ---
            (
                "idx_tool_versions_tool_id",
                f"DEFINE INDEX {if_kw} idx_tool_versions_tool_id ON TABLE {ver} "
                f"FIELDS tool_id CONCURRENTLY;",
            ),
            (
                "idx_tool_versions_tool_id_status",
                f"DEFINE INDEX {if_kw} idx_tool_versions_tool_id_status ON TABLE {ver} "
                f"FIELDS tool_id, status CONCURRENTLY;",
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

        self._logger.info("All ToolCatalogue indexes ensured.")
        return True

    # -------------------------------------------------------------------------
    # ToolCatalogueEntry CRUD
    # -------------------------------------------------------------------------

    async def create_tool_catalogue_entry(
        self, catalogue: ToolCatalogueEntry
    ) -> ToolCatalogueEntry:
        """Persist a new tool catalogue record.

        Args:
            catalogue: Tool catalogue entry to create.

        Returns:
            The created ToolCatalogueEntry with the assigned ID.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidToolCatalogueEntryException: Validation failure.
            ConflictingToolCatalogueEntryException: Duplicate name.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()

        # Validate required fields
        if not catalogue.name:
            raise InvalidToolCatalogueEntryException("ToolCatalogueEntry name must not be empty.")
        if catalogue.status is None:
            raise InvalidToolCatalogueEntryException("ToolCatalogueEntry status must not be None.")

        # Check for duplicate name
        name_escaped = self._escape_string(catalogue.name)
        check_q = f"SELECT id FROM {ToolCatalogueEntry.CollectionName()} WHERE name = '{name_escaped}';"
        try:
            raw_check = await provider.query_raw(check_q)
            raw_check = self._unwrap_result(raw_check)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to check for duplicate name.", cause=exc
            ) from exc
        if raw_check and (isinstance(raw_check, list) and len(raw_check) > 0):
            raise ConflictingToolCatalogueEntryException(
                f"A ToolCatalogueEntry with name '{catalogue.name}' already exists."
            )

        # Build CREATE query
        cat = ToolCatalogueEntry.CollectionName()
        if not catalogue.id:
            create_q = f"CREATE {cat} CONTENT {catalogue.to_json(exclude_id=True)};"
        else:
            create_q = (
                f"CREATE {self._thing_ref(cat, catalogue.id)} "
                f"CONTENT {catalogue.to_json(exclude_id=True)};"
            )

        try:
            raw = await provider.query_raw(create_q)
            raw = self._unwrap_result(raw)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to create ToolCatalogueEntry.", cause=exc
            ) from exc

        if not raw:
            raise ToolComponentOperationException("Create returned no result.")

        record_data = raw[0] if isinstance(raw, list) else raw
        record_data = self._unwrap_record(record_data)
        created = ToolCatalogueEntry.from_dict(record_data)
        self._logger.info("Created ToolCatalogueEntry: id=%s name=%s", created.id, created.name)
        return created

    async def update_tool_catalogue_entry(
        self, catalogue: ToolCatalogueEntry
    ) -> ToolCatalogueEntry:
        """Update an existing tool catalogue record.

        Args:
            catalogue: Tool catalogue entry with updated fields. id must be set.

        Returns:
            The updated ToolCatalogueEntry.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidToolCatalogueEntryException: Validation failure or empty id.
            ToolCatalogueEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()

        if not catalogue.id:
            raise InvalidToolCatalogueEntryException(
                "ToolCatalogueEntry id must not be empty for update."
            )

        # Verify the existing record exists
        existing = await self.get_tool_catalogue_entry(catalogue.id)
        # If get raises ToolCatalogueEntryNotFoundException, it propagates

        # Preserve existing description_vector if not replaced
        if catalogue.description_vector is None and existing.description_vector is not None:
            object.__setattr__(catalogue, "description_vector", existing.description_vector)

        cat = ToolCatalogueEntry.CollectionName()
        update_q = (
            f"UPDATE {self._thing_ref(cat, catalogue.id)} "
            f"MERGE {catalogue.to_json(exclude_id=True)};"
        )
        try:
            raw = await provider.query_raw(update_q)
            raw = self._unwrap_result(raw)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to update ToolCatalogueEntry.", cause=exc
            ) from exc

        if not raw:
            raise ToolComponentOperationException("Update returned no result.")

        record_data = raw[0] if isinstance(raw, list) else raw
        record_data = self._unwrap_record(record_data)
        updated = ToolCatalogueEntry.from_dict(record_data)
        self._logger.info("Updated ToolCatalogueEntry: id=%s", updated.id)
        return updated

    async def delete_tool_catalogue_entry(self, catalogue_id: str) -> None:
        """Delete a tool catalogue record and all associated version entries.

        Args:
            catalogue_id: ID of the tool catalogue entry to delete.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            ToolCatalogueEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()

        # Verify the record exists before deletion (raises ToolCatalogueEntryNotFoundException)
        await self.get_tool_catalogue_entry(catalogue_id)

        # Fetch version entries for filesystem cleanup later
        cat_id_escaped = self._escape_string(catalogue_id)
        fetch_versions_q = (
            f"SELECT id, tool_id FROM {ToolVersionEntry.CollectionName()} "
            f"WHERE tool_id = '{cat_id_escaped}';"
        )
        try:
            raw_versions = await provider.query_raw(fetch_versions_q)
            raw_versions = self._unwrap_result(raw_versions)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to fetch version entries for deletion.", cause=exc
            ) from exc

        version_ids: list[str] = []
        if raw_versions and isinstance(raw_versions, list):
            for item in raw_versions:
                item_dict = self._unwrap_record(item)
                v_entry = ToolVersionEntry.from_dict(item_dict)
                if v_entry.id:
                    version_ids.append(v_entry.id)

        # Execute transaction: delete versions then catalogue entry
        cat = ToolCatalogueEntry.CollectionName()
        ver = ToolVersionEntry.CollectionName()
        txn_q = (
            f"BEGIN TRANSACTION; "
            f"DELETE {ver} WHERE tool_id = '{cat_id_escaped}'; "
            f"DELETE {self._thing_ref(cat, catalogue_id)} RETURN BEFORE; "
            f"COMMIT TRANSACTION;"
        )
        try:
            raw = await provider.query_raw(txn_q)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to delete ToolCatalogueEntry.", cause=exc
            ) from exc

        # Check if the catalogue record was actually deleted
        # The RETURN BEFORE result is in the transaction output
        # We do a best-effort verification by trying to fetch
        try:
            still_exists = await provider.query(
                f"SELECT id FROM {self._thing_ref(cat, catalogue_id)};",
                model=ToolCatalogueEntry,
                many=False,
            )
        except Exception:
            still_exists = None

        if still_exists is not None:
            raise ToolComponentOperationException(
                f"ToolCatalogueEntry '{catalogue_id}' may not have been deleted."
            )

        # Best-effort filesystem cleanup for each version
        for v_id in version_ids:
            self._delete_code_from_filesystem(catalogue_id, v_id)

        self._logger.info("Deleted ToolCatalogueEntry: id=%s", catalogue_id)

    async def get_tool_catalogue_entry(self, catalogue_id: str) -> ToolCatalogueEntry:
        """Retrieve a single tool catalogue record by its id.

        Args:
            catalogue_id: ID of the tool catalogue entry.

        Returns:
            The matching ToolCatalogueEntry.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            ToolCatalogueEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()
        cat = ToolCatalogueEntry.CollectionName()
        query = f"SELECT * FROM {self._thing_ref(cat, catalogue_id)};"
        try:
            result = await provider.query(query, model=ToolCatalogueEntry, many=False)
        except Exception as exc:
            raise ToolComponentOperationException(
                f"Failed to get ToolCatalogueEntry '{catalogue_id}'.", cause=exc
            ) from exc

        if result is None:
            raise ToolCatalogueEntryNotFoundException(
                f"ToolCatalogueEntry '{catalogue_id}' not found.",
                details={"catalogue_id": catalogue_id},
            )
        return result

    async def get_all_tool_catalogue_entries(self) -> list[ToolCatalogueEntry]:
        """Return all tool catalogue records.

        Returns:
            List of all ToolCatalogueEntry records.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()
        query = f"SELECT * FROM {ToolCatalogueEntry.CollectionName()};"
        try:
            results = await provider.query(query, model=ToolCatalogueEntry, many=True)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to get all ToolCatalogueEntries.", cause=exc
            ) from exc
        return results or []

    async def search_tool_catalogue_entries(
        self, search_criteria: ToolCatalogueSearchCriteria
    ) -> list[ToolCatalogueSearchResultEntry]:
        """Search tool catalogue records using search_criteria.

        Args:
            search_criteria: Filter and search parameters.

        Returns:
            List of ToolCatalogueSearchResultEntry records.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidToolCatalogueSearchCriteriaException: Invalid search criteria.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()

        # Validate search criteria
        if search_criteria is None:
            raise InvalidToolCatalogueSearchCriteriaException("Search criteria must not be None.")
        if search_criteria.limit is not None and search_criteria.limit <= 0:
            raise InvalidToolCatalogueSearchCriteriaException("Limit must be positive.")

        cat = ToolCatalogueEntry.CollectionName()
        ver = ToolVersionEntry.CollectionName()

        # Build WHERE clauses dynamically
        where_clauses: list[str] = []

        if search_criteria.name is not None:
            name_esc = self._escape_string(search_criteria.name)
            where_clauses.append(f"name = '{name_esc}'")

        if search_criteria.status is not None and len(search_criteria.status) > 0:
            status_list = ", ".join(f"'{s.value}'" for s in search_criteria.status)
            where_clauses.append(f"status IN [{status_list}]")

        if search_criteria.description_keywords is not None and len(search_criteria.description_keywords) > 0:
            # BM25 full-text search: combine keywords
            keywords_str = " ".join(search_criteria.description_keywords)
            kw_esc = self._escape_string(keywords_str)
            where_clauses.append(f"description @@ '{kw_esc}'")

        if search_criteria.description_vector is not None:
            limit = search_criteria.limit or 100
            vector_json = json.dumps(search_criteria.description_vector)
            where_clauses.append(f"description_vector <|{limit}|> {vector_json}")

        if search_criteria.tags is not None:
            tags_crit = search_criteria.tags
            if tags_crit.tags and len(tags_crit.tags) > 0:
                if tags_crit.operator == LogicalOperator.AND:
                    for tag in tags_crit.tags:
                        tag_esc = self._escape_string(tag)
                        where_clauses.append(f"'{tag_esc}' IN tags")
                else:
                    # OR: any tag must be present
                    tag_conditions = " OR ".join(
                        f"'{self._escape_string(t)}' IN tags" for t in tags_crit.tags
                    )
                    where_clauses.append(f"({tag_conditions})")

        # Build the full query
        limit_val = search_criteria.limit or 100
        if where_clauses:
            where_str = " AND ".join(where_clauses)
            query = f"SELECT * FROM {cat} WHERE {where_str} LIMIT {limit_val};"
        else:
            query = f"SELECT * FROM {cat} LIMIT {limit_val};"

        try:
            catalogue_results = await provider.query(query, model=ToolCatalogueEntry, many=True)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to search ToolCatalogueEntries.", cause=exc
            ) from exc

        catalogue_results = catalogue_results or []

        # For each catalogue result, fetch associated versions if version_status is set
        result_entries: list[ToolCatalogueSearchResultEntry] = []
        for entry in catalogue_results:
            versions: list[ToolVersionEntry] = []
            if search_criteria.version_status is not None and entry.id:
                vs_list = ", ".join(f"'{s.value}'" for s in search_criteria.version_status)
                entry_id_esc = self._escape_string(entry.id)
                ver_q = (
                    f"SELECT * FROM {ver} WHERE tool_id = '{entry_id_esc}' "
                    f"AND status IN [{vs_list}];"
                )
                try:
                    versions = await provider.query(ver_q, model=ToolVersionEntry, many=True) or []
                except Exception as exc:
                    raise ToolComponentOperationException(
                        "Failed to fetch version entries for search result.", cause=exc
                    ) from exc

            result_entry = ToolCatalogueSearchResultEntry()
            object.__setattr__(result_entry, "catalogue", entry)
            object.__setattr__(result_entry, "versions", versions)
            result_entries.append(result_entry)

        return result_entries

    # -------------------------------------------------------------------------
    # ToolVersionEntry CRUD
    # -------------------------------------------------------------------------

    async def create_tool_version_entry(
        self, version: ToolVersionEntry
    ) -> ToolVersionEntry:
        """Persist a new tool version record and sync code to filesystem.

        Args:
            version: Tool version entry to create.

        Returns:
            The created ToolVersionEntry with the assigned ID.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidToolVersionEntryException: Validation failure.
            ToolCatalogueEntryNotFoundException: Referenced tool_id does not exist.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()

        # Validate required fields
        if not version.tool_id:
            raise InvalidToolVersionEntryException("ToolVersionEntry tool_id must not be empty.")
        if version.code is None and version.code_link is None:
            raise InvalidToolVersionEntryException(
                "ToolVersionEntry must have either code or code_link."
            )

        # Verify tool_id references a valid ToolCatalogueEntry
        await self.get_tool_catalogue_entry(version.tool_id)

        # Build CREATE query
        ver = ToolVersionEntry.CollectionName()
        if not version.id:
            create_q = f"CREATE {ver} CONTENT {version.to_json(exclude_id=True)};"
        else:
            create_q = (
                f"CREATE {self._thing_ref(ver, version.id)} "
                f"CONTENT {version.to_json(exclude_id=True)};"
            )

        try:
            raw = await provider.query_raw(create_q)
            raw = self._unwrap_result(raw)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to create ToolVersionEntry.", cause=exc
            ) from exc

        if not raw:
            raise ToolComponentOperationException("Create ToolVersionEntry returned no result.")

        record_data = raw[0] if isinstance(raw, list) else raw
        record_data = self._unwrap_record(record_data)
        created = ToolVersionEntry.from_dict(record_data)

        # Sync code to filesystem
        try:
            await self._sync_code_to_filesystem(created)
        except Exception as exc:
            # Rollback: delete the newly created DB record
            rollback_q = f"DELETE {self._thing_ref(ver, created.id)};" if created.id else None
            if rollback_q:
                try:
                    await provider.query_raw(rollback_q)
                except Exception as rollback_exc:
                    self._logger.error(
                        "Failed to rollback ToolVersionEntry creation: %s", rollback_exc
                    )
            raise ToolComponentOperationException(
                "Failed to sync tool code to filesystem; creation rolled back.",
                cause=exc,
            ) from exc

        self._logger.info("Created ToolVersionEntry: id=%s tool_id=%s", created.id, created.tool_id)
        return created

    async def update_tool_version_entry(
        self, version: ToolVersionEntry
    ) -> ToolVersionEntry:
        """Update an existing tool version record.

        Args:
            version: Tool version entry with updated fields. id must be set.

        Returns:
            The updated ToolVersionEntry.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidToolVersionEntryException: Validation failure or empty id.
            ToolVersionEntryNotFoundException: No record with the given id.
            ToolCatalogueEntryNotFoundException: Referenced tool_id does not exist.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()

        if not version.id:
            raise InvalidToolVersionEntryException(
                "ToolVersionEntry id must not be empty for update."
            )

        # Fetch existing record
        existing = await self.get_tool_version_entry(version.id)

        # Verify tool_id
        if version.tool_id:
            await self.get_tool_catalogue_entry(version.tool_id)

        ver = ToolVersionEntry.CollectionName()
        update_q = (
            f"UPDATE {self._thing_ref(ver, version.id)} "
            f"MERGE {version.to_json(exclude_id=True)};"
        )
        try:
            raw = await provider.query_raw(update_q)
            raw = self._unwrap_result(raw)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to update ToolVersionEntry.", cause=exc
            ) from exc

        if not raw:
            raise ToolComponentOperationException("Update ToolVersionEntry returned no result.")

        record_data = raw[0] if isinstance(raw, list) else raw
        record_data = self._unwrap_record(record_data)
        updated = ToolVersionEntry.from_dict(record_data)

        # Re-sync code if code or code_link changed
        code_changed = (version.code is not None and version.code != existing.code) or \
                       (version.code_link is not None and version.code_link != existing.code_link)
        if code_changed:
            try:
                await self._sync_code_to_filesystem(updated)
            except Exception as exc:
                # Rollback: restore the previous version
                try:
                    rollback_q = (
                        f"UPDATE {self._thing_ref(ver, version.id)} "
                        f"MERGE {existing.to_json(exclude_id=True)};"
                    )
                    await provider.query_raw(rollback_q)
                except Exception as rollback_exc:
                    self._logger.error("Failed to rollback update: %s", rollback_exc)
                raise ToolComponentOperationException(
                    "Failed to sync updated tool code to filesystem; update rolled back.",
                    cause=exc,
                ) from exc

        self._logger.info("Updated ToolVersionEntry: id=%s", updated.id)
        return updated

    async def delete_tool_version_entry(self, version_id: str) -> None:
        """Delete a tool version record.

        Args:
            version_id: ID of the tool version entry to delete.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            ToolVersionEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()

        # Fetch existing record to get tool_id for filesystem cleanup
        existing = await self.get_tool_version_entry(version_id)

        ver = ToolVersionEntry.CollectionName()
        delete_q = f"DELETE {self._thing_ref(ver, version_id)} RETURN BEFORE;"
        try:
            raw = await provider.query_raw(delete_q)
            raw = self._unwrap_result(raw)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to delete ToolVersionEntry.", cause=exc
            ) from exc

        if not raw or (isinstance(raw, list) and len(raw) == 0):
            raise ToolVersionEntryNotFoundException(
                f"ToolVersionEntry '{version_id}' not found during delete.",
                details={"version_id": version_id},
            )

        # Best-effort filesystem cleanup
        if existing.tool_id:
            self._delete_code_from_filesystem(existing.tool_id, version_id)

        self._logger.info("Deleted ToolVersionEntry: id=%s", version_id)

    async def get_tool_version_entry(self, version_id: str) -> ToolVersionEntry:
        """Retrieve a single tool version record by its id.

        Args:
            version_id: ID of the tool version entry.

        Returns:
            The matching ToolVersionEntry.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            ToolVersionEntryNotFoundException: No record with the given id.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()
        ver = ToolVersionEntry.CollectionName()
        query = f"SELECT * FROM {self._thing_ref(ver, version_id)};"
        try:
            result = await provider.query(query, model=ToolVersionEntry, many=False)
        except Exception as exc:
            raise ToolComponentOperationException(
                f"Failed to get ToolVersionEntry '{version_id}'.", cause=exc
            ) from exc

        if result is None:
            raise ToolVersionEntryNotFoundException(
                f"ToolVersionEntry '{version_id}' not found.",
                details={"version_id": version_id},
            )
        return result

    async def get_all_tool_version_entries(
        self, tool_id: str | None = None
    ) -> list[ToolVersionEntry]:
        """Return all tool version records, optionally filtered by tool_id.

        Args:
            tool_id: Optional tool catalogue ID to filter by.

        Returns:
            List of matching ToolVersionEntry records.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            ToolCatalogueEntryNotFoundException: tool_id not found (when provided).
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()

        if tool_id is not None:
            # Verify the catalogue entry exists
            await self.get_tool_catalogue_entry(tool_id)
            tool_id_esc = self._escape_string(tool_id)
            query = (
                f"SELECT * FROM {ToolVersionEntry.CollectionName()} "
                f"WHERE tool_id = '{tool_id_esc}';"
            )
        else:
            query = f"SELECT * FROM {ToolVersionEntry.CollectionName()};"

        try:
            results = await provider.query(query, model=ToolVersionEntry, many=True)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to get ToolVersionEntries.", cause=exc
            ) from exc
        return results or []

    async def search_tool_version_entries(
        self, search_criteria: ToolVersionEntrySearchCriteria
    ) -> list[ToolVersionEntry]:
        """Search tool version records using search_criteria.

        Args:
            search_criteria: Filter and search parameters.

        Returns:
            List of matching ToolVersionEntry records.

        Raises:
            ToolComponentNotInitializedException: Service not initialized.
            InvalidToolVersionSearchCriteriaException: Invalid search criteria.
            ToolComponentOperationException: Database operation failure.
        """
        provider = self._provider()

        if search_criteria is None:
            raise InvalidToolVersionSearchCriteriaException("Search criteria must not be None.")
        if search_criteria.limit is not None and search_criteria.limit <= 0:
            raise InvalidToolVersionSearchCriteriaException("Limit must be positive.")

        ver = ToolVersionEntry.CollectionName()
        where_clauses: list[str] = []

        if search_criteria.tool_id is not None:
            tool_id_esc = self._escape_string(search_criteria.tool_id)
            where_clauses.append(f"tool_id = '{tool_id_esc}'")

        if search_criteria.status is not None and len(search_criteria.status) > 0:
            status_list = ", ".join(f"'{s.value}'" for s in search_criteria.status)
            where_clauses.append(f"status IN [{status_list}]")

        limit_val = search_criteria.limit or 100
        if where_clauses:
            where_str = " AND ".join(where_clauses)
            query = f"SELECT * FROM {ver} WHERE {where_str} LIMIT {limit_val};"
        else:
            query = f"SELECT * FROM {ver} LIMIT {limit_val};"

        try:
            results = await provider.query(query, model=ToolVersionEntry, many=True)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to search ToolVersionEntries.", cause=exc
            ) from exc
        return results or []
