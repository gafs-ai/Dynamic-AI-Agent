"""model_component.py - Concrete implementation of IModelComponent.

Top-level facade that delegates catalogue/deployment CRUD to ModelCatalogueService
and inference to ModelService.  Also owns configuration lifecycle and vector index
management.
"""

from __future__ import annotations

import logging
from typing import Any

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider

from .exceptions import (
    InvalidModelComponentConfigurationException,
    ModelCatalogueEntryNotFoundException,
    ModelCatalogueIndexNotAvailableException,
    ModelComponentException,
    ModelComponentInitializationException,
    ModelComponentNotInitializedException,
    ModelComponentOperationException,
)
from .i_model_catalogue_service import IModelCatalogueService
from .i_model_component import IModelComponent
from .i_model_service import IModelService
from .models import (
    AiDeploymentType,
    AiOperationType,
    AiRequest,
    AiResponse,
    DeploymentSelectionOptions,
    EmbeddingPayload,
    ModelCatalogueEntry,
    ModelCatalogueSearchCriteria,
    ModelCatalogueSearchResultEntry,
    ModelComponentConfigurations,
    ModelDeployment,
    ModelDeploymentSearchCriteria,
)


class ModelComponent(IModelComponent):
    """Top-level model component facade.

    Wires together ``IModelCatalogueService``, ``IModelService``, and
    ``ICloudAiComponent``, manages ``ModelComponentConfigurations`` persistence,
    and orchestrates HNSW vector index rebuilding when configuration changes.
    """

    def __init__(
        self,
        logger: logging.Logger,
        model_catalogue_service: IModelCatalogueService,
        model_service: IModelService,
        cloud_ai_component: Any | None = None,
    ) -> None:
        """Initialize the component.

        Args:
            logger: Logger instance.
            model_catalogue_service: Catalogue and deployment CRUD service.
            model_service: Inference delegation service.
            cloud_ai_component: Optional cloud AI provider for embedding + inference.
        """
        self._logger: logging.Logger = logger
        self._model_catalogue_service: IModelCatalogueService = model_catalogue_service
        self._model_service: IModelService = model_service
        self._cloud_ai_component: Any | None = cloud_ai_component
        self._database_manager: IDatabaseManager | None = None
        self._configurations: ModelComponentConfigurations | None = None
        self._is_rebuilding_vector_index: bool = False

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _provider(self) -> IDatabaseProvider:
        """Return the default IDatabaseProvider.

        Raises:
            ModelComponentNotInitializedException: Component is not initialized.
        """
        if self._database_manager is None:
            raise ModelComponentNotInitializedException(
                "ModelComponent is not initialized (no IDatabaseManager)."
            )
        provider = self._database_manager.get_default_provider()
        if provider is None:
            raise ModelComponentNotInitializedException(
                "Default database provider is not available."
            )
        return provider

    async def _load_or_create_configurations(self) -> ModelComponentConfigurations:
        """Load existing or create default ``ModelComponentConfigurations``.

        Returns:
            Loaded or newly created configurations.

        Raises:
            ModelComponentOperationException: Database failure.
        """
        provider = self._provider()
        default_id = ModelComponentConfigurations.DEFAULT_DOCUMENT_ID()
        collection = ModelComponentConfigurations.COLLECTION_NAME()

        query = f"SELECT * FROM {collection}:{default_id};"
        try:
            raw = await provider.query_raw(query)
        except Exception as exc:
            raise ModelComponentOperationException(
                "Failed to query ModelComponentConfigurations.",
                cause=exc,
            ) from exc

        # Unwrap envelope.
        if hasattr(provider, "unwrap_query_raw_result"):
            raw = provider.unwrap_query_raw_result(raw)
        if isinstance(raw, list):
            raw = raw[0] if raw else None
        if raw is not None and hasattr(provider, "unwrap_record"):
            raw = provider.unwrap_record(raw)

        if raw and isinstance(raw, dict) and raw:
            return ModelComponentConfigurations.from_dict(raw)

        # No record exists — create defaults.
        defaults = ModelComponentConfigurations()
        create_q = (
            f"CREATE {collection}:{default_id} "
            f"CONTENT {defaults.to_json(exclude_id=True)};"
        )
        try:
            create_raw = await provider.query_raw(create_q)
        except Exception as exc:
            raise ModelComponentOperationException(
                "Failed to create default ModelComponentConfigurations.",
                cause=exc,
            ) from exc

        if hasattr(provider, "unwrap_query_raw_result"):
            create_raw = provider.unwrap_query_raw_result(create_raw)
        if isinstance(create_raw, list):
            create_raw = create_raw[0] if create_raw else None
        if create_raw is not None and hasattr(provider, "unwrap_record"):
            create_raw = provider.unwrap_record(create_raw)

        if create_raw and isinstance(create_raw, dict):
            return ModelComponentConfigurations.from_dict(create_raw)
        return defaults

    async def _save_configurations(
        self,
        configurations: ModelComponentConfigurations,
    ) -> ModelComponentConfigurations:
        """Persist updated ``ModelComponentConfigurations`` to the database.

        Args:
            configurations: Updated configuration values.

        Returns:
            The persisted configuration record.

        Raises:
            ModelComponentOperationException: Database failure or no result.
        """
        provider = self._provider()
        default_id = ModelComponentConfigurations.DEFAULT_DOCUMENT_ID()
        collection = ModelComponentConfigurations.COLLECTION_NAME()
        update_q = (
            f"UPDATE {collection}:{default_id} "
            f"MERGE {configurations.to_json(exclude_id=True)};"
        )
        try:
            raw = await provider.query_raw(update_q)
        except Exception as exc:
            raise ModelComponentOperationException(
                "Failed to save ModelComponentConfigurations.",
                cause=exc,
            ) from exc

        if hasattr(provider, "unwrap_query_raw_result"):
            raw = provider.unwrap_query_raw_result(raw)
        if isinstance(raw, list):
            raw = raw[0] if raw else None
        if raw is None:
            raise ModelComponentOperationException(
                "Save ModelComponentConfigurations returned no result."
            )
        if hasattr(provider, "unwrap_record"):
            raw = provider.unwrap_record(raw)
        if not isinstance(raw, dict):
            raise ModelComponentOperationException(
                f"Unexpected type saving configurations: {type(raw)}"
            )
        return ModelComponentConfigurations.from_dict(raw)

    async def _drop_vector_index_safely(self) -> None:
        """Remove the HNSW vector index on ``ModelCatalogue`` (best-effort).

        Ignores any errors to allow the caller to proceed with index recreation.
        """
        provider = self._provider()
        cat = IModelCatalogueService.CATALOGUE_COLLECTION_NAME()
        idx = "idx_model_catalogues_description_vector"
        for stmt in (
            f"ALTER INDEX {idx} ON {cat} PREPARE REMOVE;",
            f"SELECT * FROM {cat} LIMIT 1 EXPLAIN;",
            f"REMOVE INDEX {idx} ON {cat};",
        ):
            try:
                await provider.query_raw(stmt)
            except Exception as exc:
                self._logger.warning(
                    "Non-fatal error during _drop_vector_index_safely: %s", exc
                )

    async def _clear_all_description_vectors(self) -> None:
        """Null all ``description_vector`` fields on ``ModelCatalogue`` records.

        Runs in a single transaction.
        """
        provider = self._provider()
        cat = IModelCatalogueService.CATALOGUE_COLLECTION_NAME()
        tx_q = (
            f"BEGIN TRANSACTION; "
            f"UPDATE {cat} SET description_vector = NONE; "
            f"COMMIT TRANSACTION;"
        )
        try:
            await provider.query_raw(tx_q)
        except Exception as exc:
            raise ModelComponentOperationException(
                "Failed to clear description vectors.",
                cause=exc,
            ) from exc

    async def _reembed_all_catalogues(self) -> None:
        """Regenerate ``description_vector`` for all catalogue entries.

        Iterates all entries and calls ``_embed_text`` for each non-empty description,
        then persists the new vector via ``update_catalogue_entry``.
        """
        self._logger.info("Re-embedding all catalogue descriptions...")
        entries = await self._model_catalogue_service.get_all_catalogue_entries()
        for entry in entries:
            if not entry.description:
                continue
            try:
                vector = await self._embed_text(entry.description)
                object.__setattr__(entry, "description_vector", vector)
                await self._model_catalogue_service.update_catalogue_entry(entry)
            except Exception as exc:
                self._logger.warning(
                    "Failed to re-embed catalogue '%s': %s", entry.id, exc
                )
        self._logger.info("Re-embedding complete.")

    async def _embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for text via the embedding model.

        Uses the catalogue's embedding model configured in
        ``ModelComponentConfigurations.embedding_catalogue_id``.

        Args:
            text: Input text to embed.

        Returns:
            Embedding vector as ``list[float]``.

        Raises:
            InvalidModelComponentConfigurationException: No embedding model configured.
            ModelComponentOperationException: Inference failure or unexpected output.
        """
        configurations = await self.get_configurations()
        if not configurations.embedding_catalogue_id:
            raise InvalidModelComponentConfigurationException(
                "embedding_catalogue_id is not set in ModelComponentConfigurations. "
                "Configure it before using vector search or auto-embedding."
            )
        request = AiRequest(AiOperationType.EMBEDDING)
        payload = EmbeddingPayload()
        payload.text = text
        request.payload = payload
        request.parameters = {}

        selection = DeploymentSelectionOptions()
        selection.deployment_type = AiDeploymentType.CLOUD

        try:
            response = await self._model_service.invoke(
                configurations.embedding_catalogue_id, request, selection
            )
        except Exception as exc:
            raise ModelComponentOperationException(
                f"Embedding inference failed for text: '{text[:50]}...'",
                cause=exc,
            ) from exc

        output = getattr(response, "output", None)
        if output is None:
            raise ModelComponentOperationException(
                "Embedding response has no output."
            )
        embedding = getattr(output, "embedding", None)
        if not isinstance(embedding, list):
            raise ModelComponentOperationException(
                f"Unexpected embedding output type: {type(output)}"
            )
        return [float(v) for v in embedding]

    @staticmethod
    def _wrap_exception(exc: Exception) -> ModelComponentOperationException:
        """Wrap a non-``ModelComponentException`` as ``ModelComponentOperationException``."""
        if isinstance(exc, ModelComponentException):
            raise exc
        return ModelComponentOperationException(str(exc), cause=exc)

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    async def initialize(self, database_manager: IDatabaseManager) -> bool:
        """Initialize the model component.

        Loads/creates ``ModelComponentConfigurations``, then initializes the
        catalogue service and model service.

        Args:
            database_manager: Provides the default ``IDatabaseProvider``.

        Returns:
            ``True`` on success.

        Raises:
            ModelComponentInitializationException: Initialization failure.
        """
        self._logger.debug("Initializing ModelComponent...")
        try:
            self._database_manager = database_manager

            # Ensure the default database provider is available.
            _ = self._provider()

            # Load or create configurations.
            self._configurations = await self._load_or_create_configurations()

            # Initialize catalogue service, passing our embed function.
            await self._model_catalogue_service.initialize(
                database_manager,
                self._configurations,
                embed_fn=self._embed_text,
            )

            # Initialize model service.
            await self._model_service.initialize(
                database_manager,
                model_catalogue_service=self._model_catalogue_service,
                cloud_ai_component=self._cloud_ai_component,
            )
        except ModelComponentException:
            raise
        except Exception as exc:
            raise ModelComponentInitializationException(
                "Failed to initialize ModelComponent.",
                cause=exc,
            ) from exc

        self._logger.info("ModelComponent initialized.")
        return True

    # -------------------------------------------------------------------------
    # Inference
    # -------------------------------------------------------------------------

    async def invoke(
        self,
        catalogue_id: str,
        request: AiRequest,
        deployment_selection_options: DeploymentSelectionOptions | None = None,
    ) -> AiResponse:
        """Invoke an AI model. Delegates to ``IModelService.invoke``."""
        try:
            return await self._model_service.invoke(
                catalogue_id, request, deployment_selection_options
            )
        except ModelComponentException:
            raise
        except Exception as exc:
            raise self._wrap_exception(exc) from exc

    # -------------------------------------------------------------------------
    # Catalogue CRUD
    # -------------------------------------------------------------------------

    async def create_catalogue_entry(
        self,
        catalogue: ModelCatalogueEntry,
    ) -> ModelCatalogueEntry:
        """Create a new catalogue entry."""
        try:
            return await self._model_catalogue_service.create_catalogue_entry(catalogue)
        except ModelComponentException:
            raise
        except Exception as exc:
            raise self._wrap_exception(exc) from exc

    async def update_catalogue_entry(
        self,
        catalogue: ModelCatalogueEntry,
    ) -> ModelCatalogueEntry:
        """Update an existing catalogue entry."""
        try:
            return await self._model_catalogue_service.update_catalogue_entry(catalogue)
        except ModelComponentException:
            raise
        except Exception as exc:
            raise self._wrap_exception(exc) from exc

    async def delete_catalogue_entry(self, catalogue_id: str) -> None:
        """Delete a catalogue entry."""
        try:
            await self._model_catalogue_service.delete_catalogue_entry(catalogue_id)
        except ModelComponentException:
            raise
        except Exception as exc:
            raise self._wrap_exception(exc) from exc

    async def get_catalogue_entry(self, catalogue_id: str) -> ModelCatalogueEntry:
        """Get a catalogue entry by id.

        Raises:
            ModelCatalogueEntryNotFoundException: No entry found.
        """
        try:
            result = await self._model_catalogue_service.get_catalogue_entry(catalogue_id)
        except ModelComponentException:
            raise
        except Exception as exc:
            raise self._wrap_exception(exc) from exc

        if result is None:
            raise ModelCatalogueEntryNotFoundException(
                f"Catalogue entry not found: {catalogue_id}",
                details={"catalogue_id": catalogue_id},
            )
        return result

    async def get_all_catalogue_entries(self) -> list[ModelCatalogueEntry]:
        """Get all catalogue entries."""
        try:
            return await self._model_catalogue_service.get_all_catalogue_entries()
        except ModelComponentException:
            raise
        except Exception as exc:
            raise self._wrap_exception(exc) from exc

    async def search_catalogue_entries(
        self,
        search_criteria: ModelCatalogueSearchCriteria,
    ) -> list[ModelCatalogueSearchResultEntry]:
        """Search catalogue entries.

        Raises:
            ModelCatalogueIndexNotAvailableException: Vector search during index rebuild.
        """
        if (
            self._is_rebuilding_vector_index
            and getattr(search_criteria, "vector_search", None) is not None
        ):
            raise ModelCatalogueIndexNotAvailableException(
                "The vector index is currently being rebuilt. "
                "Vector search is temporarily unavailable."
            )
        try:
            return await self._model_catalogue_service.search_catalogue_entries(
                search_criteria
            )
        except ModelComponentException:
            raise
        except Exception as exc:
            raise self._wrap_exception(exc) from exc

    # -------------------------------------------------------------------------
    # Deployment CRUD
    # -------------------------------------------------------------------------

    async def create_deployment(self, deployment: ModelDeployment) -> ModelDeployment:
        """Create a new deployment."""
        try:
            return await self._model_catalogue_service.create_deployment(deployment)
        except ModelComponentException:
            raise
        except Exception as exc:
            raise self._wrap_exception(exc) from exc

    async def update_deployment(self, deployment: ModelDeployment) -> ModelDeployment:
        """Update an existing deployment."""
        try:
            return await self._model_catalogue_service.update_deployment(deployment)
        except ModelComponentException:
            raise
        except Exception as exc:
            raise self._wrap_exception(exc) from exc

    async def delete_deployment(self, deployment_id: str) -> None:
        """Delete a deployment."""
        try:
            await self._model_catalogue_service.delete_deployment(deployment_id)
        except ModelComponentException:
            raise
        except Exception as exc:
            raise self._wrap_exception(exc) from exc

    async def get_deployment(self, deployment_id: str) -> ModelDeployment | None:
        """Get a deployment by id."""
        try:
            return await self._model_catalogue_service.get_deployment(deployment_id)
        except ModelComponentException:
            raise
        except Exception as exc:
            raise self._wrap_exception(exc) from exc

    async def search_deployments(
        self,
        search_criteria: ModelDeploymentSearchCriteria,
    ) -> list[ModelDeployment]:
        """Search deployments."""
        try:
            return await self._model_catalogue_service.search_deployments(search_criteria)
        except ModelComponentException:
            raise
        except Exception as exc:
            raise self._wrap_exception(exc) from exc

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------

    async def get_configurations(self) -> ModelComponentConfigurations:
        """Return the current ``ModelComponentConfigurations``.

        Lazily loads from the database if not yet cached.
        """
        try:
            if self._configurations is None:
                self._configurations = await self._load_or_create_configurations()
            return self._configurations
        except ModelComponentException:
            raise
        except Exception as exc:
            raise self._wrap_exception(exc) from exc

    async def update_configurations(
        self,
        configurations: ModelComponentConfigurations,
    ) -> ModelComponentConfigurations:
        """Persist updated configurations.

        When vector-relevant settings change, rebuilds the HNSW index and
        re-embeds all descriptions as needed.

        Args:
            configurations: New configuration values.

        Returns:
            The persisted configuration record.
        """
        try:
            current = await self.get_configurations()

            # Determine what has changed.
            requires_reembed = (
                current.embedding_catalogue_id != configurations.embedding_catalogue_id
                or current.vector_data_type != configurations.vector_data_type
                or current.vector_dimensions != configurations.vector_dimensions
            )
            requires_rebuild_only = (
                current.vector_search_method != configurations.vector_search_method
                or current.vector_exploration_factor != configurations.vector_exploration_factor
                or current.vector_max_connections != configurations.vector_max_connections
            )
            needs_vector_rebuild = requires_reembed or requires_rebuild_only

            if not needs_vector_rebuild:
                self._configurations = await self._save_configurations(configurations)
                return self._configurations

            # Rebuild the vector index.
            self._is_rebuilding_vector_index = True
            try:
                await self._drop_vector_index_safely()

                if requires_reembed:
                    await self._clear_all_description_vectors()

                self._configurations = await self._save_configurations(configurations)
                await self._model_catalogue_service.ensure_indexes(
                    self._configurations, overwrite=True
                )

                if requires_reembed:
                    await self._reembed_all_catalogues()

            finally:
                self._is_rebuilding_vector_index = False

            return self._configurations
        except ModelComponentException:
            raise
        except Exception as exc:
            raise self._wrap_exception(exc) from exc
