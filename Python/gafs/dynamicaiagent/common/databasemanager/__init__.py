"""
gafs.dynamicaiagent.common.databasemanager - Database manager component.

Provides the DatabaseManager class for managing database connections, provider instances,
and full-text analyzer configurations.
"""

from .database_manager import DatabaseManager
from .i_database_manager import IDatabaseManager
from .models import (
    DatabaseConnection,
    FilterDefinition,
    FullTextAnalyzer,
    FunctionDefinition,
    SurrealFilter,
    SurrealTokenizer,
    TokenizerDefinition,
)
from .exceptions import (
    DatabaseManagerException,
    DatabaseManagerInitializationException,
    DatabaseManagerNotInitializedException,
    DatabaseManagerInvalidDatabaseConnectionEntryException,
    DatabaseManagerConflictingConnectionException,
    DatabaseManagerConnectionNotFoundException,
    DatabaseManagerSecretNotFoundException,
    DatabaseManagerOperationException,
    DatabaseManagerInvalidOperationException,
    DatabaseManagerConflictingAnalyzerException,
    DatabaseManagerInvalidAnalyzerException,
    DatabaseManagerAnalyzerNotFoundException,
    DatabaseManagerAnalyzerOperationException,
)

__all__ = [
    "DatabaseManager",
    "IDatabaseManager",
    "DatabaseConnection",
    "FilterDefinition",
    "FullTextAnalyzer",
    "FunctionDefinition",
    "SurrealFilter",
    "SurrealTokenizer",
    "TokenizerDefinition",
    "DatabaseManagerException",
    "DatabaseManagerInitializationException",
    "DatabaseManagerNotInitializedException",
    "DatabaseManagerInvalidDatabaseConnectionEntryException",
    "DatabaseManagerConflictingConnectionException",
    "DatabaseManagerConnectionNotFoundException",
    "DatabaseManagerSecretNotFoundException",
    "DatabaseManagerOperationException",
    "DatabaseManagerInvalidOperationException",
    "DatabaseManagerConflictingAnalyzerException",
    "DatabaseManagerInvalidAnalyzerException",
    "DatabaseManagerAnalyzerNotFoundException",
    "DatabaseManagerAnalyzerOperationException",
]
