"""model_service.py - Concrete implementation of IModelService.

Selects an appropriate ModelDeployment for a given catalogue entry and
delegates the actual inference call to the AI provider component.
"""

from __future__ import annotations

import logging
from typing import Any

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager
from gafs.dynamicaiagent.common.models import AttributeDefinition, FieldAttributeType
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider

from .exceptions import (
    InvalidAiRequestException,
    ModelCatalogueEntryNotFoundException,
    ModelComponentInitializationException,
    ModelComponentNotInitializedException,
    ModelComponentOperationException,
    ModelDeploymentNotFoundException,
)
from .i_model_catalogue_service import IModelCatalogueService
from .i_model_service import IModelService
from .models import (
    AiConnectionParameters,
    AiDeploymentType,
    AiRequest,
    AiResponse,
    DeploymentSelectionOptions,
    ModelCatalogueEntry,
    ModelDeployment,
)


class ModelService(IModelService):
    """Inference delegation service.

    Selects the best deployment for a request, resolves its connection secrets,
    and delegates the call to the appropriate cloud AI provider.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the service.

        Args:
            logger: Logger instance for operational messages.
        """
        self._logger: logging.Logger = logger
        self._database_manager: IDatabaseManager | None = None
        self._model_catalogue_service: IModelCatalogueService | None = None
        self._cloud_ai_component: Any | None = None  # ICloudAiComponent (avoid circular)

    # -------------------------------------------------------------------------
    # Helper utilities
    # -------------------------------------------------------------------------

    def _provider(self) -> IDatabaseProvider:
        """Return the default IDatabaseProvider.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
        """
        if self._database_manager is None:
            raise ModelComponentNotInitializedException(
                "ModelService is not initialized (no IDatabaseManager)."
            )
        provider = self._database_manager.get_default_provider()
        if provider is None:
            raise ModelComponentNotInitializedException(
                "Default database provider is not available."
            )
        return provider

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    async def initialize(
        self,
        database_manager: IDatabaseManager,
        model_catalogue_service: IModelCatalogueService | None = None,
        cloud_ai_component: Any | None = None,
    ) -> bool:
        """Initialize the model service.

        Args:
            database_manager: Provides the default ``IDatabaseProvider``.
            model_catalogue_service: Catalogue service for deployment lookups.
            cloud_ai_component: Cloud AI component for inference calls.

        Returns:
            ``True`` on success.

        Raises:
            ModelComponentInitializationException: Either argument is ``None``.
        """
        if model_catalogue_service is None or cloud_ai_component is None:
            raise ModelComponentInitializationException(
                "Both model_catalogue_service and cloud_ai_component are required."
            )
        self._database_manager = database_manager
        self._model_catalogue_service = model_catalogue_service
        self._cloud_ai_component = cloud_ai_component
        self._logger.info("ModelService initialized.")
        return True

    # -------------------------------------------------------------------------
    # Public interface
    # -------------------------------------------------------------------------

    async def invoke(
        self,
        catalogue_id: str,
        request: AiRequest,
        deployment_selection_options: DeploymentSelectionOptions | None = None,
    ) -> AiResponse:
        """Invoke an AI model via the most suitable deployment.

        Args:
            catalogue_id: ID of the ``ModelCatalogueEntry`` record.
            request: Operation type, payload, and inference parameters.
            deployment_selection_options: Optional filters for deployment selection.

        Returns:
            The model output and operation status.

        Raises:
            ModelComponentNotInitializedException: Service is not initialized.
            ModelCatalogueEntryNotFoundException: No catalogue entry for the id.
            ModelDeploymentNotFoundException: No eligible deployment found.
            ModelComponentOperationException: Database or inference failures.
        """
        if self._model_catalogue_service is None or self._cloud_ai_component is None:
            raise ModelComponentNotInitializedException(
                "ModelService is not initialized."
            )

        # Resolve the catalogue entry.
        catalogue = await self._model_catalogue_service.get_catalogue_entry(catalogue_id)
        if catalogue is None:
            raise ModelCatalogueEntryNotFoundException(
                f"Catalogue entry not found: {catalogue_id}",
                details={"catalogue_id": catalogue_id},
            )

        # Validate and merge inference parameters.
        self._validate_and_merge_request_parameters(catalogue, request)

        # Select deployments.
        deployments = await self._select_deployments(catalogue, deployment_selection_options)
        if len(deployments) == 0:
            raise ModelDeploymentNotFoundException(
                f"No eligible deployments found for catalogue: {catalogue_id}",
                details={"catalogue_id": catalogue_id},
            )

        # Try each deployment in priority order.
        last_error: Exception | None = None
        for deployment in deployments:
            try:
                return await self._invoke_with_deployment(deployment, request)
            except Exception as exc:
                self._logger.error(
                    "Error invoking deployment '%s': %s",
                    deployment.id,
                    exc,
                )
                last_error = exc
                continue

        if last_error is not None:
            raise last_error
        raise ModelComponentOperationException(
            f"All deployments failed for catalogue: {catalogue_id}"
        )

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _validate_and_merge_request_parameters(
        self,
        catalogue: ModelCatalogueEntry,
        request: AiRequest,
    ) -> None:
        """Validate request parameters against the catalogue schema and merge defaults.

        Unknown keys are silently discarded.  Invalid values raise
        ``InvalidAiRequestException``.

        Args:
            catalogue: Catalogue entry with schema and defaults.
            request: Request whose ``parameters`` field is modified in-place.
        """
        request_parameters: dict[str, Any] = (
            request.parameters if isinstance(request.parameters, dict) else {}
        )

        # Build lookup from key to AttributeDefinition.
        available_defs: dict[str, AttributeDefinition] = {}
        if isinstance(catalogue.available_inference_parameters, list):
            for item in catalogue.available_inference_parameters:
                if isinstance(item, AttributeDefinition) and isinstance(item.key, str):
                    available_defs[item.key] = item

        validated: dict[str, Any] = {}
        for key, value in request_parameters.items():
            param_def = available_defs.get(key)
            if param_def is None:
                # Ignore unknown parameters.
                continue
            validated[key] = self._validate_parameter_value(param_def, value)

        # Merge default inference parameters (request values take precedence).
        if catalogue.default_inference_parameters is not None:
            for key, value in catalogue.default_inference_parameters.items():
                if key not in validated:
                    validated[key] = value

        request.parameters = validated

    @staticmethod
    def _validate_parameter_value(
        parameter_def: AttributeDefinition,
        value: Any,
    ) -> Any:
        """Validate a single parameter value against an ``AttributeDefinition``.

        Args:
            parameter_def: Schema definition.
            value: Caller-supplied value.

        Returns:
            Validated (and possibly coerced) value.

        Raises:
            InvalidAiRequestException: Type mismatch, out-of-range, or disallowed value.
        """
        field_type = parameter_def.type
        if field_type == FieldAttributeType.STR:
            if not isinstance(value, str):
                raise InvalidAiRequestException(
                    f"Parameter '{parameter_def.key}' must be str."
                )
        elif field_type == FieldAttributeType.INT:
            if not isinstance(value, int) or isinstance(value, bool):
                raise InvalidAiRequestException(
                    f"Parameter '{parameter_def.key}' must be int."
                )
        elif field_type == FieldAttributeType.FLOAT:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise InvalidAiRequestException(
                    f"Parameter '{parameter_def.key}' must be float."
                )
            value = float(value)
        elif field_type == FieldAttributeType.BOOL:
            if not isinstance(value, bool):
                raise InvalidAiRequestException(
                    f"Parameter '{parameter_def.key}' must be bool."
                )

        if parameter_def.allowed_values is not None and value not in parameter_def.allowed_values:
            raise InvalidAiRequestException(
                f"Parameter '{parameter_def.key}' value is not in allowed values.",
                details={"key": parameter_def.key, "value": value},
            )
        if parameter_def.min is not None and value < parameter_def.min:
            raise InvalidAiRequestException(
                f"Parameter '{parameter_def.key}' must be >= {parameter_def.min}."
            )
        if parameter_def.max is not None and value > parameter_def.max:
            raise InvalidAiRequestException(
                f"Parameter '{parameter_def.key}' must be <= {parameter_def.max}."
            )
        return value

    async def _select_deployments(
        self,
        catalogue: ModelCatalogueEntry,
        deployment_selection_options: DeploymentSelectionOptions | None,
    ) -> list[ModelDeployment]:
        """Select and sort deployments for a catalogue entry.

        Args:
            catalogue: Entry whose ``deployments`` list is resolved.
            deployment_selection_options: Optional type and confidence filters.

        Returns:
            Eligible deployments sorted by ``priority`` descending.
        """
        if not catalogue.deployments:
            return []

        deployments: list[ModelDeployment] = []
        for dep_id in catalogue.deployments:
            dep = await self._model_catalogue_service.get_deployment(dep_id)  # type: ignore[union-attr]
            if dep is not None:
                deployments.append(dep)

        if deployment_selection_options is not None:
            if deployment_selection_options.deployment_type is not None:
                deployments = [
                    d for d in deployments
                    if d.deployment_type == deployment_selection_options.deployment_type
                ]
            if deployment_selection_options.confidence is not None:
                deployments = [
                    d for d in deployments
                    if d.max_confidence_level is not None
                    and d.max_confidence_level >= deployment_selection_options.confidence
                ]

        return sorted(
            deployments,
            key=lambda d: d.priority if d.priority is not None else 0,
            reverse=True,
        )

    async def _invoke_with_deployment(
        self,
        deployment: ModelDeployment,
        request: AiRequest,
    ) -> AiResponse:
        """Invoke the model using a single deployment.

        Merges connection secrets into the base connection parameters and
        tries each available secret in order.

        Args:
            deployment: Deployment to use.
            request: Request to execute.

        Returns:
            Inference response.

        Raises:
            ModelDeploymentNotFoundException: No accessible secret was found.
            ModelComponentOperationException: All secrets failed.
        """
        base_params: dict[str, Any] = (
            deployment.connection_parameters
            if isinstance(deployment.connection_parameters, dict)
            else {}
        )
        secret_links = deployment.secrets or []

        if not secret_links:
            return await self._invoke_model_operation(deployment, request, base_params)

        last_error: Exception | None = None
        for secret_id in secret_links:
            try:
                secret_values = await self._get_secret_values(secret_id)
                merged = {**base_params, **secret_values}
                return await self._invoke_model_operation(deployment, request, merged)
            except Exception as exc:
                self._logger.error(
                    "Error invoking deployment '%s' with secret '%s': %s",
                    deployment.id,
                    secret_id,
                    exc,
                )
                last_error = exc
                continue

        if last_error is not None:
            raise last_error
        raise ModelComponentOperationException(
            f"No accessible secret for deployment: {deployment.id}"
        )

    async def _invoke_model_operation(
        self,
        deployment: ModelDeployment,
        request: AiRequest,
        connection_parameters: dict[str, Any],
    ) -> AiResponse:
        """Dispatch an inference call to the appropriate provider.

        Args:
            deployment: Specifies the deployment type and provider type.
            request: Operation type and payload.
            connection_parameters: Merged base + secret parameters.

        Returns:
            Inference response.

        Raises:
            NotImplementedError: For LOCAL or REMOTE deployment types.
            ModelComponentOperationException: For unknown deployment types.
        """
        if deployment.deployment_type == AiDeploymentType.CLOUD:
            connection = AiConnectionParameters(
                operation_type=request.operation_type,
                deployment_type=deployment.deployment_type,
                provider_type=deployment.provider_type,
            )
            connection.parameters = connection_parameters
            return await self._cloud_ai_component.invoke(connection, request)
        elif deployment.deployment_type == AiDeploymentType.LOCAL:
            raise NotImplementedError("Local deployment is not yet implemented.")
        elif deployment.deployment_type == AiDeploymentType.REMOTE:
            raise NotImplementedError("Remote deployment is not yet implemented.")
        else:
            raise ModelComponentOperationException(
                f"Unknown deployment type: {deployment.deployment_type}"
            )

    async def _get_secret_values(self, secret_id: str) -> dict[str, Any]:
        """Retrieve plaintext secret values from the ``Secrets`` collection.

        Reads the secret record directly (without decryption support) and returns
        the ``raw_secret`` dict.  For production use with encrypted secrets, use
        ``ISecretManager.get_secret(id, decrypt=True)`` and expose the interface
        through the component's dependency injection.

        Args:
            secret_id: Record id (with or without ``Secrets:`` prefix).

        Returns:
            Plaintext secret key–value pairs from ``raw_secret``.

        Raises:
            ModelDeploymentNotFoundException: No record found or ``raw_secret`` is
                missing/None.
            ModelComponentOperationException: Database failure or unexpected format.
        """
        provider = self._provider()
        # Strip table prefix if present.
        key = secret_id.rsplit(":", 1)[-1] if ":" in secret_id else secret_id
        escaped = key.replace("'", "''")
        query = f"SELECT * FROM type::thing('Secrets', '{escaped}');"

        try:
            raw = await provider.query_raw(query)
        except Exception as exc:
            raise ModelComponentOperationException(
                f"Failed to query secret '{secret_id}'.",
                cause=exc,
            ) from exc

        # Unwrap provider envelopes.
        if hasattr(provider, "unwrap_query_raw_result"):
            raw = provider.unwrap_query_raw_result(raw)
        if isinstance(raw, list):
            raw = raw[0] if raw else None

        if raw is None:
            raise ModelDeploymentNotFoundException(
                f"Secret not found: {secret_id}",
                details={"secret_id": secret_id},
            )

        # Unwrap single record if needed.
        if hasattr(provider, "unwrap_record"):
            raw = provider.unwrap_record(raw)
        if not isinstance(raw, dict):
            raise ModelComponentOperationException(
                f"Unexpected secret record format for '{secret_id}': {type(raw)}"
            )

        # Prefer raw_secret (populated by SecretManager after decryption).
        raw_secret = raw.get("raw_secret")
        if raw_secret is None:
            raise ModelDeploymentNotFoundException(
                f"Secret '{secret_id}' has no raw_secret field (may not be decrypted).",
                details={"secret_id": secret_id},
            )
        if not isinstance(raw_secret, dict):
            raise ModelComponentOperationException(
                f"Secret '{secret_id}' raw_secret is not a dict: {type(raw_secret)}"
            )
        return raw_secret
