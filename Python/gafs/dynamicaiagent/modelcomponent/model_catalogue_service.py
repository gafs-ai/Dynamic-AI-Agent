"""Model catalogue service and search criteria.

Provides ModelCatalogueService (CRUD and search over the model catalogue)
and related types: search criteria, vector/tags criteria, and HNSW search methods.

Indexes created in initialize():
- model_catalogues: description_vector (HNSW), name / description (fulltext),
  type / status / tags (standard), as described in _initialize_indexes().
- model_deployments: name (fulltext, name_analyzer), description (fulltext,
  english_paragraph_analyzer), tags and status (standard), mirroring catalogue
  patterns for those fields.
FTS analyzers: name_analyzer (model name / deployment name), english_paragraph_analyzer
(description). Catalogue name and description are assumed to be primarily in English.
SurrealDB 1.x/2.x: SEARCH ANALYZER. SurrealDB 3.0+ uses FULLTEXT ANALYZER (see
https://surrealdb.com/docs/surrealdb/models/full-text-search).
"""
from __future__ import annotations

import logging
from typing import Any, override

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider, SurrealDbRemoteProvider

from .i_model_catalogue_service import IModelCatalogueService
from .models.model_catalogue import ModelCatalogue, ModelCatalogueSearchResultEntry,ModelDeployment
from .models.model_component_configurations import ModelComponentConfigurations
from .models.hnsw_search_method import HnswSearchMethod
from .models.model_catalogue_search_criteria import (
    LogicalOperator,
    ModelCatalogueSearchCriteria,
    TagsSearchCriteria,
    VectorSearchCriteria,
)
from .models.model_deployment_search_criteria import ModelDeploymentSearchCriteria
from .models.ai_connection_parameters import AiConnectionParameters
from .models.ai_operation_type import AiOperationType
from .models.ai_payload import EmbeddingPayload
from .models.ai_request import AiRequest


class ModelCatalogueService(IModelCatalogueService):
    """Service for model catalogue CRUD and search.

    Uses a database manager to obtain a provider (e.g. SurrealDbRemoteProvider)
    and performs create, read, update, delete, and search operations on the
    model catalogue collection.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the service with a logger.

        Args:
            logger: Logger instance for debug, , and error messages.
        """
        self._logger: logging.Logger = logger
        self._database_manager: IDatabaseManager | None = None
        self._database_provider: IDatabaseProvider | None = None

    @staticmethod
    def _doc_id_from_any(x: Any) -> str | None:
        """Extract document id from common SurrealDB link representations."""
        if x is None:
            return None
        if isinstance(x, str):
            return x.split(":")[-1] if ":" in x else x
        if isinstance(x, dict):
            for k in ("id", "$id", "rid", "record_id", "@rid"):
                v = x.get(k)
                if isinstance(v, str):
                    return v.split(":")[-1] if ":" in v else v
            v = x.get("value")
            if isinstance(v, dict):
                for k in ("id", "$id", "rid", "record_id", "@rid"):
                    vv = v.get(k)
                    if isinstance(vv, str):
                        return vv.split(":")[-1] if ":" in vv else vv
        for attr in ("id", "rid", "record_id"):
            if hasattr(x, attr):
                cand = getattr(x, attr)
                if isinstance(cand, str):
                    return cand.split(":")[-1] if ":" in cand else cand
        try:
            s = str(x)
            if s:
                return s.split(":")[-1] if ":" in s else s
        except Exception:
            pass
        return None

    def _normalize_catalogue_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize catalogue payload into the model-expected shape."""
        normalized: dict[str, Any] = dict(data)

        # Model expects: deployments: list[str] (document ids only).
        if "deployments" in normalized and isinstance(normalized.get("deployments"), list):
            out: list[str] = []
            for item in normalized["deployments"]:
                doc_id = self._doc_id_from_any(item)
                if doc_id is not None:
                    out.append(doc_id)
            normalized["deployments"] = out

        return normalized

    @staticmethod
    def _normalize_deployment_record_id(deployment_id: str) -> str:
        """Return full table:id form for a deployment record id."""
        table = IModelCatalogueService.DEPLOYMENT_COLLECTION_NAME()
        if ":" in deployment_id:
            return deployment_id
        return f"{table}:{deployment_id}"

    @staticmethod
    def _escape_surreal_string_literal(value: str) -> str:
        """Escape single quotes for use inside SurrealQL string literals."""
        return value.replace("'", "''")

    @classmethod
    def _thing_ref(cls, table: str, record_key: str) -> str:
        """SurrealQL record reference safe for arbitrary id strings (e.g. hyphens)."""
        t = cls._escape_surreal_string_literal(table)
        k = cls._escape_surreal_string_literal(record_key)
        return f"type::thing('{t}', '{k}')"

    @staticmethod
    def _deployment_record_key(id_value: str) -> str:
        """Return the record id part after the table prefix, if any."""
        return id_value.split(":", 1)[1] if ":" in id_value else id_value

    @staticmethod
    def _delete_return_before_payload_had_row(payload: Any) -> bool:
        """True if DELETE ... RETURN BEFORE payload indicates a row existed."""
        if payload is None:
            return False
        if isinstance(payload, dict):
            return len(payload) > 0
        if isinstance(payload, list):
            return len(payload) > 0
        return True

    @staticmethod
    def _delete_return_before_had_row(raw: Any) -> bool:
        """Parse SurrealDB result for DELETE ... RETURN BEFORE.

        ``query_raw`` may return (a) a list of per-statement results for a
        transaction (second-to-last is DELETE before COMMIT), (b) the inner
        ``result`` for a single-statement DELETE (dict or list of records), or
        (c) a single record dict.
        """
        if raw is None:
            return False
        if isinstance(raw, dict) and len(raw) > 0 and "result" not in raw:
            return True
        if isinstance(raw, list) and len(raw) >= 2:
            first = raw[0]
            if isinstance(first, dict) and "result" in first and "status" in first:
                last_stmt = raw[-1]
                last_res: Any = (
                    last_stmt.get("result") if isinstance(last_stmt, dict) else None
                )
                if last_res in (None, [], {}):
                    delete_payload = raw[-2].get("result")
                else:
                    delete_payload = last_res
                return ModelCatalogueService._delete_return_before_payload_had_row(
                    delete_payload
                )
        if not isinstance(raw, list) or len(raw) == 0:
            return False
        last = raw[-1]
        if isinstance(last, list):
            return len(last) > 0
        if isinstance(last, dict):
            return len(last) > 0
        return False

    @staticmethod
    def _set_description_vector(
        catalogue: ModelCatalogue,
        vector: list[float] | None,
    ) -> None:
        """Set description_vector while allowing None values."""
        object.__setattr__(catalogue, "description_vector", vector)

    async def _get_component_configurations(self) -> ModelComponentConfigurations:
        """Load model component configuration document."""
        provider = self._database_provider
        if provider is None and self._database_manager is not None:
            provider = self._database_manager.get_default_database_provider()
        if provider is None:
            raise ValueError("Default database provider is not available.")
        rid = (
            f"{ModelComponentConfigurations.COLLECTION_NAME()}:"
            f"{ModelComponentConfigurations.DEFAULT_DOCUMENT_ID()}"
        )
        query = f"SELECT * FROM {rid};"
        config = await provider.query(query, ModelComponentConfigurations)
        if config is None:
            return ModelComponentConfigurations()
        return config

    async def _embed_description_text(self, description: str) -> list[float] | None:
        """Return embedding vector for description or None on missing config/error."""
        try:
            config = await self._get_component_configurations()
        except Exception as e:
            self._logger.error(
                "Failed to load component configuration for embedding. description_vector is cleared. Error: %s",
                e,
            )
            return None

        if config.embedding_catalogue_id is None or config.embedding_catalogue_id == "":
            self._logger.warning(
                "embedding_catalogue_id is not configured. description_vector is cleared."
            )
            return None

        embedding_catalogue = await self.get_catalogue(config.embedding_catalogue_id)
        if embedding_catalogue is None:
            self._logger.warning(
                "Embedding catalogue is not found (id=%s). description_vector is cleared.",
                config.embedding_catalogue_id,
            )
            return None

        deployment_id: str | None = None
        if config.embedding_deployment_id is not None and config.embedding_deployment_id != "":
            deployment_id = config.embedding_deployment_id
        elif embedding_catalogue.deployments is not None and len(embedding_catalogue.deployments) > 0:
            deployment_id = embedding_catalogue.deployments[0]

        if deployment_id is None:
            self._logger.warning(
                "No embedding deployment is available. description_vector is cleared."
            )
            return None

        deployment = await self.get_deployment(deployment_id)
        if deployment is None:
            self._logger.warning(
                "Embedding deployment is not found (id=%s). description_vector is cleared.",
                deployment_id,
            )
            return None

        try:
            connection = AiConnectionParameters(
                operation_type=AiOperationType.EMBEDDING,
                deployment_type=deployment.deployment_type,
                provider_type=deployment.provider_type,
            )
            if deployment.connection_parameters is not None:
                connection.parameters = deployment.connection_parameters

            payload = EmbeddingPayload()
            payload.input = description
            request = AiRequest(operation_type=AiOperationType.EMBEDDING, payload=payload)

            provider = self._database_provider
            if provider is None:
                raise ValueError("ModelCatalogueService is not initialized.")
            invoke_fn = getattr(provider, "invoke", None)
            if invoke_fn is None:
                raise ValueError("Default database provider does not support invoke().")
            response = await invoke_fn(connection, request)
            output = response.output
            if output is None or not hasattr(output, "embedding"):
                self._logger.error(
                    "Embedding response has no embedding output. description_vector is cleared."
                )
                return None
            embedding = getattr(output, "embedding")
            if not isinstance(embedding, list):
                self._logger.error(
                    "Embedding response type is invalid. description_vector is cleared."
                )
                return None
            return [float(v) for v in embedding]
        except Exception as e:
            self._logger.error(
                "Embedding request failed. description_vector is cleared. Error: %s",
                e,
            )
            return None

    async def initialize(
        self,
        database_manager: IDatabaseManager,
        component_configurations: ModelComponentConfigurations,
        database_provider: IDatabaseProvider | None = None,
    ) -> bool:
        """Set the database manager and collection name, and ensure indexes exist.

        Must be called before any catalogue operations. Creates indexes only when
        they do not exist (DEFINE INDEX IF NOT EXISTS). If an index already
        exists, that is treated as success.

        Args:
            database_manager: Manager that provides the database provider.

        Returns:
            True on success (including when indexes already exist).
        """
        self._logger.debug("Initializing model catalogue service...")
        self._database_manager = database_manager
        self._database_provider = database_provider
        if self._database_provider is None:
            self._database_provider = self._database_manager.get_default_database_provider()
        if self._database_provider is None:
            raise ValueError("Default database provider is not available.")

        await self._initialize_indexes(component_configurations)
        self._logger.info("Model catalogue service is initialized.")
        return True

    @override
    async def ensure_indexes(
        self,
        component_configurations: ModelComponentConfigurations,
        overwrite: bool = False,
    ) -> bool:
        """Ensure catalogue/deployment indexes are present."""
        await self._initialize_indexes(
            component_configurations=component_configurations,
            overwrite=overwrite,
        )
        return True

    async def _initialize_indexes(
        self,
        component_configurations: ModelComponentConfigurations,
        overwrite: bool = False
    ) -> None:
        """Create Analyzers and Indexes"""

        try:
            provider: IDatabaseProvider | None = None
            if self._database_manager:
                provider = self._database_manager.get_default_database_provider()
        except Exception as e:  # noqa: BLE001
            message:str = "Could not get database provider while initializing indexes."
            self._logger.error(message)
            raise Exception(message) from e
        if provider is None:
            message:str = "No default database provider found while initializing indexes."
            self._logger.error(message)
            raise Exception(message)

        catalogue_table = IModelCatalogueService.CATALOGUE_COLLECTION_NAME()
        deployment_table = IModelCatalogueService.DEPLOYMENT_COLLECTION_NAME()

        # Analyzer for Name ("name_analyzer")
        query: str = "DEFINE ANALYZER IF NOT EXISTS name_analyzer TOKENIZERS class FILTERS ascii, lowercase;"
        
        try:
            await provider.query_raw(query)
        except Exception as e:
            message: str = f"Failed to create analyzer: 'name_analyzer'."
            self._logger.error(message)
            raise Exception(message) from e

        # Analyzer for Description ("english_paragraph_analyzer")
        query: str = "DEFINE ANALYZER IF NOT EXISTS english_paragraph_analyzer TOKENIZERS blank, punct FILTERS ascii, lowercase, snowball(english);"

        try:
            await provider.query_raw(query)
        except Exception as e:
            message: str = f"Failed to create analyzer: 'english_paragraph_analyzer'."
            self._logger.error(message)
            raise Exception(message) from e

        # Model Name Index(Full Text)
        query: str = (
            f"DEFINE INDEX IF NOT EXISTS idx_model_catalogues_name ON TABLE {catalogue_table} "
            f"FIELDS name SEARCH ANALYZER name_analyzer BM25 CONCURRENTLY;"
        )

        try:
            await provider.query_raw(query)
        except Exception as e:
            message: str = f"Failed to create index: 'idx_model_catalogues_name'."
            self._logger.error(message)
            raise Exception(message) from e

        # Model Type Index
        query: str = (
            f"DEFINE INDEX IF NOT EXISTS idx_model_catalogues_type ON TABLE {catalogue_table} "
            f"FIELDS `type` CONCURRENTLY;"
        )

        try:
            await provider.query_raw(query)
        except Exception as e:
            message: str = f"Failed to create index: 'idx_model_catalogues_type'."
            self._logger.error(message)
            raise Exception(message) from e

        # Status Index
        query: str = (
            f"DEFINE INDEX IF NOT EXISTS idx_model_catalogues_status ON TABLE {catalogue_table} "
            f"FIELDS status CONCURRENTLY;"
        )

        try:
            await provider.query_raw(query)
        except Exception as e:
            message: str = f"Failed to create index: 'idx_model_catalogues_status'."
            self._logger.error(message)
            raise Exception(message) from e

        # Description Index (Full Text)
        query: str = (
            f"DEFINE INDEX IF NOT EXISTS idx_model_catalogues_description ON TABLE {catalogue_table} "
            f"FIELDS description SEARCH ANALYZER english_paragraph_analyzer BM25 CONCURRENTLY;"
        )

        try:
            await provider.query_raw(query)
        except Exception as e:
            message: str = f"Failed to create index: 'idx_model_catalogues_description'."
            self._logger.error(message)
            raise Exception(message) from e

        # Description Vector Index (HNSW)
        if overwrite:
            query: str = (
                f"DEFINE INDEX OVERWRITE idx_model_catalogues_description_vector ON TABLE {catalogue_table} "
                f"FIELDS description_vector HNSW DIMENSION {component_configurations.vector_dimensions} "
                f"TYPE {component_configurations.vector_data_type.value} DIST {component_configurations.vector_search_method.value} "
                f"EFC {component_configurations.vector_exploration_factor} "
                f"M {component_configurations.vector_max_connections} CONCURRENTLY;"
            )
        else:
            query: str = (
                f"DEFINE INDEX IF NOT EXISTS idx_model_catalogues_description_vector ON TABLE {catalogue_table} "
                f"FIELDS description_vector HNSW DIMENSION {component_configurations.vector_dimensions} "
                f"TYPE F64 DIST {component_configurations.vector_search_method.value} "
                f"EFC {component_configurations.vector_exploration_factor} "
                f"M {component_configurations.vector_max_connections} CONCURRENTLY;"
            )

        try:
            await provider.query_raw(query)
        except Exception as e:
            message: str = f"Failed to create index: 'idx_model_catalogues_description_vector'."
            self._logger.error(message)
            raise Exception(message) from e

        # Tags Index
        query: str = (
            f"DEFINE INDEX IF NOT EXISTS idx_model_catalogues_tags ON TABLE {catalogue_table} "
            f"FIELDS tags CONCURRENTLY;"
        )

        try:
            await provider.query_raw(query)
        except Exception as e:
            message: str = f"Failed to create index: 'idx_model_catalogues_tags'."
            self._logger.error(message)
            raise Exception(message) from e

        # Deployment: name (fulltext, same analyzer as catalogue name)
        query = (
            f"DEFINE INDEX IF NOT EXISTS idx_model_deployments_name ON TABLE {deployment_table} "
            f"FIELDS name SEARCH ANALYZER name_analyzer BM25 CONCURRENTLY;"
        )
        try:
            await provider.query_raw(query)
        except Exception as e:
            message: str = "Failed to create index: 'idx_model_deployments_name'."
            self._logger.error(message)
            raise Exception(message) from e

        # Deployment: description (fulltext, same analyzer as catalogue description)
        query = (
            f"DEFINE INDEX IF NOT EXISTS idx_model_deployments_description ON TABLE {deployment_table} "
            f"FIELDS description SEARCH ANALYZER english_paragraph_analyzer BM25 CONCURRENTLY;"
        )
        try:
            await provider.query_raw(query)
        except Exception as e:
            message: str = "Failed to create index: 'idx_model_deployments_description'."
            self._logger.error(message)
            raise Exception(message) from e

        # Deployment: tags (standard index, same pattern as catalogue tags)
        query = (
            f"DEFINE INDEX IF NOT EXISTS idx_model_deployments_tags ON TABLE {deployment_table} "
            f"FIELDS tags CONCURRENTLY;"
        )
        try:
            await provider.query_raw(query)
        except Exception as e:
            message: str = "Failed to create index: 'idx_model_deployments_tags'."
            self._logger.error(message)
            raise Exception(message) from e

        # Deployment: status (standard index, same pattern as catalogue status)
        query = (
            f"DEFINE INDEX IF NOT EXISTS idx_model_deployments_status ON TABLE {deployment_table} "
            f"FIELDS status CONCURRENTLY;"
        )
        try:
            await provider.query_raw(query)
        except Exception as e:
            message: str = "Failed to create index: 'idx_model_deployments_status'."
            self._logger.error(message)
            raise Exception(message) from e

    @override
    async def create_catalogue(self, catalogue: ModelCatalogue) -> ModelCatalogue:
        """Create a new model catalogue record.

        If catalogue.id is None or empty, the store generates an ID.
        Otherwise the record is created with the given id.

        Args:
            catalogue: Model catalogue data. id may be "" or None to
                request an auto-generated ID.

        Returns:
            The created catalogue (with id set).

        Raises:
            Exception: When the database provider is unavailable or the
                create operation fails.
        """
        self._logger.debug(
            "Creating Model Catalogue. Input: %s", catalogue
        )

        try:
            database_provider: SurrealDbRemoteProvider = (
                self._database_manager.get_default_database_provider()
            )
        except Exception as e:
            message: str = f"Failed to get database provider. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        # Attempt to embed description if description-vector is not provided
        if catalogue.description_vector is None:
            if catalogue.description is not None and catalogue.description != "":
                vector = await self._embed_description_text(catalogue.description)
                self._set_description_vector(catalogue, vector)

        if catalogue.id is None or catalogue.id == "":
            # When requesting auto-generated IDs, do not send an empty/blank `id`
            # field in the content payload.
            query: str = (
                f"CREATE {IModelCatalogueService.CATALOGUE_COLLECTION_NAME()} CONTENT {catalogue.to_json(exclude_id=True)};"
            )
        else:
            query: str = (
                f"CREATE {ModelCatalogueService._thing_ref(IModelCatalogueService.CATALOGUE_COLLECTION_NAME(), catalogue.id)} "
                f"CONTENT {catalogue.to_json()};"
            )

        self._logger.debug(
            "Creating Model Catalogue with query: %s", query
        )

        try:
            result: ModelCatalogue = await database_provider.query(query, ModelCatalogue)
        except Exception as e:
            message = f"Failed to create model catalogue. Query: {query}. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        self._logger.info(
            "Created Model Catalogue: %s", result
        )

        return result

    @override
    async def update_catalogue(self, catalogue: ModelCatalogue) -> ModelCatalogue:
        """Update an existing model catalogue record.

        Args:
            catalogue: Catalogue with id and updated fields.

        Returns:
            The updated catalogue as returned by the store.

        Raises:
            ValueError: When id is None or empty.
            Exception: When the database provider is unavailable or the
                update operation fails.
        """
        self._logger.debug(
            "Updating Model Catalogue: %s", catalogue
        )

        try:
            database_provider = self._database_manager.get_default_database_provider()
        except Exception as e:
            message = f"Failed to get database provider. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        if catalogue.id is None or catalogue.id == "":
            message = "Id is required when updating a model catalogue."
            self._logger.error(message)
            raise ValueError(message)

        previous = await self.get_catalogue(catalogue.id)
        if previous is None:
            message = f"Model catalogue not found for update: {catalogue.id}"
            self._logger.error(message)
            raise ValueError(message)

        description_changed = previous.description != catalogue.description
        # If the description has changed but vector is not changed or is None, embed the new description and set the vector
        if description_changed:
            if catalogue.description_vector is None or catalogue.description_vector == [] or catalogue.description_vector == previous.description_vector:
                vector = await self._embed_description_text(catalogue.description)
                self._set_description_vector(catalogue, vector)
        # If the description is not changed, use the previous description vector
        else:
            if catalogue.description_vector is None:
                self._set_description_vector(catalogue, previous.description_vector)

        query = (
            f"UPDATE {ModelCatalogueService._thing_ref(IModelCatalogueService.CATALOGUE_COLLECTION_NAME(), catalogue.id)} "
            f"MERGE {catalogue.to_json()};"
        )
        self._logger.debug(
            "Updating Model Catalogue with query: %s", query
        )
        try:
            result = await database_provider.query(query, ModelCatalogue)
        except Exception as e:
            message = f"Failed to update model catalogue. Query: {query}. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        self._logger.info(
            "Updated Model Catalogue: %s", result
        )

        return result

    @override
    async def get_catalogue(self, id: str) -> ModelCatalogue | None:
        """Get a single model catalogue by ID.

        Args:
            id: Record ID of the catalogue.

        Returns:
            The catalogue if found, None otherwise.

        Raises:
            Exception: When the database provider is unavailable or the
                query fails.
        """
        self._logger.debug(
            "Getting Model Catalogue by ID: %s", id
        )

        try:
            database_provider = self._database_manager.get_default_database_provider()
        except Exception as e:
            message = f"Failed to get database provider. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        query = (
            f"SELECT * FROM {ModelCatalogueService._thing_ref(IModelCatalogueService.CATALOGUE_COLLECTION_NAME(), id)};"
        )
        self._logger.debug(
            "Getting Model Catalogue with query: %s", query
        )
        try:
            raw = await database_provider.query_raw(query)
            raw = database_provider.unwrap_query_raw_result(raw)

            if raw is None:
                catalogue = None
            elif isinstance(raw, list):
                if len(raw) == 0:
                    catalogue = None
                else:
                    payload = database_provider.unwrap_record(raw[0])
                    catalogue = ModelCatalogue.from_dict(
                        self._normalize_catalogue_dict(payload)
                    )
            elif isinstance(raw, dict):
                catalogue = ModelCatalogue.from_dict(self._normalize_catalogue_dict(raw))
            else:
                payload = database_provider.unwrap_record(raw)
                catalogue = ModelCatalogue.from_dict(
                    self._normalize_catalogue_dict(payload)
                )
        except Exception as e:
            message = f"Failed to get model catalogue. Query: {query}. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        self._logger.debug(
            "Model Catalogue found: %s", catalogue
        )

        return catalogue

    @override
    async def search_catalogues(
        self, catalogue_search_criteria: ModelCatalogueSearchCriteria
    ) -> list[ModelCatalogueSearchResultEntry]:
        """Search model catalogues by criteria.

        Builds a SurrealQL query from the criteria (including optional
        vector similarity) and returns matching catalogues.

        Args:
            catalogue_search_criteria: Search filters (name, type, status,
                keywords, tags, deployment types, confidence level, limit).

        Returns:
            List of matching catalogues; empty list if none or on error.

        Raises:
            Exception: When the database provider is unavailable or the
                search fails.
        """
        self._logger.debug(
            "Searching Model Catalogues with criteria: %s", catalogue_search_criteria
        )

        try:
            database_provider = self._database_manager.get_default_database_provider()
        except Exception as e:
            message = f"Failed to get database provider. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        query = catalogue_search_criteria.to_query(
            database_provider, IModelCatalogueService.CATALOGUE_COLLECTION_NAME()
        )
        self._logger.debug(
            "Searching Model Catalogues with query: %s", query
        )

        try:
            raw = await database_provider.query_raw(query)
            raw = database_provider.unwrap_query_raw_result(raw)

            if raw is None:
                catalogues = []
            elif isinstance(raw, list):
                catalogues = []
                for item in raw:
                    payload = database_provider.unwrap_record(item)
                    catalogues.append(
                        ModelCatalogueSearchResultEntry.from_dict(
                            self._normalize_catalogue_dict(payload)
                        )
                    )
            elif isinstance(raw, dict):
                catalogues = [
                    ModelCatalogueSearchResultEntry.from_dict(
                        self._normalize_catalogue_dict(raw)
                    )
                ]
            else:
                payload = database_provider.unwrap_record(raw)
                catalogues = [
                    ModelCatalogueSearchResultEntry.from_dict(
                        self._normalize_catalogue_dict(payload)
                    )
                ]
        except Exception as e:
            message = (
                f"Failed to search model catalogues. Query: {query}. Error: {e}"
            )
            self._logger.error(message)
            raise Exception(message) from e

        if catalogues is None:
            self._logger.debug(
                "No Model Catalogues found"
            )
            return []

        self._logger.debug(
            "Model Catalogues found: %d, catalogues: %s",
            len(catalogues),
            catalogues,
        )

        return catalogues

    @override
    async def delete_catalogue(self, id: str) -> bool:
        """Delete a model catalogue by ID.

        Args:
            id: Record ID of the catalogue to delete.

        Returns:
            True if a record was deleted, False if not found.

        Raises:
            Exception: When the database provider is unavailable or the
                delete operation fails.
        """
        self._logger.debug(
            "Deleting Model Catalogue by ID: %s", id
        )

        try:
            database_provider = self._database_manager.get_default_database_provider()
        except Exception as e:
            message = f"Failed to get database provider. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        query = (
            f"DELETE {ModelCatalogueService._thing_ref(IModelCatalogueService.CATALOGUE_COLLECTION_NAME(), id)} "
            f"RETURN BEFORE;"
        )
        self._logger.debug(
            "Deleting Model Catalogue with query: %s", query
        )
        try:
            result = await database_provider.query(
                query, ModelCatalogue, many=True
            )
        except Exception as e:
            message = f"Failed to delete model catalogue. Query: {query}. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        deleted: bool = len(result) > 0
        self._logger.info(
            "Model Catalogue deleted: %s, result count: %d",
            deleted,
            len(result),
        )

        return deleted
        
    @override
    async def create_deployment(self, deployment: ModelDeployment) -> ModelDeployment:
        """Create a new model deployment record.

        If deployment.id is None or empty, the store generates an ID.

        Args:
            deployment: Model deployment data.

        Returns:
            The created deployment (with id set).

        Raises:
            Exception: When the database provider is unavailable or the
                create operation fails.
        """
        self._logger.debug("Creating Model Deployment. Input: %s", deployment)

        try:
            database_provider: SurrealDbRemoteProvider = (
                self._database_manager.get_default_database_provider()
            )
        except Exception as e:
            message: str = f"Failed to get database provider. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        if deployment.id is None or deployment.id == "":
            query: str = (
                f"CREATE {IModelCatalogueService.DEPLOYMENT_COLLECTION_NAME()} CONTENT {deployment.to_json(exclude_id=True)};"
            )
        else:
            record_key = self._deployment_record_key(deployment.id)
            query = (
                f"CREATE {self._thing_ref(IModelCatalogueService.DEPLOYMENT_COLLECTION_NAME(), record_key)} "
                f"CONTENT {deployment.to_json()};"
            )

        self._logger.debug("Creating Model Deployment with query: %s", query)

        try:
            result: ModelDeployment = await database_provider.query(
                query, ModelDeployment
            )
        except Exception as e:
            message = (
                f"Failed to create model deployment. Query: {query}. Error: {e}"
            )
            self._logger.error(message)
            raise Exception(message) from e

        self._logger.info("Created Model Deployment: %s", result)
        return result

    @override
    async def update_deployment(self, deployment: ModelDeployment) -> ModelDeployment:
        """Update an existing model deployment record.

        Args:
            deployment: Deployment with id and updated fields.

        Returns:
            The updated deployment as returned by the store.

        Raises:
            ValueError: When id is None or empty.
            Exception: When the database provider is unavailable or the
                update operation fails.
        """
        self._logger.debug("Updating Model Deployment: %s", deployment)

        try:
            database_provider = self._database_manager.get_default_database_provider()
        except Exception as e:
            message = f"Failed to get database provider. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        if deployment.id is None or deployment.id == "":
            message = "Id is required when updating a model deployment."
            self._logger.error(message)
            raise ValueError(message)

        record_key = self._deployment_record_key(deployment.id)
        query = (
            f"UPDATE {self._thing_ref(IModelCatalogueService.DEPLOYMENT_COLLECTION_NAME(), record_key)} "
            f"MERGE {deployment.to_json()};"
        )
        self._logger.debug("Updating Model Deployment with query: %s", query)
        try:
            result = await database_provider.query(query, ModelDeployment)
        except Exception as e:
            message = (
                f"Failed to update model deployment. Query: {query}. Error: {e}"
            )
            self._logger.error(message)
            raise Exception(message) from e

        self._logger.info("Updated Model Deployment: %s", result)
        return result

    @override
    async def get_deployment(self, id: str) -> ModelDeployment | None:
        """Get a single model deployment by ID.

        Args:
            id: Record ID of the deployment (with or without table prefix).

        Returns:
            The deployment if found, None otherwise.

        Raises:
            Exception: When the database provider is unavailable or the
                query fails.
        """
        self._logger.debug("Getting Model Deployment by ID: %s", id)

        try:
            database_provider = self._database_manager.get_default_database_provider()
        except Exception as e:
            message = f"Failed to get database provider. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        record_key = self._deployment_record_key(id)
        query = (
            f"SELECT * FROM {self._thing_ref(IModelCatalogueService.DEPLOYMENT_COLLECTION_NAME(), record_key)};"
        )

        self._logger.debug("Getting Model Deployment with query: %s", query)
        try:
            deployment = await database_provider.query(query, ModelDeployment)
        except Exception as e:
            message = f"Failed to get model deployment. Query: {query}. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        self._logger.debug("Model Deployment found: %s", deployment)
        return deployment

    @override
    async def search_deployments(
        self, deployment_search_criteria: ModelDeploymentSearchCriteria
    ) -> list[ModelDeployment]:
        """Search model deployments by criteria.

        Args:
            deployment_search_criteria: Search filters (no vector similarity).

        Returns:
            List of matching deployments; empty list if none.

        Raises:
            Exception: When the database provider is unavailable or the
                search fails.
        """
        self._logger.debug(
            "Searching Model Deployments with criteria: %s", deployment_search_criteria
        )

        try:
            database_provider = self._database_manager.get_default_database_provider()
        except Exception as e:
            message = f"Failed to get database provider. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        query = deployment_search_criteria.to_query(
            database_provider, IModelCatalogueService.DEPLOYMENT_COLLECTION_NAME()
        )
        self._logger.debug("Searching Model Deployments with query: %s", query)

        try:
            deployments: list[ModelDeployment] = await database_provider.query(
                query, ModelDeployment, many=True
            )
        except Exception as e:
            message = (
                f"Failed to search model deployments. Query: {query}. Error: {e}"
            )
            self._logger.error(message)
            raise Exception(message) from e

        if deployments is None:
            self._logger.debug("No Model Deployments found")
            return []

        self._logger.debug(
            "Model Deployments found: %d, deployments: %s",
            len(deployments),
            deployments,
        )
        return deployments

    @override
    async def delete_deployment(self, id: str) -> bool:
        """Delete a model deployment by ID.

        Runs in a single SurrealDB transaction: first removes this deployment
        id from every ``model_catalogues.deployments`` array that references
        it, then deletes the deployment record. If any step fails, the
        transaction is rolled back.

        Args:
            id: Record ID of the deployment to delete (with or without table prefix).

        Returns:
            True if a deployment record was deleted, False if not found.

        Raises:
            Exception: When the database provider is unavailable or the
                delete operation fails.
        """
        self._logger.debug("Deleting Model Deployment by ID: %s", id)

        deployment_full_id = self._normalize_deployment_record_id(id)
        record_key = self._deployment_record_key(id)

        try:
            database_provider = self._database_manager.get_default_database_provider()
        except Exception as e:
            message = f"Failed to get database provider. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        escaped_full = self._escape_surreal_string_literal(deployment_full_id)
        record_key_only = self._deployment_record_key(deployment_full_id)
        escaped_key = self._escape_surreal_string_literal(record_key_only)

        catalogue_table = IModelCatalogueService.CATALOGUE_COLLECTION_NAME()
        deployment_table = IModelCatalogueService.DEPLOYMENT_COLLECTION_NAME()

        # Unlink from catalogues, then delete deployment in one transaction.
        # Use "-=" to remove array elements to avoid function compatibility issues.
        unlink_full = (
            f"UPDATE {catalogue_table} SET deployments -= '{escaped_full}' "
            f"WHERE (deployments ?? []) CONTAINS '{escaped_full}';"
        )
        unlink_key = (
            f"UPDATE {catalogue_table} SET deployments -= '{escaped_key}' "
            f"WHERE (deployments ?? []) CONTAINS '{escaped_key}';"
        )
        delete_stmt = (
            f"DELETE {self._thing_ref(deployment_table, record_key)} RETURN BEFORE;"
        )
        tx_query = "\n".join(
            (
                "BEGIN TRANSACTION;",
                unlink_full,
                unlink_key,
                delete_stmt,
                "COMMIT TRANSACTION;",
            )
        )

        self._logger.debug("Deleting Model Deployment (transaction): %s", tx_query)

        try:
            raw_result: Any = await database_provider.query_raw(tx_query)
        except Exception as e:
            message = f"Failed to delete model deployment (transaction). Query: {tx_query}. Error: {e}"
            self._logger.error(message)
            raise Exception(message) from e

        deleted: bool = self._delete_return_before_had_row(raw_result)
        self._logger.debug(
            "Model Deployment delete transaction raw result: %s, deleted=%s",
            raw_result,
            deleted,
        )
        self._logger.info(
            "Model Deployment deleted: %s, raw result type: %s",
            deleted,
            type(raw_result).__name__,
        )
        return deleted
