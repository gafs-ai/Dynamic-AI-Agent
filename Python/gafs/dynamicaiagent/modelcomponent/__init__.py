"""gafs.dynamicaiagent.modelcomponent - Model catalogue and AI model functionality.

Provides the model catalogue (metadata store for AI models), catalogue service
(CRUD and search), search criteria, and payload types for completion/embedding.
model_provider_service and model_component are to be implemented.
"""
from gafs.dynamicaiagent.modelcomponent.models.model_catalogue import (
    ModelCatalogue,
    ModelCatalogueSearchResultEntry,
    ModelDeployment,
    ModelStatus,
    AiOperationType
)
from gafs.dynamicaiagent.modelcomponent.model_catalogue_service import (
    ModelCatalogueService,
)
from gafs.dynamicaiagent.modelcomponent.models.hnsw_search_method import HnswSearchMethod
from gafs.dynamicaiagent.modelcomponent.models.model_catalogue_search_criteria import (
    LogicalOperator,
    ModelCatalogueSearchCriteria,
    TagsSearchCriteria,
    VectorSearchCriteria,
)
from gafs.dynamicaiagent.modelcomponent.i_model_catalogue_service import (
    IModelCatalogueService,
)
from gafs.dynamicaiagent.modelcomponent.models.ai_connection_parameters import AiConnectionParameters
from gafs.dynamicaiagent.modelcomponent.models.ai_deployment_type import AiDeploymentType
from gafs.dynamicaiagent.modelcomponent.models.ai_payload import (
    AiPayload,
    ChatCompletionPayload,
    EmbeddingPayload,
    TextCompletionPayload,
)
from gafs.dynamicaiagent.modelcomponent.models.message import ContentType, Message

AiOptions = AiConnectionParameters

__all__ = [
    # model_catalogue
    "AiDeploymentType",
    "ModelCatalogue",
    "ModelCatalogueSearchResultEntry",
    "ModelDeployment",
    "ModelStatus",
    "AiOperationType",
    # model_catalogue_service
    "HnswSearchMethod",
    "LogicalOperator",
    "ModelCatalogueSearchCriteria",
    "ModelCatalogueService",
    "TagsSearchCriteria",
    "VectorSearchCriteria",
    # interface
    "IModelCatalogueService",
    # connection parameters (AiOptions is a backward-compatibility alias)
    "AiConnectionParameters",
    "AiOptions",
    # payload / models
    "AiPayload",
    "ChatCompletionPayload",
    "ContentType",
    "EmbeddingPayload",
    "Message",
    "TextCompletionPayload",
]

