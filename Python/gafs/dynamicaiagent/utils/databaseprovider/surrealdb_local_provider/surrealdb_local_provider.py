from __future__ import annotations

import asyncio
import sys
from logging import Logger
from pathlib import Path
from typing import Any, TypeVar, override

from surrealdb import AsyncSurreal

from ..i_database_provider import IDatabaseProvider
from ..database_provider_status import DatabaseProviderStatus
from ..exceptions import (
    DatabaseProviderException,
    DatabaseProviderInitializationException,
    DatabaseDisconnectedException,
    DatabaseQueryErrorException,
)
from .local_surrealdb_options import LocalSurrealDbOptions, LocalSurrealDbStorageType

T = TypeVar('T')


class SurrealDbLocalProvider(IDatabaseProvider):
    """
    SurrealDB Local (Embedded) Provider implementation.
    Runs SurrealDB as an embedded database within the application process.
    Please call `initialize` method to initialize the provider before starting to send queries.
    """
    PROVIDER_NAME: str = "SurrealDBLocalProvider"

    def __init__(self, logger: Logger):
        super().__init__(logger)
        self._database: AsyncSurreal | None = None
        self._options: LocalSurrealDbOptions | None = None

    @override
    async def close(self) -> None:
        if self._database is not None:
            try:
                await self._database.close()
                self._database = None
                self._status = DatabaseProviderStatus.TERMINATED
            except Exception as e:
                self._logger.error(f"Error closing database: {e}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @override
    async def initialize(self, options: LocalSurrealDbOptions) -> bool:
        """Initialize the embedded database provider.

        Args:
            options: Local SurrealDB options.

        Returns:
            True if initialization was successful.

        Raises:
            DatabaseProviderInitializationException: When initialization fails.
        """
        self._options = options
        return await self._connect()

    def _build_url(self) -> str:
        """Build the connection URL from the configured storage type and path."""
        storage = self._options.storage_type
        if storage == LocalSurrealDbStorageType.MEM:
            return "mem://"

        if storage == LocalSurrealDbStorageType.SURREALKV:
            default_path = "surrealkv_data"
            scheme = "surrealkv"
        else:
            default_path = "rocksdb_data"
            scheme = "rocksdb"

        raw_path: str = self._options.path or default_path

        # On Windows, absolute paths containing a drive letter (e.g. C:\...)
        # would be mis-parsed by the URL parser as netloc=C:\..., which then
        # fails trying to extract a port number.  Prepend an additional '/'
        # so the path lands in the URL path component (netloc stays empty).
        p = Path(raw_path)
        if p.is_absolute() and sys.platform == "win32":
            forward = raw_path.replace("\\", "/")
            return f"{scheme}:///{forward}"

        return f"{scheme}://{raw_path}"

    async def _connect(self) -> bool:
        """Connect to (or reconnect to) the embedded SurrealDB database.

        Returns:
            True when connection and namespace/database selection succeeded.

        Raises:
            DatabaseProviderInitializationException: When no options have been set,
                or when the embedded database engine fails to initialize.
        """
        # Check current status
        if self._status == DatabaseProviderStatus.INITIALIZING:
            self._logger.info(
                "Database provider is already initializing by another call. "
                "Waiting for initialization to complete..."
            )
            sleep_seconds: int = 0
            while sleep_seconds < 60:  # TODO: Move to configuration
                await asyncio.sleep(1)
                sleep_seconds += 1
                if self._status == DatabaseProviderStatus.INITIALIZING:
                    continue
                elif self._status == DatabaseProviderStatus.AVAILABLE:
                    self._logger.info("Database provider is initialized by another call")
                    return True
                else:
                    self._logger.error("Database initialization failure by another call")
                    return False

        # Update provider status
        self._status = DatabaseProviderStatus.INITIALIZING
        self._logger.debug("Connecting (Reconnecting) to embedded database...")

        # Check options
        if self._options is None:
            message: str = "No options detected"
            self._status = DatabaseProviderStatus.ERROR
            self._logger.error(message)
            exception_details: dict[str, Any] = {
                "db_provider": self.PROVIDER_NAME,
            }
            raise DatabaseProviderInitializationException(message=message, details=exception_details)

        # Close existing connection if present
        if self._database is not None:
            self._logger.debug("Existing database connection detected. Closing...")
            try:
                await self._database.close()
                self._logger.debug("Closed existing database connection")
            except Exception:
                self._logger.debug(
                    "Could not close existing database connection. Detected connection is ignored."
                )

        # Connect to embedded database
        url: str = self._build_url()
        try:
            self._database = AsyncSurreal(url)
            self._logger.info(f"Connected to embedded database at {url}")
        except Exception as e:
            message = f"Cannot connect to embedded database at {url}"
            self._status = DatabaseProviderStatus.ERROR
            self._logger.error(message)
            exception_details = {
                "db_provider": self.PROVIDER_NAME,
                "url": url,
            }
            raise DatabaseProviderInitializationException(message=message, details=exception_details, cause=e)

        # Select namespace and database
        try:
            await self._database.use(self._options.namespace, self._options.database)
            self._logger.info(
                f"Using namespace `{self._options.namespace}` database `{self._options.database}`"
            )
        except Exception as e:
            message = (
                f"Cannot select namespace `{self._options.namespace}` "
                f"database `{self._options.database}`"
            )
            self._status = DatabaseProviderStatus.ERROR
            self._logger.error(message)
            exception_details = {
                "db_provider": self.PROVIDER_NAME,
                "url": url,
            }
            raise DatabaseProviderInitializationException(message=message, details=exception_details, cause=e)

        self._status = DatabaseProviderStatus.AVAILABLE
        return True

    @override
    async def query(self, query: str, model: type[T] = None, many: bool = False) -> T | list[T] | None:
        """Execute a query.

        Args:
            query: SQL query string to execute.
            model: Model type to parse the query result into. If None, the query will return None.
            many: Whether to return a list of models or a single model.

        Returns:
            Query result of type T | list[T] | None.

        Raises:
            DatabaseDisconnectedException: When the database provider is not available.
            DatabaseQueryErrorException: When query execution fails.
        """
        raw_result: Any = await self.query_raw(query)
        raw_result = self.unwrap_query_raw_result(raw_result)

        if model is None:
            return None
        else:
            if not hasattr(model, 'from_dict'):
                exception_details: dict[str, Any] = {
                    "db_provider": self.PROVIDER_NAME
                }
                raise DatabaseQueryErrorException(
                    message=f"Model class {model.__name__} must have a 'from_dict' class method for deserialization.",
                    details=exception_details
                )

        def _normalize_item(obj: Any) -> Any:
            if obj is None or isinstance(obj, (str, int, float, bool)):
                return obj
            return self.unwrap_record(obj)

        try:
            if many:
                if isinstance(raw_result, list):
                    return [model.from_dict(_normalize_item(item)) for item in raw_result]
                elif isinstance(raw_result, dict):
                    return [model.from_dict(_normalize_item(raw_result))]
                elif isinstance(raw_result, str):
                    message: str = f"Database provider returned error result. {raw_result}"
                    self._logger.error(message)
                    exception_details = {"db_provider": self.PROVIDER_NAME}
                    raise DatabaseQueryErrorException(message=message, details=exception_details)
                elif raw_result is None:
                    return []
                else:
                    raise DatabaseQueryErrorException(
                        message=f"Failed to parse the query result into a model. Query: {query}"
                    )
            else:
                if isinstance(raw_result, dict):
                    return model.from_dict(_normalize_item(raw_result))
                elif isinstance(raw_result, list):
                    if len(raw_result) == 0:
                        return None
                    else:
                        return model.from_dict(_normalize_item(raw_result[0]))
                elif isinstance(raw_result, str):
                    message = f"Database provider returned error result. {raw_result}"
                    self._logger.error(message)
                    raise DatabaseQueryErrorException(message=message)
                elif raw_result is None:
                    return None
                else:
                    message = f"Failed to parse the query result into a model. Query: {query}"
                    self._logger.error(message)
                    raise DatabaseQueryErrorException(message=message)
        except Exception as e:
            raise DatabaseQueryErrorException(
                message=f"Failed to parse the query result into a model. Query: {query}", cause=e
            )

    @override
    async def query_raw(self, query: str) -> Any:
        """Execute a query and return the raw result.

        This method returns the raw result from the embedded database driver without
        any model parsing. Use `query` instead when model deserialization is needed.

        Args:
            query: SQL query string to execute.

        Returns:
            Raw query result as returned by the SurrealDB driver.

        Raises:
            DatabaseDisconnectedException: When the provider is unavailable and
                reconnection fails.
            DatabaseQueryErrorException: When query execution fails or the database
                returns an error response.
        """
        if self._status == DatabaseProviderStatus.INITIALIZING:
            self._logger.debug(
                "Database provider is now initializing. Waiting for initialization to complete..."
            )
            sleep_seconds: int = 0
            while sleep_seconds < 60:  # TODO: Move to configuration
                await asyncio.sleep(1)
                sleep_seconds += 1
                if self._status == DatabaseProviderStatus.AVAILABLE:
                    break
            else:
                self._logger.debug("Initialization timeout. Database provider is not available.")
                message: str = f"Failed to execute query. Database provider is not available. Query: {query}"
                self._logger.error(message)
                exception_details: dict[str, Any] = {
                    "db_provider": self.PROVIDER_NAME,
                    "query": query,
                }
                raise DatabaseDisconnectedException(message=message, details=exception_details)

        if self._status != DatabaseProviderStatus.AVAILABLE:
            self._logger.debug("Executing query, but database provider is not available. Reconnecting...")
            try:
                result: bool = await self._connect()
            except DatabaseProviderException as e:
                raise e

            if not result:
                message = f"Failed to reconnect to database. Query was not executed. Query: {query}"
                self._logger.error(message)
                exception_details = {
                    "db_provider": self.PROVIDER_NAME,
                }
                raise DatabaseDisconnectedException(message=message, details=exception_details)

        try:
            response: Any = await self._database.query_raw(query)
        except Exception as e:
            exception_details: dict[str, Any] = {
                "db_provider": self.PROVIDER_NAME,
            }
            raise DatabaseQueryErrorException(
                message=f"Failed to execute query. Query: {query}",
                details=exception_details,
                cause=e,
            ) from e

        if not isinstance(response, dict):
            exception_details = {"db_provider": self.PROVIDER_NAME}
            raise DatabaseQueryErrorException(
                message=f"Unexpected query response type: {type(response).__name__}. Query: {query}",
                details=exception_details,
            )

        top_error: Any = response.get("error")
        if top_error is not None:
            exception_details = {"db_provider": self.PROVIDER_NAME, "surreal_error": top_error}
            raise DatabaseQueryErrorException(
                message=f"Failed to execute query: {top_error}. Query: {query}",
                details=exception_details,
            )

        statements: Any = response.get("result")
        if statements is None:
            return None

        if isinstance(statements, list):
            for i, stmt in enumerate(statements):
                if not isinstance(stmt, dict):
                    continue
                status: Any = stmt.get("status")
                if status is not None and str(status).upper() not in {"OK"}:
                    detail: Any = stmt.get("result", stmt)
                    exception_details = {
                        "db_provider": self.PROVIDER_NAME,
                        "statement_index": i,
                        "statement_status": status,
                        "statement_detail": detail,
                    }
                    raise DatabaseQueryErrorException(
                        message=(
                            f"Query statement {i} failed (status={status!r}, detail={detail!r}). "
                            f"Query: {query}"
                        ),
                        details=exception_details,
                    )
            if len(statements) == 1:
                return statements[0].get("result")
            return statements

        return statements

    @override
    def unwrap_query_raw_result(self, raw_result: Any) -> Any:
        if isinstance(raw_result, list) and len(raw_result) > 0:
            if all(isinstance(item, dict) and "result" in item for item in raw_result):
                return raw_result[-1].get("result")
            if all(hasattr(item, "result") for item in raw_result):
                return getattr(raw_result[-1], "result")
        return raw_result

    @override
    def unwrap_record(self, obj: Any) -> dict[str, Any]:
        if obj is None:
            return {}

        if isinstance(obj, dict):
            normalized: dict[str, Any] = dict(obj)
        else:
            normalized = {}
            if hasattr(obj, "value") and isinstance(getattr(obj, "value"), dict):
                normalized.update(getattr(obj, "value"))
            if hasattr(obj, "data") and isinstance(getattr(obj, "data"), dict):
                normalized.update(getattr(obj, "data"))
            if not normalized:
                try:
                    normalized = dict(obj)  # type: ignore[arg-type]
                except Exception:
                    return {}

        if "$id" in normalized and "id" not in normalized:
            normalized["id"] = normalized["$id"]
        if "$value" in normalized and isinstance(normalized.get("$value"), dict):
            payload = normalized.pop("$value")
            normalized.update(payload)
        if "value" in normalized and isinstance(normalized.get("value"), dict):
            payload = normalized.pop("value")
            normalized.update(payload)

        return normalized
