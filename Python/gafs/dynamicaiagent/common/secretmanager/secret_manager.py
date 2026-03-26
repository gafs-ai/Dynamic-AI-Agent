from logging import Logger
from typing import Any

from gafs.dynamicaiagent.common.databasemanager import IDatabaseManager
from gafs.dynamicaiagent.common.secretmanager.i_secret_manager import (
    SecretSearchCriteria,
)
from gafs.dynamicaiagent.common.secretmanager.secret import Secret
from gafs.dynamicaiagent.utils.databaseprovider import SurrealDbRemoteProvider
from gafs.dynamicaiagent.utils.symmetriccryptoutil import SymmetricCryptoType, SymmetricCryptoUtil
from gafs.dynamicaiagent.utils.databaseprovider.exceptions import DatabaseQueryErrorException, DatabaseRecordNotFoundException

class SecretManager:
    """Secret manager class.

    This class is responsible for managing `Secret` entities, including:

    - generating and managing symmetric keys
    - encrypting and decrypting secret values
    - persisting secrets to and retrieving secrets from the database
    """

    DEFAULT_CRYPTO_TYPE: SymmetricCryptoType = SymmetricCryptoType.AES_256_GCM

    def __init__(self, logger: Logger) -> None:
        """Create a new instance of `SecretManager`.

        Args:
            logger: Logger instance used for logging.
        """
        self._logger: Logger = logger
        self._database_manager: IDatabaseManager | None = None
        self._database_provider: SurrealDbRemoteProvider | None = None
        self._crypto_util: SymmetricCryptoUtil | None = None
        self._keys: dict[str, str] = {}

    def initialize(
        self,
        database_manager: IDatabaseManager,
        crypto_util: SymmetricCryptoUtil,
        keys: dict[str, str],
    ) -> bool:
        """Initialize the secret manager.

        Args:
            database_manager: Database manager used to access the underlying database.
            crypto_util: Utility used to perform symmetric encryption and decryption.
            keys: Mapping from crypto type value to symmetric key string.

        Returns:
            True if the initialization succeeded, False otherwise.
        """
        self._logger.debug("Initializing secret manager...")
        self._database_manager = database_manager
        self._crypto_util = crypto_util
        self._keys = keys
        self._database_provider = self._database_manager.get_default_database_provider()
        if self._database_provider is None:
            self._logger.error("Default database provider not found.")
            return False

        self._logger.info("Secret manager initialized successfully.")
        return True

    def add_symmetric_key(self, crypto_type: SymmetricCryptoType, key: str) -> bool:
        """Add a symmetric key for the specified crypto type.

        Args:
            crypto_type: Crypto type to register the key for.
            key: Symmetric key string to register.

        Returns:
            True if the key was registered successfully, False otherwise.
        """
        self._logger.debug(f"Adding symmetric key for {crypto_type.value}...")
        if crypto_type.value not in self._keys:
            self._keys[crypto_type.value] = key
            self._logger.debug(
                f"Symmetric key for {crypto_type.value} added successfully."
            )
            return True
        else:
            message: str = f"Symmetric key for {crypto_type.value} already exists."
            self._logger.error(message)
            return False

    def get_symmetric_key(self, crypto_type: SymmetricCryptoType) -> str | None:
        """Get the symmetric key for the specified crypto type.

        Args:
            crypto_type: Crypto type to get the key for.

        Returns:
            The symmetric key string for the specified crypto type.
        """
        return self._keys[crypto_type.value]

    def generate_symmetric_key(self, crypto_type: SymmetricCryptoType) -> str:
        """Generate and register a symmetric key for the specified crypto type.

        Args:
            crypto_type: Crypto type for which a key will be generated.

        Returns:
            The generated symmetric key.

        Raises:
            ValueError: If a key for the specified crypto type already exists.
        """
        if self._crypto_util is None:
            message: str = "Crypto util is not initialized."
            self._logger.error(message)
            raise ValueError(message)

        self._logger.debug(f"Generating symmetric key for {crypto_type.value}...")
        key: str = self._crypto_util.generate_key(crypto_type)
        if crypto_type.value not in self._keys:
            self._keys[crypto_type.value] = key
        else:
            message = f"Symmetric key for {crypto_type.value} already exists."
            self._logger.error(message)
            raise ValueError(message)

        self._logger.debug(
            f"Symmetric key for {crypto_type.value} generated successfully."
        )
        return key

    async def create_secret(self, secret: Secret) -> Secret:
        """Create a new secret.

        Raw values in the `secret.secret` dictionary will be encrypted and stored
        as encrypted values.

        Args:
            secret: Secret entity to be created.

        Returns:
            The created secret with masked encrypted values.

        Raises:
            ValueError: When SecretManager is not initialized.
            DatabaseQueryErrorException: When the database query fails.
        """
        if self._database_provider is None or self._crypto_util is None:
            message: str = "SecretManager is not initialized."
            self._logger.error(message)
            raise ValueError(message)

        self._logger.debug("Creating secret...")
        for key in list(secret.secret.keys()):
            if key.startswith("raw_"):
                new_key: str = key.replace("raw_", "encrypted_")
                encrypted_value: str = self._crypto_util.encrypt(
                    self.DEFAULT_CRYPTO_TYPE,
                    secret.secret[key],
                    self._keys[self.DEFAULT_CRYPTO_TYPE.value],
                )
                secret.secret[new_key] = (
                    f"{self.DEFAULT_CRYPTO_TYPE.value}:{encrypted_value}"
                )
                secret.secret.pop(key)

        # If id is not specified, let SurrealDB generate it automatically.
        query: str
        if secret.id is None:
            query = f"CREATE secret CONTENT {secret.to_json()}"
        else:
            query = f"CREATE secret:{secret.id} CONTENT {secret.to_json()}"

        try:
            created_secret: Secret = await self._database_provider.query(query, Secret)
        except Exception as error:  # pylint: disable=broad-except
            self._logger.error("Failed to create secret.", exc_info=True)
            raise error

        self._logger.info("Created secret: %s", created_secret.id)
        return created_secret

    async def update_secret(self, secret: Secret) -> Secret:
        """Update an existing secret.

        Raw values in the `secret.secret` dictionary will be encrypted and stored
        as encrypted values.

        Args:
            secret: Secret entity with updated values.

        Returns:
            The updated secret with masked encrypted values.

        Raises:
            ValueError: When SecretManager is not initialized.
            DatabaseRecordNotFoundException: When the secret to update is not found.
            DatabaseQueryErrorException: When the database query fails.
        """
        if self._database_provider is None or self._crypto_util is None:
            message: str = "SecretManager is not initialized."
            self._logger.error(message)
            raise ValueError(message)

        self._logger.debug("Updating secret...")
        for key in list(secret.secret.keys()):
            if key.startswith("raw_"):
                new_key: str = key.replace("raw_", "encrypted_")
                encrypted_value: str = self._crypto_util.encrypt(
                    self.DEFAULT_CRYPTO_TYPE,
                    secret.secret[key],
                    self._keys[self.DEFAULT_CRYPTO_TYPE.value],
                )
                secret.secret[new_key] = (
                    f"{self.DEFAULT_CRYPTO_TYPE.value}:{encrypted_value}"
                )
                secret.secret.pop(key)

        query: str = f"UPDATE secret:{secret.id} MERGE {secret.to_json()}"

        try:
            updated_secret: Secret | None = await self._database_provider.query(
                query, Secret
            )
        except Exception as error:  # pylint: disable=broad-except
            self._logger.error("Failed to update secret.", exc_info=True)
            raise error

        if updated_secret is None:
            message = f"Secret not found for id: {secret.id}"
            self._logger.error(message)
            raise DatabaseRecordNotFoundException(message=message)

        self._logger.info("Updated secret: %s", updated_secret.id)
        return updated_secret

    async def get_secret(self, secret_id: str) -> Secret | None:
        """Get a secret by id.

        Encrypted values in the `secret.secret` dictionary will be decrypted and
        returned as raw values.

        Args:
            secret_id: Identifier of the secret to retrieve.

        Returns:
            The retrieved secret with decrypted values, or None if not found.

        Raises:
            ValueError: When SecretManager is not initialized.
            DatabaseQueryErrorException: When the database query fails.
        """
        if self._database_provider is None or self._crypto_util is None:
            message: str = "SecretManager is not initialized."
            self._logger.error(message)
            raise ValueError(message)

        self._logger.debug("Getting secret: %s", secret_id)

        query: str = f"SELECT * FROM secret:{secret_id}"

        try:
            result: Secret | None = await self._database_provider.query(query, Secret)
        except Exception as error:  # pylint: disable=broad-except
            self._logger.error("Failed to get secret: %s", secret_id, exc_info=True)
            raise error

        if result is None:
            self._logger.debug("Secret not found: %s", secret_id)
            return None

        for key in list(result.secret.keys()):
            if key.startswith("encrypted_"):
                new_key: str = key.replace("encrypted_", "raw_")
                encrypted_value: str = result.secret[key]
                decryptor_name, encrypted_payload = encrypted_value.split(":", 1)
                decryptor_type: SymmetricCryptoType = SymmetricCryptoType(
                    decryptor_name
                )
                decrypted_value: str = self._crypto_util.decrypt(
                    decryptor_type,
                    encrypted_payload,
                    self._keys[decryptor_type.value],
                )

                result.secret[new_key] = decrypted_value
                result.secret.pop(key)

        # NOTE: Remove any remaining encrypted_* keys just in case.
        result.secret = {
            key: value
            for key, value in result.secret.items()
            if not key.startswith("encrypted_")
        }

        self._logger.info("Got secret: %s", secret_id)
        return result

    async def search_secrets(
        self, secret_search_criteria: SecretSearchCriteria
    ) -> list[Secret]:
        """Search secrets by criteria.

        Encrypted values in the `secret.secret` dictionary of each result
        will be decrypted and returned as raw values.

        Args:
            secret_search_criteria: The criteria to search for secrets.

        Returns:
            A list of secrets matching the criteria with decrypted values.

        Raises:
            ValueError: When SecretManager is not initialized.
            DatabaseQueryErrorException: When the database query fails.
        """
        if self._database_provider is None or self._crypto_util is None:
            message: str = "SecretManager is not initialized."
            self._logger.error(message)
            raise ValueError(message)

        self._logger.debug(
            "Searching secrets with criteria: %s", secret_search_criteria
        )

        query: str = secret_search_criteria.to_query(
            self._database_provider, "secret"
        )
        self._logger.debug("Searching secrets with query: %s", query)

        try:
            results: list[Secret] | None = await self._database_provider.query(
                query, Secret, many=True
            )
        except Exception as error:  # pylint: disable=broad-except
            self._logger.error(
                "Failed to search secrets. Query: %s. Error: %s",
                query,
                error,
                exc_info=True,
            )
            raise error

        if results is None:
            self._logger.debug("No secrets found")
            return []

        for result in results:
            if result.secret is None:
                continue
            for key in list(result.secret.keys()):
                if key.startswith("encrypted_"):
                    new_key: str = key.replace("encrypted_", "raw_")
                    encrypted_value: str = result.secret[key]
                    decryptor_name, encrypted_payload = encrypted_value.split(
                        ":", 1
                    )
                    decryptor_type: SymmetricCryptoType = SymmetricCryptoType(
                        decryptor_name
                    )
                    decrypted_value: str = self._crypto_util.decrypt(
                        decryptor_type,
                        encrypted_payload,
                        self._keys[decryptor_type.value],
                    )
                    result.secret[new_key] = decrypted_value
                    result.secret.pop(key)
            result.secret = {
                k: v
                for k, v in result.secret.items()
                if not k.startswith("encrypted_")
            }

        self._logger.info("Found %d secret(s)", len(results))
        return results

    async def delete_secret(self, secret_id: str) -> bool:
        """Delete a secret by id.

        Args:
            secret_id: Identifier of the secret to delete.

        Returns:
            True if the secret was deleted successfully. False is not used at this time.

        Raises:
            ValueError: When SecretManager is not initialized.
            DatabaseRecordNotFoundException: When the secret to delete is not found.
            DatabaseQueryErrorException: When the database query fails.
        """
        if self._database_provider is None:
            message: str = "SecretManager is not initialized."
            self._logger.error(message)
            raise ValueError(message)

        self._logger.debug("Deleting secret: %s", secret_id)

        query: str = f"DELETE secret:{secret_id} RETURN BEFORE"

        try:
            result: Any = await self._database_provider.query_raw(query)
        except DatabaseQueryErrorException as error:
            # If the query fails, it may indicate the record was not found.
            # Re-raise as DatabaseRecordNotFoundException for clarity.
            self._logger.error(
                "Failed to delete secret: %s", secret_id, exc_info=True
            )
            raise DatabaseRecordNotFoundException(
                message=f"Secret not found for id: {secret_id}", cause=error
            ) from error
        except Exception as error:  # pylint: disable=broad-except
            self._logger.error(
                "Failed to delete secret: %s", secret_id, exc_info=True
            )
            raise error

        # With RETURN BEFORE: empty list means no record was deleted
        if not result or (isinstance(result, list) and len(result) == 0):
            message = f"Secret not found for id: {secret_id}"
            self._logger.error(message)
            raise DatabaseRecordNotFoundException(message=message)

        self._logger.info("Deleted secret: %s", secret_id)
        return True
