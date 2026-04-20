from __future__ import annotations

import asyncio
from logging import Logger
from typing import Any, TypeVar

from surrealdb import AsyncSurreal

from ..database_provider_status import DatabaseProviderStatus
from ..i_database_provider import IDatabaseProvider
from ..retry_options import RetryOptions
from ..exceptions import (
    DatabaseProviderInitializationException,
    DatabaseProviderOptionsException,
    DatabaseProviderUnconnectableException,
    DatabaseProviderAuthenticationException,
    DatabaseQueryErrorException,
    DatabaseConnectionException,
    DatabaseOperationException,
)
from .remote_surrealdb_options import RemoteSurrealDbOptions

T = TypeVar("T")


class SurrealDbRemoteProvider(IDatabaseProvider):
    """Remote SurrealDB provider (WebSocket connection).

    Connects to a remote SurrealDB server over WebSocket and authenticates
    using username / password.  A session token is cached after the first
    successful authentication and reused on reconnection attempts.

    Call ``initialize()`` before issuing any queries.  The provider can be
    used as an async context manager; ``close()`` is called automatically
    when the ``async with`` block exits.
    """

    PROVIDER_NAME: str = "SurrealDBRemoteProvider"

    def __init__(self, logger: Logger) -> None:
        super().__init__(logger)
        # The underlying SurrealDB async client instance (set in initialize).
        self._database: AsyncSurreal | None = None
        # Provider configuration stored on initialize.
        self._options: RemoteSurrealDbOptions | None = None
        # Cached session token for reconnection (avoids re-authentication each time).
        self._token: str | None = None

    # ── Async context manager support ────────────────────────────────────────

    async def __aenter__(self) -> "SurrealDbRemoteProvider":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def initialize(self, options: RemoteSurrealDbOptions) -> bool:
        """Connect to the remote SurrealDB endpoint and authenticate.

        Args:
            options: Connection and authentication options.

        Returns:
            True when successfully connected and authenticated.

        Raises:
            DatabaseProviderInitializationException: Options not set or
                general initialization failure.
            DatabaseProviderUnconnectableException: Endpoint is unreachable.
            DatabaseProviderAuthenticationException: Credentials rejected.
        """
        # Step 1: Validate and store options.
        if not isinstance(options, RemoteSurrealDbOptions):
            raise DatabaseProviderOptionsException(
                message="Invalid options type; expected RemoteSurrealDbOptions.",
                details={"db_provider": self.PROVIDER_NAME},
            )
        if options.endpoint is None or options.namespace is None or options.database is None:
            raise DatabaseProviderOptionsException(
                message="endpoint, namespace and database must be set.",
                details={"db_provider": self.PROVIDER_NAME},
            )
        if options.username is None or options.password is None:
            raise DatabaseProviderOptionsException(
                message="username and password must be set.",
                details={"db_provider": self.PROVIDER_NAME},
            )

        self._options = options

        # Step 2: Establish connection and authenticate.
        return await self._connect()

    async def close(self) -> None:
        """Close the WebSocket connection and release all resources.

        Sets status to ``TERMINATED`` on success.  If an exception occurs
        during shutdown it is logged at ERROR level and silently ignored,
        because the application cannot meaningfully recover from a close
        failure.
        """
        self._status = DatabaseProviderStatus.TERMINATING
        self._logger.debug("Closing remote SurrealDB provider...")

        if self._database is not None:
            try:
                await self._database.close()
            except Exception as e:
                # Nothing the application can do here; log and continue.
                self._logger.error("Error while closing remote database connection: %s", e)
            finally:
                self._database = None

        self._status = DatabaseProviderStatus.TERMINATED
        self._logger.debug("Remote SurrealDB provider closed.")

    # ── Query methods ─────────────────────────────────────────────────────────

    async def query(
        self,
        query: str,
        model: type[T] | None = None,
        many: bool = False,
        retry_options: RetryOptions | None = None,
    ) -> "T | list[T] | None":
        """Execute a SurrealQL query and optionally deserialize results.

        Args:
            query: SurrealQL query string.
            model: Model class with a ``from_dict`` class method.  Pass
                ``None`` to skip deserialization and return ``None``.
            many: When ``True`` return a ``list[T]``; when ``False`` return
                the first record as ``T`` or ``None``.
            retry_options: Per-request retry override.

        Returns:
            Deserialized model instance(s) or ``None``.

        Raises:
            DatabaseConnectionException: Provider is not connected and all
                retry attempts are exhausted.
            DatabaseQueryErrorException: Server returns a query error.
            DatabaseOperationException: Other unexpected failures.
        """
        # Step 1: Send query via query_raw (handles retries and error checking).
        raw_result: Any = await self.query_raw(query, retry_options)

        # Step 2: If no model is requested, nothing to deserialize.
        if model is None:
            return None

        # Validate that the model class supports deserialization.
        if not hasattr(model, "from_dict"):
            raise DatabaseQueryErrorException(
                message=f"Model class '{model.__name__}' must have a 'from_dict' class method.",
                details={"db_provider": self.PROVIDER_NAME},
            )

        # Helper: normalize a single driver record object into a plain dict.
        def _normalize(obj: Any) -> Any:
            if obj is None or isinstance(obj, (str, int, float, bool)):
                return obj
            return self._unwrap_record(obj)

        # Step 3: Convert the result list into model instance(s).
        try:
            if many:
                # Return a list of model instances.
                if isinstance(raw_result, list):
                    return [model.from_dict(_normalize(item)) for item in raw_result]
                elif isinstance(raw_result, dict):
                    return [model.from_dict(_normalize(raw_result))]
                elif raw_result is None:
                    return []
                else:
                    raise DatabaseQueryErrorException(
                        message=f"Unexpected result type for many=True: {type(raw_result).__name__}.",
                        details={"db_provider": self.PROVIDER_NAME},
                    )
            else:
                # Return a single model instance or None.
                if isinstance(raw_result, dict):
                    return model.from_dict(_normalize(raw_result))
                elif isinstance(raw_result, list):
                    if len(raw_result) == 0:
                        return None
                    return model.from_dict(_normalize(raw_result[0]))
                elif raw_result is None:
                    return None
                else:
                    raise DatabaseQueryErrorException(
                        message=f"Unexpected result type for many=False: {type(raw_result).__name__}.",
                        details={"db_provider": self.PROVIDER_NAME},
                    )
        except DatabaseQueryErrorException:
            raise
        except Exception as e:
            raise DatabaseQueryErrorException(
                message=f"Failed to deserialize query result. Query: {query}",
                details={"db_provider": self.PROVIDER_NAME},
                cause=e,
            ) from e

    async def query_raw(
        self,
        query: str,
        retry_options: RetryOptions | None = None,
    ) -> Any:
        """Execute a SurrealQL query and return the unwrapped raw result.

        Retries on connection errors according to the effective
        ``RetryOptions``.  Query syntax errors and authentication errors are
        raised immediately without retrying.

        Args:
            query: SurrealQL query string.
            retry_options: Per-request retry override.

        Returns:
            The result payload (typically a list of records or a dict).
            Returns ``None`` when the query produces no result.

        Raises:
            DatabaseConnectionException: Provider unreachable after all
                retry attempts.
            DatabaseQueryErrorException: Query syntax or server-side error.
            DatabaseOperationException: Other unexpected failures.
        """
        # Resolve the effective retry configuration.
        effective_timeout, effective_max_retry, effective_retry_interval = (
            self._resolve_retry_options(retry_options)
        )

        # Verify the provider is ready before attempting the first call.
        if self._database is None or self._status not in (
            DatabaseProviderStatus.AVAILABLE,
            DatabaseProviderStatus.TEMPORARILY_UNAVAILABLE,
        ):
            raise DatabaseConnectionException(
                message="Provider is not initialized. Call initialize() first.",
                details={"db_provider": self.PROVIDER_NAME},
            )

        last_exc: Exception | None = None

        # Retry loop: attempt 0 is the first try, subsequent attempts are retries.
        for attempt in range(effective_max_retry + 1):
            if attempt > 0:
                # Wait before each retry; interval grows linearly with attempt number.
                wait_seconds = effective_retry_interval * attempt
                self._logger.debug(
                    "Retrying query (attempt %d/%d) after %ds...",
                    attempt,
                    effective_max_retry,
                    wait_seconds,
                )
                await asyncio.sleep(wait_seconds)

            try:
                # Send the query with a timeout guard.
                response: Any = await asyncio.wait_for(
                    self._database.query_raw(query),
                    timeout=float(effective_timeout),
                )
                # Query succeeded — break out of the retry loop.
                break

            except RuntimeError as e:
                # RuntimeError from the SurrealDB SDK indicates a query-level
                # failure (e.g. parse error).  Never retry these.
                self._logger.error("Query error: %s. Query: %s", e, query)
                raise DatabaseQueryErrorException(
                    message=f"Query failed: {e}",
                    details={"db_provider": self.PROVIDER_NAME, "query": query},
                    cause=e,
                ) from e

            except asyncio.TimeoutError as e:
                self._logger.warning(
                    "Query timed out (attempt %d/%d). Query: %s",
                    attempt + 1,
                    effective_max_retry + 1,
                    query,
                )
                last_exc = e

            except (OSError, ConnectionError, TimeoutError) as e:
                self._logger.warning(
                    "Connection error (attempt %d/%d): %s. Query: %s",
                    attempt + 1,
                    effective_max_retry + 1,
                    e,
                    query,
                )
                last_exc = e

            except Exception as e:
                self._logger.warning(
                    "Unexpected error (attempt %d/%d): %s. Query: %s",
                    attempt + 1,
                    effective_max_retry + 1,
                    e,
                    query,
                )
                last_exc = e

        else:
            # The for-loop completed without a break — all retries exhausted.
            raise DatabaseConnectionException(
                message=(
                    f"Failed to execute query after {effective_max_retry} retries. "
                    "Provider unreachable."
                ),
                details={"db_provider": self.PROVIDER_NAME, "query": query},
                cause=last_exc,
            )

        # Step 2: Parse the response dict for top-level errors.
        if not isinstance(response, dict):
            raise DatabaseOperationException(
                message=f"Unexpected response type: {type(response).__name__}.",
                details={"db_provider": self.PROVIDER_NAME},
            )

        top_error: Any = response.get("error")
        if top_error is not None:
            raise DatabaseQueryErrorException(
                message=f"Query failed: {top_error}.",
                details={"db_provider": self.PROVIDER_NAME, "surreal_error": top_error},
            )

        statements: Any = response.get("result")
        if statements is None:
            return None

        # Check each statement for per-statement errors.
        if isinstance(statements, list):
            for i, stmt in enumerate(statements):
                if not isinstance(stmt, dict):
                    continue
                status: Any = stmt.get("status")
                if status is not None and str(status).upper() != "OK":
                    detail: Any = stmt.get("result", stmt)
                    raise DatabaseQueryErrorException(
                        message=f"Query statement {i} failed (status={status!r}): {detail}.",
                        details={
                            "db_provider": self.PROVIDER_NAME,
                            "statement_index": i,
                            "detail": detail,
                        },
                    )

        # Step 3: Unwrap and return the result payload.
        return self._unwrap_query_raw_result(statements)

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _connect(self) -> bool:
        """Establish a WebSocket connection and authenticate.

        Attempts token-based reconnection first; falls back to
        username/password authentication when the token is missing or
        invalid.

        Returns:
            True when connection and authentication succeeded.

        Raises:
            DatabaseProviderInitializationException: Options not set.
            DatabaseProviderUnconnectableException: Endpoint is unreachable.
            DatabaseProviderAuthenticationException: Credentials rejected.
        """
        if self._options is None:
            raise DatabaseProviderInitializationException(
                message="No options set. Call initialize() first.",
                details={"db_provider": self.PROVIDER_NAME},
            )

        self._status = DatabaseProviderStatus.INITIALIZING
        self._logger.debug("Connecting to remote SurrealDB at '%s'...", self._options.endpoint)

        # Close any existing connection before opening a new one.
        if self._database is not None:
            self._logger.debug("Closing existing connection before reconnecting...")
            try:
                await self._database.close()
            except Exception:
                self._logger.debug("Could not close existing connection; continuing.")
            self._database = None

        # Open the WebSocket connection.
        try:
            self._database = AsyncSurreal(self._options.endpoint)
        except Exception as e:
            self._status = DatabaseProviderStatus.ERROR
            self._logger.error(
                "Cannot open connection to '%s': %s", self._options.endpoint, e
            )
            raise DatabaseProviderUnconnectableException(
                message=f"Cannot connect to '{self._options.endpoint}'.",
                details={"db_provider": self.PROVIDER_NAME, "endpoint": self._options.endpoint},
                cause=e,
            ) from e

        # Try reconnecting with a cached session token.
        if self._token is not None:
            try:
                self._logger.debug("Attempting token-based re-authentication...")
                await self._database.authenticate(self._token)
                # Token auth does not re-select namespace/database automatically.
                await self._database.use(self._options.namespace, self._options.database)
                self._status = DatabaseProviderStatus.AVAILABLE
                self._logger.info(
                    "Reconnected to '%s' using cached token.", self._options.endpoint
                )
                return True
            except Exception:
                self._logger.debug("Cached token is no longer valid; using password auth.")
                self._token = None

        # Build the authentication payload according to the auth level.
        if self._options.auth_level == "namespace":
            auth_payload: dict[str, str] = {
                "namespace": self._options.namespace,
                "username": self._options.username,
                "password": self._options.password,
            }
        else:
            # Default: database-level authentication.
            auth_payload = {
                "namespace": self._options.namespace,
                "database": self._options.database,
                "username": self._options.username,
                "password": self._options.password,
            }

        # Authenticate with username/password.
        try:
            self._logger.debug("Authenticating with username/password...")
            self._token = await self._database.signin(auth_payload)
        except Exception as e:
            self._status = DatabaseProviderStatus.ERROR
            error_text: str = str(e)

            # Detect network-level failures (DNS, socket errors).
            if isinstance(e, OSError) or "getaddrinfo failed" in error_text:
                self._logger.error(
                    "Cannot reach endpoint '%s': %s", self._options.endpoint, e
                )
                raise DatabaseProviderUnconnectableException(
                    message=f"Cannot reach endpoint '{self._options.endpoint}'.",
                    details={
                        "db_provider": self.PROVIDER_NAME,
                        "endpoint": self._options.endpoint,
                    },
                    cause=e,
                ) from e

            # All other signin failures are treated as authentication errors.
            self._logger.error(
                "Authentication failed for user '%s': %s", self._options.username, e
            )
            raise DatabaseProviderAuthenticationException(
                message=(
                    f"Authentication failed for user '{self._options.username}' "
                    f"at '{self._options.endpoint}'."
                ),
                details={
                    "db_provider": self.PROVIDER_NAME,
                    "endpoint": self._options.endpoint,
                },
                cause=e,
            ) from e

        self._status = DatabaseProviderStatus.AVAILABLE

        # For namespace-level auth, SurrealDB does not auto-select a database.
        if self._options.auth_level == "namespace" and self._options.database is not None:
            await self._database.use(self._options.namespace, self._options.database)

        self._logger.info(
            "Connected and authenticated to '%s' (namespace='%s', database='%s').",
            self._options.endpoint,
            self._options.namespace,
            self._options.database,
        )
        return True

    def _resolve_retry_options(
        self,
        per_request: RetryOptions | None,
    ) -> tuple[int, int, int]:
        """Resolve the effective retry parameters from the priority chain.

        Priority: per-request retry_options → provider-level retry_options →
        RetryOptions class defaults.

        Args:
            per_request: Optional per-request RetryOptions.

        Returns:
            Tuple of (timeout, max_retry, retry_interval).
        """
        provider_opts = self._options.retry_options if self._options else None

        def _get(attr: str, default: int) -> int:
            for src in [per_request, provider_opts]:
                if src is not None:
                    val = getattr(src, attr, None)
                    if val is not None:
                        return val
            return default

        return (
            _get("timeout", RetryOptions.DEFAULT_TIMEOUT),
            _get("max_retry", RetryOptions.DEFAULT_MAX_RETRY),
            _get("retry_interval", RetryOptions.DEFAULT_RETRY_INTERVAL),
        )

    def _unwrap_query_raw_result(self, raw_result: Any) -> Any:
        """Extract the payload from a SurrealDB statement result list.

        SurrealDB ``query_raw`` returns a dict whose ``"result"`` key is a
        list of statement result dicts:
        ``[{"status": "OK", "time": "...", "result": [...]}, ...]``

        This method returns the ``"result"`` field of the last statement.

        Args:
            raw_result: The statements list extracted from the raw response.

        Returns:
            The result payload of the last statement, or *raw_result* as-is
            when the expected structure is not found.
        """
        if isinstance(raw_result, list) and len(raw_result) > 0:
            # Check if this is a list of statement-result dicts.
            if all(isinstance(item, dict) and "result" in item for item in raw_result):
                return raw_result[-1].get("result")
            # Some driver versions return objects with a .result attribute.
            if all(hasattr(item, "result") for item in raw_result):
                return getattr(raw_result[-1], "result")

        return raw_result

    def _unwrap_record(self, obj: Any) -> dict[str, Any]:
        """Convert a SurrealDB driver record object into a plain dict.

        Handles ``RecordID`` normalization: strips the table prefix from the
        ``id`` field (e.g. ``"Secrets:abc"`` → ``"abc"``).

        Args:
            obj: A record object returned by the SurrealDB driver.

        Returns:
            A plain ``dict[str, Any]`` representation of the record.
        """
        if obj is None:
            return {}

        # If already a dict, work with a copy to avoid mutating the original.
        if isinstance(obj, dict):
            normalized: dict[str, Any] = dict(obj)
        else:
            normalized = {}
            # Common driver pattern: record payload lives in .value or .data.
            if hasattr(obj, "value") and isinstance(getattr(obj, "value"), dict):
                normalized.update(getattr(obj, "value"))
            if hasattr(obj, "data") and isinstance(getattr(obj, "data"), dict):
                normalized.update(getattr(obj, "data"))
            if not normalized:
                try:
                    normalized = dict(obj)  # type: ignore[arg-type]
                except Exception:
                    return {}

        # Normalize SurrealDB-specific wrapper keys.
        if "$id" in normalized and "id" not in normalized:
            normalized["id"] = normalized["$id"]
        if "$value" in normalized and isinstance(normalized.get("$value"), dict):
            payload = normalized.pop("$value")
            normalized.update(payload)
        if "value" in normalized and isinstance(normalized.get("value"), dict):
            payload = normalized.pop("value")
            normalized.update(payload)

        return normalized
