"""Pytest-based tests for Secret, SecretSearchCriteria, and SecretManager.

Tests cover entity serialization, search criteria query generation,
symmetric key management, and CRUD/search operations on secrets.

Requirements:
    - pytest
    - pytest-asyncio

Run with:
    cd Python
    pytest gafs/dynamicaiagent/common/secretmanager/test/test_secret_manager.py -v
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from gafs.dynamicaiagent.common.databasemanager import (
    DatabaseManager,
    IDatabaseManager,
)
from gafs.dynamicaiagent.common.secretmanager.i_secret_manager import (
    SecretSearchCriteria,
)
from gafs.dynamicaiagent.common.secretmanager.secret import Secret
from gafs.dynamicaiagent.common.secretmanager.secret_manager import SecretManager
from gafs.dynamicaiagent.utils.databaseprovider import (
    DatabaseType,
    RemoteSurrealDbOptions,
    SurrealDbRemoteProvider,
)
from gafs.dynamicaiagent.utils.databaseprovider.exceptions import (
    DatabaseQueryErrorException,
    DatabaseRecordNotFoundException,
)
from gafs.dynamicaiagent.utils.symmetriccryptoutil import (
    SymmetricCryptoType,
    SymmetricCryptoUtil,
)


# ==================== Fixtures ====================


@pytest.fixture(scope="module")
def logger() -> logging.Logger:
    """Create a logger for tests."""
    test_logger = logging.getLogger("secret_manager_pytest")
    test_logger.setLevel(logging.DEBUG)
    if not test_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s - %(message)s")
        )
        test_logger.addHandler(handler)
    return test_logger


@pytest.fixture(scope="module")
def config() -> dict:
    """Load test configuration from JSON file."""
    python_root = Path(__file__).resolve().parents[5]
    config_path = (
        python_root
        / "gafs"
        / "dynamicaiagent"
        / "utils"
        / "databaseprovider"
        / "test"
        / "secret_test_config_0.json"
    )
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def db_options(config: dict) -> RemoteSurrealDbOptions:
    """Build RemoteSurrealDbOptions from config."""
    options = RemoteSurrealDbOptions()
    options.endpoint = config["endpoint"]
    options.namespace = config["namespace"]
    options.database = config["database"]
    options.username = config["username"]
    options.password = config["password"]
    options.database_type = DatabaseType.SURREALDB_REMOTE
    options.database_name = IDatabaseManager.DEFAULT_DATABASE_NAME()
    return options


@pytest.fixture
async def initialized_secret_manager(
    logger: logging.Logger,
    db_options: RemoteSurrealDbOptions,
) -> SecretManager:
    """Create and initialize SecretManager with database connection."""
    db_manager = DatabaseManager(logger)
    await db_manager.add_provider(db_options, overwrite=True)
    crypto_util = SymmetricCryptoUtil()
    aes_key: str = crypto_util.generate_key(SymmetricCryptoType.AES_256_GCM)
    keys: dict[str, str] = {SymmetricCryptoType.AES_256_GCM.value: aes_key}
    secret_manager = SecretManager(logger)
    result = secret_manager.initialize(db_manager, crypto_util, keys)
    assert result is True, "SecretManager should initialize successfully"
    yield secret_manager


# ==================== Secret (data class) tests ====================


def test_secret_serialization() -> None:
    """Test Secret to_dict, to_json, from_dict, from_json round-trip."""
    secret = Secret()
    secret.name = "test-name"
    secret.description = "test-desc"
    secret.secret = {"raw_key": "value"}

    d = secret.to_dict()
    assert d["name"] == "test-name"
    assert d["description"] == "test-desc"
    assert d["secret"] == {"raw_key": "value"}

    j = secret.to_json()
    parsed = json.loads(j)
    assert parsed["name"] == "test-name"

    restored = Secret.from_dict(d)
    assert restored.name == secret.name
    assert restored.description == secret.description
    assert restored.secret == secret.secret

    restored2 = Secret.from_json(j)
    assert restored2.name == secret.name


def test_secret_validation() -> None:
    """Test Secret __setattr__ validation."""
    secret = Secret()
    secret.name = "ok"
    assert secret.name == "ok"

    with pytest.raises(ValueError):
        secret.name = 123  # type: ignore[assignment]

    with pytest.raises(ValueError):
        Secret.from_json("[]")


# ==================== SecretSearchCriteria tests ====================


def test_secret_search_criteria_to_query_empty() -> None:
    """Test SecretSearchCriteria.to_query with empty criteria."""
    criteria = SecretSearchCriteria()
    provider = SurrealDbRemoteProvider(logging.getLogger("test"))
    q = criteria.to_query(provider, "secret")
    assert "SELECT * FROM secret WHERE" in q
    assert "true" in q


def test_secret_search_criteria_to_query_name() -> None:
    """Test SecretSearchCriteria.to_query with name."""
    criteria = SecretSearchCriteria(name="api-key")
    provider = SurrealDbRemoteProvider(logging.getLogger("test"))
    q = criteria.to_query(provider, "secret")
    assert "name ∋ 'api-key'" in q


def test_secret_search_criteria_to_query_description_keywords() -> None:
    """Test SecretSearchCriteria.to_query with description_keywords."""
    criteria = SecretSearchCriteria(description_keywords=["token", "api"])
    provider = SurrealDbRemoteProvider(logging.getLogger("test"))
    q = criteria.to_query(provider, "secret")
    assert "description ∋ 'token'" in q
    assert "description ∋ 'api'" in q


def test_secret_search_criteria_to_query_limit() -> None:
    """Test SecretSearchCriteria.to_query with limit."""
    criteria = SecretSearchCriteria(limit=10)
    provider = SurrealDbRemoteProvider(logging.getLogger("test"))
    q = criteria.to_query(provider, "secret")
    assert "LIMIT 10" in q


def test_secret_search_criteria_to_query_not_implemented() -> None:
    """Test SecretSearchCriteria.to_query raises for non-SurrealDB provider."""
    class DummyProvider:
        pass

    criteria = SecretSearchCriteria()
    with pytest.raises(NotImplementedError):
        criteria.to_query(DummyProvider(), "secret")


# ==================== Symmetric key tests (no DB) ====================


def test_add_symmetric_key_success() -> None:
    """Test add_symmetric_key and get_symmetric_key when not registered."""
    mgr = SecretManager(logging.getLogger("test"))
    added = mgr.add_symmetric_key(SymmetricCryptoType.AES_256_GCM, "key1")
    assert added is True
    assert mgr.get_symmetric_key(SymmetricCryptoType.AES_256_GCM) == "key1"


def test_add_symmetric_key_duplicate() -> None:
    """Test add_symmetric_key returns False when already registered."""
    mgr = SecretManager(logging.getLogger("test"))
    mgr.add_symmetric_key(SymmetricCryptoType.AES_256_GCM, "key1")
    added = mgr.add_symmetric_key(SymmetricCryptoType.AES_256_GCM, "key2")
    assert added is False
    assert mgr.get_symmetric_key(SymmetricCryptoType.AES_256_GCM) == "key1"


def test_get_symmetric_key_missing() -> None:
    """Test get_symmetric_key raises KeyError when key not registered."""
    mgr = SecretManager(logging.getLogger("test"))
    with pytest.raises(KeyError):
        mgr.get_symmetric_key(SymmetricCryptoType.AES_256_GCM)


def test_generate_symmetric_key_success() -> None:
    """Test generate_symmetric_key produces key."""
    mgr = SecretManager(logging.getLogger("test"))
    mgr._crypto_util = SymmetricCryptoUtil()
    key = mgr.generate_symmetric_key(SymmetricCryptoType.AES_256_GCM)
    assert key
    assert mgr.get_symmetric_key(SymmetricCryptoType.AES_256_GCM) == key


def test_generate_symmetric_key_without_crypto_util() -> None:
    """Test generate_symmetric_key raises when crypto_util not set."""
    mgr = SecretManager(logging.getLogger("test"))
    with pytest.raises(ValueError):
        mgr.generate_symmetric_key(SymmetricCryptoType.AES_256_GCM)


# ==================== Initialize tests ====================


@pytest.mark.asyncio
async def test_initialize_success(
    logger: logging.Logger,
    db_options: RemoteSurrealDbOptions,
) -> None:
    """Test initialize returns True when default provider exists."""
    db_manager = DatabaseManager(logger)
    await db_manager.add_provider(db_options, overwrite=True)
    crypto_util = SymmetricCryptoUtil()
    aes_key = crypto_util.generate_key(SymmetricCryptoType.AES_256_GCM)
    keys = {SymmetricCryptoType.AES_256_GCM.value: aes_key}
    mgr = SecretManager(logger)
    result = mgr.initialize(db_manager, crypto_util, keys)
    assert result is True


@pytest.mark.asyncio
async def test_initialize_failure_no_default_provider(logger: logging.Logger) -> None:
    """Test initialize returns False when no default provider."""
    db_manager = DatabaseManager(logger)
    crypto_util = SymmetricCryptoUtil()
    aes_key = crypto_util.generate_key(SymmetricCryptoType.AES_256_GCM)
    keys = {SymmetricCryptoType.AES_256_GCM.value: aes_key}
    mgr = SecretManager(logger)
    result = mgr.initialize(db_manager, crypto_util, keys)
    assert result is False


# ==================== Without-initialization tests ====================


@pytest.mark.asyncio
async def test_create_secret_without_initialization(logger: logging.Logger) -> None:
    """Test create_secret raises ValueError when not initialized."""
    mgr = SecretManager(logger)
    secret = Secret()
    secret.name = "x"
    secret.description = "x"
    secret.secret = {"raw_x": "x"}
    with pytest.raises(ValueError):
        await mgr.create_secret(secret)


@pytest.mark.asyncio
async def test_get_secret_without_initialization(logger: logging.Logger) -> None:
    """Test get_secret raises ValueError when not initialized."""
    mgr = SecretManager(logger)
    with pytest.raises(ValueError):
        await mgr.get_secret("any_id")


@pytest.mark.asyncio
async def test_delete_secret_without_initialization(logger: logging.Logger) -> None:
    """Test delete_secret raises ValueError when not initialized."""
    mgr = SecretManager(logger)
    with pytest.raises(ValueError):
        await mgr.delete_secret("any_id")


@pytest.mark.asyncio
async def test_search_secrets_without_initialization(logger: logging.Logger) -> None:
    """Test search_secrets raises ValueError when not initialized."""
    mgr = SecretManager(logger)
    with pytest.raises(ValueError):
        await mgr.search_secrets(SecretSearchCriteria())


# ==================== CRUD tests (require DB) ====================


@pytest.mark.asyncio
async def test_create_secret_with_id(
    initialized_secret_manager: SecretManager,
) -> None:
    """Test create_secret with explicit id and get_secret."""
    mgr = initialized_secret_manager
    secret_id = "test_create_with_id_001"
    created_ids: list[str] = []
    try:
        secret = Secret()
        secret.id = secret_id
        secret.name = "create-with-id"
        secret.description = "desc"
        secret.secret = {"raw_token": "token1"}
        created = await mgr.create_secret(secret)
        created_ids.append(created.id)
        assert created.id == secret_id
        fetched = await mgr.get_secret(secret_id)
        assert fetched is not None
        assert fetched.name == "create-with-id"
        assert "raw_token" in fetched.secret
        assert fetched.secret["raw_token"] == "token1"
    finally:
        for sid in created_ids:
            try:
                await mgr.delete_secret(sid)
            except Exception:
                pass


@pytest.mark.asyncio
async def test_create_secret_without_id(
    initialized_secret_manager: SecretManager,
) -> None:
    """Test create_secret without id (auto-generated) and get_secret."""
    mgr = initialized_secret_manager
    created_ids: list[str] = []
    try:
        secret = Secret()
        secret.name = "create-no-id"
        secret.description = "desc"
        secret.secret = {"raw_x": "x"}
        created = await mgr.create_secret(secret)
        assert created.id is not None
        created_ids.append(created.id)
        fetched = await mgr.get_secret(created.id)
        assert fetched is not None
        assert fetched.name == "create-no-id"
    finally:
        for sid in created_ids:
            try:
                await mgr.delete_secret(sid)
            except Exception:
                pass


@pytest.mark.asyncio
async def test_create_secret_duplicate_id(
    initialized_secret_manager: SecretManager,
) -> None:
    """Test create_secret with duplicate id raises error or overwrites."""
    mgr = initialized_secret_manager
    secret_id = "test_dup_001"
    created_ids: list[str] = []
    try:
        s1 = Secret()
        s1.id = secret_id
        s1.name = "first"
        s1.description = "desc"
        s1.secret = {"raw_x": "x"}
        await mgr.create_secret(s1)
        created_ids.append(secret_id)

        s2 = Secret()
        s2.id = secret_id
        s2.name = "second"
        s2.description = "desc"
        s2.secret = {"raw_y": "y"}
        try:
            await mgr.create_secret(s2)
            # SurrealDB may overwrite on CREATE; verify we have second content
            fetched = await mgr.get_secret(secret_id)
            assert fetched is not None
            assert fetched.name == "second"
        except (DatabaseQueryErrorException, Exception):
            # Expected when DB enforces uniqueness
            pass
    finally:
        for sid in created_ids:
            try:
                await mgr.delete_secret(sid)
            except Exception:
                pass


@pytest.mark.asyncio
async def test_update_secret_success(
    initialized_secret_manager: SecretManager,
) -> None:
    """Test update_secret and verify via get_secret."""
    mgr = initialized_secret_manager
    secret_id = "test_update_001"
    created_ids: list[str] = []
    try:
        s = Secret()
        s.id = secret_id
        s.name = "original"
        s.description = "original desc"
        s.secret = {"raw_t": "t"}
        created = await mgr.create_secret(s)
        created_ids.append(created.id)

        created.description = "updated desc"
        await mgr.update_secret(created)
        fetched = await mgr.get_secret(secret_id)
        assert fetched is not None
        assert fetched.description == "updated desc"
    finally:
        for sid in created_ids:
            try:
                await mgr.delete_secret(sid)
            except Exception:
                pass


@pytest.mark.asyncio
async def test_update_secret_not_found(
    initialized_secret_manager: SecretManager,
) -> None:
    """Test update_secret raises when secret does not exist."""
    mgr = initialized_secret_manager
    s = Secret()
    s.id = "test_update_nonexistent_001"
    s.name = "x"
    s.description = "x"
    s.secret = {}
    with pytest.raises(DatabaseRecordNotFoundException):
        await mgr.update_secret(s)


@pytest.mark.asyncio
async def test_get_secret_success(
    initialized_secret_manager: SecretManager,
) -> None:
    """Test get_secret returns decrypted secret."""
    mgr = initialized_secret_manager
    secret_id = "test_get_001"
    created_ids: list[str] = []
    try:
        s = Secret()
        s.id = secret_id
        s.name = "get-test"
        s.description = "desc"
        s.secret = {"raw_apikey": "secret-value"}
        await mgr.create_secret(s)
        created_ids.append(secret_id)

        fetched = await mgr.get_secret(secret_id)
        assert fetched is not None
        assert "raw_apikey" in fetched.secret
        assert fetched.secret["raw_apikey"] == "secret-value"
    finally:
        for sid in created_ids:
            try:
                await mgr.delete_secret(sid)
            except Exception:
                pass


@pytest.mark.asyncio
async def test_get_secret_not_found(
    initialized_secret_manager: SecretManager,
) -> None:
    """Test get_secret returns None for non-existent id."""
    mgr = initialized_secret_manager
    result = await mgr.get_secret("nonexistent_secret_id_999")
    assert result is None


@pytest.mark.asyncio
async def test_delete_secret_success(
    initialized_secret_manager: SecretManager,
) -> None:
    """Test delete_secret and verify get_secret returns None."""
    mgr = initialized_secret_manager
    secret_id = "test_delete_001"
    s = Secret()
    s.id = secret_id
    s.name = "delete-test"
    s.description = "desc"
    s.secret = {"raw_x": "x"}
    await mgr.create_secret(s)

    deleted = await mgr.delete_secret(secret_id)
    assert deleted is True
    fetched = await mgr.get_secret(secret_id)
    assert fetched is None


@pytest.mark.asyncio
async def test_delete_secret_not_found(
    initialized_secret_manager: SecretManager,
) -> None:
    """Test delete_secret raises for non-existent id."""
    mgr = initialized_secret_manager
    with pytest.raises(DatabaseRecordNotFoundException):
        await mgr.delete_secret("nonexistent_id_999")


# ==================== search_secrets tests ====================


@pytest.mark.asyncio
async def test_search_secrets_by_name(
    initialized_secret_manager: SecretManager,
) -> None:
    """Test search_secrets with name criterion."""
    mgr = initialized_secret_manager
    created_ids: list[str] = []
    try:
        s1 = Secret()
        s1.name = "search-name-alpha"
        s1.description = "desc"
        s1.secret = {"raw_x": "x"}
        c1 = await mgr.create_secret(s1)
        created_ids.append(c1.id)
        s2 = Secret()
        s2.name = "search-name-beta"
        s2.description = "desc"
        s2.secret = {"raw_y": "y"}
        c2 = await mgr.create_secret(s2)
        created_ids.append(c2.id)

        criteria = SecretSearchCriteria(name="alpha")
        results = await mgr.search_secrets(criteria)
        assert isinstance(results, list)
        assert len(results) >= 1
        names = [r.name for r in results]
        assert "search-name-alpha" in names
    finally:
        for sid in created_ids:
            try:
                await mgr.delete_secret(sid)
            except Exception:
                pass


@pytest.mark.asyncio
async def test_search_secrets_by_description_keywords(
    initialized_secret_manager: SecretManager,
) -> None:
    """Test search_secrets with description_keywords criterion."""
    mgr = initialized_secret_manager
    created_ids: list[str] = []
    try:
        s = Secret()
        s.name = "search-desc-kw"
        s.description = "contains unique-word-xyz-123"
        s.secret = {"raw_x": "x"}
        c = await mgr.create_secret(s)
        created_ids.append(c.id)

        criteria = SecretSearchCriteria(description_keywords=["unique-word-xyz-123"])
        results = await mgr.search_secrets(criteria)
        assert isinstance(results, list)
        assert len(results) >= 1
        assert any(
            r.description and "unique-word-xyz-123" in r.description
            for r in results
        )
    finally:
        for sid in created_ids:
            try:
                await mgr.delete_secret(sid)
            except Exception:
                pass


@pytest.mark.asyncio
async def test_search_secrets_by_limit(
    initialized_secret_manager: SecretManager,
) -> None:
    """Test search_secrets with limit criterion returns at most limit items."""
    mgr = initialized_secret_manager
    created_ids: list[str] = []
    try:
        # Create our own secrets so we only get back records we can decrypt
        s = Secret()
        s.name = "search-limit-unique-xyz"
        s.description = "desc"
        s.secret = {"raw_x": "x"}
        c = await mgr.create_secret(s)
        created_ids.append(c.id)
        criteria = SecretSearchCriteria(
            name="search-limit-unique-xyz",
            limit=5,
        )
        results = await mgr.search_secrets(criteria)
        assert isinstance(results, list)
        assert len(results) <= 5
        assert len(results) >= 1
    finally:
        for sid in created_ids:
            try:
                await mgr.delete_secret(sid)
            except Exception:
                pass


@pytest.mark.asyncio
async def test_search_secrets_combined(
    initialized_secret_manager: SecretManager,
) -> None:
    """Test search_secrets with name + description_keywords."""
    mgr = initialized_secret_manager
    created_ids: list[str] = []
    try:
        s = Secret()
        s.name = "search-combined-abc"
        s.description = "unique-combined-xyz-456"
        s.secret = {"raw_x": "x"}
        c = await mgr.create_secret(s)
        created_ids.append(c.id)

        criteria = SecretSearchCriteria(
            name="combined",
            description_keywords=["unique-combined-xyz-456"],
        )
        results = await mgr.search_secrets(criteria)
        assert isinstance(results, list)
        assert len(results) >= 1
    finally:
        for sid in created_ids:
            try:
                await mgr.delete_secret(sid)
            except Exception:
                pass


@pytest.mark.asyncio
async def test_search_secrets_empty_result(
    initialized_secret_manager: SecretManager,
) -> None:
    """Test search_secrets returns empty list when no match."""
    mgr = initialized_secret_manager
    criteria = SecretSearchCriteria(
        name="nonexistent-name-xyz-999-no-match",
    )
    results = await mgr.search_secrets(criteria)
    assert results == []
