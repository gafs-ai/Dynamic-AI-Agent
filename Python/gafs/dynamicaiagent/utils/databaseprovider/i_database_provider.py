from abc import ABC, abstractmethod
from logging import Logger
from typing import Any, TypeVar

from .database_provider_options import DatabaseProviderOptions
from .database_provider_status import DatabaseProviderStatus
from .retry_options import RetryOptions

T = TypeVar("T")


class IDatabaseProvider(ABC):
    """Unified contract for all database provider implementations.

    Provides two query modes:
    - ``query``: typed query that optionally deserializes records into a model class.
    - ``query_raw``: raw query that returns the driver-level result without
      deserialization.

    Retry behaviour:
    - Connection errors are retried according to the effective ``RetryOptions``
      (per-request > provider-level > defaults).
    - Authentication errors and query errors are **never** retried.

    NOTE: Callers must call ``initialize()`` before issuing any queries.
    Implementations should also implement ``__aenter__`` / ``__aexit__`` so
    that the provider can be used as an async context manager; ``__aexit__``
    must call ``close()``.
    """

    def __init__(self, logger: Logger) -> None:
        # Logger used throughout the provider lifetime.
        self._logger: Logger = logger
        # Current lifecycle status; starts UNINITIALIZED.
        self._status: DatabaseProviderStatus = DatabaseProviderStatus.UNINITIALIZED

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def status(self) -> DatabaseProviderStatus:
        """Current lifecycle status of this provider."""
        return self._status

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @abstractmethod
    async def initialize(self, options: DatabaseProviderOptions) -> bool:
        """Connect to the database and apply the given options.

        Must be called before any query method.

        Args:
            options: Provider-specific options (subclass of
                ``DatabaseProviderOptions``).

        Returns:
            True when successfully initialized.

        Raises:
            DatabaseProviderInitializationException: Connection or
                authentication fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """Close the database connection and release all resources.

        Implementations must also implement ``__aexit__`` and call this
        method inside it.
        """
        raise NotImplementedError

    # ── Query ─────────────────────────────────────────────────────────────────

    @abstractmethod
    async def query(
        self,
        query: str,
        model: type[T] | None = None,
        many: bool = False,
        retry_options: RetryOptions | None = None,
    ) -> "T | list[T] | None":
        """Execute a query and optionally deserialize the result into a typed model.

        Args:
            query: Query string to execute (syntax is provider-specific).
            model: Model class to deserialize each result record into.
                ``None`` means do not deserialize; return ``None``.
            many: ``True`` returns ``list[T]``; ``False`` returns a single
                ``T`` or ``None``.
            retry_options: Per-request retry options.  Overrides
                ``DatabaseProviderOptions.retry_options``.  If ``None``,
                falls back to the provider-level options or
                ``RetryOptions`` defaults.

        Returns:
            - ``T`` when *model* is given, *many* is ``False``, and a record
              was found.
            - ``list[T]`` when *model* is given and *many* is ``True``.
            - ``None`` when *model* is ``None`` or no record was found.

        Raises:
            DatabaseOperationException: Query execution fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def query_raw(
        self,
        query: str,
        retry_options: RetryOptions | None = None,
    ) -> Any:
        """Execute a query and return the raw driver-level result.

        The exact return type is driver-specific.  Use this method when you
        need the raw result for further processing.

        Args:
            query: Query string to execute.
            retry_options: Per-request retry options.  Overrides
                ``DatabaseProviderOptions.retry_options``.  If ``None``,
                falls back to the provider-level options or
                ``RetryOptions`` defaults.

        Returns:
            Raw result as returned by the underlying database driver.

        Raises:
            DatabaseOperationException: Query execution fails.
        """
        raise NotImplementedError
