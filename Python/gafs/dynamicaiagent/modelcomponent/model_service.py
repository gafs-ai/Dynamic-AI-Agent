from __future__ import annotations

import logging
from typing import Any, override

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager
from gafs.dynamicaiagent.common.secretmanager.secret import Secret
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider
from gafs.dynamicaiagent.cloudaicomponent.cloud_ai_component import ICloudAiComponent
from .i_model_catalogue_service import IModelCatalogueService
from .i_model_service import IModelService
from .models.ai_connection_parameters import AiConnectionParameters
from .models.ai_deployment_type import AiDeploymentType
from .models.ai_request import AiRequest
from .models.ai_response import AiResponse
from .models.deployment_selection_options import DeploymentSelectionOptions
from .models.model_catalogue import (
    AvailableInferenceParameters,
    ModelCatalogue,
    ModelDeployment,
    ParameterType,
)


class ModelService(IModelService):
    """Service for the model."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger: logging.Logger = logger

    @override
    async def initialize(
        self,
        database_manager: IDatabaseManager,
        model_catalogue_service: IModelCatalogueService | None = None,
        cloud_ai_component: ICloudAiComponent | None = None,
    ) -> bool:
        """Initialize the model service."""
        if model_catalogue_service is None or cloud_ai_component is None:
            raise ValueError(
                "model_catalogue_service and cloud_ai_component are required."
            )
        self._database_manager = database_manager
        self._model_catalogue_service = model_catalogue_service
        self._cloud_ai_component = cloud_ai_component
        return True

    def _provider(self) -> IDatabaseProvider:
        provider = self._database_manager.get_default_database_provider()
        if provider is None:
            raise ValueError("Default database provider is not available.")
        return provider

    @override
    async def invoke(
        self,
        catalogue_id: str,
        request: AiRequest,
        deployment_selection_options: DeploymentSelectionOptions | None = None,
    ) -> AiResponse:
        """Invoke the model."""
        catalogue: ModelCatalogue = await self._model_catalogue_service.get_catalogue(
            catalogue_id
        )
        if catalogue is None:
            raise ValueError(f"Catalogue not found: {catalogue_id}")

        self._validate_and_merge_request_parameters(catalogue, request)

        deployments = await self._select_deployments(catalogue, deployment_selection_options)
        if len(deployments) == 0:
            raise ValueError(f"No deployments found for catalogue: {catalogue_id}")

        last_error: Exception | None = None
        for deployment in deployments:
            try:
                return await self._invoke_with_deployment(deployment, request)
            except Exception as e:
                self._logger.error("Error invoking deployment %s: %s", deployment.id, e)
                last_error = e
                continue

        if last_error is not None:
            raise last_error
        raise ValueError(f"No deployments were successful for catalogue: {catalogue_id}")

    def _validate_and_merge_request_parameters(
        self, catalogue: ModelCatalogue, request: AiRequest
    ) -> None:
        request_parameters: dict[str, Any] = (
            request.parameters if isinstance(request.parameters, dict) else {}
        )

        available_defs_by_key: dict[str, AvailableInferenceParameters] = {}
        if isinstance(catalogue.available_inference_parameters, list):
            for item in catalogue.available_inference_parameters:
                if isinstance(item, AvailableInferenceParameters) and isinstance(
                    item.key, str
                ):
                    available_defs_by_key[item.key] = item

        validated_parameters: dict[str, Any] = {}
        for key, value in request_parameters.items():
            parameter_def = available_defs_by_key.get(key)
            if parameter_def is None:
                # Ignore unknown keys.
                continue
            validated_parameters[key] = self._validate_parameter_value(parameter_def, value)

        if catalogue.default_inference_parameters is not None:
            for key, value in catalogue.default_inference_parameters.items():
                if key not in validated_parameters:
                    validated_parameters[key] = value

        request.parameters = validated_parameters

    @staticmethod
    def _validate_parameter_value(
        parameter_def: AvailableInferenceParameters, value: Any
    ) -> Any:
        if parameter_def.type == ParameterType.STR:
            if not isinstance(value, str):
                raise ValueError(f"Parameter '{parameter_def.key}' must be str.")
        elif parameter_def.type == ParameterType.INT:
            if not isinstance(value, int):
                raise ValueError(f"Parameter '{parameter_def.key}' must be int.")
        elif parameter_def.type == ParameterType.FLOAT:
            if not isinstance(value, (int, float)):
                raise ValueError(f"Parameter '{parameter_def.key}' must be float.")
            value = float(value)
        elif parameter_def.type == ParameterType.BOOL:
            if not isinstance(value, bool):
                raise ValueError(f"Parameter '{parameter_def.key}' must be bool.")

        if parameter_def.allowed_values is not None and value not in parameter_def.allowed_values:
            raise ValueError(f"Parameter '{parameter_def.key}' has an unsupported value.")
        if parameter_def.min is not None and value < parameter_def.min:
            raise ValueError(f"Parameter '{parameter_def.key}' must be >= {parameter_def.min}.")
        if parameter_def.max is not None and value > parameter_def.max:
            raise ValueError(f"Parameter '{parameter_def.key}' must be <= {parameter_def.max}.")
        return value

    async def _select_deployments(
        self,
        catalogue: ModelCatalogue,
        deployment_selection_options: DeploymentSelectionOptions | None,
    ) -> list[ModelDeployment]:
        if catalogue.deployments is None or len(catalogue.deployments) == 0:
            return []

        deployments: list[ModelDeployment] = []
        for deployment_id in catalogue.deployments:
            deployment = await self._model_catalogue_service.get_deployment(deployment_id)
            if deployment is not None:
                deployments.append(deployment)

        if deployment_selection_options is not None:
            if deployment_selection_options.deployment_type is not None:
                deployments = [
                    deployment
                    for deployment in deployments
                    if deployment.deployment_type == deployment_selection_options.deployment_type
                ]
            if deployment_selection_options.confidence is not None:
                deployments = [
                    deployment
                    for deployment in deployments
                    if deployment.max_confidence_level is not None
                    and deployment.max_confidence_level >= deployment_selection_options.confidence
                ]

        return sorted(
            deployments,
            key=lambda item: item.priority if item.priority is not None else 0,
            reverse=True,
        )

    async def _invoke_with_deployment(
        self, deployment: ModelDeployment, request: AiRequest
    ) -> AiResponse:
        base_connection_parameters: dict[str, Any] = (
            deployment.connection_parameters
            if deployment.connection_parameters is not None
            else {}
        )
        secret_links = self._get_secret_links(deployment)

        if len(secret_links) == 0:
            return await self._invoke_model_operation(
                deployment, request, base_connection_parameters
            )

        last_error: Exception | None = None
        for secret_link in secret_links:
            try:
                secret_values = await self._get_secret_values(secret_link)
                merged_connection_parameters = {
                    **base_connection_parameters,
                    **secret_values,
                }
                return await self._invoke_model_operation(
                    deployment, request, merged_connection_parameters
                )
            except Exception as e:
                self._logger.error(
                    "Error invoking deployment %s with secret %s: %s",
                    deployment.id,
                    secret_link,
                    e,
                )
                last_error = e
                continue

        if last_error is not None:
            raise last_error
        raise ValueError(f"No available secret for deployment: {deployment.id}")

    @staticmethod
    def _get_secret_links(deployment: ModelDeployment) -> list[str]:
        links: list[str] = []
        secret_links = getattr(deployment, "secret_links", None)
        if isinstance(secret_links, list):
            links.extend([item for item in secret_links if isinstance(item, str)])
        legacy_secrets = getattr(deployment, "secrets", None)
        if isinstance(legacy_secrets, list):
            links.extend([item for item in legacy_secrets if isinstance(item, str)])
        return list(dict.fromkeys(links))

    async def _get_secret_values(self, secret_link: str) -> dict[str, Any]:
        secret_id = secret_link.split(":", 1)[1] if ":" in secret_link else secret_link
        query = f"SELECT * FROM secret:{secret_id};"
        secret = await self._provider().query(query, Secret)
        if secret is None or secret.secret is None:
            raise ValueError(f"Secret not found: {secret_link}")
        if not isinstance(secret.secret, dict):
            raise ValueError(f"Invalid secret payload: {secret_link}")

        values: dict[str, Any] = {}
        for key, value in secret.secret.items():
            if key.startswith("raw_"):
                values[key[4:]] = value
            else:
                values[key] = value
        return values

    async def _invoke_model_operation(
        self,
        deployment: ModelDeployment,
        request: AiRequest,
        connection_parameters: dict[str, Any],
    ) -> AiResponse:
        match deployment.deployment_type:
            case AiDeploymentType.CLOUD:
                connection = AiConnectionParameters(
                    operation_type=request.operation_type,
                    deployment_type=deployment.deployment_type,
                    provider_type=deployment.provider_type,
                )
                connection.parameters = connection_parameters
                return await self._cloud_ai_component.invoke(connection, request)
            case AiDeploymentType.LOCAL:
                raise NotImplementedError("Local deployment is not implemented yet")
            case AiDeploymentType.REMOTE:
                raise NotImplementedError("Remote deployment is not implemented yet")
            case _:
                raise ValueError(f"Invalid deployment type: {deployment.deployment_type}")
