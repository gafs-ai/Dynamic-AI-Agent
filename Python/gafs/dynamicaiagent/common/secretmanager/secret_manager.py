"""secret_manager.py - Concrete implementation of ISecretManager."""

from __future__ import annotations

import json
import logging
from logging import Logger
from pathlib import Path
from typing import Any

import platformdirs

from gafs.dynamicaiagent.common.configurationloader import IConfigurationLoader
from gafs.dynamicaiagent.utils.cryptoutil import CryptoType, CryptoUtil
from gafs.dynamicaiagent.utils.databaseprovider import IDatabaseProvider
from gafs.dynamicaiagent.utils.databaseprovider.exceptions import (
    DatabaseRecordNotFoundException,
)

from .exceptions import (
    SecretManagerCryptoException,
    SecretManagerInitializationException,
    SecretManagerInvalidSecretEntryException,
    SecretManagerKeyNotFoundException,
    SecretManagerNotInitializedException,
    SecretManagerOperationException,
    SecretManagerSecretNotFoundException,
)
from .i_secret_manager import ISecretManager, SecretSearchCriteria
from .models import Secret, SecretKey


class SecretManager(ISecretManager):
    """Concrete implementation of ISecretManager.

    Manages cryptographic keys and encrypted secret entries in the ``Secrets``
    collection of the default database.

    Key loading priority during ``initialize()``:
        A. Config:    ``config["secret_keys"]`` is present and non-empty.
        B. File:      ``secret_keys.json`` in the application data folder exists.
        C. Generate:  Auto-generate one key per ``CryptoType`` and persist them.
    """

    @staticmethod
    def DEFAULT_CRYPTO_TYPE() -> CryptoType:
        """Default crypto type used for encrypting and decrypting secret values."""
        return CryptoType.AES_256_GCM

    # ---------------------------------------------------------------------------
    # Construction
    # ---------------------------------------------------------------------------

    def __init__(self, logger: Logger) -> None:
        """Initialize SecretManager with a logger.

        All internal state starts as None/empty.
        Call ``initialize()`` to complete setup.

        Args:
            logger: Logger instance for this component.
        """
        # Logger for this instance
        self._logger: Logger = logger

        # The IDatabaseManager reference, registered during initialize()
        self._database_manager: Any | None = None

        # The default IDatabaseProvider, obtained from _database_manager during initialize()
        self._database_provider: IDatabaseProvider | None = None

        # CryptoUtil instance, registered during initialize()
        self._crypto_util: CryptoUtil | None = None

        # Internal key store: maps CryptoType.value (str) → SecretKey
        self._keys: dict[str, SecretKey] = {}

        # Tracks whether initialize() has completed successfully
        self._initialized: bool = False

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    def _get_data_folder(self) -> Path:
        """Resolve the application data folder path using platformdirs.

        Returns:
            Path to the OS-specific application data directory.
        """
        # Use the application name and author from IConfigurationLoader constants
        return Path(
            platformdirs.user_data_dir(
                appname=IConfigurationLoader.APPLICATION_NAME,
                appauthor=IConfigurationLoader.APPLICATION_AUTHOR,
            )
        )

    def _load_keys_from_data_folder(self) -> list[SecretKey] | None:
        """Load SecretKey entries from ``secret_keys.json`` in the application data folder.

        Returns:
            List of SecretKey entries if the file exists and is non-empty, otherwise None.
        """
        # Build the full path to the key file
        key_file: Path = self._get_data_folder() / "secret_keys.json"

        # Return None if the file does not exist
        if not key_file.exists():
            self._logger.debug(f"Key file not found: {key_file}")
            return None

        # Read and parse the JSON array from the file
        try:
            with open(key_file, encoding="utf-8") as f:
                data: Any = json.load(f)
        except Exception as e:
            self._logger.warning(f"Failed to read key file '{key_file}': {e}")
            return None

        # The file must contain a JSON array
        if not isinstance(data, list):
            self._logger.warning(f"Key file '{key_file}' does not contain a JSON array.")
            return None

        # Return None if the array is empty
        if not data:
            return None

        # Deserialize each element as a SecretKey
        keys: list[SecretKey] = []
        for entry in data:
            if isinstance(entry, dict):
                keys.append(SecretKey.from_dict(entry))

        return keys if keys else None

    def _save_keys_to_data_folder(self, keys: list[SecretKey]) -> None:
        """Merge the given SecretKey entries into ``secret_keys.json``.

        Existing entries whose ``name`` does not match any entry in ``keys`` are preserved.
        Entries whose ``name`` matches an entry in ``keys`` are replaced.

        Args:
            keys: Key entries to add or update.
        """
        key_file: Path = self._get_data_folder() / "secret_keys.json"

        # Ensure the data folder exists before writing
        key_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing entries from the file (if any)
        existing: list[SecretKey] = []
        if key_file.exists():
            try:
                with open(key_file, encoding="utf-8") as f:
                    raw: Any = json.load(f)
                if isinstance(raw, list):
                    for entry in raw:
                        if isinstance(entry, dict):
                            existing.append(SecretKey.from_dict(entry))
            except Exception as e:
                # Non-fatal: start with an empty list if reading fails
                self._logger.warning(f"Failed to read existing key file for merge: {e}")

        # Build a lookup of the new keys by name for efficient merging
        new_keys_by_name: dict[str, SecretKey] = {k.name: k for k in keys if k.name}

        # Merge: keep existing entries for names not in new_keys, replace others
        merged: list[SecretKey] = []
        existing_names: set[str] = set()
        for entry in existing:
            if entry.name in new_keys_by_name:
                # Replace with the new entry
                merged.append(new_keys_by_name[entry.name])
            else:
                # Keep the existing entry unchanged
                merged.append(entry)
            if entry.name:
                existing_names.add(entry.name)

        # Append new entries that did not exist before
        for key in keys:
            if key.name and key.name not in existing_names:
                merged.append(key)

        # Serialize the merged list and overwrite the file
        try:
            merged_data: list[dict[str, Any]] = [k.to_dict() for k in merged]
            with open(key_file, "w", encoding="utf-8") as f:
                json.dump(merged_data, f, indent=2)
            self._logger.debug(f"Saved {len(merged)} key(s) to '{key_file}'.")
        except Exception as e:
            self._logger.error(f"Failed to save keys to '{key_file}': {e}")
            raise

    def _check_initialized(self) -> None:
        """Raise SecretManagerNotInitializedException if not yet initialized.

        Raises:
            SecretManagerNotInitializedException: If initialize() has not been called.
        """
        if not self._initialized or self._database_provider is None:
            raise SecretManagerNotInitializedException(
                "SecretManager is not initialized. Call initialize() first."
            )

    def _apply_masking_or_decryption(self, entry: Secret, decrypt: bool) -> Secret:
        """Apply value masking or decryption to a Secret entry returned from the database.

        When ``decrypt=True``:
            - Each encrypted value in ``entry.secret`` is decrypted.
            - The decrypted values are stored in ``entry.raw_secret``.
            - ``entry.secret`` is set to None.
        When ``decrypt=False``:
            - Each value in ``entry.secret`` is replaced with ``"******"``.
            - ``entry.raw_secret`` is set to None (already None from DB deserialization).

        Args:
            entry: Secret entry deserialized from the database.
            decrypt: Whether to decrypt the values.

        Returns:
            The same entry after applying masking or decryption.

        Raises:
            SecretManagerCryptoException: If decryption fails.
        """
        if entry.secret is None:
            return entry

        if decrypt:
            # Decrypt each value and store in raw_secret
            raw: dict[str, Any] = {}
            for key, value in entry.secret.items():
                if not isinstance(value, str):
                    # Non-string values are passed through as-is
                    raw[key] = value
                    continue

                try:
                    # Parse the format: "{crypto_type}:{encrypted_payload}"
                    if ":" not in value:
                        raise SecretManagerCryptoException(
                            f"Unexpected encrypted value format for key '{key}': '{value}'."
                        )
                    crypto_type_str, payload = value.split(":", 1)

                    # Look up the registered decryption key for this algorithm
                    crypto_type = CryptoType(crypto_type_str)
                    secret_key = self.get_key(crypto_type)

                    # Decrypt using CryptoUtil
                    decrypted = self._crypto_util.decrypt(
                        crypto_type, payload, secret_key.decryption_key
                    )
                    raw[key] = decrypted
                except (SecretManagerCryptoException, SecretManagerKeyNotFoundException):
                    raise
                except Exception as e:
                    self._logger.error(
                        f"Failed to decrypt value for key '{key}': {e}", exc_info=True
                    )
                    raise SecretManagerCryptoException(
                        f"Failed to decrypt value for key '{key}'.", cause=e
                    )

            # Populate raw_secret with decrypted values; clear secret
            entry.raw_secret = raw
            entry.secret = None

        else:
            # Mask every value in secret with "******" (keys are preserved)
            masked: dict[str, Any] = {k: "******" for k in entry.secret}
            entry.secret = masked
            entry.raw_secret = None

        return entry

    # ---------------------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------------------

    def initialize(
        self,
        database_manager: Any,
        crypto_util: CryptoUtil,
        config: dict[str, Any],
    ) -> bool:
        """Phase-2 initialization: register dependencies and load cryptographic keys.

        Steps:
            1. Register ``database_manager`` and ``crypto_util`` to internal fields.
            2. Obtain the default ``IDatabaseProvider`` from the database manager.
            3. Load keys via priority A → B → C.
            4. Return True.

        Args:
            database_manager: Already Phase-1-initialized ``DatabaseManager`` instance.
            crypto_util: Utility used to perform encryption and decryption.
            config: Component configuration. ``config["secret_keys"]`` (list[dict], optional)
                provides key entries directly.

        Returns:
            True on success.

        Raises:
            SecretManagerInitializationException: If the default database provider is not
                available or key loading/generation fails.
        """
        self._logger.debug("Initializing SecretManager...")

        # --- Step 1: Register dependencies ---
        self._database_manager = database_manager
        self._crypto_util = crypto_util

        # --- Step 2: Obtain the default IDatabaseProvider ---
        try:
            self._database_provider = database_manager.get_default_provider()
        except Exception as e:
            self._logger.error(f"Failed to obtain default database provider: {e}")
            raise SecretManagerInitializationException(
                "Failed to obtain the default database provider.", cause=e
            )

        # --- Step 3: Load keys (priority A → B → C) ---
        try:
            config_keys: Any = config.get("secret_keys") if isinstance(config, dict) else None

            if config_keys:
                # Priority A: keys provided directly in the config
                self._logger.debug("Loading secret keys from config (priority A).")
                for entry in config_keys:
                    key = SecretKey.from_dict(entry) if isinstance(entry, dict) else entry
                    self.add_key(key)

            else:
                # Priority B: load keys from secret_keys.json in the data folder
                self._logger.debug("Attempting to load secret keys from file (priority B).")
                file_keys = self._load_keys_from_data_folder()

                if file_keys:
                    for key in file_keys:
                        self.add_key(key)
                    self._logger.debug(f"Loaded {len(file_keys)} key(s) from file.")

                else:
                    # Priority C: auto-generate one key per CryptoType
                    self._logger.debug(
                        "No keys found in file. Auto-generating keys (priority C)."
                    )
                    generated: list[SecretKey] = []
                    for crypto_type in CryptoType:
                        key_pair = crypto_util.generate_key_pair(crypto_type)
                        new_key = SecretKey()
                        new_key.name = crypto_type.value
                        new_key.encryption_key = key_pair.encryption_key
                        new_key.decryption_key = key_pair.decryption_key
                        self.add_key(new_key)
                        generated.append(new_key)

                    # Persist all generated keys to the data folder
                    self._save_keys_to_data_folder(generated)
                    self._logger.info(f"Auto-generated and saved {len(generated)} key(s).")

        except (SecretManagerInitializationException, SecretManagerInvalidSecretEntryException):
            raise
        except Exception as e:
            self._logger.error(f"Failed to load or generate secret keys: {e}")
            raise SecretManagerInitializationException(
                "Failed to load or generate secret keys.", cause=e
            )

        # Mark as fully initialized
        self._initialized = True
        self._logger.info("SecretManager initialized successfully.")
        return True

    # ---------------------------------------------------------------------------
    # Key management
    # ---------------------------------------------------------------------------

    def add_key(self, key: SecretKey) -> None:
        """Register a SecretKey entry in the internal key store.

        Args:
            key: Key entry to register. ``key.name`` must not already be registered.

        Raises:
            SecretManagerInvalidSecretEntryException: A key for ``key.name`` is already registered.
        """
        # Reject duplicate key registrations
        if key.name in self._keys:
            raise SecretManagerInvalidSecretEntryException(
                f"A key for '{key.name}' is already registered."
            )

        self._keys[key.name] = key
        self._logger.debug(f"Registered key for '{key.name}'.")

    def get_key(self, crypto_type: CryptoType) -> SecretKey:
        """Retrieve the registered SecretKey for the specified crypto type.

        Args:
            crypto_type: Crypto type to look up.

        Returns:
            Registered SecretKey entry.

        Raises:
            SecretManagerKeyNotFoundException: No key is registered for the specified crypto type.
        """
        key = self._keys.get(crypto_type.value)
        if key is None:
            raise SecretManagerKeyNotFoundException(
                f"No key registered for crypto type '{crypto_type.value}'."
            )
        return key

    def generate_key(self, crypto_type: CryptoType) -> SecretKey:
        """Generate a new SecretKey, register it, and persist all keys to disk.

        Args:
            crypto_type: Crypto type for which to generate a key.

        Returns:
            The newly generated and registered SecretKey.

        Raises:
            SecretManagerNotInitializedException: SecretManager is not initialized.
            SecretManagerInvalidSecretEntryException: A key for the crypto type already exists.
        """
        # Verify that the manager is initialized before generating keys
        self._check_initialized()

        # Reject if a key already exists for this type (add_key will raise if duplicate)
        key_pair = self._crypto_util.generate_key_pair(crypto_type)

        new_key = SecretKey()
        new_key.name = crypto_type.value
        new_key.encryption_key = key_pair.encryption_key
        new_key.decryption_key = key_pair.decryption_key

        # Register the key (raises SecretManagerInvalidSecretEntryException if duplicate)
        self.add_key(new_key)

        # Persist all currently registered keys to the data folder
        self._save_keys_to_data_folder(list(self._keys.values()))

        self._logger.info(f"Generated and registered new key for '{crypto_type.value}'.")
        return new_key

    # ---------------------------------------------------------------------------
    # Secret CRUD
    # ---------------------------------------------------------------------------

    async def create_secret(self, secret: Secret) -> Secret:
        """Encrypt and persist a new Secret entry in the Secrets collection.

        The values in ``secret.raw_secret`` are encrypted before persisting.
        The returned entry has ``raw_secret`` populated with the original plaintext
        and ``secret`` set to None.

        Args:
            secret: Secret entry to create. ``raw_secret`` must be populated.

        Returns:
            Created entry with ``raw_secret`` populated and ``secret`` = None.

        Raises:
            SecretManagerNotInitializedException: SecretManager is not initialized.
            SecretManagerInvalidSecretEntryException: Entry data is invalid.
            SecretManagerCryptoException: Encryption fails.
            SecretManagerOperationException: Database persistence fails.
        """
        self._check_initialized()

        # --- Step 2: Validate the secret entry ---
        if secret.name is None or not secret.name.strip():
            raise SecretManagerInvalidSecretEntryException(
                "Secret.name is required and must not be empty."
            )
        if not secret.raw_secret:
            raise SecretManagerInvalidSecretEntryException(
                "Secret.raw_secret must be populated with plaintext credentials."
            )

        # Keep a copy of the original plaintext values for the return value
        original_raw: dict[str, Any] = dict(secret.raw_secret)

        # --- Step 3: Obtain the encryption key ---
        secret_key = self.get_key(self.DEFAULT_CRYPTO_TYPE())
        crypto_type = self.DEFAULT_CRYPTO_TYPE()

        # --- Step 4: Encrypt each value in raw_secret → secret ---
        encrypted_dict: dict[str, Any] = {}
        for field_name, value in secret.raw_secret.items():
            try:
                # Encrypt the plaintext value
                encrypted_payload = self._crypto_util.encrypt(
                    crypto_type, str(value), secret_key.encryption_key
                )
                # Store as "{crypto_type}:{payload}" to identify the algorithm on decryption
                encrypted_dict[field_name] = f"{crypto_type.value}:{encrypted_payload}"
            except Exception as e:
                self._logger.error(
                    f"Failed to encrypt value for field '{field_name}': {e}", exc_info=True
                )
                raise SecretManagerCryptoException(
                    f"Failed to encrypt value for field '{field_name}'.", cause=e
                )

        # Set the encrypted values on the secret object
        # (to_dict will include secret but not raw_secret)
        secret.secret = encrypted_dict

        # --- Step 5: Persist to the Secrets collection ---
        # Build the CREATE query with the encrypted payload only
        collection = Secret.COLLECTION_NAME()
        try:
            if secret.id is None:
                # Let the database assign an id automatically
                query = f"CREATE {collection} CONTENT {secret.to_json(exclude_id=True)}"
            else:
                # Use the caller-provided id; wrap in backticks to allow hyphens and special chars
                query = f"CREATE {collection}:`{secret.id}` CONTENT {secret.to_json(exclude_id=True)}"

            result: Secret | None = await self._database_provider.query(
                query, Secret, many=False
            )
        except Exception as e:
            self._logger.error(f"Failed to create Secret: {e}", exc_info=True)
            raise SecretManagerOperationException(
                "Failed to create Secret in the database.", cause=e
            )

        if result is None:
            raise SecretManagerOperationException(
                "Database returned no result after creating Secret."
            )

        # --- Step 6: Populate raw_secret on the returned entry, clear secret ---
        result.raw_secret = original_raw
        result.secret = None

        self._logger.info(f"Created Secret with id='{result.id}'.")
        return result

    async def update_secret(self, secret: Secret) -> Secret:
        """Encrypt and merge-update an existing Secret entry.

        Args:
            secret: Updated entry. ``id`` and ``raw_secret`` are required.

        Returns:
            Updated entry with ``raw_secret`` populated and ``secret`` = None.

        Raises:
            SecretManagerNotInitializedException: SecretManager is not initialized.
            SecretManagerInvalidSecretEntryException: Entry data is invalid (e.g. ``id`` missing).
            SecretManagerCryptoException: Encryption fails.
            SecretManagerSecretNotFoundException: Target record does not exist.
            SecretManagerOperationException: Database operation fails.
        """
        self._check_initialized()

        # --- Step 2: Validate the secret entry ---
        if not secret.id:
            raise SecretManagerInvalidSecretEntryException(
                "Secret.id is required for update_secret."
            )
        if not secret.raw_secret:
            raise SecretManagerInvalidSecretEntryException(
                "Secret.raw_secret must be populated with plaintext credentials."
            )

        # Keep a copy of the original plaintext values
        original_raw: dict[str, Any] = dict(secret.raw_secret)

        # --- Step 3: Obtain the encryption key ---
        secret_key = self.get_key(self.DEFAULT_CRYPTO_TYPE())
        crypto_type = self.DEFAULT_CRYPTO_TYPE()

        # --- Step 4: Encrypt each value ---
        encrypted_dict: dict[str, Any] = {}
        for field_name, value in secret.raw_secret.items():
            try:
                encrypted_payload = self._crypto_util.encrypt(
                    crypto_type, str(value), secret_key.encryption_key
                )
                encrypted_dict[field_name] = f"{crypto_type.value}:{encrypted_payload}"
            except Exception as e:
                self._logger.error(
                    f"Failed to encrypt value for field '{field_name}': {e}", exc_info=True
                )
                raise SecretManagerCryptoException(
                    f"Failed to encrypt value for field '{field_name}'.", cause=e
                )

        secret.secret = encrypted_dict

        # --- Step 5: Execute MERGE update ---
        collection = Secret.COLLECTION_NAME()
        try:
            # Build a dict of only the fields to update (exclude id and raw_secret)
            merge_data = secret.to_dict(recursive=True, exclude_id=True)
            merge_json = json.dumps(merge_data)
            # Wrap id in backticks to allow hyphens and special characters in the record id
            query = f"UPDATE {collection}:`{secret.id}` MERGE {merge_json}"

            result: Secret | None = await self._database_provider.query(
                query, Secret, many=False
            )
        except Exception as e:
            self._logger.error(
                f"Failed to update Secret id='{secret.id}': {e}", exc_info=True
            )
            raise SecretManagerOperationException(
                f"Failed to update Secret id='{secret.id}'.", cause=e
            )

        # A None result means no record was found/updated
        if result is None:
            raise SecretManagerSecretNotFoundException(
                f"Secret with id='{secret.id}' was not found."
            )

        # --- Step 6: Populate raw_secret, clear secret ---
        result.raw_secret = original_raw
        result.secret = None

        self._logger.info(f"Updated Secret id='{result.id}'.")
        return result

    async def get_secret(self, secret_id: str, decrypt: bool = False) -> Secret | None:
        """Retrieve a Secret entry by record id.

        Args:
            secret_id: Record id to look up.
            decrypt: If True, decrypt values into ``raw_secret``. If False, mask values.

        Returns:
            Matching Secret entry, or None if not found.

        Raises:
            SecretManagerNotInitializedException: SecretManager is not initialized.
            SecretManagerCryptoException: Decryption fails (only when ``decrypt=True``).
            SecretManagerOperationException: Database query fails.
        """
        self._check_initialized()

        # --- Step 2: Query the Secrets collection by id ---
        collection = Secret.COLLECTION_NAME()
        try:
            # Wrap id in backticks to allow hyphens and special characters
            query = f"SELECT * FROM {collection}:`{secret_id}`"
            result: Secret | None = await self._database_provider.query(
                query, Secret, many=False
            )
        except Exception as e:
            self._logger.error(
                f"Failed to query Secret id='{secret_id}': {e}", exc_info=True
            )
            raise SecretManagerOperationException(
                f"Failed to query Secret id='{secret_id}'.", cause=e
            )

        # --- Step 3: Return None if not found ---
        if result is None:
            self._logger.debug(f"Secret id='{secret_id}' not found.")
            return None

        # --- Steps 4–5: Apply masking or decryption ---
        return self._apply_masking_or_decryption(result, decrypt)

    async def search_secrets(
        self, criteria: SecretSearchCriteria, decrypt: bool = False
    ) -> list[Secret]:
        """Search for Secret entries matching the given criteria.

        Args:
            criteria: Search criteria built via SecretSearchCriteria.
            decrypt: If True, decrypt values in results. If False, mask values.

        Returns:
            List of matching Secret entries. Empty list if nothing matches.

        Raises:
            SecretManagerNotInitializedException: SecretManager is not initialized.
            SecretManagerCryptoException: Decryption fails (only when ``decrypt=True``).
            SecretManagerOperationException: Database query fails.
        """
        self._check_initialized()

        # --- Step 2: Build the SurrealQL SELECT query ---
        try:
            query = criteria.to_query(self._database_provider, Secret.COLLECTION_NAME())
        except NotImplementedError:
            raise
        except Exception as e:
            self._logger.error(f"Failed to build search query: {e}", exc_info=True)
            raise SecretManagerOperationException(
                "Failed to build Secret search query.", cause=e
            )

        # --- Step 3: Execute the query ---
        self._logger.debug(f"Searching Secrets with query: {query}")
        try:
            results: list[Secret] | None = await self._database_provider.query(
                query, Secret, many=True
            )
        except Exception as e:
            self._logger.error(f"Failed to search Secrets: {e}", exc_info=True)
            raise SecretManagerOperationException(
                "Failed to search Secrets in the database.", cause=e
            )

        # --- Step 4: Return empty list if no results ---
        if not results:
            return []

        # --- Step 5: Apply masking or decryption to each result ---
        processed: list[Secret] = []
        for entry in results:
            processed.append(self._apply_masking_or_decryption(entry, decrypt))

        self._logger.debug(f"Found {len(processed)} Secret(s).")
        return processed

    async def delete_secret(self, secret_id: str) -> None:
        """Delete a Secret entry by record id.

        Args:
            secret_id: Record id of the entry to delete.

        Raises:
            SecretManagerNotInitializedException: SecretManager is not initialized.
            SecretManagerSecretNotFoundException: No record with the given id exists.
            SecretManagerOperationException: Database operation fails.
        """
        self._check_initialized()

        # --- Step 2: Execute DELETE with RETURN BEFORE to detect missing records ---
        collection = Secret.COLLECTION_NAME()
        try:
            # Wrap id in backticks to allow hyphens and special characters
            query = f"DELETE {collection}:`{secret_id}` RETURN BEFORE"
            raw_result: Any = await self._database_provider.query_raw(query)
        except Exception as e:
            self._logger.error(
                f"Failed to delete Secret id='{secret_id}': {e}", exc_info=True
            )
            raise SecretManagerOperationException(
                f"Failed to delete Secret id='{secret_id}'.", cause=e
            )

        # An empty result means no record was deleted (not found)
        was_deleted = (
            isinstance(raw_result, list) and len(raw_result) > 0
        ) or (
            raw_result is not None and not isinstance(raw_result, list)
        )
        if not was_deleted:
            raise SecretManagerSecretNotFoundException(
                f"Secret with id='{secret_id}' was not found."
            )

        self._logger.info(f"Deleted Secret id='{secret_id}'.")
