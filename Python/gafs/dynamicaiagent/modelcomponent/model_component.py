from __future__ import annotations

import logging
from typing import Any, override

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider

from .i_model_component import IModelComponent
from .i_model_catalogue_service import IModelCatalogueService
from .i_model_service import IModelService
from .exceptions.model_component_exception import ModelComponentException
from .exceptions.model_component_exceptions import (
    ModelComponentConfigurationException,
    ModelComponentOperationException,
    ModelComponentResourceNotFoundException,
    ModelCatalogueIndexNotAvailableException,
)
from .models.ai_deployment_type import AiDeploymentType
from .models.ai_operation_type import AiOperationType
from .models.ai_payload import EmbeddingPayload
from .models.ai_request import AiRequest
from .models.ai_response import AiResponse
from .models.deployment_selection_options import DeploymentSelectionOptions
from .models.model_catalogue import (
    ModelCatalogue,
    ModelCatalogueSearchResultEntry,
    ModelDeployment,
)
from .models.model_catalogue_search_criteria import ModelCatalogueSearchCriteria
from .models.model_component_configurations import ModelComponentConfigurations
from .models.model_deployment_search_criteria import ModelDeploymentSearchCriteria

class ModelComponent(IModelComponent):
    """Facade that wraps model catalogue/service operations for external callers."""

    def __init__(
        self,
        logger: logging.Logger,
        model_catalogue_service: IModelCatalogueService,
        model_service: IModelService,
        cloud_ai_component: Any | None = None,
    ) -> None:
        self._logger = logger
        self._model_catalogue_service = model_catalogue_service
        self._model_service = model_service
        self._cloud_ai_component = cloud_ai_component
        self._database_manager: IDatabaseManager | None = None
        self._configurations: ModelComponentConfigurations | None = None
        self._is_rebuilding_vector_index: bool = False

    @staticmethod
    def _configuration_record_id() -> str:
        return (
            f"{ModelComponentConfigurations.COLLECTION_NAME()}:"
            f"{ModelComponentConfigurations.DEFAULT_DOCUMENT_ID()}"
        )

    @staticmethod
    def _raise_as_model_component_exception(
        ex: Exception,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        if isinstance(ex, ModelComponentException):
            raise ex
        raise ModelComponentOperationException(
            message=message,
            details=details,
            cause=ex,
        ) from ex

    async def _provider(self) -> IDatabaseProvider:
        if self._database_manager is None:
            raise ModelComponentConfigurationException(
                message="ModelComponent is not initialized."
            )
        provider = self._database_manager.get_default_database_provider()
        if provider is None:
            raise ModelComponentConfigurationException(
                message="Default database provider is not available."
            )
        return provider

    async def _load_or_create_configurations(self) -> ModelComponentConfigurations:
        provider = await self._provider()
        rid = self._configuration_record_id()
        query = f"SELECT * FROM {rid};"
        current = await provider.query(query, ModelComponentConfigurations)
        if current is not None:
            return current

        default_config = ModelComponentConfigurations()
        create_query = f"CREATE {rid} CONTENT {default_config.to_json()};"
        created = await provider.query(create_query, ModelComponentConfigurations)
        if created is None:
            raise ModelComponentOperationException(
                message="Failed to create default model component configurations."
            )
        return created

    async def _save_configurations(
        self,
        configurations: ModelComponentConfigurations,
    ) -> ModelComponentConfigurations:
        provider = await self._provider()
        rid = self._configuration_record_id()
        query = f"UPDATE {rid} MERGE {configurations.to_json()};"
        updated = await provider.query(query, ModelComponentConfigurations)
        if updated is None:
            raise ModelComponentOperationException(
                message="Failed to update model component configurations."
            )
        return updated

    @override
    async def initialize(self, database_manager: IDatabaseManager) -> bool:
        try:
            self._database_manager = database_manager
            provider = await self._provider()
            self._configurations = await self._load_or_create_configurations()

            await self._model_catalogue_service.initialize(
                database_manager=database_manager,
                component_configurations=self._configurations,
                database_provider=provider,
            )

            # Keep compatibility with services using either old or expanded signature.
            try:
                await self._model_service.initialize(
                    database_manager,
                    self._model_catalogue_service,
                    self._cloud_ai_component,
                )
            except TypeError:
                await self._model_service.initialize(database_manager)
        except Exception as ex:
            self._raise_as_model_component_exception(
                ex,
                "Failed to initialize ModelComponent.",
            )

        return True

    @override
    async def invoke(
        self,
        catalogue_id: str,
        request: AiRequest,
        deployment_selection_options: DeploymentSelectionOptions | None = None,
    ) -> AiResponse:
        try:
            return await self._model_service.invoke(
                catalogue_id,
                request,
                deployment_selection_options,
            )
        except Exception as ex:
            self._raise_as_model_component_exception(
                ex,
                "Failed to invoke model operation.",
                details={"catalogue_id": catalogue_id},
            )

    @override
    async def create_catalogue(self, catalogue: ModelCatalogue) -> ModelCatalogue:
        try:
            return await self._model_catalogue_service.create_catalogue(catalogue)
        except Exception as ex:
            self._raise_as_model_component_exception(
                ex,
                "Failed to create model catalogue.",
            )

    @override
    async def update_catalogue(self, catalogue: ModelCatalogue) -> ModelCatalogue:
        try:
            return await self._model_catalogue_service.update_catalogue(catalogue)
        except Exception as ex:
            self._raise_as_model_component_exception(
                ex,
                "Failed to update model catalogue.",
            )

    @override
    async def delete_catalogue(self, catalogue_id: str) -> bool:
        try:
            return await self._model_catalogue_service.delete_catalogue(catalogue_id)
        except Exception as ex:
            self._raise_as_model_component_exception(
                ex,
                "Failed to delete model catalogue.",
                details={"catalogue_id": catalogue_id},
            )

    @override
    async def get_catalogue(self, catalogue_id: str) -> ModelCatalogue:
        try:
            catalogue = await self._model_catalogue_service.get_catalogue(catalogue_id)
            if catalogue is None:
                raise ModelComponentResourceNotFoundException(
                    message=f"Catalogue not found: {catalogue_id}",
                    details={"catalogue_id": catalogue_id},
                )
            return catalogue
        except Exception as ex:
            self._raise_as_model_component_exception(
                ex,
                "Failed to get model catalogue.",
                details={"catalogue_id": catalogue_id},
            )

    @override
    async def search_catalogues(
        self,
        search_criteria: ModelCatalogueSearchCriteria,
    ) -> list[ModelCatalogueSearchResultEntry]:
        try:
            if self._is_rebuilding_vector_index and search_criteria.vector is not None:
                raise ModelCatalogueIndexNotAvailableException(
                    "Vector index is rebuilding. Vector search is temporarily unavailable."
                )
            return await self._model_catalogue_service.search_catalogues(search_criteria)
        except Exception as ex:
            self._raise_as_model_component_exception(
                ex,
                "Failed to search model catalogues.",
            )

    @override
    async def create_deployment(self, deployment: ModelDeployment) -> ModelDeployment:
        try:
            return await self._model_catalogue_service.create_deployment(deployment)
        except Exception as ex:
            self._raise_as_model_component_exception(
                ex,
                "Failed to create model deployment.",
            )

    @override
    async def update_deployment(self, deployment: ModelDeployment) -> ModelDeployment:
        try:
            return await self._model_catalogue_service.update_deployment(deployment)
        except Exception as ex:
            self._raise_as_model_component_exception(
                ex,
                "Failed to update model deployment.",
            )

    @override
    async def delete_deployment(self, deployment_id: str) -> bool:
        try:
            return await self._model_catalogue_service.delete_deployment(deployment_id)
        except Exception as ex:
            self._raise_as_model_component_exception(
                ex,
                "Failed to delete model deployment.",
                details={"deployment_id": deployment_id},
            )

    @override
    async def get_deployment(self, deployment_id: str) -> ModelDeployment | None:
        try:
            return await self._model_catalogue_service.get_deployment(deployment_id)
        except Exception as ex:
            self._raise_as_model_component_exception(
                ex,
                "Failed to get model deployment.",
                details={"deployment_id": deployment_id},
            )

    @override
    async def search_deployments(
        self,
        search_criteria: ModelDeploymentSearchCriteria,
    ) -> list[ModelDeployment]:
        try:
            return await self._model_catalogue_service.search_deployments(search_criteria)
        except Exception as ex:
            self._raise_as_model_component_exception(
                ex,
                "Failed to search model deployments.",
            )

    @override
    async def get_configurations(self) -> ModelComponentConfigurations:
        try:
            if self._configurations is None:
                self._configurations = await self._load_or_create_configurations()
            return self._configurations
        except Exception as ex:
            self._raise_as_model_component_exception(
                ex,
                "Failed to get model component configurations.",
            )

    async def _drop_vector_index_safely(self) -> None:
        provider = await self._provider()
        table = IModelCatalogueService.CATALOGUE_COLLECTION_NAME()
        index_name = "idx_model_catalogues_description_vector"

        # SurrealDB syntax differs across versions / deployments.
        # Try best-effort drop strategies; the subsequent ensure_indexes(overwrite=True)
        # will recreate the index as needed.
        try:
            await provider.query_raw(
                f"ALTER INDEX {index_name} ON {table} PREPARE REMOVE;"
            )
        except Exception:
            pass

        # Keep explicit EXPLAIN query step as requested by spec.
        try:
            await provider.query_raw(f"SELECT * FROM {table} LIMIT 1 EXPLAIN;")
        except Exception:
            pass

        try:
            await provider.query_raw(f"REMOVE INDEX {index_name} ON {table};")
        except Exception:
            pass

    async def _clear_all_description_vectors(self) -> None:
        provider = await self._provider()
        table = IModelCatalogueService.CATALOGUE_COLLECTION_NAME()
        tx = (
            f"BEGIN TRANSACTION; "
            f"UPDATE {table} SET description_vector = NONE; "
            f"COMMIT TRANSACTION;"
        )
        await provider.query_raw(tx)

    async def _embed_text(self, text: str) -> list[float]:
        configurations = await self.get_configurations()
        if configurations.embedding_catalogue_id is None:
            raise ModelComponentConfigurationException(
                message="embedding_catalogue_id is required for re-embedding."
            )

        payload = EmbeddingPayload()
        payload.input = text
        request = AiRequest(operation_type=AiOperationType.EMBEDDING, payload=payload)

        selection = DeploymentSelectionOptions()
        selection.deployment_type = AiDeploymentType.CLOUD

        response = await self._model_service.invoke(
            catalogue_id=configurations.embedding_catalogue_id,
            request=request,
            deployment_selection_options=selection,
        )

        if response.output is None or not hasattr(response.output, "embedding"):
            raise ModelComponentOperationException(
                message="Embedding response does not contain embedding output."
            )
        embedding = getattr(response.output, "embedding")
        if not isinstance(embedding, list):
            raise ModelComponentOperationException(
                message="Embedding output type is invalid."
            )
        return [float(v) for v in embedding]

    async def _reembed_all_catalogues(self) -> None:
        provider = await self._provider()
        table = IModelCatalogueService.CATALOGUE_COLLECTION_NAME()
        catalogues = await provider.query(
            f"SELECT * FROM {table};",
            ModelCatalogue,
            many=True,
        )
        if catalogues is None:
            return

        for catalogue in catalogues:
            if catalogue.description is None or catalogue.description == "":
                continue
            catalogue.description_vector = await self._embed_text(catalogue.description)
            await self._model_catalogue_service.update_catalogue(catalogue)

    @override
    async def update_configurations(
        self,
        configurations: ModelComponentConfigurations,
    ) -> ModelComponentConfigurations:
        try:
            current = await self.get_configurations()

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

            self._is_rebuilding_vector_index = True
            try:
                # [1] Drop vector index safely.
                await self._drop_vector_index_safely()

                # [2] Clear vectors for full-reembed scenario.
                if requires_reembed:
                    await self._clear_all_description_vectors()

                # Persist new configurations before rebuilding/re-embedding.
                self._configurations = await self._save_configurations(configurations)

                # [3] Recreate vector index with new settings.
                await self._model_catalogue_service.ensure_indexes(
                    self._configurations,
                    overwrite=True,
                )

                # [4] Re-embed all catalogue descriptions when required.
                if requires_reembed:
                    await self._reembed_all_catalogues()
            finally:
                # [5] Re-enable vector search.
                self._is_rebuilding_vector_index = False
        except Exception as ex:
            self._raise_as_model_component_exception(
                ex,
                "Failed to update model component configurations.",
            )

        return self._configurations
