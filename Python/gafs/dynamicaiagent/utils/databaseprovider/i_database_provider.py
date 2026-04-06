from __future__ import annotations

from abc import ABC, abstractmethod
from logging import Logger
from typing import Any, TypeVar

from .database_provider_options import DatabaseProviderOptions
from .database_provider_status import DatabaseProviderStatus


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
        """Return the current status of the database provider."""
        return self._status
    
    # ------------ Database Provider Features ------------

    @property
    def support_vector_search(self) -> bool:
        """Return True if the database provider supports vector search."""
        return self._support_vector_search
    
    @property
    def vector_graph_search_max_depth(self) -> int:
        """Return the maximum depth limit for vector graph search.

        Returns:
            0 if vector graph search is not supported (always 0 when support_vector_search is False).
            Positive integer for the configured depth limit.
            Negative integer (-1) for unlimited depth (not recommended).
        """
        return self._vector_graph_search_max_depth
    
    @property
    def support_full_text_search(self) -> bool:
        """Return True if the database provider supports full-text search."""
        return self._support_full_text_search
    
    @property
    def max_limit(self) -> int:
        """Return the maximum number of records returned per query."""
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
        """Close the database provider and release all resources.

        NOTE: Implementations must also define __aexit__ and call this method inside it.
        """
        pass


