"""model_catalogue_service.py - Concrete implementation of IModelCatalogueService.

Provides CRUD operations on ``ModelCatalogueEntry`` and ``ModelDeployment`` records
stored in a SurrealDB database, along with index management and optional auto-embedding
of catalogue descriptions.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider
from gafs.dynamicaiagent.utils.databaseprovider.surrealdbremote import SurrealDbRemoteProvider

from .exceptions import (
    FullTextAnalyzerNotExistException,
    InvalidModelCatalogueEntryException,
    InvalidModelDeploymentException,
    ModelCatalogueEntryNotFoundException,
    ModelComponentInitializationException,
    ModelComponentNotInitializedException,
    ModelComponentOperationException,
    ModelDeploymentNotFoundException,
)
from .i_model_catalogue_service import IModelCatalogueService
from .models import (
    ModelCatalogueEntry,
    ModelCatalogueSearchCriteria,
    ModelCatalogueSearchResultEntry,
    ModelComponentConfigurations,
    ModelDeployment,
    ModelDeploymentSearchCriteria,
)


class ModelCatalogueService(IModelCatalogueService):
    """CRUD and search operations on ModelCatalogueEntry and ModelDeployment records.

    Uses SurrealDB as the underlying data store.  Edge relationships (deployed_as,
    references_secret) are managed transactionally together with the parent records.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the service.

        Args:
            logger: Logger instance for operational messages.
        """
        self._logger: logging.Logger = logger
        self._database_manager: IDatabaseManager | None = None
        self._database_provider: IDatabaseProvider | None = None
        self._configurations: ModelComponentConfigurations | None = None
        # Optional async callable: (text) -> list[float] | None
        self._embed_fn: Callable[[str], Awaitable[list[float] | None]] | None = None

    # -------------------------------------------------------------------------
    # Helper utilities
    # -------------------------------------------------------------------------

    @staticmethod
    def _doc_id_from_any(x: Any) -> str | None:
        """Extract the bare record id from various SurrealDB link representations."""
        if x is None:
            return None
        if isinstance(x, str):
            return x.rsplit(":", 1)[-1] if ":" in x else x
        if isinstance(x, dict):
            # Try common field names for the record id.
            for k in ("id", "$id"):
                v = x.get(k)
                if isinstance(v, str):
                    return v.rsplit(":", 1)[-1] if ":" in v else v
        try:
            if hasattr(x, "id"):
                cand = str(x.id)
                return cand.rsplit(":", 1)[-1] if ":" in cand else cand
        except Exception:
            pass
        try:
            s = str(x)
            return s.rsplit(":", 1)[-1] if ":" in s else s
        except Exception:
            return None

    @classmethod
    def _thing_ref(cls, table: str, record_key: str) -> str:
        """Return a safe SurrealQL record reference: type::thing('table', 'key')."""
        t = table.replace("'", "''")
        k = record_key.replace("'", "''")
        return f"type::thing('{t}', '{k}')"

    @classmethod
    def _record_ref(cls, table: str, record_key: str) -> str:
        """Return a SurrealQL record reference suitable for RELATE: table:⟨key⟩.

        Uses backtick-escaped key to safely handle arbitrary key strings.
        ``type::thing()`` is not supported in RELATE source/target positions.
        """
        k = record_key.replace("`", "\\`")
        return f"{table}:`{k}`"

    @staticmethod
    def _record_key(id_value: str) -> str:
        """Strip table prefix from an id string, returning the bare key."""
        return id_value.rsplit(":", 1)[-1] if ":" in id_value else id_value

    def _normalize_catalogue_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize a catalogue record dict from the database.

        Converts ``deployments`` from edge-resolved ids (which may carry a table
        prefix) to bare string ids, as expected by ``ModelCatalogueEntry.from_dict``.
        """
        normalized: dict[str, Any] = dict(data)
        if isinstance(normalized.get("deployments"), list):
            normalized["deployments"] = [
                self._doc_id_from_any(item)
                for item in normalized["deployments"]
                if self._doc_id_from_any(item) is not None
            ]
        return normalized

    def _normalize_deployment_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize a deployment record dict from the database.

        Converts ``secrets`` from edge-resolved ids (which may carry a table prefix)
        to bare string ids.
        """
        normalized: dict[str, Any] = dict(data)
        if isinstance(normalized.get("secrets"), list):
            normalized["secrets"] = [
                self._doc_id_from_any(item)
                for item in normalized["secrets"]
                if self._doc_id_from_any(item) is not None
            ]
        return normalized

    def _provider(self) -> IDatabaseProvider:
        """Return the default IDatabaseProvider.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
        """
        if self._database_provider is not None:
            return self._database_provider
        if self._database_manager is None:
            raise ModelComponentNotInitializedException(
                "ModelCatalogueService is not initialized (no IDatabaseManager)."
            )
        provider = self._database_manager.get_default_provider()
        if provider is None:
            raise ModelComponentNotInitializedException(
                "Default database provider is not available."
            )
        return provider

    async def _embed_description_text(
        self,
        description: str,
    ) -> list[float] | None:
        """Generate an embedding vector for a description text.

        Uses the ``_embed_fn`` callable provided at initialization.  Returns ``None``
        when no function is configured or on any error (to make embedding optional).

        Args:
            description: Text to embed.

        Returns:
            Embedding vector as ``list[float]``, or ``None`` on failure.
        """
        if self._embed_fn is None:
            return None
        try:
            result = await self._embed_fn(description)
            if result is None:
                return None
            return [float(v) for v in result]
        except Exception as exc:
            self._logger.warning(
                "Auto-embedding failed for description; description_vector will be None. "
                "Error: %s",
                exc,
            )
            return None

    def _unwrap_raw_result(self, raw: Any, provider: IDatabaseProvider) -> Any:
        """Unwrap the raw SurrealDB query result using provider helpers when available."""
        if hasattr(provider, "unwrap_query_raw_result"):
            return provider.unwrap_query_raw_result(raw)
        # Fallback: handle common shapes ourselves.
        if isinstance(raw, list) and len(raw) > 0:
            first = raw[0]
            if isinstance(first, dict) and "result" in first:
                # SurrealDB statement-level result envelope.
                return first["result"]
        return raw

    def _unwrap_record(self, item: Any, provider: IDatabaseProvider) -> dict[str, Any]:
        """Unwrap a single record from a driver-level result."""
        if hasattr(provider, "unwrap_record"):
            return provider.unwrap_record(item)
        if isinstance(item, dict):
            return item
        return {}

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    async def initialize(
        self,
        database_manager: IDatabaseManager,
        component_configurations: ModelComponentConfigurations,
        embed_fn: Callable[[str], Awaitable[list[float] | None]] | None = None,
    ) -> bool:
        """Initialize the catalogue service.

        Stores the manager and configurations, then calls ``ensure_indexes`` to
        create or verify all required database indexes.

        Args:
            database_manager: Provides the default ``IDatabaseProvider``.
            component_configurations: Index and analyzer settings.
            embed_fn: Optional async callable for auto-embedding descriptions.

        Returns:
            ``True`` on success.

        Raises:
            ModelComponentInitializationException: Any failure during initialization.
        """
        self._logger.debug("Initializing ModelCatalogueService...")
        try:
            self._database_manager = database_manager
            self._configurations = component_configurations
            self._embed_fn = embed_fn
            # Store a direct provider reference for convenience.
            self._database_provider = database_manager.get_default_provider()
            await self.ensure_indexes(component_configurations, overwrite=False)
        except Exception as exc:
            raise ModelComponentInitializationException(
                "Failed to initialize ModelCatalogueService.",
                cause=exc,
            ) from exc
        self._logger.info("ModelCatalogueService initialized.")
        return True

    async def ensure_indexes(
        self,
        component_configurations: ModelComponentConfigurations,
        overwrite: bool = False,
    ) -> bool:
        """Create or update all required database indexes.

        Creates full-text and HNSW indexes on ``ModelCatalogue`` and standard/full-text
        indexes on ``model_deployments`` according to ``component_configurations``.

        Args:
            component_configurations: Analyzer names and HNSW settings.
            overwrite: When ``True``, use OVERWRITE to force-update existing indexes.

        Returns:
            ``True`` on success.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            FullTextAnalyzerNotExistException: A referenced analyzer does not exist.
            ModelComponentOperationException: Index creation failures.
        """
        self._logger.debug("Ensuring indexes (overwrite=%s)...", overwrite)
        provider = self._provider()

        # Verify that the referenced analyzers exist via DatabaseManager.
        if self._database_manager is not None:
            for analyzer_name in (
                component_configurations.name_analyzer,
                component_configurations.description_analyzer,
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
                        "Create it via DatabaseManager before initializing ModelComponent."
                    )

        cat = self.CATALOGUE_COLLECTION_NAME()
        dep = self.DEPLOYMENT_COLLECTION_NAME()
        if_kw = "OVERWRITE" if overwrite else "IF NOT EXISTS"
        name_a = component_configurations.name_analyzer
        desc_a = component_configurations.description_analyzer

        indexes: list[tuple[str, str]] = [
            # --- ModelCatalogue indexes ---
            (
                "idx_model_catalogues_name_unique",
                f"DEFINE INDEX {if_kw} idx_model_catalogues_name_unique ON TABLE {cat} "
                f"FIELDS name UNIQUE CONCURRENTLY;",
            ),
            (
                "idx_model_catalogues_name_ft",
                f"DEFINE INDEX {if_kw} idx_model_catalogues_name_ft ON TABLE {cat} "
                f"FIELDS name SEARCH ANALYZER {name_a} BM25 CONCURRENTLY;",
            ),
            (
                "idx_model_catalogues_type",
                f"DEFINE INDEX {if_kw} idx_model_catalogues_type ON TABLE {cat} "
                f"FIELDS `type` CONCURRENTLY;",
            ),
            (
                "idx_model_catalogues_status",
                f"DEFINE INDEX {if_kw} idx_model_catalogues_status ON TABLE {cat} "
                f"FIELDS status CONCURRENTLY;",
            ),
            (
                "idx_model_catalogues_description",
                f"DEFINE INDEX {if_kw} idx_model_catalogues_description ON TABLE {cat} "
                f"FIELDS description SEARCH ANALYZER {desc_a} BM25 CONCURRENTLY;",
            ),
            (
                "idx_model_catalogues_tags",
                f"DEFINE INDEX {if_kw} idx_model_catalogues_tags ON TABLE {cat} "
                f"FIELDS tags CONCURRENTLY;",
            ),
            # HNSW vector index for description_vector.
            (
                "idx_model_catalogues_description_vector",
                f"DEFINE INDEX {if_kw} idx_model_catalogues_description_vector ON TABLE {cat} "
                f"FIELDS description_vector HNSW "
                f"DIMENSION {component_configurations.vector_dimensions} "
                f"TYPE {component_configurations.vector_data_type.value} "
                f"DIST {component_configurations.vector_search_method.value} "
                f"EFC {component_configurations.vector_exploration_factor} "
                f"M {component_configurations.vector_max_connections} CONCURRENTLY;",
            ),
            # --- model_deployments indexes ---
            (
                "idx_model_deployments_name_unique",
                f"DEFINE INDEX {if_kw} idx_model_deployments_name_unique ON TABLE {dep} "
                f"FIELDS name UNIQUE CONCURRENTLY;",
            ),
            (
                "idx_model_deployments_name_ft",
                f"DEFINE INDEX {if_kw} idx_model_deployments_name_ft ON TABLE {dep} "
                f"FIELDS name SEARCH ANALYZER {name_a} BM25 CONCURRENTLY;",
            ),
            (
                "idx_model_deployments_description",
                f"DEFINE INDEX {if_kw} idx_model_deployments_description ON TABLE {dep} "
                f"FIELDS description SEARCH ANALYZER {desc_a} BM25 CONCURRENTLY;",
            ),
            (
                "idx_model_deployments_tags",
                f"DEFINE INDEX {if_kw} idx_model_deployments_tags ON TABLE {dep} "
                f"FIELDS tags CONCURRENTLY;",
            ),
            (
                "idx_model_deployments_status",
                f"DEFINE INDEX {if_kw} idx_model_deployments_status ON TABLE {dep} "
                f"FIELDS status CONCURRENTLY;",
            ),
        ]

        for index_name, query in indexes:
            try:
                await provider.query_raw(query)
                self._logger.debug("Index ensured: %s", index_name)
            except Exception as exc:
                raise ModelComponentOperationException(
                    f"Failed to ensure index '{index_name}'.",
                    cause=exc,
                ) from exc

        self._logger.info("All indexes ensured.")
        return True

    # -------------------------------------------------------------------------
    # Catalogue CRUD
    # -------------------------------------------------------------------------

    async def create_catalogue_entry(
        self,
        catalogue: ModelCatalogueEntry,
    ) -> ModelCatalogueEntry:
        """Create a new ``ModelCatalogueEntry`` and its edge relationships.

        If ``description_vector`` is not set and ``description`` is non-empty,
        an embedding is generated automatically.

        Args:
            catalogue: Entry to persist.

        Returns:
            The created entry with its assigned id.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            InvalidModelCatalogueEntryException: Validation failure.
            ModelDeploymentNotFoundException: A referenced deployment does not exist.
            ModelComponentOperationException: Database failures.
        """
        self._logger.debug("Creating catalogue entry: %s", catalogue.name)
        provider = self._provider()

        # Auto-embed description if vector is missing.
        if catalogue.description_vector is None and catalogue.description:
            vector = await self._embed_description_text(catalogue.description)
            object.__setattr__(catalogue, "description_vector", vector)

        # Validate referenced deployments before writing.
        if catalogue.deployments:
            for dep_id in catalogue.deployments:
                dep = await self.get_deployment(dep_id)
                if dep is None:
                    raise ModelDeploymentNotFoundException(
                        f"Deployment '{dep_id}' referenced by catalogue entry does not exist.",
                        details={"deployment_id": dep_id},
                    )

        # Build CREATE query (omit id from content when auto-generating).
        cat = self.CATALOGUE_COLLECTION_NAME()
        if catalogue.id is None or catalogue.id == "":
            create_q = f"CREATE {cat} CONTENT {catalogue.to_json(exclude_id=True)};"
        else:
            create_q = (
                f"CREATE {self._thing_ref(cat, catalogue.id)} "
                f"CONTENT {catalogue.to_json(exclude_id=True)};"
            )

        try:
            raw = await provider.query_raw(create_q)
            raw = self._unwrap_raw_result(raw, provider)
        except Exception as exc:
            raise ModelComponentOperationException(
                f"Failed to create catalogue entry. Query: {create_q}. Error: {exc}",
                cause=exc,
            ) from exc

        if raw is None or (isinstance(raw, list) and len(raw) == 0):
            raise ModelComponentOperationException(
                "Create catalogue entry returned no result."
            )

        # Deserialize the created record.
        record_data = raw[0] if isinstance(raw, list) else raw
        record_data = self._unwrap_record(record_data, provider)
        created_id = self._doc_id_from_any(record_data.get("id") or record_data)
        if created_id is None:
            # Try to extract id from top-level dict.
            created_id = self._doc_id_from_any(record_data)

        # Create deployed_as edges for each linked deployment.
        if catalogue.deployments and created_id:
            for dep_id in catalogue.deployments:
                dep_key = self._record_key(dep_id)
                relate_q = (
                    f"RELATE {self._record_ref(cat, created_id)} "
                    f"-> deployed_as -> "
                    f"{self._record_ref(self.DEPLOYMENT_COLLECTION_NAME(), dep_key)};"
                )
                try:
                    await provider.query_raw(relate_q)
                except Exception as exc:
                    raise ModelComponentOperationException(
                        f"Failed to create deployed_as edge to '{dep_id}'.",
                        cause=exc,
                    ) from exc

        # Re-fetch with edge-resolved deployments.
        result = await self.get_catalogue_entry(created_id or "")
        if result is None:
            result = ModelCatalogueEntry.from_dict(self._normalize_catalogue_dict(record_data))
        self._logger.info("Created catalogue entry: id=%s", result.id)
        return result

    async def update_catalogue_entry(
        self,
        catalogue: ModelCatalogueEntry,
    ) -> ModelCatalogueEntry:
        """Update an existing ``ModelCatalogueEntry``.

        Handles description embedding, edge replacement, and transactional consistency.

        Args:
            catalogue: Entry with updated fields. ``id`` must be set.

        Returns:
            The updated entry.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            InvalidModelCatalogueEntryException: ``id`` is missing.
            ModelCatalogueEntryNotFoundException: No record with the given id.
            ModelDeploymentNotFoundException: A referenced deployment does not exist.
            ModelComponentOperationException: Database failures.
        """
        if not catalogue.id:
            raise InvalidModelCatalogueEntryException(
                "id is required when updating a catalogue entry."
            )
        self._logger.debug("Updating catalogue entry: id=%s", catalogue.id)
        provider = self._provider()

        # Fetch the current record to compare fields.
        previous = await self.get_catalogue_entry(catalogue.id)
        if previous is None:
            raise ModelCatalogueEntryNotFoundException(
                f"Catalogue entry not found: {catalogue.id}",
                details={"catalogue_id": catalogue.id},
            )

        # Update description_vector when description changes.
        description_changed = previous.description != catalogue.description
        if description_changed:
            if catalogue.description:
                vector = await self._embed_description_text(catalogue.description)
                object.__setattr__(catalogue, "description_vector", vector)
            else:
                object.__setattr__(catalogue, "description_vector", None)
        elif catalogue.description_vector is None:
            # Preserve the existing vector when description is unchanged.
            object.__setattr__(catalogue, "description_vector", previous.description_vector)

        # Validate referenced deployments.
        if catalogue.deployments:
            for dep_id in catalogue.deployments:
                dep = await self.get_deployment(dep_id)
                if dep is None:
                    raise ModelDeploymentNotFoundException(
                        f"Deployment '{dep_id}' referenced by catalogue entry does not exist.",
                        details={"deployment_id": dep_id},
                    )

        cat = self.CATALOGUE_COLLECTION_NAME()
        cat_key = self._record_key(catalogue.id)

        # Build transaction: UPDATE + delete old edges + create new edges.
        update_q = (
            f"UPDATE {self._thing_ref(cat, cat_key)} MERGE {catalogue.to_json(exclude_id=True)};"
        )
        delete_edges_q = f"DELETE deployed_as WHERE in = {self._thing_ref(cat, cat_key)};"

        tx_parts = [
            "BEGIN TRANSACTION;",
            update_q,
            delete_edges_q,
        ]

        if catalogue.deployments:
            for dep_id in catalogue.deployments:
                dep_key = self._record_key(dep_id)
                tx_parts.append(
                    f"RELATE {self._record_ref(cat, cat_key)} "
                    f"-> deployed_as -> "
                    f"{self._record_ref(self.DEPLOYMENT_COLLECTION_NAME(), dep_key)};"
                )

        tx_parts.append("COMMIT TRANSACTION;")
        tx_query = " ".join(tx_parts)

        try:
            await provider.query_raw(tx_query)
        except Exception as exc:
            raise ModelComponentOperationException(
                f"Failed to update catalogue entry '{catalogue.id}'.",
                cause=exc,
            ) from exc

        # Re-fetch to return the fully updated record.
        result = await self.get_catalogue_entry(cat_key)
        if result is None:
            raise ModelCatalogueEntryNotFoundException(
                f"Catalogue entry not found after update: {catalogue.id}",
                details={"catalogue_id": catalogue.id},
            )
        self._logger.info("Updated catalogue entry: id=%s", result.id)
        return result

    async def get_catalogue_entry(
        self,
        id: str,
    ) -> ModelCatalogueEntry | None:
        """Retrieve a catalogue entry by record id.

        Args:
            id: Record id (with or without table prefix).

        Returns:
            Matching entry with ``deployments`` resolved from edges, or ``None``.
        """
        self._logger.debug("Getting catalogue entry: id=%s", id)
        provider = self._provider()
        cat = self.CATALOGUE_COLLECTION_NAME()
        key = self._record_key(id)
        query = (
            f"SELECT *, ->deployed_as->model_deployments.id AS deployments "
            f"FROM {self._thing_ref(cat, key)};"
        )
        try:
            raw = await provider.query_raw(query)
            raw = self._unwrap_raw_result(raw, provider)
        except Exception as exc:
            raise ModelComponentOperationException(
                f"Failed to get catalogue entry '{id}'.",
                cause=exc,
            ) from exc

        if raw is None or (isinstance(raw, list) and len(raw) == 0):
            return None
        record = raw[0] if isinstance(raw, list) else raw
        record = self._unwrap_record(record, provider)
        return ModelCatalogueEntry.from_dict(self._normalize_catalogue_dict(record))

    async def get_all_catalogue_entries(self) -> list[ModelCatalogueEntry]:
        """Retrieve all catalogue entries with edge-resolved deployments.

        Returns:
            All entries. Empty list if none.
        """
        self._logger.debug("Getting all catalogue entries.")
        provider = self._provider()
        cat = self.CATALOGUE_COLLECTION_NAME()
        query = (
            f"SELECT *, ->deployed_as->model_deployments.id AS deployments FROM {cat};"
        )
        try:
            raw = await provider.query_raw(query)
            raw = self._unwrap_raw_result(raw, provider)
        except Exception as exc:
            raise ModelComponentOperationException(
                "Failed to get all catalogue entries.",
                cause=exc,
            ) from exc

        if raw is None:
            return []
        items = raw if isinstance(raw, list) else [raw]
        results: list[ModelCatalogueEntry] = []
        for item in items:
            record = self._unwrap_record(item, provider)
            results.append(
                ModelCatalogueEntry.from_dict(self._normalize_catalogue_dict(record))
            )
        return results

    async def search_catalogue_entries(
        self,
        catalogue_search_criteria: ModelCatalogueSearchCriteria,
    ) -> list[ModelCatalogueSearchResultEntry]:
        """Search catalogue entries using the provided criteria.

        Builds a SurrealQL query via ``ModelCatalogueSearchCriteria.to_query`` and
        returns the matching entries.

        Args:
            catalogue_search_criteria: Filters (name, type, status, keywords, tags,
                vector similarity).

        Returns:
            Matching entries. Empty list if none.
        """
        self._logger.debug("Searching catalogue entries: %s", catalogue_search_criteria)
        provider = self._provider()
        query = catalogue_search_criteria.to_query(
            provider, self.CATALOGUE_COLLECTION_NAME()
        )
        self._logger.debug("Search query: %s", query)
        try:
            raw = await provider.query_raw(query)
            raw = self._unwrap_raw_result(raw, provider)
        except Exception as exc:
            raise ModelComponentOperationException(
                f"Failed to search catalogue entries. Query: {query}.",
                cause=exc,
            ) from exc

        if raw is None:
            return []
        items = raw if isinstance(raw, list) else [raw]
        results: list[ModelCatalogueSearchResultEntry] = []
        for item in items:
            record = self._unwrap_record(item, provider)
            results.append(
                ModelCatalogueSearchResultEntry.from_dict(
                    self._normalize_catalogue_dict(record)
                )
            )
        self._logger.debug("Search returned %d catalogue entries.", len(results))
        return results

    async def delete_catalogue_entry(
        self,
        id: str,
    ) -> None:
        """Delete a catalogue entry and its outbound ``deployed_as`` edges.

        Args:
            id: Record id of the entry to delete.

        Raises:
            ModelCatalogueEntryNotFoundException: No record with the given id.
            ModelComponentOperationException: Database failures.
        """
        self._logger.debug("Deleting catalogue entry: id=%s", id)
        provider = self._provider()
        cat = self.CATALOGUE_COLLECTION_NAME()
        key = self._record_key(id)

        tx_query = (
            f"BEGIN TRANSACTION; "
            f"DELETE deployed_as WHERE in = {self._thing_ref(cat, key)}; "
            f"DELETE {self._thing_ref(cat, key)} RETURN BEFORE; "
            f"COMMIT TRANSACTION;"
        )

        try:
            raw = await provider.query_raw(tx_query)
        except Exception as exc:
            raise ModelComponentOperationException(
                f"Failed to delete catalogue entry '{id}'.",
                cause=exc,
            ) from exc

        # Check whether the DELETE actually removed a record.
        deleted = self._check_delete_result(raw)
        if not deleted:
            raise ModelCatalogueEntryNotFoundException(
                f"Catalogue entry not found: {id}",
                details={"catalogue_id": id},
            )
        self._logger.info("Deleted catalogue entry: id=%s", id)

    # -------------------------------------------------------------------------
    # Deployment CRUD
    # -------------------------------------------------------------------------

    async def create_deployment(
        self,
        deployment: ModelDeployment,
    ) -> ModelDeployment:
        """Create a new ``ModelDeployment`` and its edge relationships.

        Args:
            deployment: Deployment to persist.

        Returns:
            The created deployment with its assigned id.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            InvalidModelDeploymentException: Validation failure.
            ModelComponentOperationException: Database failures.
        """
        self._logger.debug("Creating deployment: %s", deployment.name)
        provider = self._provider()
        dep = self.DEPLOYMENT_COLLECTION_NAME()

        if deployment.id is None or deployment.id == "":
            create_q = f"CREATE {dep} CONTENT {deployment.to_json(exclude_id=True)};"
        else:
            key = self._record_key(deployment.id)
            create_q = (
                f"CREATE {self._thing_ref(dep, key)} "
                f"CONTENT {deployment.to_json(exclude_id=True)};"
            )

        try:
            raw = await provider.query_raw(create_q)
            raw = self._unwrap_raw_result(raw, provider)
        except Exception as exc:
            raise ModelComponentOperationException(
                f"Failed to create deployment. Error: {exc}",
                cause=exc,
            ) from exc

        if raw is None or (isinstance(raw, list) and len(raw) == 0):
            raise ModelComponentOperationException("Create deployment returned no result.")

        record_data = raw[0] if isinstance(raw, list) else raw
        record_data = self._unwrap_record(record_data, provider)
        created_id = self._doc_id_from_any(record_data.get("id") or record_data)

        # Create references_secret edges.
        if deployment.secrets and created_id:
            for secret_id in deployment.secrets:
                s_key = self._record_key(secret_id)
                relate_q = (
                    f"RELATE {self._record_ref(dep, created_id)} "
                    f"-> references_secret -> "
                    f"{self._record_ref('Secrets', s_key)};"
                )
                try:
                    await provider.query_raw(relate_q)
                except Exception as exc:
                    raise ModelComponentOperationException(
                        f"Failed to create references_secret edge to '{secret_id}'.",
                        cause=exc,
                    ) from exc

        # Re-fetch with edge-resolved secrets.
        result = await self.get_deployment(created_id or "")
        if result is None:
            result = ModelDeployment.from_dict(self._normalize_deployment_dict(record_data))
        self._logger.info("Created deployment: id=%s", result.id)
        return result

    async def update_deployment(
        self,
        deployment: ModelDeployment,
    ) -> ModelDeployment:
        """Update an existing ``ModelDeployment``.

        Args:
            deployment: Deployment with updated fields. ``id`` must be set.

        Returns:
            The updated deployment.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            InvalidModelDeploymentException: ``id`` is missing.
            ModelDeploymentNotFoundException: No record with the given id.
            ModelComponentOperationException: Database failures.
        """
        if not deployment.id:
            raise InvalidModelDeploymentException(
                "id is required when updating a deployment."
            )
        self._logger.debug("Updating deployment: id=%s", deployment.id)
        provider = self._provider()
        dep = self.DEPLOYMENT_COLLECTION_NAME()
        key = self._record_key(deployment.id)

        # Verify that the record exists.
        existing = await self.get_deployment(deployment.id)
        if existing is None:
            raise ModelDeploymentNotFoundException(
                f"Deployment not found: {deployment.id}",
                details={"deployment_id": deployment.id},
            )

        # Transactional update + edge replacement.
        tx_parts = [
            "BEGIN TRANSACTION;",
            f"UPDATE {self._thing_ref(dep, key)} MERGE {deployment.to_json(exclude_id=True)};",
            f"DELETE references_secret WHERE in = {self._thing_ref(dep, key)};",
        ]

        if deployment.secrets:
            for secret_id in deployment.secrets:
                s_key = self._record_key(secret_id)
                tx_parts.append(
                    f"RELATE {self._record_ref(dep, key)} "
                    f"-> references_secret -> "
                    f"{self._record_ref('Secrets', s_key)};"
                )

        tx_parts.append("COMMIT TRANSACTION;")
        tx_query = " ".join(tx_parts)

        try:
            await provider.query_raw(tx_query)
        except Exception as exc:
            raise ModelComponentOperationException(
                f"Failed to update deployment '{deployment.id}'.",
                cause=exc,
            ) from exc

        result = await self.get_deployment(key)
        if result is None:
            raise ModelDeploymentNotFoundException(
                f"Deployment not found after update: {deployment.id}",
                details={"deployment_id": deployment.id},
            )
        self._logger.info("Updated deployment: id=%s", result.id)
        return result

    async def get_deployment(
        self,
        id: str,
    ) -> ModelDeployment | None:
        """Retrieve a deployment by record id.

        Args:
            id: Record id (with or without table prefix).

        Returns:
            Matching deployment with ``secrets`` resolved from edges, or ``None``.
        """
        self._logger.debug("Getting deployment: id=%s", id)
        provider = self._provider()
        dep = self.DEPLOYMENT_COLLECTION_NAME()
        key = self._record_key(id)
        query = (
            f"SELECT *, ->references_secret->Secrets.id AS secrets "
            f"FROM {self._thing_ref(dep, key)};"
        )
        try:
            raw = await provider.query_raw(query)
            raw = self._unwrap_raw_result(raw, provider)
        except Exception as exc:
            raise ModelComponentOperationException(
                f"Failed to get deployment '{id}'.",
                cause=exc,
            ) from exc

        if raw is None or (isinstance(raw, list) and len(raw) == 0):
            return None
        record = raw[0] if isinstance(raw, list) else raw
        record = self._unwrap_record(record, provider)
        return ModelDeployment.from_dict(self._normalize_deployment_dict(record))

    async def search_deployments(
        self,
        search_criteria: ModelDeploymentSearchCriteria,
    ) -> list[ModelDeployment]:
        """Search deployments using the provided criteria.

        Args:
            search_criteria: Filters (name, deployment_type, status, keywords, tags).

        Returns:
            Matching deployments. Empty list if none.
        """
        self._logger.debug("Searching deployments: %s", search_criteria)
        provider = self._provider()
        query = search_criteria.to_query(provider, self.DEPLOYMENT_COLLECTION_NAME())
        self._logger.debug("Search query: %s", query)
        try:
            raw = await provider.query_raw(query)
            raw = self._unwrap_raw_result(raw, provider)
        except Exception as exc:
            raise ModelComponentOperationException(
                f"Failed to search deployments. Query: {query}.",
                cause=exc,
            ) from exc

        if raw is None:
            return []
        items = raw if isinstance(raw, list) else [raw]
        results: list[ModelDeployment] = []
        for item in items:
            record = self._unwrap_record(item, provider)
            results.append(
                ModelDeployment.from_dict(self._normalize_deployment_dict(record))
            )
        self._logger.debug("Search returned %d deployments.", len(results))
        return results

    async def delete_deployment(
        self,
        id: str,
    ) -> None:
        """Delete a deployment, its outbound ``references_secret`` edges, and any
        inbound ``deployed_as`` edges pointing to it.

        Args:
            id: Record id of the deployment to delete.

        Raises:
            ModelDeploymentNotFoundException: No record with the given id.
            ModelComponentOperationException: Database failures.
        """
        self._logger.debug("Deleting deployment: id=%s", id)
        provider = self._provider()
        dep = self.DEPLOYMENT_COLLECTION_NAME()
        key = self._record_key(id)

        tx_query = (
            f"BEGIN TRANSACTION; "
            f"DELETE deployed_as WHERE out = {self._thing_ref(dep, key)}; "
            f"DELETE references_secret WHERE in = {self._thing_ref(dep, key)}; "
            f"DELETE {self._thing_ref(dep, key)} RETURN BEFORE; "
            f"COMMIT TRANSACTION;"
        )

        try:
            raw = await provider.query_raw(tx_query)
        except Exception as exc:
            raise ModelComponentOperationException(
                f"Failed to delete deployment '{id}'.",
                cause=exc,
            ) from exc

        deleted = self._check_delete_result(raw)
        if not deleted:
            raise ModelDeploymentNotFoundException(
                f"Deployment not found: {id}",
                details={"deployment_id": id},
            )
        self._logger.info("Deleted deployment: id=%s", id)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _check_delete_result(raw: Any) -> bool:
        """Determine whether a ``DELETE ... RETURN BEFORE`` query deleted a record.

        SurrealDB returns the previous record content from DELETE RETURN BEFORE.
        A non-empty result means a record was deleted.
        """
        if raw is None:
            return False
        if isinstance(raw, list):
            if len(raw) == 0:
                return False
            # Transaction result: list of per-statement results.
            # The DELETE RETURN BEFORE is the second-to-last statement (before COMMIT).
            if isinstance(raw[-1], dict) and "result" in raw[-1]:
                # Envelope format — find the last non-empty result.
                for item in reversed(raw):
                    res = item.get("result") if isinstance(item, dict) else None
                    if res is not None and res != [] and res != {}:
                        return True
                return False
            # Plain list of records.
            last = raw[-1]
            if isinstance(last, list):
                return len(last) > 0
            if isinstance(last, dict):
                return len(last) > 0
            return False
        if isinstance(raw, dict):
            return len(raw) > 0
        return False
