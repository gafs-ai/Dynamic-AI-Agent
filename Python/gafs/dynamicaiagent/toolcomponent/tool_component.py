"""tool_component.py - Concrete implementation of IToolComponent.

Top-level facade that delegates catalogue/sandbox CRUD to the respective
services and tool invocation to DockerSandboxService. Also owns configuration
lifecycle and vector index management.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider

from .exceptions import (
    InvalidToolComponentConfigurationException,
    SandboxCatalogueEntryNotFoundException,
    ToolCatalogueEntryNotFoundException,
    ToolCatalogueIndexNotAvailableException,
    ToolComponentException,
    ToolComponentInitializationException,
    ToolComponentNotInitializedException,
    ToolComponentOperationException,
    ToolVersionEntryNotFoundException,
    InvalidToolInvocationException,
)
from .i_docker_sandbox_service import IDockerSandboxService
from .i_sandbox_catalogue_service import ISandboxCatalogueService
from .i_tool_catalogue_service import IToolCatalogueService
from .i_tool_component import IToolComponent
from .models import (
    SandboxCatalogueDockerEntry,
    SandboxCatalogueEntry,
    SandboxCatalogueSearchCriteria,
    ToolCatalogueEntry,
    ToolCatalogueSearchCriteria,
    ToolCatalogueSearchResultEntry,
    ToolComponentConfigurations,
    ToolVersionEntry,
    ToolVersionEntrySearchCriteria,
)
from .models.sandbox_catalogue import SandboxStatus
from .models.tool_catalogue_search_criteria import TagsSearchCriteria


class ToolComponent(IToolComponent):
    """Top-level tool component facade.

    Wires together IToolCatalogueService, ISandboxCatalogueService, and
    IDockerSandboxService. Manages ToolComponentConfigurations persistence
    and orchestrates HNSW vector index rebuilding when configuration changes.
    """

    def __init__(
        self,
        logger: logging.Logger,
        tool_catalogue_service: IToolCatalogueService,
        sandbox_catalogue_service: ISandboxCatalogueService,
        docker_sandbox_service: IDockerSandboxService,
        model_component: Any | None = None,
    ) -> None:
        """Initialize the component.

        Args:
            logger: Logger instance.
            tool_catalogue_service: Tool catalogue CRUD service.
            sandbox_catalogue_service: Sandbox catalogue CRUD service.
            docker_sandbox_service: Docker container execution service.
            model_component: Optional IModelComponent for vector embedding.
        """
        self._logger: logging.Logger = logger
        self._tool_catalogue_service: IToolCatalogueService = tool_catalogue_service
        self._sandbox_catalogue_service: ISandboxCatalogueService = sandbox_catalogue_service
        self._docker_sandbox_service: IDockerSandboxService = docker_sandbox_service
        self._model_component: Any | None = model_component
        self._database_manager: IDatabaseManager | None = None
        self._configurations: ToolComponentConfigurations | None = None
        self._is_rebuilding_vector_index: bool = False

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    async def _provider(self) -> IDatabaseProvider:
        """Return the default IDatabaseProvider.

        Raises:
            ToolComponentNotInitializedException: Component is not initialized.
        """
        if self._database_manager is None:
            raise ToolComponentNotInitializedException(
                "ToolComponent is not initialized (no IDatabaseManager)."
            )
        provider = self._database_manager.get_default_provider()
        if provider is None:
            raise ToolComponentNotInitializedException(
                "Default database provider is not available."
            )
        return provider

    async def _load_configurations(self) -> ToolComponentConfigurations:
        """Load ToolComponentConfigurations from the database.

        Returns:
            Loaded ToolComponentConfigurations.

        Raises:
            InvalidToolComponentConfigurationException: Record does not exist.
            ToolComponentOperationException: Database operation failure.
        """
        provider = await self._provider()
        doc_id = ToolComponentConfigurations.DEFAULT_DOCUMENT_ID()
        collection = ToolComponentConfigurations.COLLECTION_NAME()
        query = f"SELECT * FROM {collection}:{doc_id};"
        try:
            result = await provider.query(
                query, model=ToolComponentConfigurations, many=False
            )
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to load ToolComponentConfigurations.", cause=exc
            ) from exc

        if result is None:
            raise InvalidToolComponentConfigurationException(
                "ToolComponentConfigurations record does not exist. "
                "Create a 'component_configurations:tool_component' record "
                "with at least 'app_data_folder' set before initializing ToolComponent."
            )
        return result

    async def _save_configurations(
        self, configurations: ToolComponentConfigurations
    ) -> ToolComponentConfigurations:
        """Persist ToolComponentConfigurations to the database.

        Args:
            configurations: Configuration to save.

        Returns:
            The persisted ToolComponentConfigurations.

        Raises:
            InvalidToolComponentConfigurationException: Validation failure.
            ToolComponentOperationException: Database operation failure.
        """
        if not configurations.app_data_folder:
            raise InvalidToolComponentConfigurationException(
                "ToolComponentConfigurations.app_data_folder must not be empty."
            )

        provider = await self._provider()
        doc_id = ToolComponentConfigurations.DEFAULT_DOCUMENT_ID()
        collection = ToolComponentConfigurations.COLLECTION_NAME()
        config_json = configurations.to_json(exclude_id=True)
        update_q = f"UPDATE {collection}:{doc_id} MERGE {config_json};"
        try:
            result = await provider.query(
                update_q, model=ToolComponentConfigurations, many=False
            )
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to save ToolComponentConfigurations.", cause=exc
            ) from exc

        if result is None:
            raise ToolComponentOperationException(
                "Saving ToolComponentConfigurations returned no result."
            )
        return result

    async def _select_sandbox(
        self, version_entry: ToolVersionEntry
    ) -> SandboxCatalogueDockerEntry:
        """Select the appropriate Docker sandbox for a tool version.

        Args:
            version_entry: Tool version whose sandbox should be selected.

        Returns:
            A SandboxCatalogueDockerEntry to use for execution.

        Raises:
            SandboxCatalogueEntryNotFoundException: No suitable sandbox found.
            ToolComponentOperationException: Selected sandbox is not Docker type.
        """
        if version_entry.sandbox_id:
            # Use the specifically designated sandbox
            entry = await self._sandbox_catalogue_service.get_catalogue_entry(
                version_entry.sandbox_id
            )
            if not isinstance(entry, SandboxCatalogueDockerEntry):
                raise ToolComponentOperationException(
                    f"Sandbox '{version_entry.sandbox_id}' is not a Docker sandbox."
                )
            return entry

        if version_entry.sandbox_selection_tags:
            # Auto-select by tags
            criteria = SandboxCatalogueSearchCriteria()
            object.__setattr__(criteria, "status", [SandboxStatus.ACTIVE])
            tags_criteria = TagsSearchCriteria(
                tags=version_entry.sandbox_selection_tags
            )
            from .models.tool_catalogue_search_criteria import LogicalOperator
            object.__setattr__(tags_criteria, "operator", LogicalOperator.AND)
            object.__setattr__(criteria, "tags", tags_criteria)

            results = await self._sandbox_catalogue_service.search_catalogue_entries(criteria)
            docker_results = [r for r in results if isinstance(r, SandboxCatalogueDockerEntry)]
            if not docker_results:
                raise SandboxCatalogueEntryNotFoundException(
                    f"No active Docker sandbox found with tags: {version_entry.sandbox_selection_tags}"
                )
            return docker_results[0]

        raise ToolComponentOperationException(
            "No sandbox is configured for this tool version. "
            "Set either sandbox_id or sandbox_selection_tags."
        )

    def _validate_input_parameters(
        self,
        version_entry: ToolVersionEntry,
        input_parameters: dict[str, Any],
    ) -> None:
        """Validate input parameters against the tool version's parameter definitions.

        Args:
            version_entry: Tool version with parameter definitions.
            input_parameters: Actual parameter values to validate.

        Raises:
            InvalidToolInvocationException: A required parameter is missing or invalid.
        """
        if not version_entry.input_parameters:
            return

        # Build lookup from parameter name to definition
        param_lookup = {p.name: p for p in version_entry.input_parameters if p.name}

        # Check required parameters
        for name, definition in param_lookup.items():
            if definition.required and name not in input_parameters:
                if definition.default is None:
                    raise InvalidToolInvocationException(
                        f"Required input parameter '{name}' is missing.",
                        details={"parameter_name": name},
                    )

        # Validate provided parameter values
        for key, value in input_parameters.items():
            if key not in param_lookup:
                self._logger.warning(
                    "Unknown input parameter '%s' will be passed to the tool.", key
                )
                continue

            definition = param_lookup[key]

            # Validate against allowed_values
            if definition.allowed_values is not None and value not in definition.allowed_values:
                raise InvalidToolInvocationException(
                    f"Parameter '{key}' value '{value}' is not in the allowed values.",
                    details={"parameter_name": key, "value": value},
                )

            # Validate min/max values for comparable types
            try:
                if definition.min_value is not None and value < definition.min_value:
                    raise InvalidToolInvocationException(
                        f"Parameter '{key}' value {value} is below minimum {definition.min_value}.",
                        details={"parameter_name": key, "value": value},
                    )
                if definition.max_value is not None and value >= definition.max_value:
                    raise InvalidToolInvocationException(
                        f"Parameter '{key}' value {value} is at or above maximum {definition.max_value}.",
                        details={"parameter_name": key, "value": value},
                    )
            except TypeError:
                pass  # Incomparable types; skip range validation

    async def _embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for text using the configured model.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector as list of floats.

        Raises:
            InvalidToolComponentConfigurationException: No model component or missing config.
            ToolComponentOperationException: Embedding operation failure.
        """
        if self._model_component is None:
            raise InvalidToolComponentConfigurationException(
                "No model component is configured for embedding."
            )

        configs = await self.get_configurations()
        if configs.embedding_catalogue_id is None:
            raise InvalidToolComponentConfigurationException(
                "ToolComponentConfigurations.embedding_catalogue_id is not set."
            )

        # Import model component types here to avoid circular dependency
        try:
            from gafs.dynamicaiagent.modelcomponent.models import (
                AiOperationType,
                AiRequest,
                DeploymentSelectionOptions,
                EmbeddingPayload,
            )
            from gafs.dynamicaiagent.modelcomponent.models.ai_deployment_type import (
                AiDeploymentType,
            )
        except ImportError as exc:
            raise InvalidToolComponentConfigurationException(
                "modelcomponent is required for embedding but is not installed.",
                cause=exc,
            ) from exc

        payload = EmbeddingPayload()
        payload.input = text

        request = AiRequest()
        request.operation_type = AiOperationType.EMBEDDING
        request.payload = payload

        selection = DeploymentSelectionOptions()
        selection.deployment_type = AiDeploymentType.CLOUD

        try:
            response = await self._model_component.invoke(
                configs.embedding_catalogue_id, request, selection
            )
        except Exception as exc:
            raise ToolComponentOperationException(
                "Embedding request failed.", cause=exc
            ) from exc

        if response is None or response.output is None:
            raise ToolComponentOperationException("Embedding response is empty.")

        try:
            embedding = response.output.embedding
            if embedding is None:
                raise ToolComponentOperationException("Embedding output has no 'embedding' field.")
            return [float(v) for v in embedding]
        except AttributeError as exc:
            raise ToolComponentOperationException(
                "Could not extract embedding from response output.", cause=exc
            ) from exc

    async def _drop_vector_index_safely(self) -> None:
        """Drop the HNSW vector index on ToolCatalogue (best-effort)."""
        try:
            provider = await self._provider()
            cat = ToolCatalogueEntry.CollectionName()
            # Three-step safe drop sequence
            for query in [
                f"ALTER INDEX idx_tool_catalogue_description_vector ON {cat} PREPARE REMOVE;",
                f"SELECT * FROM {cat} LIMIT 1 EXPLAIN;",
                f"REMOVE INDEX idx_tool_catalogue_description_vector ON {cat};",
            ]:
                try:
                    await provider.query_raw(query)
                except Exception:
                    pass  # Best-effort; ignore errors
        except Exception as exc:
            self._logger.warning("Failed during vector index drop: %s", exc)

    async def _clear_all_description_vectors(self) -> None:
        """Set description_vector to NONE for all ToolCatalogue entries (single transaction)."""
        provider = await self._provider()
        cat = ToolCatalogueEntry.CollectionName()
        txn_q = (
            f"BEGIN TRANSACTION; "
            f"UPDATE {cat} SET description_vector = NONE; "
            f"COMMIT TRANSACTION;"
        )
        try:
            await provider.query_raw(txn_q)
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to clear description vectors.", cause=exc
            ) from exc

    async def _reembed_all_catalogues(self) -> None:
        """Regenerate description_vector for all ToolCatalogue entries with a description."""
        entries = await self._tool_catalogue_service.get_all_tool_catalogue_entries()
        for entry in entries:
            if not entry.description:
                continue
            try:
                vector = await self._embed_text(entry.description)
                object.__setattr__(entry, "description_vector", vector)
                await self._tool_catalogue_service.update_tool_catalogue_entry(entry)
            except Exception as exc:
                self._logger.warning(
                    "Failed to re-embed catalogue entry '%s': %s", entry.id, exc
                )

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    async def initialize(self, database_manager: IDatabaseManager) -> bool:
        """Initialize the tool component.

        Args:
            database_manager: Initialized database manager.

        Returns:
            True on success.

        Raises:
            ToolComponentInitializationException: Initialization failure.
        """
        self._logger.debug("Initializing ToolComponent...")
        try:
            self._database_manager = database_manager

            # Verify the default provider is available
            provider = database_manager.get_default_provider()
            if provider is None:
                raise ToolComponentInitializationException(
                    "Default database provider is not available."
                )

            # Load configurations from DB
            try:
                self._configurations = await self._load_configurations()
            except Exception as exc:
                raise ToolComponentInitializationException(
                    "Failed to load ToolComponentConfigurations during initialization.",
                    cause=exc,
                ) from exc

            # Initialize sub-services
            try:
                await self._tool_catalogue_service.initialize(
                    database_manager, self._configurations
                )
            except Exception as exc:
                raise ToolComponentInitializationException(
                    "Failed to initialize ToolCatalogueService.",
                    cause=exc,
                ) from exc

            try:
                await self._sandbox_catalogue_service.initialize(
                    database_manager, self._configurations
                )
            except Exception as exc:
                raise ToolComponentInitializationException(
                    "Failed to initialize SandboxCatalogueService.",
                    cause=exc,
                ) from exc

            try:
                await self._docker_sandbox_service.initialize(
                    database_manager, self._sandbox_catalogue_service, self._configurations
                )
            except Exception as exc:
                raise ToolComponentInitializationException(
                    "Failed to initialize DockerSandboxService.",
                    cause=exc,
                ) from exc

        except ToolComponentInitializationException:
            raise
        except Exception as exc:
            raise ToolComponentInitializationException(
                "ToolComponent initialization failed.", cause=exc
            ) from exc

        self._logger.info("ToolComponent initialized.")
        return True

    # -------------------------------------------------------------------------
    # Tool invocation
    # -------------------------------------------------------------------------

    async def invoke(
        self,
        tool_id: str,
        version_id: str,
        input_parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a tool by tool_id and version_id.

        Args:
            tool_id: ID of the ToolCatalogueEntry.
            version_id: ID of the ToolVersionEntry.
            input_parameters: Actual values for the tool's input parameters.

        Returns:
            Output parameter values produced by the tool.

        Raises:
            ToolComponentNotInitializedException: Component not initialized.
            ToolCatalogueEntryNotFoundException: No ToolCatalogueEntry for tool_id.
            ToolVersionEntryNotFoundException: No ToolVersionEntry for version_id.
            InvalidToolInvocationException: input_parameters fail validation.
            SandboxCatalogueEntryNotFoundException: No suitable sandbox found.
            ToolComponentOperationException: Tool execution failure.
        """
        if self._database_manager is None:
            raise ToolComponentNotInitializedException(
                "ToolComponent is not initialized."
            )

        # Fetch catalogue and version entries (raises if not found)
        await self._tool_catalogue_service.get_tool_catalogue_entry(tool_id)
        version_entry = await self._tool_catalogue_service.get_tool_version_entry(version_id)

        # Validate input parameters
        self._validate_input_parameters(version_entry, input_parameters)

        # Select sandbox
        sandbox_entry = await self._select_sandbox(version_entry)

        # Execute the tool
        try:
            output = await self._docker_sandbox_service.execute_code(
                version_entry, sandbox_entry, input_parameters
            )
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Tool execution failed.", cause=exc
            ) from exc

        return output

    # -------------------------------------------------------------------------
    # ToolCatalogueEntry delegation
    # -------------------------------------------------------------------------

    async def create_tool_catalogue_entry(
        self, catalogue: ToolCatalogueEntry
    ) -> ToolCatalogueEntry:
        """Create a new tool catalogue entry, auto-embedding description if possible."""
        # Auto-embed description if vector is missing and model is configured
        if catalogue.description and catalogue.description_vector is None:
            try:
                vector = await self._embed_text(catalogue.description)
                object.__setattr__(catalogue, "description_vector", vector)
            except Exception as exc:
                self._logger.warning("Auto-embedding failed for new catalogue entry: %s", exc)

        try:
            return await self._tool_catalogue_service.create_tool_catalogue_entry(catalogue)
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to create ToolCatalogueEntry.", cause=exc
            ) from exc

    async def update_tool_catalogue_entry(
        self, catalogue: ToolCatalogueEntry
    ) -> ToolCatalogueEntry:
        """Update an existing tool catalogue entry, auto-embedding description if changed."""
        if catalogue.description and catalogue.description_vector is None:
            try:
                vector = await self._embed_text(catalogue.description)
                object.__setattr__(catalogue, "description_vector", vector)
            except Exception as exc:
                self._logger.warning("Auto-embedding failed for catalogue update: %s", exc)

        try:
            return await self._tool_catalogue_service.update_tool_catalogue_entry(catalogue)
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to update ToolCatalogueEntry.", cause=exc
            ) from exc

    async def delete_tool_catalogue_entry(self, catalogue_id: str) -> None:
        """Delete a tool catalogue entry."""
        try:
            await self._tool_catalogue_service.delete_tool_catalogue_entry(catalogue_id)
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to delete ToolCatalogueEntry.", cause=exc
            ) from exc

    async def get_tool_catalogue_entry(self, catalogue_id: str) -> ToolCatalogueEntry:
        """Retrieve a tool catalogue entry by ID."""
        try:
            return await self._tool_catalogue_service.get_tool_catalogue_entry(catalogue_id)
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to get ToolCatalogueEntry.", cause=exc
            ) from exc

    async def get_all_tool_catalogue_entries(self) -> list[ToolCatalogueEntry]:
        """Return all tool catalogue entries."""
        try:
            return await self._tool_catalogue_service.get_all_tool_catalogue_entries()
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to get all ToolCatalogueEntries.", cause=exc
            ) from exc

    async def search_tool_catalogue_entries(
        self, search_criteria: ToolCatalogueSearchCriteria
    ) -> list[ToolCatalogueSearchResultEntry]:
        """Search tool catalogue entries."""
        if self._is_rebuilding_vector_index and search_criteria.description_vector is not None:
            raise ToolCatalogueIndexNotAvailableException(
                "The tool catalogue vector index is currently being rebuilt."
            )
        try:
            return await self._tool_catalogue_service.search_tool_catalogue_entries(
                search_criteria
            )
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to search ToolCatalogueEntries.", cause=exc
            ) from exc

    # -------------------------------------------------------------------------
    # ToolVersionEntry delegation
    # -------------------------------------------------------------------------

    async def create_tool_version_entry(
        self, version: ToolVersionEntry
    ) -> ToolVersionEntry:
        """Create a new tool version entry."""
        try:
            return await self._tool_catalogue_service.create_tool_version_entry(version)
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to create ToolVersionEntry.", cause=exc
            ) from exc

    async def update_tool_version_entry(
        self, version: ToolVersionEntry
    ) -> ToolVersionEntry:
        """Update an existing tool version entry."""
        try:
            return await self._tool_catalogue_service.update_tool_version_entry(version)
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to update ToolVersionEntry.", cause=exc
            ) from exc

    async def delete_tool_version_entry(self, version_id: str) -> None:
        """Delete a tool version entry."""
        try:
            await self._tool_catalogue_service.delete_tool_version_entry(version_id)
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to delete ToolVersionEntry.", cause=exc
            ) from exc

    async def get_tool_version_entry(self, version_id: str) -> ToolVersionEntry:
        """Retrieve a tool version entry by ID."""
        try:
            return await self._tool_catalogue_service.get_tool_version_entry(version_id)
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to get ToolVersionEntry.", cause=exc
            ) from exc

    async def get_all_tool_version_entries(
        self, tool_id: str | None = None
    ) -> list[ToolVersionEntry]:
        """Return all tool version entries."""
        try:
            return await self._tool_catalogue_service.get_all_tool_version_entries(tool_id)
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to get all ToolVersionEntries.", cause=exc
            ) from exc

    async def search_tool_version_entries(
        self, search_criteria: ToolVersionEntrySearchCriteria
    ) -> list[ToolVersionEntry]:
        """Search tool version entries."""
        try:
            return await self._tool_catalogue_service.search_tool_version_entries(
                search_criteria
            )
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to search ToolVersionEntries.", cause=exc
            ) from exc

    # -------------------------------------------------------------------------
    # SandboxCatalogueEntry delegation
    # -------------------------------------------------------------------------

    async def create_sandbox_catalogue_entry(
        self, catalogue: SandboxCatalogueEntry
    ) -> SandboxCatalogueEntry:
        """Create a new sandbox catalogue entry."""
        try:
            return await self._sandbox_catalogue_service.create_catalogue_entry(catalogue)
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to create SandboxCatalogueEntry.", cause=exc
            ) from exc

    async def update_sandbox_catalogue_entry(
        self, catalogue: SandboxCatalogueEntry
    ) -> SandboxCatalogueEntry:
        """Update an existing sandbox catalogue entry."""
        try:
            return await self._sandbox_catalogue_service.update_catalogue_entry(catalogue)
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to update SandboxCatalogueEntry.", cause=exc
            ) from exc

    async def delete_sandbox_catalogue_entry(self, catalogue_id: str) -> None:
        """Delete a sandbox catalogue entry."""
        try:
            await self._sandbox_catalogue_service.delete_catalogue_entry(catalogue_id)
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to delete SandboxCatalogueEntry.", cause=exc
            ) from exc

    async def get_sandbox_catalogue_entry(
        self, catalogue_id: str
    ) -> SandboxCatalogueEntry:
        """Retrieve a sandbox catalogue entry by ID."""
        try:
            return await self._sandbox_catalogue_service.get_catalogue_entry(catalogue_id)
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to get SandboxCatalogueEntry.", cause=exc
            ) from exc

    async def get_all_sandbox_catalogue_entries(self) -> list[SandboxCatalogueEntry]:
        """Return all sandbox catalogue entries."""
        try:
            return await self._sandbox_catalogue_service.get_all_catalogue_entries()
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to get all SandboxCatalogueEntries.", cause=exc
            ) from exc

    async def search_sandbox_catalogue_entries(
        self, search_criteria: SandboxCatalogueSearchCriteria
    ) -> list[SandboxCatalogueEntry]:
        """Search sandbox catalogue entries."""
        try:
            return await self._sandbox_catalogue_service.search_catalogue_entries(
                search_criteria
            )
        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to search SandboxCatalogueEntries.", cause=exc
            ) from exc

    # -------------------------------------------------------------------------
    # Configuration management
    # -------------------------------------------------------------------------

    async def get_configurations(self) -> ToolComponentConfigurations:
        """Return the current ToolComponentConfigurations.

        Returns:
            The current ToolComponentConfigurations.

        Raises:
            ToolComponentNotInitializedException: Component not initialized.
            InvalidToolComponentConfigurationException: Configurations invalid.
        """
        if self._configurations is None:
            try:
                self._configurations = await self._load_configurations()
            except Exception as exc:
                raise ToolComponentOperationException(
                    "Failed to load ToolComponentConfigurations.", cause=exc
                ) from exc
        return self._configurations

    async def update_configurations(
        self, configurations: ToolComponentConfigurations
    ) -> ToolComponentConfigurations:
        """Update the ToolComponentConfigurations.

        Determines if the HNSW vector index needs to be rebuilt based on what changed.
        If vector settings changed, rebuilds the index. If embedding settings changed,
        also re-embeds all catalogue descriptions.

        Args:
            configurations: New configuration values to persist.

        Returns:
            The updated ToolComponentConfigurations.

        Raises:
            ToolComponentNotInitializedException: Component not initialized.
            ToolComponentOperationException: Operation failure.
        """
        try:
            current = await self.get_configurations()

            # Determine if vector-related changes require index/embedding rebuild
            requires_reembed = (
                configurations.embedding_catalogue_id != current.embedding_catalogue_id or
                configurations.vector_data_type != current.vector_data_type or
                configurations.vector_dimensions != current.vector_dimensions
            )
            requires_rebuild_only = (
                configurations.vector_search_method != current.vector_search_method or
                configurations.vector_exploration_factor != current.vector_exploration_factor or
                configurations.vector_max_connections != current.vector_max_connections
            )
            needs_vector_rebuild = requires_reembed or requires_rebuild_only

            if not needs_vector_rebuild:
                # Simple persist
                self._configurations = await self._save_configurations(configurations)
                return self._configurations

            # Rebuild the vector index
            self._is_rebuilding_vector_index = True
            try:
                await self._drop_vector_index_safely()

                if requires_reembed:
                    await self._clear_all_description_vectors()

                self._configurations = await self._save_configurations(configurations)

                # Recreate the HNSW index with new settings
                await self._tool_catalogue_service.ensure_indexes(
                    self._configurations, overwrite=True
                )

                if requires_reembed:
                    await self._reembed_all_catalogues()
            finally:
                self._is_rebuilding_vector_index = False

            return self._configurations

        except ToolComponentException:
            raise
        except Exception as exc:
            raise ToolComponentOperationException(
                "Failed to update ToolComponentConfigurations.", cause=exc
            ) from exc
