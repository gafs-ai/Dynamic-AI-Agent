"""gafs.dynamicaiagent.toolcomponent - Tool Component.

Provides tool catalogue management, sandbox catalogue management, and
sandboxed tool execution via Docker containers.
"""

from .exceptions import (
    ConflictingSandboxCatalogueEntryException,
    ConflictingToolCatalogueEntryException,
    ConflictingToolVersionEntryException,
    FullTextAnalyzerNotExistException,
    InvalidSandboxCatalogueEntryException,
    InvalidSandboxCatalogueSearchCriteriaException,
    InvalidToolCatalogueEntryException,
    InvalidToolCatalogueSearchCriteriaException,
    InvalidToolComponentConfigurationException,
    InvalidToolInvocationException,
    InvalidToolVersionEntryException,
    InvalidToolVersionSearchCriteriaException,
    SandboxCatalogueEntryNotFoundException,
    ToolCatalogueEntryNotFoundException,
    ToolCatalogueIndexNotAvailableException,
    ToolComponentConfigurationException,
    ToolComponentConflictException,
    ToolComponentException,
    ToolComponentInitializationException,
    ToolComponentNotInitializedException,
    ToolComponentOperationException,
    ToolComponentResourceNotFoundException,
    ToolComponentValidationException,
    ToolVersionEntryNotFoundException,
)
from .i_docker_sandbox_service import IDockerSandboxService
from .i_sandbox_catalogue_service import ISandboxCatalogueService
from .i_tool_catalogue_service import IToolCatalogueService
from .i_tool_component import IToolComponent
from .docker_sandbox_service import DockerSandboxService
from .sandbox_catalogue_service import SandboxCatalogueService
from .tool_catalogue_service import ToolCatalogueService
from .tool_component import ToolComponent
from .models import (
    InputFileDefinition,
    InputParameterDefinition,
    LogicalOperator,
    OutputFileDefinition,
    OutputParameterDefinition,
    SandboxCatalogueDockerEntry,
    SandboxCatalogueEntry,
    SandboxCatalogueHostEntry,
    SandboxCatalogueSearchCriteria,
    SandboxStatus,
    SandboxType,
    TagsSearchCriteria,
    ToolCatalogueEntry,
    ToolCatalogueSearchCriteria,
    ToolCatalogueSearchResultEntry,
    ToolComponentConfigurations,
    ToolStatus,
    ToolVersionEntry,
    ToolVersionEntrySearchCriteria,
    ToolVersionStatus,
)

__all__ = [
    # Exceptions
    "ToolComponentException",
    "ToolComponentConfigurationException",
    "ToolComponentInitializationException",
    "ToolComponentNotInitializedException",
    "InvalidToolComponentConfigurationException",
    "ToolComponentValidationException",
    "InvalidToolCatalogueEntryException",
    "InvalidToolCatalogueSearchCriteriaException",
    "InvalidToolVersionEntryException",
    "InvalidToolVersionSearchCriteriaException",
    "InvalidSandboxCatalogueEntryException",
    "InvalidSandboxCatalogueSearchCriteriaException",
    "InvalidToolInvocationException",
    "ToolComponentConflictException",
    "ConflictingToolCatalogueEntryException",
    "ConflictingToolVersionEntryException",
    "ConflictingSandboxCatalogueEntryException",
    "ToolComponentResourceNotFoundException",
    "ToolCatalogueEntryNotFoundException",
    "ToolVersionEntryNotFoundException",
    "SandboxCatalogueEntryNotFoundException",
    "ToolComponentOperationException",
    "ToolCatalogueIndexNotAvailableException",
    "FullTextAnalyzerNotExistException",
    # Interfaces
    "IDockerSandboxService",
    "ISandboxCatalogueService",
    "IToolCatalogueService",
    "IToolComponent",
    # Implementations
    "DockerSandboxService",
    "SandboxCatalogueService",
    "ToolCatalogueService",
    "ToolComponent",
    # Models
    "InputFileDefinition",
    "InputParameterDefinition",
    "LogicalOperator",
    "OutputFileDefinition",
    "OutputParameterDefinition",
    "SandboxCatalogueDockerEntry",
    "SandboxCatalogueEntry",
    "SandboxCatalogueHostEntry",
    "SandboxCatalogueSearchCriteria",
    "SandboxStatus",
    "SandboxType",
    "TagsSearchCriteria",
    "ToolCatalogueEntry",
    "ToolCatalogueSearchCriteria",
    "ToolCatalogueSearchResultEntry",
    "ToolComponentConfigurations",
    "ToolStatus",
    "ToolVersionEntry",
    "ToolVersionEntrySearchCriteria",
    "ToolVersionStatus",
]
