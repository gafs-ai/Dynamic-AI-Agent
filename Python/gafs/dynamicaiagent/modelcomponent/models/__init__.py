"""
gafs.dynamicaiagent.modelcomponent.models - Model Component data classes and enums.
"""

from .ai_deployment_type import AiDeploymentType
from .ai_operation_type import AiOperationType
from .ai_provider_type import AiProviderType
from .ai_operation_status import AiOperationStatus, AiOperationStatusEnum
from .message import (
    Role,
    ContentType,
    MessagePart,
    TextMessagePart,
    ImageUrlMessagePart,
    AudioData,
    AudioDataMessagePart,
    FileData,
    FileMessagePart,
    RefusalMessagePart,
    Message,
)
from .ai_payload import AiPayload, TextCompletionPayload, ChatCompletionPayload, EmbeddingPayload
from .ai_output import AiOutput, TextCompletionOutput, ChatCompletionOutput, EmbeddingOutput
from .ai_response import AiResponse
from .ai_request import AiRequest
from .ai_connection_parameters import AiConnectionParameters
from .deployment_selection_options import DeploymentSelectionOptions
from .model_catalogue import (
    ModelStatus,
    DeploymentStatus,
    ModelDeployment,
    ModelCatalogueEntry,
    ModelCatalogueSearchResultEntry,
)
from .model_component_configurations import ModelComponentConfigurations
from .model_deployment_edge import ModelDeploymentEdge
from .deployment_secret_edge import DeploymentSecretEdge
from .model_catalogue_search_criteria import (
    LogicalOperator,
    TagsSearchCriteria,
    VectorSearchCriteria,
    ModelCatalogueSearchCriteria,
)
from .model_deployment_search_criteria import ModelDeploymentSearchCriteria

__all__ = [
    # AI operation models
    "AiConnectionParameters",
    "AiDeploymentType",
    "AiOperationStatus",
    "AiOperationStatusEnum",
    "AiOperationType",
    "AiPayload",
    "AiProviderType",
    "AiRequest",
    "AiResponse",
    "AiOutput",
    "ChatCompletionOutput",
    "ChatCompletionPayload",
    "EmbeddingOutput",
    "EmbeddingPayload",
    "Message",
    "MessagePart",
    "TextCompletionOutput",
    "TextCompletionPayload",
    "Role",
    "ContentType",
    "TextMessagePart",
    "ImageUrlMessagePart",
    "AudioData",
    "AudioDataMessagePart",
    "FileData",
    "FileMessagePart",
    "RefusalMessagePart",
    # Deployment selection
    "DeploymentSelectionOptions",
    # Catalogue and deployment data models
    "ModelStatus",
    "DeploymentStatus",
    "ModelDeployment",
    "ModelCatalogueEntry",
    "ModelCatalogueSearchResultEntry",
    "ModelComponentConfigurations",
    "ModelDeploymentEdge",
    "DeploymentSecretEdge",
    # Search criteria
    "LogicalOperator",
    "TagsSearchCriteria",
    "VectorSearchCriteria",
    "ModelCatalogueSearchCriteria",
    "ModelDeploymentSearchCriteria",
]
