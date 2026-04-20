"""
gafs.dynamicaiagent.common.secretmanager - Secret manager component.

Provides SecretManager for managing cryptographic keys and encrypted secret entries.
"""

from .i_secret_manager import ISecretManager, SecretSearchCriteria
from .secret_manager import SecretManager
from .models import Secret, SecretKey
from .exceptions import (
    SecretManagerException,
    SecretManagerInitializationException,
    SecretManagerNotInitializedException,
    SecretManagerInvalidSecretEntryException,
    SecretManagerKeyNotFoundException,
    SecretManagerSecretNotFoundException,
    SecretManagerOperationException,
    SecretManagerCryptoException,
)

__all__ = [
    "ISecretManager",
    "SecretSearchCriteria",
    "SecretManager",
    "Secret",
    "SecretKey",
    "SecretManagerException",
    "SecretManagerInitializationException",
    "SecretManagerNotInitializedException",
    "SecretManagerInvalidSecretEntryException",
    "SecretManagerKeyNotFoundException",
    "SecretManagerSecretNotFoundException",
    "SecretManagerOperationException",
    "SecretManagerCryptoException",
]
