"""
gafs.dynamicaiagent.common.databasemanager.exceptions - Exception classes for DatabaseManager.
"""

from .database_manager_exception import DatabaseManagerException
from .database_manager_initialization_exception import DatabaseManagerInitializationException
from .database_manager_not_initialized_exception import DatabaseManagerNotInitializedException
from .database_manager_invalid_database_connection_entry_exception import (
    DatabaseManagerInvalidDatabaseConnectionEntryException,
)
from .database_manager_conflicting_connection_exception import (
    DatabaseManagerConflictingConnectionException,
)
from .database_manager_connection_not_found_exception import (
    DatabaseManagerConnectionNotFoundException,
)
from .database_manager_secret_not_found_exception import DatabaseManagerSecretNotFoundException
from .database_manager_operation_exception import DatabaseManagerOperationException
from .database_manager_invalid_operation_exception import DatabaseManagerInvalidOperationException
from .database_manager_conflicting_analyzer_exception import (
    DatabaseManagerConflictingAnalyzerException,
)
from .database_manager_invalid_analyzer_exception import DatabaseManagerInvalidAnalyzerException
from .database_manager_analyzer_not_found_exception import DatabaseManagerAnalyzerNotFoundException
from .database_manager_analyzer_operation_exception import (
    DatabaseManagerAnalyzerOperationException,
)

__all__ = [
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
