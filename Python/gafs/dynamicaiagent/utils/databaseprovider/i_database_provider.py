from __future__ import annotations

import json
from abc import ABC, abstractmethod
from enum import Enum
from logging import Logger
from typing import Any, TypeVar


T = TypeVar("T")

class IDatabaseProvider(ABC):
    """
    Base class for database provider.
    Each database provider should implement this class and implement the methods.

    NOTE: Only the generic query method is supported for now.
    """

    def __init__(self, logger: Logger):
        self._logger: Logger = logger
        self._status: DatabaseProviderStatus = DatabaseProviderStatus.UNINITIALIZED
        self._support_vector_search: bool = False
        self._vector_graph_search_max_depth: int = 0
        self._support_full_text_search: bool = False
        self._max_limit: int = 100

    # ------------ Database Provider Status ------------

    @property
    def status(self) -> DatabaseProviderStatus:
        """
        Return the status of the database provider.
        """
        return self._status
    
    # ------------ Database Provider Features ------------

    @property
    def support_vector_search(self) -> bool:
        """
        Return True if the database provider supports vector search.
        """
        return self._support_vector_search
    
    @property
    def vector_graph_search_max_depth(self) -> int:
        """
        Return the maximum depth of the vector graph search.
        0: Graph search is not supported. If support_vector_search is False, this should always return 0.
        positive integer: Maximum depth of the vector graph search.
        -1 (or negative integer): Maximum depth of the vector graph search is not limited. Not recommended.
        """
        return self._vector_graph_search_max_depth
    
    @property
    def support_full_text_search(self) -> bool:
        """
        Return True if the database provider supports full text search.
        """
        return self._support_full_text_search
    
    @property
    def max_limit(self) -> int:
        """
        Return the maximum limit of the database provider.
        """
        return self._max_limit
    
    # ------------ Initializer ------------

    @abstractmethod
    async def initialize(self, options: DatabaseProviderOptions) -> bool:
        pass

    # ------------ Query ------------

    @abstractmethod
    async def query(
        self,
        query: str,
        model: type[T] | None = None,
        many: bool = False,
    ) -> T | list[T] | None:
        """Execute a query and optionally parse the result into a model.

        Args:
            query: SQL query string to execute.
            model: Model type to parse the query result into. If None, the
                implementation should not attempt to parse the result and
                should return None.
            many: Whether to return a list of models or a single model.

        Returns:
            Parsed query result of type ``T`` or ``list[T]`` when ``model`` is
            specified, otherwise ``None``.
        """
        raise NotImplementedError

    @abstractmethod
    async def query_raw(self, query: str) -> Any:
        """Execute a query and return the raw result from the provider.

        This method should not parse the query result into a model. The exact
        return type depends on the underlying database driver.

        Args:
            query: SQL query string to execute.

        Returns:
            Raw query result as returned by the database driver.
        """
        raise NotImplementedError

    # ------------ Driver/DB unwrapping ------------

    @abstractmethod
    def unwrap_query_raw_result(self, raw_result: Any) -> Any:
        """Unwrap driver-specific statement wrapper into the query result.

        Example (SurrealDB): query_raw returns a list of statement results and the
        actual payload lives under the last statement's ``result`` field.
        """
        raise NotImplementedError

    @abstractmethod
    def unwrap_record(self, obj: Any) -> dict[str, Any]:
        """Convert a driver record object into a plain dict.

        This is database-driver-specific but schema-agnostic. It should only deal
        with wrapper/record shapes (e.g. Record.value / Record.data / $value).
        """
        raise NotImplementedError

    # ------------ Close ------------

    @abstractmethod
    async def close(self) -> None:
        """
        Close the database provider and release resources.
        Please define __aexit__ and call this method inside, too.
        """
        pass

class DatabaseProviderStatus(Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    AVAILABLE = "available"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"
    ERROR = "error"
    TERMINATING = "terminating"
    TERMINATED = "terminated"

class DatabaseProviderOptions(ABC):
    """Base class for database provider options.

    The actual option class should inherit this and be implemented for each database provider.
    Each implementation should define the following attributes:
        database_type: DatabaseType
        database_name: str
        support_vector_search: bool
        vector_graph_search_max_depth: int
        support_full_text_search: bool
        max_limit: int
    """
    def __init__(self):
        object.__setattr__(self, "database_type", None)
        object.__setattr__(self, "database_name", None)
        object.__setattr__(self, "support_vector_search", False)
        object.__setattr__(self, "vector_graph_search_max_depth", 0)
        object.__setattr__(self, "support_full_text_search", False)
        object.__setattr__(self, "max_limit", 100)
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name == "database_type":
            if isinstance(value, DatabaseType):
                object.__setattr__(self, "database_type", value)
            elif isinstance(value, str):
                object.__setattr__(self, "database_type", DatabaseType(value))
            else:
                raise ValueError
        elif name == "database_name":
            if isinstance(value, str):
                object.__setattr__(self, "database_name", value)
            else:
                raise ValueError
        elif name == "support_vector_search":
            if isinstance(value, bool):
                object.__setattr__(self, "support_vector_search", value)
            else:
                raise ValueError
        elif name == "vector_graph_search_max_depth":
            if isinstance(value, int):
                object.__setattr__(self, "vector_graph_search_max_depth", value)
            else:
                raise ValueError
        elif name == "support_full_text_search":
            if isinstance(value, bool):
                object.__setattr__(self, "support_full_text_search", value)
            else:
                raise ValueError
        elif name == "max_limit":
            if isinstance(value, int):
                object.__setattr__(self, "max_limit", value)
            else:
                raise ValueError
        else:
            raise ValueError
    
    def __repr__(self) -> str:
        return self.to_json(recursive=True)
        
    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.database_type is not None:
            if recursive:
                result["database_type"] = self.database_type.value
            else:
                result["database_type"] = self.database_type
        if self.database_name is not None:
            result["database_name"] = self.database_name
        if self.support_vector_search is not None:
            result["support_vector_search"] = self.support_vector_search
        if self.vector_graph_search_max_depth is not None:
            result["vector_graph_search_max_depth"] = self.vector_graph_search_max_depth
        if self.support_full_text_search is not None:
            result["support_full_text_search"] = self.support_full_text_search
        if self.max_limit is not None:
            result["max_limit"] = self.max_limit
        return result
    
    def to_json(self, **kwargs) -> str:
        """Convert to JSON string.
        
        Args:
            **kwargs: Additional arguments to pass to to_dict().
        
        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(recursive=True, **kwargs))
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DatabaseProviderOptions":
        """Create instance from dictionary.
        
        Args:
            data: Dictionary containing field data.
        
        Returns:
            New instance of DatabaseProviderOptions.
        """
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                if value is not None:
                    setattr(entity, key, value)
            else:
                continue
        return entity
    
    @classmethod
    def from_json(cls, json_str: str) -> "DatabaseProviderOptions":
        """Create instance from JSON string.
        
        Args:
            json_str: JSON string containing field data.
        
        Returns:
            New instance of DatabaseProviderOptions.
        
        Raises:
            ValueError: If JSON string is not a dictionary.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
        return cls.from_dict(converted)


class DatabaseType(Enum):
    """
    List all the supported database providers here.
    """
    SURREALDB_REMOTE = "surrealdb-remote"
    # Current verion of surrealdb does not support embedding in python.
    # So, we are planning to port from subprocess implementation to embedding one in future.
    # SURREALDB_EMBEDDED = "surrealdb_embedded"
    SURREALDB_SUBPROCESS = "surrealdb-subprocess"
