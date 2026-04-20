"""test_database_manager.py - Integration and unit tests for DatabaseManager.

Tests are split into three categories:

1. Model tests (no database required):
   - DatabaseConnection serialization, deserialization, and validation.
   - FullTextAnalyzer serialization, SurrealQL generation, and static factories.
   - SurrealFilter / SurrealTokenizer enum values and static helpers.

2. Phase-1 integration tests (embedded local SurrealDB, no SecretManager):
   - initialize_default_connection (normal and abnormal cases).
   - FullTextAnalyzer CRUD (create_analyzer, get_analyzer, update_analyzer,
     get_all_analyzers, get_analyzers_by_name, delete_analyzer).
   - get_default_provider (before/after initialization).

3. Phase-3 integration tests (requires initialize with a test SecretManager):
   - Connection CRUD (create_connection, get_connection, get_all_connections,
     get_connections_by_name, update_connection, delete_connection).
   - get_provider for non-default connections.
   - create_connection with raw_secret via test SecretManager.

NOTE: For remote SurrealDB tests, create:
  test/secret_test_config_default_database_configurations.json
with the following format:
  {
    "id": "default",
    "name": "default",
    "description": "...",
    "database_type": "surrealdb_remote",
    "parameters": { "endpoint": "...", "namespace": "...", "database": "..." },
    "raw_secret": { "username": "...", "password": "..." }
  }
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any

import pytest

from gafs.dynamicaiagent.common.databasemanager import (
    DatabaseConnection,
    DatabaseManager,
    DatabaseManagerAnalyzerNotFoundException,
    DatabaseManagerAnalyzerOperationException,
    DatabaseManagerConflictingAnalyzerException,
    DatabaseManagerConflictingConnectionException,
    DatabaseManagerConnectionNotFoundException,
    DatabaseManagerInitializationException,
    DatabaseManagerInvalidAnalyzerException,
    DatabaseManagerInvalidDatabaseConnectionEntryException,
    DatabaseManagerInvalidOperationException,
    DatabaseManagerNotInitializedException,
    DatabaseManagerOperationException,
    DatabaseManagerSecretNotFoundException,
    FilterDefinition,
    FullTextAnalyzer,
    FunctionDefinition,
    IDatabaseManager,
    SurrealFilter,
    SurrealTokenizer,
    TokenizerDefinition,
)
from gafs.dynamicaiagent.utils.databaseprovider import DatabaseProviderType

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

_LOGGER = logging.getLogger(__name__)

_TEST_DIR = Path(__file__).resolve().parent
_REMOTE_CONFIG_PATH = _TEST_DIR / "secret_test_config_default_database_configurations.json"


def _make_logger(name: str = "test") -> logging.Logger:
    """Return a logger for tests."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
    return logger


def _load_remote_config() -> dict[str, Any] | None:
    """Load the remote SurrealDB configuration from the secret config file.

    Returns:
        Config dict if the file exists, otherwise None.
    """
    if not _REMOTE_CONFIG_PATH.exists():
        return None
    with open(_REMOTE_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _build_local_config() -> DatabaseConnection:
    """Build a DatabaseConnection for an in-memory local SurrealDB instance.

    Returns:
        DatabaseConnection configured for local in-memory SurrealDB.
    """
    conn = DatabaseConnection()
    conn.id = "default"
    conn.name = "default"
    conn.description = "In-memory test database"
    conn.database_type = DatabaseProviderType.SURREALDB_LOCAL
    conn.parameters = {
        "namespace": "test",
        "database": "test",
        "storage_type": "mem",
    }
    return conn


def _build_remote_config(config_data: dict[str, Any]) -> DatabaseConnection:
    """Build a DatabaseConnection from a remote config dict.

    Args:
        config_data: Dict loaded from the secret config file.

    Returns:
        DatabaseConnection for the remote database.
    """
    return DatabaseConnection.from_dict(config_data)


# ---------------------------------------------------------------------------
# Minimal test SecretManager (concrete implementation for testing)
# ---------------------------------------------------------------------------

class _SimpleSecret:
    """Minimal Secret-compatible object for testing."""

    def __init__(self, secret_id: str, credentials: dict[str, Any]) -> None:
        self.id = secret_id
        # Both 'secret' and 'raw_secret' attributes provided for compatibility
        self.secret = credentials
        self.raw_secret = credentials


class _TestSecretManager:
    """Minimal concrete SecretManager implementation for testing DatabaseManager.

    This is NOT a mock — it provides real in-memory storage of secrets.
    It is used solely to enable phase-3 initialization during tests.
    """

    def __init__(self) -> None:
        self._secrets: dict[str, _SimpleSecret] = {}
        self._next_id = 1

    async def create_secret(self, secret: Any) -> _SimpleSecret:
        """Create and store a secret in memory.

        Args:
            secret: Secret-compatible object with a .secret or .raw_secret dict.

        Returns:
            Created secret with an auto-assigned id.
        """
        secret_id = f"test_secret_{self._next_id}"
        self._next_id += 1
        credentials: dict[str, Any] = {}
        if hasattr(secret, "secret") and isinstance(secret.secret, dict):
            credentials = secret.secret
        elif hasattr(secret, "raw_secret") and isinstance(secret.raw_secret, dict):
            credentials = secret.raw_secret
        result = _SimpleSecret(secret_id, credentials)
        self._secrets[secret_id] = result
        return result

    async def get_secret(self, secret_id: str) -> _SimpleSecret:
        """Retrieve a stored secret by id.

        Args:
            secret_id: The id of the secret to retrieve.

        Returns:
            The stored secret.

        Raises:
            DatabaseRecordNotFoundException: If no secret with the given id exists.
        """
        if secret_id not in self._secrets:
            from gafs.dynamicaiagent.utils.databaseprovider.exceptions import (
                DatabaseRecordNotFoundException,
            )
            raise DatabaseRecordNotFoundException(f"Secret not found: {secret_id}")
        return self._secrets[secret_id]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def local_config() -> DatabaseConnection:
    """DatabaseConnection for an in-memory local SurrealDB."""
    return _build_local_config()


@pytest.fixture
async def initialized_db_manager(local_config: DatabaseConnection) -> DatabaseManager:
    """DatabaseManager initialized through all three phases using local SurrealDB.

    Phase 1: initialize_default_connection with local in-memory SurrealDB.
    Phase 3: initialize with _TestSecretManager.
    """
    mgr = DatabaseManager(_make_logger("dbmgr_fixture"))
    await mgr.initialize_default_connection(local_config)
    await mgr.initialize(_TestSecretManager())
    return mgr


@pytest.fixture
async def phase1_db_manager(local_config: DatabaseConnection) -> DatabaseManager:
    """DatabaseManager initialized through phase 1 only (no SecretManager)."""
    mgr = DatabaseManager(_make_logger("dbmgr_phase1"))
    await mgr.initialize_default_connection(local_config)
    return mgr


# ---------------------------------------------------------------------------
# Model tests — DatabaseConnection
# ---------------------------------------------------------------------------

class TestDatabaseConnectionModel:
    """Tests for DatabaseConnection serialization and attribute handling."""

    def test_collection_name(self) -> None:
        """COLLECTION_NAME() must return 'DatabaseConnections'."""
        assert DatabaseConnection.COLLECTION_NAME() == "DatabaseConnections"

    def test_default_values(self) -> None:
        """All fields must default to None."""
        conn = DatabaseConnection()
        assert conn.id is None
        assert conn.name is None
        assert conn.description is None
        assert conn.database_type is None
        assert conn.secret is None
        assert conn.raw_secret is None
        assert conn.parameters is None

    def test_set_database_type_enum(self) -> None:
        """database_type accepts DatabaseProviderType enum."""
        conn = DatabaseConnection()
        conn.database_type = DatabaseProviderType.SURREALDB_LOCAL
        assert conn.database_type == DatabaseProviderType.SURREALDB_LOCAL

    def test_set_database_type_string(self) -> None:
        """database_type accepts and auto-converts a valid string."""
        conn = DatabaseConnection()
        conn.database_type = "surrealdb_remote"
        assert conn.database_type == DatabaseProviderType.SURREALDB_REMOTE

    def test_set_database_type_invalid_raises(self) -> None:
        """Setting an invalid database_type raises ValueError."""
        conn = DatabaseConnection()
        with pytest.raises(ValueError):
            conn.database_type = 123

    def test_id_normalization_with_prefix(self) -> None:
        """id is normalized by stripping the SurrealDB table prefix."""
        conn = DatabaseConnection()
        conn.id = "DatabaseConnections:abc123"
        assert conn.id == "abc123"

    def test_id_without_prefix(self) -> None:
        """id without a table prefix is stored as-is."""
        conn = DatabaseConnection()
        conn.id = "abc123"
        assert conn.id == "abc123"

    def test_secret_normalization(self) -> None:
        """secret id is normalized by stripping the table prefix."""
        conn = DatabaseConnection()
        conn.secret = "Secrets:mysecret"
        assert conn.secret == "mysecret"

    def test_to_dict_excludes_raw_secret(self) -> None:
        """to_dict must never include raw_secret."""
        conn = DatabaseConnection()
        conn.name = "test"
        conn.database_type = DatabaseProviderType.SURREALDB_LOCAL
        conn.raw_secret = {"username": "user", "password": "pass"}
        d = conn.to_dict(recursive=True)
        assert "raw_secret" not in d

    def test_to_dict_recursive_serializes_enum(self) -> None:
        """to_dict(recursive=True) converts database_type to its string value."""
        conn = DatabaseConnection()
        conn.database_type = DatabaseProviderType.SURREALDB_LOCAL
        d = conn.to_dict(recursive=True)
        assert d["database_type"] == "surrealdb_local"

    def test_to_dict_exclude_id(self) -> None:
        """to_dict(exclude_id=True) omits the id field."""
        conn = DatabaseConnection()
        conn.id = "myid"
        conn.name = "test"
        d = conn.to_dict(recursive=True, exclude_id=True)
        assert "id" not in d
        assert "name" in d

    def test_to_json_roundtrip(self) -> None:
        """to_json / from_json roundtrip preserves all safe fields."""
        conn = DatabaseConnection()
        conn.id = "test_conn"
        conn.name = "Test Connection"
        conn.description = "A test connection"
        conn.database_type = DatabaseProviderType.SURREALDB_LOCAL
        conn.parameters = {"namespace": "test", "database": "test"}

        json_str = conn.to_json()
        restored = DatabaseConnection.from_json(json_str)

        assert restored.id == "test_conn"
        assert restored.name == "Test Connection"
        assert restored.description == "A test connection"
        assert restored.database_type == DatabaseProviderType.SURREALDB_LOCAL
        assert restored.parameters == {"namespace": "test", "database": "test"}
        assert restored.raw_secret is None

    def test_from_dict_ignores_unknown_keys(self) -> None:
        """from_dict silently ignores keys that are not valid attributes."""
        data = {"name": "test", "database_type": "surrealdb_local", "unknown_key": "value"}
        conn = DatabaseConnection.from_dict(data)
        assert conn.name == "test"
        assert not hasattr(conn, "unknown_key")

    def test_set_raw_secret_invalid_raises(self) -> None:
        """Setting raw_secret to a non-dict raises ValueError."""
        conn = DatabaseConnection()
        with pytest.raises(ValueError):
            conn.raw_secret = "not_a_dict"

    def test_repr(self) -> None:
        """__repr__ returns a JSON string (same as to_json)."""
        conn = DatabaseConnection()
        conn.name = "x"
        conn.database_type = DatabaseProviderType.SURREALDB_LOCAL
        assert json.loads(repr(conn))["name"] == "x"


# ---------------------------------------------------------------------------
# Model tests — FullTextAnalyzer
# ---------------------------------------------------------------------------

class TestFullTextAnalyzerModel:
    """Tests for FullTextAnalyzer, FilterDefinition, and TokenizerDefinition."""

    def test_collection_name(self) -> None:
        """COLLECTION_NAME() must return 'FullTextAnalyzers'."""
        assert FullTextAnalyzer.COLLECTION_NAME() == "FullTextAnalyzers"

    def test_default_analyzer(self) -> None:
        """DEFAULT_ANALYZER returns a FullTextAnalyzer with id 'default_ngram_analyzer'."""
        a = FullTextAnalyzer.DEFAULT_ANALYZER()
        assert a.id == "default_ngram_analyzer"
        assert a.name == "default_ngram_analyzer"
        assert a.tokenizers is not None and len(a.tokenizers) == 2
        assert a.filters is not None and len(a.filters) == 1
        assert a.filters[0].filter == SurrealFilter.NGRAM

    def test_default_english_analyzer(self) -> None:
        """DEFAULT_ENGLISH_ANALYZER returns a FullTextAnalyzer with id 'default_english_analyzer'."""
        a = FullTextAnalyzer.DEFAULT_ENGLISH_ANALYZER()
        assert a.id == "default_english_analyzer"
        assert a.name == "default_english_analyzer"
        assert a.filters is not None and len(a.filters) == 1
        assert a.filters[0].filter == SurrealFilter.SNOWBALL

    def test_get_define_analyzer_statement_if_not_exists(self) -> None:
        """get_define_analyzer_statement with overwrite=False includes IF NOT EXISTS."""
        a = FullTextAnalyzer.DEFAULT_ANALYZER()
        stmt = a.get_define_analyzer_statement(overwrite=False)
        assert "IF NOT EXISTS" in stmt
        assert "default_ngram_analyzer" in stmt
        assert "TOKENIZERS" in stmt
        assert "FILTERS" in stmt
        assert "ngram(3,5)" in stmt

    def test_get_define_analyzer_statement_overwrite(self) -> None:
        """get_define_analyzer_statement with overwrite=True includes OVERWRITE."""
        a = FullTextAnalyzer.DEFAULT_ANALYZER()
        stmt = a.get_define_analyzer_statement(overwrite=True)
        assert "OVERWRITE" in stmt
        assert "IF NOT EXISTS" not in stmt

    def test_get_alter_analyzer_statement(self) -> None:
        """get_alter_analyzer_statement uses DEFINE ANALYZER OVERWRITE (not ALTER ANALYZER)."""
        a = FullTextAnalyzer.DEFAULT_ANALYZER()
        stmt = a.get_alter_analyzer_statement()
        assert "OVERWRITE" in stmt
        assert "default_ngram_analyzer" in stmt
        # Must not use ALTER ANALYZER (not supported in surrealdb 1.0.x)
        assert "ALTER ANALYZER" not in stmt

    def test_get_drop_analyzer_statement(self) -> None:
        """get_drop_analyzer_statement produces REMOVE ANALYZER."""
        a = FullTextAnalyzer.DEFAULT_ANALYZER()
        stmt = a.get_drop_analyzer_statement()
        assert "REMOVE ANALYZER" in stmt
        assert "default_ngram_analyzer" in stmt

    def test_validate_and_normalize_valid(self) -> None:
        """validate_and_normalize returns True for a valid analyzer."""
        a = FullTextAnalyzer.DEFAULT_ANALYZER()
        assert a.validate_and_normalize() is True

    def test_validate_and_normalize_missing_name(self) -> None:
        """validate_and_normalize raises when name is empty."""
        a = FullTextAnalyzer()
        with pytest.raises(DatabaseManagerInvalidAnalyzerException):
            a.validate_and_normalize()

    def test_validate_and_normalize_invalid_snowball_language(self) -> None:
        """validate_and_normalize raises for an invalid snowball language."""
        a = FullTextAnalyzer()
        a.name = "test_analyzer"
        fd = FilterDefinition()
        fd.filter = SurrealFilter.SNOWBALL
        fd.parameters = {"language": "klingon"}
        a.filters = [fd]
        with pytest.raises(DatabaseManagerInvalidAnalyzerException):
            a.validate_and_normalize()

    def test_to_dict_roundtrip(self) -> None:
        """to_dict / from_dict roundtrip preserves all fields."""
        a = FullTextAnalyzer.DEFAULT_ANALYZER()
        d = a.to_dict(recursive=True)
        restored = FullTextAnalyzer.from_dict(d)
        assert restored.name == a.name
        assert restored.tokenizers is not None
        assert len(restored.tokenizers) == len(a.tokenizers)

    def test_tokenizer_definition_auto_converts_str(self) -> None:
        """TokenizerDefinition.tokenizer accepts a string and converts to enum."""
        td = TokenizerDefinition()
        td.tokenizer = "blank"
        assert td.tokenizer == SurrealTokenizer.BLANK

    def test_filter_definition_auto_converts_str(self) -> None:
        """FilterDefinition.filter accepts a string and converts to enum."""
        fd = FilterDefinition()
        fd.filter = "ngram"
        assert fd.filter == SurrealFilter.NGRAM

    def test_filter_definition_surreal_str_ascii(self) -> None:
        """to_surreal_filter_str returns 'ascii' for ASCII filter."""
        fd = FilterDefinition()
        fd.filter = SurrealFilter.ASCII
        assert fd.to_surreal_filter_str() == "ascii"

    def test_filter_definition_surreal_str_ngram(self) -> None:
        """to_surreal_filter_str returns 'ngram(3,5)' with default params."""
        fd = FilterDefinition()
        fd.filter = SurrealFilter.NGRAM
        assert fd.to_surreal_filter_str() == "ngram(3,5)"

    def test_filter_definition_surreal_str_snowball(self) -> None:
        """to_surreal_filter_str returns 'snowball(english)' with default language."""
        fd = FilterDefinition()
        fd.filter = SurrealFilter.SNOWBALL
        assert fd.to_surreal_filter_str() == "snowball(english)"

    def test_filter_definition_custom_params(self) -> None:
        """to_surreal_filter_str uses provided parameters."""
        fd = FilterDefinition()
        fd.filter = SurrealFilter.EDGENGRAM
        fd.parameters = {"min": 2, "max": 8}
        assert fd.to_surreal_filter_str() == "edgengram(2,8)"


# ---------------------------------------------------------------------------
# Model tests — SurrealFilter / SurrealTokenizer
# ---------------------------------------------------------------------------

class TestSurrealEnums:
    """Tests for SurrealFilter and SurrealTokenizer enums."""

    def test_surreal_filter_values(self) -> None:
        """All expected filter values are present."""
        assert SurrealFilter.ASCII.value == "ascii"
        assert SurrealFilter.SNOWBALL.value == "snowball"
        assert SurrealFilter.NGRAM.value == "ngram"
        assert SurrealFilter.EDGENGRAM.value == "edgengram"

    def test_surreal_filter_snowball_languages(self) -> None:
        """SNOWBALL_LANGUAGES includes 'english'."""
        langs = SurrealFilter.SNOWBALL_LANGUAGES()
        assert "english" in langs
        assert len(langs) > 0

    def test_surreal_tokenizer_values(self) -> None:
        """All expected tokenizer values are present."""
        assert SurrealTokenizer.BLANK.value == "blank"
        assert SurrealTokenizer.PUNCT.value == "punct"
        assert SurrealTokenizer.CAMEL.value == "camel"
        assert SurrealTokenizer.CLASS.value == "class"


# ---------------------------------------------------------------------------
# Phase-1 integration tests — initialization
# ---------------------------------------------------------------------------

class TestInitialization:
    """Tests for initialize_default_connection and phase-1 behavior."""

    async def test_initialize_local_success(self, local_config: DatabaseConnection) -> None:
        """initialize_default_connection succeeds with a valid local config."""
        mgr = DatabaseManager(_make_logger("init_test"))
        result = await mgr.initialize_default_connection(local_config)
        assert result is True
        # Default provider should now be available
        provider = mgr.get_default_provider()
        assert provider is not None

    async def test_initialize_missing_database_type_raises(self) -> None:
        """initialize_default_connection raises when database_type is not set."""
        mgr = DatabaseManager(_make_logger("init_err"))
        conn = DatabaseConnection()
        conn.name = "default"
        # database_type is intentionally omitted
        with pytest.raises(DatabaseManagerInitializationException):
            await mgr.initialize_default_connection(conn)

    async def test_initialize_missing_parameters_raises(self) -> None:
        """initialize_default_connection raises when parameters and raw_secret are both absent."""
        mgr = DatabaseManager(_make_logger("init_err2"))
        conn = DatabaseConnection()
        conn.name = "default"
        conn.database_type = DatabaseProviderType.SURREALDB_LOCAL
        # parameters intentionally omitted
        with pytest.raises(DatabaseManagerInitializationException):
            await mgr.initialize_default_connection(conn)

    async def test_get_default_provider_before_init_raises(self) -> None:
        """get_default_provider raises DatabaseManagerNotInitializedException before phase-1."""
        mgr = DatabaseManager(_make_logger("pre_init"))
        with pytest.raises(DatabaseManagerNotInitializedException):
            mgr.get_default_provider()

    async def test_phase3_methods_raise_before_init(self, local_config: DatabaseConnection) -> None:
        """Connection catalogue methods raise NotInitializedException before phase-3."""
        mgr = DatabaseManager(_make_logger("pre_phase3"))
        await mgr.initialize_default_connection(local_config)
        # Phase-3 not completed — these must raise
        with pytest.raises(DatabaseManagerNotInitializedException):
            await mgr.get_all_connections()

    async def test_initialize_phase3(self, local_config: DatabaseConnection) -> None:
        """initialize (phase-3) accepts a SecretManager and returns True."""
        mgr = DatabaseManager(_make_logger("phase3"))
        await mgr.initialize_default_connection(local_config)
        result = await mgr.initialize(_TestSecretManager())
        assert result is True

    @pytest.mark.skipif(
        not _REMOTE_CONFIG_PATH.exists(),
        reason="Remote config file not found: secret_test_config_default_database_configurations.json",
    )
    async def test_initialize_remote_success(self) -> None:
        """initialize_default_connection succeeds with the remote SurrealDB config."""
        config_data = _load_remote_config()
        assert config_data is not None
        mgr = DatabaseManager(_make_logger("remote_init"))
        config = _build_remote_config(config_data)
        result = await mgr.initialize_default_connection(config)
        assert result is True


# ---------------------------------------------------------------------------
# Phase-1 integration tests — Analyzer catalogue
# ---------------------------------------------------------------------------

class TestAnalyzerCatalogue:
    """Tests for FullTextAnalyzer CRUD operations."""

    def _make_unique_analyzer(self, name_suffix: str = "") -> FullTextAnalyzer:
        """Create a uniquely-named test analyzer."""
        unique = uuid.uuid4().hex[:8]
        a = FullTextAnalyzer()
        a.name = f"test_analyzer_{unique}{name_suffix}"
        td = TokenizerDefinition()
        td.tokenizer = SurrealTokenizer.BLANK
        a.tokenizers = [td]
        fd = FilterDefinition()
        fd.filter = SurrealFilter.LOWERCASE
        a.filters = [fd]
        return a

    async def test_create_analyzer_success(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """create_analyzer creates a new FullTextAnalyzer entry."""
        mgr = phase1_db_manager
        analyzer = self._make_unique_analyzer()
        created = await mgr.create_analyzer(analyzer)
        assert created.id is not None
        assert created.name == analyzer.name

    async def test_get_analyzer_success(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """get_analyzer returns the created entry by id."""
        mgr = phase1_db_manager
        analyzer = self._make_unique_analyzer()
        created = await mgr.create_analyzer(analyzer)
        fetched = await mgr.get_analyzer(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == created.name

    async def test_get_analyzer_not_found_returns_none(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """get_analyzer returns None for a non-existent id."""
        mgr = phase1_db_manager
        result = await mgr.get_analyzer("nonexistent_id_xyz")
        assert result is None

    async def test_get_all_analyzers(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """get_all_analyzers returns a list including created entries."""
        mgr = phase1_db_manager
        # The default analyzers should already exist from initialization
        all_analyzers = await mgr.get_all_analyzers()
        assert isinstance(all_analyzers, list)
        names = [a.name for a in all_analyzers]
        assert "default_ngram_analyzer" in names
        assert "default_english_analyzer" in names

    async def test_get_analyzers_by_name_exact(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """get_analyzers_by_name with ambiguous=False returns exact match only."""
        mgr = phase1_db_manager
        analyzer = self._make_unique_analyzer()
        created = await mgr.create_analyzer(analyzer)
        results = await mgr.get_analyzers_by_name(created.name, ambiguous=False)
        assert len(results) == 1
        assert results[0].id == created.id

    async def test_get_analyzers_by_name_not_found(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """get_analyzers_by_name returns empty list when no match found."""
        mgr = phase1_db_manager
        results = await mgr.get_analyzers_by_name("completely_nonexistent_xyz", ambiguous=False)
        assert results == []

    async def test_update_analyzer_success(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """update_analyzer changes the analyzer's filters and updates the entry."""
        mgr = phase1_db_manager
        analyzer = self._make_unique_analyzer()
        created = await mgr.create_analyzer(analyzer)

        # Modify filters
        updated = FullTextAnalyzer()
        updated.id = created.id
        updated.name = created.name
        td = TokenizerDefinition()
        td.tokenizer = SurrealTokenizer.BLANK
        updated.tokenizers = [td]
        fd = FilterDefinition()
        fd.filter = SurrealFilter.UPPERCASE
        updated.filters = [fd]

        result = await mgr.update_analyzer(updated)
        assert result.id == created.id
        # Verify the change persisted
        refetched = await mgr.get_analyzer(created.id)
        assert refetched is not None
        assert refetched.filters[0].filter == SurrealFilter.UPPERCASE

    async def test_update_analyzer_missing_id_raises(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """update_analyzer raises when id is not set."""
        mgr = phase1_db_manager
        a = FullTextAnalyzer()
        a.name = "no_id_analyzer"
        with pytest.raises(DatabaseManagerInvalidAnalyzerException):
            await mgr.update_analyzer(a)

    async def test_update_analyzer_not_found_raises(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """update_analyzer raises AnalyzerNotFoundException for a non-existent id."""
        mgr = phase1_db_manager
        a = FullTextAnalyzer()
        a.id = "nonexistent_id_xyz"
        a.name = "nonexistent_name"
        td = TokenizerDefinition()
        td.tokenizer = SurrealTokenizer.BLANK
        a.tokenizers = [td]
        with pytest.raises(DatabaseManagerAnalyzerNotFoundException):
            await mgr.update_analyzer(a)

    async def test_delete_analyzer_success(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """delete_analyzer removes the entry and the SurrealDB analyzer definition."""
        mgr = phase1_db_manager
        analyzer = self._make_unique_analyzer()
        created = await mgr.create_analyzer(analyzer)
        # Delete
        await mgr.delete_analyzer(created.id)
        # Verify it's gone
        fetched = await mgr.get_analyzer(created.id)
        assert fetched is None

    async def test_delete_analyzer_not_found_raises(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """delete_analyzer raises AnalyzerNotFoundException for a non-existent id."""
        mgr = phase1_db_manager
        with pytest.raises(DatabaseManagerAnalyzerNotFoundException):
            await mgr.delete_analyzer("nonexistent_xyz")

    async def test_create_analyzer_duplicate_name_raises(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """create_analyzer raises ConflictingAnalyzerException for a duplicate name."""
        mgr = phase1_db_manager
        analyzer = self._make_unique_analyzer()
        await mgr.create_analyzer(analyzer)
        # Try to create again with the same name
        duplicate = FullTextAnalyzer()
        duplicate.name = analyzer.name
        td = TokenizerDefinition()
        td.tokenizer = SurrealTokenizer.PUNCT
        duplicate.tokenizers = [td]
        with pytest.raises(DatabaseManagerConflictingAnalyzerException):
            await mgr.create_analyzer(duplicate)

    async def test_create_analyzer_invalid_missing_name_raises(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """create_analyzer raises InvalidAnalyzerException when name is not set."""
        mgr = phase1_db_manager
        a = FullTextAnalyzer()
        # name intentionally omitted
        with pytest.raises(DatabaseManagerInvalidAnalyzerException):
            await mgr.create_analyzer(a)


# ---------------------------------------------------------------------------
# Phase-3 integration tests — Connection catalogue
# ---------------------------------------------------------------------------

class TestConnectionCatalogue:
    """Tests for DatabaseConnection CRUD operations (requires phase-3)."""

    def _make_unique_connection(self) -> DatabaseConnection:
        """Create a uniquely-named DatabaseConnection for testing."""
        unique = uuid.uuid4().hex[:8]
        conn = DatabaseConnection()
        conn.name = f"test_conn_{unique}"
        conn.description = "Test connection"
        conn.database_type = DatabaseProviderType.SURREALDB_LOCAL
        conn.parameters = {
            "namespace": "test",
            "database": "test_sub",
            "storage_type": "mem",
        }
        return conn

    async def test_create_connection_success(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """create_connection creates and persists a DatabaseConnection entry."""
        mgr = initialized_db_manager
        conn = self._make_unique_connection()
        created = await mgr.create_connection(conn)
        assert created.id is not None
        assert created.name == conn.name
        # raw_secret must not be in the returned entry
        assert created.raw_secret is None

    async def test_get_connection_success(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """get_connection returns the created entry by id."""
        mgr = initialized_db_manager
        conn = self._make_unique_connection()
        created = await mgr.create_connection(conn)
        fetched = await mgr.get_connection(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == created.name

    async def test_get_connection_not_found_returns_none(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """get_connection returns None for a non-existent id."""
        mgr = initialized_db_manager
        result = await mgr.get_connection("nonexistent_xyz")
        assert result is None

    async def test_get_all_connections(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """get_all_connections returns a list including the default entry."""
        mgr = initialized_db_manager
        all_conns = await mgr.get_all_connections()
        assert isinstance(all_conns, list)
        ids = [c.id for c in all_conns]
        assert "default" in ids

    async def test_get_connections_by_name_exact(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """get_connections_by_name with ambiguous=False returns exact match only."""
        mgr = initialized_db_manager
        conn = self._make_unique_connection()
        created = await mgr.create_connection(conn)
        results = await mgr.get_connections_by_name(created.name, ambiguous=False)
        assert len(results) >= 1
        found_ids = [r.id for r in results]
        assert created.id in found_ids

    async def test_get_connections_by_name_not_found(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """get_connections_by_name returns empty list when no match found."""
        mgr = initialized_db_manager
        results = await mgr.get_connections_by_name("completely_nonexistent_xyz", ambiguous=False)
        assert results == []

    async def test_update_connection_success(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """update_connection updates the description field."""
        mgr = initialized_db_manager
        conn = self._make_unique_connection()
        created = await mgr.create_connection(conn)

        # Build an update payload
        update = DatabaseConnection()
        update.id = created.id
        update.description = "Updated description"

        result = await mgr.update_connection(update)
        assert result.description == "Updated description"

        # Verify the change persisted
        refetched = await mgr.get_connection(created.id)
        assert refetched is not None
        assert refetched.description == "Updated description"

    async def test_update_connection_default_raises(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """update_connection raises InvalidOperationException for the default connection."""
        mgr = initialized_db_manager
        update = DatabaseConnection()
        update.id = "default"
        update.description = "Attempting to update default"
        with pytest.raises(DatabaseManagerInvalidOperationException):
            await mgr.update_connection(update)

    async def test_update_connection_missing_id_raises(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """update_connection raises InvalidDatabaseConnectionEntryException when id is not set."""
        mgr = initialized_db_manager
        update = DatabaseConnection()
        update.description = "No id"
        with pytest.raises(DatabaseManagerInvalidDatabaseConnectionEntryException):
            await mgr.update_connection(update)

    async def test_update_connection_with_raw_secret_raises(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """update_connection raises when raw_secret is set."""
        mgr = initialized_db_manager
        conn = self._make_unique_connection()
        created = await mgr.create_connection(conn)

        update = DatabaseConnection()
        update.id = created.id
        update.raw_secret = {"password": "new_pass"}
        with pytest.raises(DatabaseManagerInvalidDatabaseConnectionEntryException):
            await mgr.update_connection(update)

    async def test_update_connection_not_found_raises(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """update_connection raises ConnectionNotFoundException for a non-existent id."""
        mgr = initialized_db_manager
        update = DatabaseConnection()
        update.id = "nonexistent_xyz"
        update.description = "Ghost update"
        with pytest.raises(DatabaseManagerConnectionNotFoundException):
            await mgr.update_connection(update)

    async def test_delete_connection_success(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """delete_connection removes the entry from the database."""
        mgr = initialized_db_manager
        conn = self._make_unique_connection()
        created = await mgr.create_connection(conn)
        # Delete
        await mgr.delete_connection(created.id)
        # Verify it's gone
        fetched = await mgr.get_connection(created.id)
        assert fetched is None

    async def test_delete_connection_default_raises(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """delete_connection raises InvalidOperationException for the default connection."""
        mgr = initialized_db_manager
        with pytest.raises(DatabaseManagerInvalidOperationException):
            await mgr.delete_connection("default")

    async def test_delete_connection_not_found_raises(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """delete_connection raises ConnectionNotFoundException for a non-existent id."""
        mgr = initialized_db_manager
        with pytest.raises(DatabaseManagerConnectionNotFoundException):
            await mgr.delete_connection("nonexistent_xyz")

    async def test_create_connection_both_secret_and_raw_secret_raises(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """create_connection raises when both secret and raw_secret are set."""
        mgr = initialized_db_manager
        conn = self._make_unique_connection()
        conn.secret = "some_secret_id"
        conn.raw_secret = {"password": "pass"}
        with pytest.raises(DatabaseManagerInvalidDatabaseConnectionEntryException):
            await mgr.create_connection(conn)

    async def test_create_connection_duplicate_id_raises(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """create_connection raises ConflictingConnectionException for a duplicate id."""
        mgr = initialized_db_manager
        conn = self._make_unique_connection()
        created = await mgr.create_connection(conn)

        duplicate = self._make_unique_connection()
        duplicate.id = created.id  # Force the same id
        with pytest.raises(DatabaseManagerConflictingConnectionException):
            await mgr.create_connection(duplicate)

    async def test_create_connection_missing_name_raises(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """create_connection raises when name is not set."""
        mgr = initialized_db_manager
        conn = DatabaseConnection()
        conn.database_type = DatabaseProviderType.SURREALDB_LOCAL
        conn.parameters = {"namespace": "t", "database": "t", "storage_type": "mem"}
        with pytest.raises(DatabaseManagerInvalidDatabaseConnectionEntryException):
            await mgr.create_connection(conn)

    async def test_create_connection_secret_not_found_raises(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """create_connection raises SecretNotFoundException for a non-existent secret id."""
        mgr = initialized_db_manager
        conn = self._make_unique_connection()
        conn.secret = "nonexistent_secret_id"
        with pytest.raises(DatabaseManagerSecretNotFoundException):
            await mgr.create_connection(conn)

    async def test_create_connection_with_raw_secret(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """create_connection with raw_secret creates a Secret and stores the secret id."""
        mgr = initialized_db_manager
        conn = self._make_unique_connection()
        conn.raw_secret = {"username": "testuser", "password": "testpass"}

        created = await mgr.create_connection(conn)
        # raw_secret must be absent from the returned entry
        assert created.raw_secret is None
        # secret id should be set from the created Secret
        assert created.secret is not None


# ---------------------------------------------------------------------------
# Provider getter tests
# ---------------------------------------------------------------------------

class TestProviderGetters:
    """Tests for get_provider and get_default_provider."""

    async def test_get_default_provider_after_phase1(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """get_default_provider returns the provider after phase-1."""
        mgr = phase1_db_manager
        provider = mgr.get_default_provider()
        assert provider is not None

    async def test_get_provider_default_id(
        self, phase1_db_manager: DatabaseManager
    ) -> None:
        """get_provider('default') returns the default provider."""
        mgr = phase1_db_manager
        provider = await mgr.get_provider("default")
        assert provider is mgr.get_default_provider()

    async def test_get_provider_nondefault_not_found_raises(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """get_provider for a non-existent connection raises ConnectionNotFoundException."""
        mgr = initialized_db_manager
        with pytest.raises(DatabaseManagerConnectionNotFoundException):
            await mgr.get_provider("nonexistent_xyz")

    async def test_get_provider_caches_instance(
        self, initialized_db_manager: DatabaseManager
    ) -> None:
        """get_provider returns the same cached instance on repeated calls."""
        mgr = initialized_db_manager

        # Create a connection entry first
        conn = DatabaseConnection()
        conn.name = f"cache_test_{uuid.uuid4().hex[:8]}"
        conn.database_type = DatabaseProviderType.SURREALDB_LOCAL
        conn.parameters = {"namespace": "test", "database": "test_cache", "storage_type": "mem"}
        created = await mgr.create_connection(conn)

        # First call creates the provider
        p1 = await mgr.get_provider(created.id)
        # Second call returns the cached instance
        p2 = await mgr.get_provider(created.id)
        assert p1 is p2
