"""test_secret_manager.py - Integration tests for SecretManager.

Tests cover:
1. Model tests (no database required):
   - SecretKey serialization, deserialization, and validation.
   - Secret serialization, deserialization, and validation.
   - SecretSearchCriteria construction and to_query() generation.

2. SecretManager key management tests (no database required):
   - add_key, get_key, generate_key (using CryptoUtil).
   - initialize with config keys (priority A).
   - initialize with file keys (priority B).
   - initialize with auto-generated keys (priority C).

3. SecretManager CRUD integration tests (uses local embedded SurrealDB):
   - create_secret (normal and error cases).
   - get_secret with decrypt=True and decrypt=False.
   - update_secret (normal and not-found cases).
   - search_secrets.
   - delete_secret (normal and not-found cases).

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
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from gafs.dynamicaiagent.common.databasemanager import DatabaseConnection, DatabaseManager
from gafs.dynamicaiagent.common.secretmanager import (
    ISecretManager,
    Secret,
    SecretKey,
    SecretManager,
    SecretManagerCryptoException,
    SecretManagerInitializationException,
    SecretManagerInvalidSecretEntryException,
    SecretManagerKeyNotFoundException,
    SecretManagerNotInitializedException,
    SecretManagerOperationException,
    SecretManagerSecretNotFoundException,
    SecretSearchCriteria,
)
from gafs.dynamicaiagent.utils.cryptoutil import CryptoType, CryptoUtil
from gafs.dynamicaiagent.utils.databaseprovider import DatabaseProviderType

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

_LOGGER = logging.getLogger(__name__)

_TEST_DIR = Path(__file__).resolve().parent
_REMOTE_CONFIG_PATH = _TEST_DIR / "secret_test_config_default_database_configurations.json"

# Unique tag prefix to isolate records created by this test run
_TEST_TAG = f"test-{uuid.uuid4().hex[:8]}"


def _make_logger(name: str = "test") -> logging.Logger:
    """Return a configured logger for tests."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
    return logger


def _load_remote_config() -> dict[str, Any] | None:
    """Load the remote SurrealDB config from the secret config file if it exists."""
    if not _REMOTE_CONFIG_PATH.exists():
        return None
    with open(_REMOTE_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _build_local_config() -> DatabaseConnection:
    """Build a DatabaseConnection for an in-memory local SurrealDB instance."""
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
    """Build a DatabaseConnection from a remote config dict."""
    return DatabaseConnection.from_dict(config_data)


async def _setup_secrets_collection_indexes(database_manager: DatabaseManager) -> None:
    """Set up the Secrets collection indexes required for testing.

    Creates a unique index on ``name`` and a standard index on ``tags``.
    These are defined in the Secret data model specification.
    """
    provider = database_manager.get_default_provider()
    collection = Secret.COLLECTION_NAME()

    # Unique standard index on name
    await provider.query_raw(
        f"DEFINE INDEX IF NOT EXISTS secrets_name_unique ON {collection} FIELDS name UNIQUE;"
    )
    # Full-text search index on name (requires default_ngram_analyzer from DatabaseManager init)
    try:
        await provider.query_raw(
            f"DEFINE INDEX IF NOT EXISTS secrets_name_search ON {collection} "
            f"FIELDS name SEARCH ANALYZER default_ngram_analyzer BM25 HIGHLIGHTS;"
        )
    except Exception:
        # Analyzer may not be available in all test configurations — non-fatal
        pass
    # Standard index on tags
    await provider.query_raw(
        f"DEFINE INDEX IF NOT EXISTS secrets_tags ON {collection} FIELDS tags;"
    )


@pytest.fixture
async def db_manager():
    """Provide a Phase-1-initialized DatabaseManager for tests.

    Uses local in-memory SurrealDB if available, otherwise falls back to remote config.
    """
    logger = _make_logger("db_manager")
    manager = DatabaseManager(logger)

    remote_data = _load_remote_config()
    if remote_data:
        config = _build_remote_config(remote_data)
    else:
        config = _build_local_config()

    await manager.initialize_default_connection(config)
    yield manager


@pytest.fixture
async def initialized_secret_manager(db_manager):
    """Provide a fully initialized SecretManager with a Phase-1 DatabaseManager.

    Phase-3 (DatabaseManager.initialize) is also called so the full setup is complete.
    """
    logger = _make_logger("secret_manager")
    crypto_util = CryptoUtil()
    sm = SecretManager(logger)

    # Phase 2: initialize SecretManager (no config keys → auto-generate)
    sm.initialize(db_manager, crypto_util, {})

    # Phase 3: complete DatabaseManager initialization
    await db_manager.initialize(sm)

    # Set up the Secrets collection indexes
    await _setup_secrets_collection_indexes(db_manager)

    yield sm, db_manager


# ---------------------------------------------------------------------------
# 1. Model tests
# ---------------------------------------------------------------------------


class TestSecretKeyModel:
    """Tests for the SecretKey model class."""

    def test_init_all_none(self):
        """All fields are None after __init__."""
        key = SecretKey()
        assert key.name is None
        assert key.encryption_key is None
        assert key.decryption_key is None

    def test_set_valid_fields(self):
        """Fields accept valid string values."""
        key = SecretKey()
        key.name = "aes-256-gcm"
        key.encryption_key = "base64_enc_key"
        key.decryption_key = "base64_dec_key"
        assert key.name == "aes-256-gcm"
        assert key.encryption_key == "base64_enc_key"
        assert key.decryption_key == "base64_dec_key"

    def test_set_invalid_name(self):
        """Setting name to a non-string raises ValueError."""
        key = SecretKey()
        with pytest.raises(ValueError):
            key.name = 123

    def test_set_invalid_encryption_key(self):
        """Setting encryption_key to a non-string raises ValueError."""
        key = SecretKey()
        with pytest.raises(ValueError):
            key.encryption_key = ["not", "a", "string"]

    def test_set_invalid_decryption_key(self):
        """Setting decryption_key to a non-string raises ValueError."""
        key = SecretKey()
        with pytest.raises(ValueError):
            key.decryption_key = 42

    def test_to_dict(self):
        """to_dict returns all set fields."""
        key = SecretKey()
        key.name = "aes-256-gcm"
        key.encryption_key = "enc"
        key.decryption_key = "dec"
        d = key.to_dict()
        assert d["name"] == "aes-256-gcm"
        assert d["encryption_key"] == "enc"
        assert d["decryption_key"] == "dec"

    def test_to_dict_partial(self):
        """to_dict excludes None fields."""
        key = SecretKey()
        key.name = "aes-256-gcm"
        d = key.to_dict()
        assert "name" in d
        assert "encryption_key" not in d

    def test_to_json_from_json_roundtrip(self):
        """from_json(to_json()) roundtrip preserves all fields."""
        key = SecretKey()
        key.name = "aes-256-gcm"
        key.encryption_key = "enc_key_value"
        key.decryption_key = "dec_key_value"
        restored = SecretKey.from_json(key.to_json())
        assert restored.name == key.name
        assert restored.encryption_key == key.encryption_key
        assert restored.decryption_key == key.decryption_key

    def test_from_dict(self):
        """from_dict creates a SecretKey with the given values."""
        d = {
            "name": "rsa-oaep",
            "encryption_key": "pub_key",
            "decryption_key": "priv_key",
        }
        key = SecretKey.from_dict(d)
        assert key.name == "rsa-oaep"
        assert key.encryption_key == "pub_key"
        assert key.decryption_key == "priv_key"

    def test_from_dict_skips_none_values(self):
        """from_dict skips None values in the input."""
        d = {"name": "aes-256-gcm", "encryption_key": None}
        key = SecretKey.from_dict(d)
        assert key.name == "aes-256-gcm"
        assert key.encryption_key is None  # not set

    def test_from_json_invalid_not_dict(self):
        """from_json raises ValueError when JSON is not a dict."""
        with pytest.raises(ValueError):
            SecretKey.from_json(json.dumps(["array", "not", "dict"]))


class TestSecretModel:
    """Tests for the Secret model class."""

    def test_init_all_none(self):
        """All fields are None after __init__."""
        s = Secret()
        assert s.id is None
        assert s.name is None
        assert s.secret is None
        assert s.raw_secret is None
        assert s.description is None
        assert s.tags is None
        assert s.created_at is None
        assert s.updated_at is None
        assert s.valid_until is None

    def test_set_id_strips_table_prefix(self):
        """Setting id with table prefix strips the prefix."""
        s = Secret()
        s.id = "Secrets:abc123"
        assert s.id == "abc123"

    def test_set_id_without_prefix(self):
        """Setting id without table prefix keeps the value as-is."""
        s = Secret()
        s.id = "abc123"
        assert s.id == "abc123"

    def test_set_id_none(self):
        """Setting id to None is allowed."""
        s = Secret()
        s.id = None
        assert s.id is None

    def test_set_name(self):
        """name accepts string values."""
        s = Secret()
        s.name = "my-secret"
        assert s.name == "my-secret"

    def test_set_name_invalid(self):
        """Setting name to a non-string raises ValueError."""
        s = Secret()
        with pytest.raises(ValueError):
            s.name = 42

    def test_set_secret_dict(self):
        """secret accepts dict values."""
        s = Secret()
        s.secret = {"key1": "encrypted_value"}
        assert s.secret == {"key1": "encrypted_value"}

    def test_set_secret_none(self):
        """Setting secret to None is allowed."""
        s = Secret()
        s.secret = {"key": "value"}
        s.secret = None
        assert s.secret is None

    def test_set_raw_secret_dict(self):
        """raw_secret accepts dict values."""
        s = Secret()
        s.raw_secret = {"api_key": "plaintext"}
        assert s.raw_secret == {"api_key": "plaintext"}

    def test_set_tags_list(self):
        """tags accepts list values."""
        s = Secret()
        s.tags = ["prod", "database"]
        assert s.tags == ["prod", "database"]

    def test_set_created_at_datetime(self):
        """created_at accepts datetime objects."""
        s = Secret()
        now = datetime.now()
        s.created_at = now
        assert s.created_at == now

    def test_set_created_at_string(self):
        """created_at accepts ISO datetime strings."""
        s = Secret()
        s.created_at = "2025-01-15T10:00:00"
        assert isinstance(s.created_at, datetime)

    def test_set_valid_until_epoch_int(self):
        """valid_until accepts Unix epoch integer."""
        s = Secret()
        s.valid_until = 1700000000
        assert isinstance(s.valid_until, datetime)

    def test_to_dict_excludes_raw_secret(self):
        """to_dict never includes raw_secret (transient field)."""
        s = Secret()
        s.name = "test"
        s.secret = {"key": "encrypted"}
        s.raw_secret = {"key": "plaintext"}
        d = s.to_dict()
        assert "raw_secret" not in d
        assert "secret" in d

    def test_to_dict_exclude_id(self):
        """to_dict with exclude_id=True omits the id field."""
        s = Secret()
        s.id = "abc"
        s.name = "test"
        d = s.to_dict(exclude_id=True)
        assert "id" not in d

    def test_to_json_excludes_raw_secret(self):
        """to_json output never contains raw_secret."""
        s = Secret()
        s.name = "test"
        s.secret = {"k": "v"}
        s.raw_secret = {"k": "plaintext"}
        js = s.to_json()
        parsed = json.loads(js)
        assert "raw_secret" not in parsed

    def test_from_dict_roundtrip(self):
        """from_dict restores all persisted fields correctly."""
        original = Secret()
        original.id = "abc123"
        original.name = "my-secret"
        original.secret = {"key": "aes-256-gcm:encrypted"}
        original.description = "desc"
        original.tags = ["tag1", "tag2"]
        d = original.to_dict()
        restored = Secret.from_dict(d)
        assert restored.id == "abc123"
        assert restored.name == "my-secret"
        assert restored.secret == {"key": "aes-256-gcm:encrypted"}
        assert restored.description == "desc"
        assert restored.tags == ["tag1", "tag2"]
        assert restored.raw_secret is None  # not in dict

    def test_from_json_invalid(self):
        """from_json raises ValueError for non-dict JSON."""
        with pytest.raises(ValueError):
            Secret.from_json(json.dumps("not-a-dict"))


class TestSecretSearchCriteria:
    """Tests for SecretSearchCriteria construction and query building."""

    def test_default_values(self):
        """Default criteria has all filters None and limit=100."""
        c = SecretSearchCriteria()
        assert c.name is None
        assert c.description_keywords is None
        assert c.limit == 100

    def test_set_name(self):
        """name accepts string values."""
        c = SecretSearchCriteria(name="my")
        assert c.name == "my"

    def test_set_name_invalid(self):
        """Setting name to a non-string raises ValueError."""
        with pytest.raises(ValueError):
            SecretSearchCriteria(name=123)

    def test_set_description_keywords(self):
        """description_keywords accepts list of strings."""
        c = SecretSearchCriteria(description_keywords=["prod", "api"])
        assert c.description_keywords == ["prod", "api"]

    def test_set_datetime_from_iso_string(self):
        """Datetime fields accept ISO datetime strings."""
        c = SecretSearchCriteria(created_at_from="2025-01-01T00:00:00")
        assert isinstance(c.created_at_from, datetime)

    def test_set_datetime_from_epoch(self):
        """Datetime fields accept Unix epoch integers."""
        c = SecretSearchCriteria(created_at_to=1700000000)
        assert isinstance(c.created_at_to, datetime)

    def test_set_invalid_datetime(self):
        """Datetime fields reject invalid ISO strings."""
        with pytest.raises(ValueError):
            SecretSearchCriteria(created_at_from="not-a-date")

    def test_set_limit_zero(self):
        """limit=0 is valid (no LIMIT clause)."""
        c = SecretSearchCriteria(limit=0)
        assert c.limit == 0

    def test_set_limit_negative(self):
        """Negative limit raises ValueError."""
        with pytest.raises(ValueError):
            SecretSearchCriteria(limit=-1)

    def test_to_query_no_conditions(self):
        """to_query with no conditions produces a 'WHERE true' clause."""
        from gafs.dynamicaiagent.utils.databaseprovider import SurrealDbRemoteProvider
        # An uninitialized SurrealDbRemoteProvider is sufficient for type-check in to_query
        provider = SurrealDbRemoteProvider(_make_logger("provider"))
        c = SecretSearchCriteria()
        q = c.to_query(provider)
        assert "WHERE true" in q

    def test_to_query_with_name(self):
        """to_query with name produces a name substring condition."""
        from gafs.dynamicaiagent.utils.databaseprovider import SurrealDbRemoteProvider
        provider = SurrealDbRemoteProvider(_make_logger("provider"))
        c = SecretSearchCriteria(name="test")
        q = c.to_query(provider)
        assert "string::contains(name, 'test')" in q

    def test_to_query_with_limit(self):
        """to_query appends LIMIT clause when limit > 0."""
        from gafs.dynamicaiagent.utils.databaseprovider import SurrealDbRemoteProvider
        provider = SurrealDbRemoteProvider(_make_logger("provider"))
        c = SecretSearchCriteria(limit=10)
        q = c.to_query(provider)
        assert "LIMIT 10" in q

    def test_to_query_no_limit_when_zero(self):
        """to_query omits LIMIT clause when limit=0."""
        from gafs.dynamicaiagent.utils.databaseprovider import SurrealDbRemoteProvider
        provider = SurrealDbRemoteProvider(_make_logger("provider"))
        c = SecretSearchCriteria(limit=0)
        q = c.to_query(provider)
        assert "LIMIT" not in q

    def test_to_query_unsupported_provider(self):
        """to_query raises NotImplementedError for non-SurrealDB providers."""
        from unittest.mock import MagicMock
        from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider
        # Use a non-SurrealDbRemoteProvider mock
        mock_provider = MagicMock(spec=IDatabaseProvider)
        c = SecretSearchCriteria()
        with pytest.raises(NotImplementedError):
            c.to_query(mock_provider)


# ---------------------------------------------------------------------------
# 2. SecretManager key management tests (no DB operations)
# ---------------------------------------------------------------------------


class TestSecretManagerKeyManagement:
    """Tests for SecretManager key management (add_key, get_key, generate_key)."""

    def setup_method(self):
        """Set up a fresh SecretManager with a mock DB for each test."""
        self.logger = _make_logger("key_test")
        self.crypto_util = CryptoUtil()
        self.sm = SecretManager(self.logger)

    def _make_key(self, name: str) -> SecretKey:
        """Create a SecretKey with a generated key pair."""
        crypto_type = CryptoType(name)
        kp = self.crypto_util.generate_key_pair(crypto_type)
        key = SecretKey()
        key.name = name
        key.encryption_key = kp.encryption_key
        key.decryption_key = kp.decryption_key
        return key

    def test_add_key_success(self):
        """add_key registers a key successfully."""
        key = self._make_key(CryptoType.AES_256_GCM.value)
        self.sm.add_key(key)
        # Should be retrievable
        retrieved = self.sm.get_key(CryptoType.AES_256_GCM)
        assert retrieved.name == CryptoType.AES_256_GCM.value

    def test_add_key_duplicate_raises(self):
        """add_key raises SecretManagerInvalidSecretEntryException for duplicate key."""
        key = self._make_key(CryptoType.AES_256_GCM.value)
        self.sm.add_key(key)
        with pytest.raises(SecretManagerInvalidSecretEntryException):
            self.sm.add_key(key)

    def test_get_key_not_found_raises(self):
        """get_key raises SecretManagerKeyNotFoundException when key is not registered."""
        with pytest.raises(SecretManagerKeyNotFoundException):
            self.sm.get_key(CryptoType.AES_256_GCM)

    def test_get_key_all_crypto_types(self):
        """get_key retrieves keys for all CryptoTypes after adding them."""
        for crypto_type in CryptoType:
            key = self._make_key(crypto_type.value)
            self.sm.add_key(key)
        for crypto_type in CryptoType:
            retrieved = self.sm.get_key(crypto_type)
            assert retrieved.name == crypto_type.value

    def test_generate_key_not_initialized_raises(self):
        """generate_key raises SecretManagerNotInitializedException when not initialized."""
        with pytest.raises(SecretManagerNotInitializedException):
            self.sm.generate_key(CryptoType.AES_256_GCM)

    def test_initialize_with_config_keys(self, tmp_path, monkeypatch):
        """initialize loads keys from config (priority A)."""
        # Generate a real key pair for config injection
        kp = self.crypto_util.generate_key_pair(CryptoType.AES_256_GCM)
        config = {
            "secret_keys": [
                {
                    "name": CryptoType.AES_256_GCM.value,
                    "encryption_key": kp.encryption_key,
                    "decryption_key": kp.decryption_key,
                }
            ]
        }

        # Provide a minimal DB manager stub that returns a dummy provider
        class _FakeProvider:
            pass

        class _FakeDbManager:
            def get_default_provider(self):
                return _FakeProvider()

        sm = SecretManager(self.logger)
        sm.initialize(_FakeDbManager(), self.crypto_util, config)
        key = sm.get_key(CryptoType.AES_256_GCM)
        assert key.encryption_key == kp.encryption_key

    def test_initialize_db_provider_failure_raises(self):
        """initialize raises SecretManagerInitializationException when DB provider fails."""
        class _FailDbManager:
            def get_default_provider(self):
                raise RuntimeError("Provider not available")

        sm = SecretManager(self.logger)
        with pytest.raises(SecretManagerInitializationException):
            sm.initialize(_FailDbManager(), self.crypto_util, {})

    def test_initialize_generates_keys_when_no_file(self, tmp_path, monkeypatch):
        """initialize auto-generates keys (priority C) when no file exists."""
        # Redirect the data folder to a temp directory with no key file
        monkeypatch.setattr(
            "gafs.dynamicaiagent.common.secretmanager.secret_manager.platformdirs.user_data_dir",
            lambda appname, appauthor: str(tmp_path),
        )

        class _FakeProvider:
            pass

        class _FakeDbManager:
            def get_default_provider(self):
                return _FakeProvider()

        sm = SecretManager(self.logger)
        sm.initialize(_FakeDbManager(), self.crypto_util, {})

        # All CryptoTypes should have keys registered
        for crypto_type in CryptoType:
            key = sm.get_key(crypto_type)
            assert key.encryption_key is not None

        # secret_keys.json should have been created
        key_file = tmp_path / "secret_keys.json"
        assert key_file.exists()


# ---------------------------------------------------------------------------
# 3. SecretManager CRUD integration tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSecretManagerCRUD:
    """Integration tests for SecretManager CRUD operations against a real database."""

    async def test_create_secret_normal(self, initialized_secret_manager):
        """create_secret creates an entry and returns raw_secret with secret=None."""
        sm, _ = initialized_secret_manager

        secret = Secret()
        secret.name = f"test-create-{_TEST_TAG}"
        secret.raw_secret = {"api_key": "plaintext-api-key", "password": "my-password"}
        secret.tags = [_TEST_TAG]

        result = await sm.create_secret(secret)

        assert result.id is not None
        assert result.raw_secret is not None
        assert result.raw_secret["api_key"] == "plaintext-api-key"
        assert result.raw_secret["password"] == "my-password"
        assert result.secret is None

        # Cleanup
        await sm.delete_secret(result.id)

    async def test_create_secret_missing_name_raises(self, initialized_secret_manager):
        """create_secret raises SecretManagerInvalidSecretEntryException when name is missing."""
        sm, _ = initialized_secret_manager

        secret = Secret()
        secret.raw_secret = {"key": "value"}
        # name is not set

        with pytest.raises(SecretManagerInvalidSecretEntryException):
            await sm.create_secret(secret)

    async def test_create_secret_missing_raw_secret_raises(self, initialized_secret_manager):
        """create_secret raises SecretManagerInvalidSecretEntryException when raw_secret is empty."""
        sm, _ = initialized_secret_manager

        secret = Secret()
        secret.name = f"test-no-raw-{_TEST_TAG}"
        # raw_secret is None

        with pytest.raises(SecretManagerInvalidSecretEntryException):
            await sm.create_secret(secret)

    async def test_get_secret_decrypt_true(self, initialized_secret_manager):
        """get_secret with decrypt=True returns raw_secret populated and secret=None."""
        sm, _ = initialized_secret_manager

        # Create a secret first
        secret = Secret()
        secret.name = f"test-get-decrypt-{_TEST_TAG}"
        secret.raw_secret = {"token": "my-secret-token"}
        secret.tags = [_TEST_TAG]
        created = await sm.create_secret(secret)

        # Retrieve with decryption
        retrieved = await sm.get_secret(created.id, decrypt=True)

        assert retrieved is not None
        assert retrieved.raw_secret is not None
        assert retrieved.raw_secret["token"] == "my-secret-token"
        assert retrieved.secret is None

        # Cleanup
        await sm.delete_secret(created.id)

    async def test_get_secret_decrypt_false(self, initialized_secret_manager):
        """get_secret with decrypt=False returns masked secret values and raw_secret=None."""
        sm, _ = initialized_secret_manager

        # Create a secret
        secret = Secret()
        secret.name = f"test-get-nodecrypt-{_TEST_TAG}"
        secret.raw_secret = {"password": "super-secret"}
        secret.tags = [_TEST_TAG]
        created = await sm.create_secret(secret)

        # Retrieve without decryption
        retrieved = await sm.get_secret(created.id, decrypt=False)

        assert retrieved is not None
        assert retrieved.raw_secret is None
        assert retrieved.secret is not None
        # All values should be masked
        for v in retrieved.secret.values():
            assert v == "******"

        # Cleanup
        await sm.delete_secret(created.id)

    async def test_get_secret_not_found_returns_none(self, initialized_secret_manager):
        """get_secret returns None when the id does not exist."""
        sm, _ = initialized_secret_manager

        result = await sm.get_secret("nonexistent-id-99999", decrypt=False)
        assert result is None

    async def test_update_secret_normal(self, initialized_secret_manager):
        """update_secret updates the entry and returns raw_secret with secret=None."""
        sm, _ = initialized_secret_manager

        # Create initial secret
        secret = Secret()
        secret.name = f"test-update-{_TEST_TAG}"
        secret.raw_secret = {"api_key": "original-key"}
        secret.tags = [_TEST_TAG]
        created = await sm.create_secret(secret)

        # Update the secret
        update = Secret()
        update.id = created.id
        update.raw_secret = {"api_key": "updated-key"}

        result = await sm.update_secret(update)

        assert result.raw_secret is not None
        assert result.raw_secret["api_key"] == "updated-key"
        assert result.secret is None

        # Verify by retrieving and decrypting
        fetched = await sm.get_secret(created.id, decrypt=True)
        assert fetched.raw_secret["api_key"] == "updated-key"

        # Cleanup
        await sm.delete_secret(created.id)

    async def test_update_secret_missing_id_raises(self, initialized_secret_manager):
        """update_secret raises SecretManagerInvalidSecretEntryException when id is missing."""
        sm, _ = initialized_secret_manager

        update = Secret()
        update.raw_secret = {"key": "value"}
        # id is not set

        with pytest.raises(SecretManagerInvalidSecretEntryException):
            await sm.update_secret(update)

    async def test_update_secret_not_found_raises(self, initialized_secret_manager):
        """update_secret raises SecretManagerSecretNotFoundException for non-existent id."""
        sm, _ = initialized_secret_manager

        update = Secret()
        update.id = "nonexistent-id-99999"
        update.raw_secret = {"key": "value"}

        with pytest.raises(SecretManagerSecretNotFoundException):
            await sm.update_secret(update)

    async def test_search_secrets_by_name(self, initialized_secret_manager):
        """search_secrets returns entries matching the name criterion."""
        sm, _ = initialized_secret_manager

        # Create test secrets
        name_unique = f"searchable-{_TEST_TAG}"
        secret = Secret()
        secret.name = name_unique
        secret.raw_secret = {"key": "value"}
        secret.tags = [_TEST_TAG]
        created = await sm.create_secret(secret)

        # Search by unique name substring
        criteria = SecretSearchCriteria(name=_TEST_TAG)
        results = await sm.search_secrets(criteria, decrypt=False)

        # The created secret should be in results
        ids = [r.id for r in results]
        assert created.id in ids

        # All values should be masked
        for r in results:
            if r.secret:
                for v in r.secret.values():
                    assert v == "******"

        # Cleanup
        await sm.delete_secret(created.id)

    async def test_search_secrets_no_match_returns_empty(self, initialized_secret_manager):
        """search_secrets returns an empty list when no entries match."""
        sm, _ = initialized_secret_manager

        criteria = SecretSearchCriteria(name="absolutely-no-match-xyz-99999")
        results = await sm.search_secrets(criteria, decrypt=False)
        assert results == []

    async def test_delete_secret_normal(self, initialized_secret_manager):
        """delete_secret removes the entry without raising."""
        sm, _ = initialized_secret_manager

        # Create a secret to delete
        secret = Secret()
        secret.name = f"test-delete-{_TEST_TAG}"
        secret.raw_secret = {"key": "value"}
        created = await sm.create_secret(secret)

        # Delete — should not raise
        await sm.delete_secret(created.id)

        # Verify it's gone
        result = await sm.get_secret(created.id, decrypt=False)
        assert result is None

    async def test_delete_secret_not_found_raises(self, initialized_secret_manager):
        """delete_secret raises SecretManagerSecretNotFoundException for non-existent id."""
        sm, _ = initialized_secret_manager

        with pytest.raises(SecretManagerSecretNotFoundException):
            await sm.delete_secret("nonexistent-id-99999")

    async def test_not_initialized_raises_on_crud(self):
        """All async operations raise SecretManagerNotInitializedException when not initialized."""
        sm = SecretManager(_make_logger("uninit_test"))

        secret = Secret()
        secret.name = "test"
        secret.raw_secret = {"k": "v"}

        with pytest.raises(SecretManagerNotInitializedException):
            await sm.create_secret(secret)

        with pytest.raises(SecretManagerNotInitializedException):
            await sm.get_secret("any-id")

        with pytest.raises(SecretManagerNotInitializedException):
            await sm.delete_secret("any-id")

    async def test_create_and_retrieve_with_description_and_tags(
        self, initialized_secret_manager
    ):
        """create_secret preserves description and tags; get_secret returns them."""
        sm, _ = initialized_secret_manager

        secret = Secret()
        secret.name = f"test-full-{_TEST_TAG}"
        secret.raw_secret = {"service_key": "sk_live_abcdef"}
        secret.description = "API key for the test service"
        secret.tags = [_TEST_TAG, "api", "live"]

        created = await sm.create_secret(secret)

        # Retrieve and verify metadata is preserved
        fetched = await sm.get_secret(created.id, decrypt=True)
        assert fetched.description == "API key for the test service"
        assert _TEST_TAG in fetched.tags
        assert fetched.raw_secret["service_key"] == "sk_live_abcdef"

        # Cleanup
        await sm.delete_secret(created.id)
