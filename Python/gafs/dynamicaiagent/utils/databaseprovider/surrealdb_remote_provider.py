from __future__ import annotations

import asyncio
import json
from logging import Logger
from typing import Any, TypeVar, override

from surrealdb import AsyncSurreal

from .i_database_provider import (
    IDatabaseProvider,
    DatabaseProviderOptions,
    DatabaseType,
    DatabaseProviderStatus,
)
from .exceptions import (
    DatabaseProviderAuthenticationException,
    DatabaseProviderException,
    DatabaseProviderInitializationException,
    DatabaseProviderUnconnectableException,
    DatabaseDisconnectedException,
    DatabaseQueryErrorException,
)

T = TypeVar('T')

class SurrealDbRemoteProvider(IDatabaseProvider):
    """
    SurrealDB Remote Provider implementation.
    Please call `initialize` method to initialize the provider before starting to send queries.
    """
    PROVIDER_NAME: str = "SurrealDBRemoteProvider"

    def __init__(self, logger: Logger):
        super().__init__(logger)
        self._database: AsyncSurreal | None = None
        self._options: RemoteSurrealDbOptions | None = None
        self._token: str | None = None

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
    async def initialize(self, options: RemoteSurrealDbOptions) -> bool:
        """Initialize the database provider.
        
        Args:
            options: Remote SurrealDB options.
        
        Returns:
            True if initialization was successful.
        
        Raises:
            DatabaseProviderInitializationException: When initialization fails.
            DatabaseProviderUnconnectableException: When connection to database fails.
            DatabaseProviderAuthenticationException: When authentication fails.
        """
        self._options = options
        return await self._connect()
    
    async def _connect(self) -> bool:
        """
        Connect to database.
        This method also can be used for reconnection.
        """
        # Check current status
        if self._status == DatabaseProviderStatus.INITIALIZING:
            self._logger.info("Database provider is already initializing by another call. Waiting for initialization to complete...")

            sleep_seconds: int = 0

            while sleep_seconds < 60: # TODO: Move to configuration
                await asyncio.sleep(1)
                sleep_seconds += 1

                if self._status == DatabaseProviderStatus.INITIALIZING:
                    continue
                elif self._status == DatabaseProviderStatus.AVAILABLE:
                    self._logger.info(f"Database provider is initialized by another call")
                    return True
                else:
                    self._logger.error(f"Database initialization failure by another call")
                    return False
        
        # Update provider status
        self._status = DatabaseProviderStatus.INITIALIZING
        self._logger.debug("Connecting (Reconnecting) to database...")

        # Check options
        if self._options is None:
            message: str = "No options detected"
            self._status = DatabaseProviderStatus.ERROR
            self._logger.error(message)
            exception_details: dict[str, Any] = {
                "db_provider": self.PROVIDER_NAME,
            }
            raise DatabaseProviderInitializationException(message=message, details=exception_details)

        # Connect to database
        if self._database is not None:
            self._logger.debug("Existing database connection detected. Closing...")
            try:
                await self._database.close()
                self._logger.debug("Closed existing database connection")
            except Exception:
                self._logger.debug("Could not close existing database connection. Detected connection is ignored.")
                pass

        try:
            self._database = AsyncSurreal(self._options.endpoint)
            self._logger.info(f"Connected to database at {self._options.endpoint}")
        except Exception as e:
            message: str = f"Cannot connect to database at {self._options.endpoint}"
            self._status = DatabaseProviderStatus.ERROR
            self._logger.error(message)
            exception_details: dict[str, Any] = {
                "db_provider": self.PROVIDER_NAME,
                "endpoint": self._options.endpoint,
            }
            raise DatabaseProviderUnconnectableException(message=message, details=exception_details, cause=e)
        
        # Try Token Authentication
        # If the client is disconnected and reconnecting, the existing token can work.
        if self._token is not None:
            try:
                self._logger.debug("Authentication token detected. Trying to authenticate with existing token...")
                await self._database.authenticate(self._token)
                self._logger.info("Token authentication successful")
                self._status = DatabaseProviderStatus.AVAILABLE
                return True
            except Exception:
                self._logger.debug("Could not authenticate with existing token")
                self._token = None
                pass
        
        # Authenticate with username and password.
        # The payload shape depends on the auth_level:
        #   "namespace" – namespace-level user: omit the "database" key.
        #   "database"  – database-level user (default): include both namespace and database.
        if self._options.auth_level == "namespace":
            authentication_payload: dict[str, str] = {
                "namespace": self._options.namespace,
                "username": self._options.username,
                "password": self._options.password,
            }
        else:
            authentication_payload: dict[str, str] = {
                "namespace": self._options.namespace,
                "database": self._options.database,
                "username": self._options.username,
                "password": self._options.password,
            }

        try:
            self._logger.debug("Authenticating with username and password")
            self._token = await self._database.signin(authentication_payload)
        except Exception as e:
            error_text: str = str(e)
            self._status = DatabaseProviderStatus.ERROR

            # Treat as "unreachable" if the error is dns or socket related
            if isinstance(e, OSError) or "getaddrinfo failed" in error_text:
                message: str = f"Cannot connect to database at {self._options.endpoint}"
                self._logger.error(message)
                exception_details: dict[str, Any] = {
                    "db_provider": self.PROVIDER_NAME,
                    "endpoint": self._options.endpoint
                }
                raise DatabaseProviderUnconnectableException(message=message, details=exception_details, cause=e)

            # Treat other type of errors as authentication error
            message = (
                f"Cannot authenticate for user `{self._options.username}` "
                f"namespace `{self._options.namespace}` database `{self._options.database}`"
            )
            self._logger.error(message)
            exception_details: dict[str, Any] = {
                "db_provider": self.PROVIDER_NAME,
                "endpoint": self._options.endpoint
            }
            raise DatabaseProviderAuthenticationException(message=message, details=exception_details, cause=e)
        
        self._status = DatabaseProviderStatus.AVAILABLE

        # After namespace-level auth, SurrealDB does not auto-select a database.
        # Explicitly select the target namespace and database so queries can execute.
        if self._options.auth_level == "namespace" and self._options.database is not None:
            await self._database.use(self._options.namespace, self._options.database)

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
            # Check if model has from_dict method (custom serialization)
            if not hasattr(model, 'from_dict'):
                exception_details: dict[str, Any] = {
                    "db_provider": self.PROVIDER_NAME
                }
                raise DatabaseQueryErrorException(
                    message=f"Model class {model.__name__} must have a 'from_dict' class method for deserialization.",
                    details=exception_details
                )
        
        def _normalize_item(obj: Any) -> Any:
            # Normalize driver-dependent record objects into dicts for model.from_dict().
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
                    exception_details: dict[str, Any] = {
                        "db_provider": self.PROVIDER_NAME
                    }
                    raise DatabaseQueryErrorException(message=message, details=exception_details)
                elif raw_result is None:
                    return []
                else:
                    raise DatabaseQueryErrorException(message=f"Failed to parse the query result into a model. Query: {query}")
            else:
                if isinstance(raw_result, dict):
                    return model.from_dict(_normalize_item(raw_result))
                elif isinstance(raw_result, list):
                    if len(raw_result) == 0:
                        return None
                    else:
                        return model.from_dict(_normalize_item(raw_result[0]))
                elif isinstance(raw_result, str):
                    message: str = f"Database provider returned error result. {raw_result}"
                    self._logger.error(message)
                    raise DatabaseQueryErrorException(message=message)
                elif raw_result is None:
                    return None
                else:
                    message: str = f"Failed to parse the query result into a model. Query: {query}"
                    self._logger.error(message)
                    raise DatabaseQueryErrorException(message=message)
        except Exception as e:
            raise DatabaseQueryErrorException(message=f"Failed to parse the query result into a model. Query: {query}", cause=e)


    @override
    async def query_raw(self, query: str) -> Any:
        """Execute a query and return the raw result.

        This method will not parse the query result into a model, but return the raw result as is.
        This method is not recommended as the possible return types depends on the database driver.
        However, you can use this method when `query` method is not adequate for your use case.
        
        Args:
            query: SQL query string to execute.
        
        Returns:
            Raw query result.
        """
        if self._status == DatabaseProviderStatus.INITIALIZING:
            self._logger.debug("Database provider is now initializing. Waiting for initialization to complete...")

            sleep_seconds: int = 0

            while sleep_seconds < 60: # TODO: Move to configuration
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
                    "query": query
                }
                raise DatabaseDisconnectedException(message=message, details=exception_details)

        if self._status != DatabaseProviderStatus.AVAILABLE:
            self._logger.debug("Executing query, but database provider is not available. Initializing...")
            try:
                result:bool = await self._connect()
            except DatabaseProviderException as e:
                raise e

            if not result:
                message: str = f"Failed to reconnect to database. Query was not executed. Query: {query}"
                self._logger.error(message)
                exception_details: dict[str, Any] = {
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
        # SurrealDB client returns a list of statement results:
        # [{"status": "...", "time": "...", "result": [...]}, ...]
        # Unwrap to the last statement's "result".
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
            # Common driver pattern: Record.value or Record.data carries the payload dict.
            if hasattr(obj, "value") and isinstance(getattr(obj, "value"), dict):
                normalized.update(getattr(obj, "value"))
            if hasattr(obj, "data") and isinstance(getattr(obj, "data"), dict):
                normalized.update(getattr(obj, "data"))
            if not normalized:
                try:
                    normalized = dict(obj)  # type: ignore[arg-type]
                except Exception:
                    return {}

        # SurrealDB may return wrappers.
        if "$id" in normalized and "id" not in normalized:
            normalized["id"] = normalized["$id"]
        if "$value" in normalized and isinstance(normalized.get("$value"), dict):
            payload = normalized.pop("$value")
            normalized.update(payload)
        if "value" in normalized and isinstance(normalized.get("value"), dict):
            payload = normalized.pop("value")
            normalized.update(payload)

        return normalized


class RemoteSurrealDbOptions(DatabaseProviderOptions):
    """Options for Remote SurrealDB provider.

    Attributes:
        endpoint: SurrealDB server endpoint URL.
        namespace: SurrealDB namespace.
        database: SurrealDB database name.
        username: Authentication username.
        password: Authentication password.
        database_type: Database type (should be SURREALDB_REMOTE).
        database_name: Logical database name for the provider.
        auth_level: Authentication level (default: "database").
        support_vector_search: Whether vector search is supported (default: True).
        vector_graph_search_max_depth: Maximum depth for vector graph search (default: 5).
        support_full_text_search: Whether full-text search is supported (default: True).
        max_limit: Maximum query result limit (default: 100).
    """

    def __init__(self) -> None:
        """Initialize all fields to None or appropriate default values."""
        # Initialize parent class fields first
        super().__init__()
        
        # Initialize child class specific fields
        object.__setattr__(self, "endpoint", None)
        object.__setattr__(self, "namespace", None)
        object.__setattr__(self, "database", None)
        object.__setattr__(self, "username", None)
        object.__setattr__(self, "password", None)
        object.__setattr__(self, "auth_level", "database")
        
        # Override parent class defaults with child class specific values
        object.__setattr__(self, "database_type", DatabaseType.SURREALDB_REMOTE)
        object.__setattr__(self, "support_vector_search", True)
        object.__setattr__(self, "vector_graph_search_max_depth", 5)
        object.__setattr__(self, "support_full_text_search", True)

    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute with type validation and conversion.

        Args:
            name: The name of the attribute to set.
            value: The value to set.

        Raises:
            ValueError: If the value type is invalid.
        """
        if name == "endpoint":
            if isinstance(value, str):
                object.__setattr__(self, "endpoint", value)
            else:
                raise ValueError
        elif name == "namespace":
            if isinstance(value, str):
                object.__setattr__(self, "namespace", value)
            else:
                raise ValueError
        elif name == "database":
            if isinstance(value, str):
                object.__setattr__(self, "database", value)
            else:
                raise ValueError
        elif name == "username":
            if isinstance(value, str):
                object.__setattr__(self, "username", value)
            else:
                raise ValueError
        elif name == "password":
            if isinstance(value, str):
                object.__setattr__(self, "password", value)
            else:
                raise ValueError
        elif name == "auth_level":
            if isinstance(value, str):
                object.__setattr__(self, "auth_level", value)
            else:
                raise ValueError
        elif name == "database_type":
            if isinstance(value, DatabaseType):
                # Always ensure it's SURREALDB_REMOTE
                if value != DatabaseType.SURREALDB_REMOTE:
                    raise ValueError
                else:
                    pass
            elif isinstance(value, str):
                converted_type = DatabaseType(value)
                if converted_type != DatabaseType.SURREALDB_REMOTE:
                    raise ValueError
                else:
                    pass
            else:
                raise ValueError
        else:
            super().__setattr__(name, value)

    def __repr__(self) -> str:
        """Return string representation of RemoteSurrealDbOptions.
        
        Returns:
            JSON string representation.
        """
        return self.to_json()

    def to_dict(self, recursive: bool = False) -> dict[str, Any]:
        """Convert the RemoteSurrealDbOptions instance to a dictionary.

        Args:
            recursive: If True, convert nested objects to primitive types.

        Returns:
            A dictionary representation of the RemoteSurrealDbOptions instance.
        """
        # Get parent class fields
        result: dict[str, Any] = super().to_dict(recursive=recursive)

        # Add child class specific fields
        if self.endpoint is not None:
            result["endpoint"] = self.endpoint

        if self.namespace is not None:
            result["namespace"] = self.namespace

        if self.database is not None:
            result["database"] = self.database

        if self.username is not None:
            result["username"] = self.username

        if self.password is not None:
            result["password"] = self.password

        if self.auth_level is not None:
            result["auth_level"] = self.auth_level

        return result

    def to_json(self) -> str:
        """Convert the RemoteSurrealDbOptions instance to a JSON string.

        Returns:
            A JSON string representation of the RemoteSurrealDbOptions instance.
        """
        return json.dumps(self.to_dict(recursive=True))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RemoteSurrealDbOptions":
        """Create a RemoteSurrealDbOptions instance from a dictionary.

        Args:
            data: A dictionary containing RemoteSurrealDbOptions data.

        Returns:
            A new RemoteSurrealDbOptions instance.
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
    def from_json(cls, json_str: str) -> "RemoteSurrealDbOptions":
        """Create a RemoteSurrealDbOptions instance from a JSON string.

        Args:
            json_str: A JSON string containing RemoteSurrealDbOptions data.

        Returns:
            A new RemoteSurrealDbOptions instance.

        Raises:
            ValueError: If the JSON string is not a dictionary.
        """
        converted: Any = json.loads(json_str)
        if not isinstance(converted, dict):
            raise ValueError
            
        return cls.from_dict(converted)
