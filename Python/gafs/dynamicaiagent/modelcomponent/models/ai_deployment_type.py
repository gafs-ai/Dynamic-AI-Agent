from enum import Enum


class AiDeploymentType(Enum):
    """Enum for AI provider deployment type (cloud, local, remote)."""

    CLOUD = "cloud"
    LOCAL = "local"
    REMOTE = "remote"
