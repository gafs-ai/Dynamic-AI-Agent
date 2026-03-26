"""Create a model catalogue with vector [0.1, 0.2, 0.3, 0.4], persist it, then search with the same vector and print results.

Uses DB connection from secret_test_db_config.json in this directory.
Run from Python source root: python -m gafs.dynamicaiagent.modelcomponent.test.run_vector_persist_and_search
Or: cd Python && python gafs/dynamicaiagent/modelcomponent/test/run_vector_persist_and_search.py (after path fix).
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add Python source root to path for direct script execution
PYTHON_SRC: Path = Path(__file__).resolve().parents[4]
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from gafs.dynamicaiagent.common.databasemanager import (
    DatabaseManager,
    IDatabaseManager,
)
from gafs.dynamicaiagent.modelcomponent.model_catalogue import (
    ModelCatalogue,
    ModelStatus,
)
from gafs.dynamicaiagent.modelcomponent.model_catalogue_service import (
    ModelCatalogueService,
    ModelCatalogueSearchCriteria,
    VectorSearchCriteria,
)
from gafs.dynamicaiagent.modelcomponent.models.ai_operation_type import AiOperationType
from gafs.dynamicaiagent.modelcomponent.models.model_component_configurations import (
    ModelComponentConfigurations,
)
from gafs.dynamicaiagent.utils.databaseprovider import DatabaseType
from gafs.dynamicaiagent.utils.databaseprovider.surrealdb_remote_provider import RemoteSurrealDbOptions


COLLECTION = "model_catalogues"
CONFIG_NAME = "secret_test_db_config.json"
VECTOR_4D = [0.1, 0.2, 0.3, 0.4]
PERSIST_ID = "vector_persist_4d"


def _logger() -> logging.Logger:
    logger = logging.getLogger("run_vector_persist_and_search")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s - %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


def _config_path() -> Path:
    return Path(__file__).resolve().parent / CONFIG_NAME


def _load_config() -> dict[str, Any] | None:
    path = _config_path()
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _build_options(config: dict[str, Any]) -> RemoteSurrealDbOptions:
    options = RemoteSurrealDbOptions()
    options.endpoint = config["endpoint"]
    options.namespace = config["namespace"]
    options.database = config["database"]
    options.username = config["username"]
    options.password = config["password"]
    options.database_type = DatabaseType.SURREALDB_REMOTE
    options.database_name = IDatabaseManager.DEFAULT_DATABASE_NAME()
    return options


async def _create_manager_and_service(
    logger: logging.Logger,
) -> tuple[DatabaseManager, ModelCatalogueService]:
    config = _load_config()
    if not config:
        raise FileNotFoundError(
            f"Config not found: {_config_path()}. "
            "Add secret_test_db_config.json to run this script."
        )
    options = _build_options(config)
    manager = DatabaseManager(logger)
    await manager.add_provider(options)
    if manager.get_default_database_provider() is None:
        raise RuntimeError("Default database provider is None.")
    service = ModelCatalogueService(logger)
    await service.initialize(manager, ModelComponentConfigurations())
    return manager, service


def _print_result(i: int, r: ModelCatalogue) -> None:
    distance = getattr(r, "distance", None)
    line = (
        f"  [{i}] id={r.id!r} name={r.name!r} "
        f"description_vector={r.description_vector!r}"
    )
    if distance is not None:
        line += f" distance={distance}"
    print(line)


async def main() -> None:
    logger = _logger()
    manager, service = await _create_manager_and_service(logger)
    try:
        # 1. Create entity with vector [0.1, 0.2, 0.3, 0.4] and persist (do not delete)
        catalogue = ModelCatalogue()
        catalogue.id = PERSIST_ID
        catalogue.name = "persist-vector-4d"
        catalogue.type = AiOperationType.EMBEDDING
        catalogue.status = ModelStatus.ACTIVE
        catalogue.description_vector = VECTOR_4D
        # Create or update if id already exists (idempotent for re-runs)
        existing = await service.get_catalogue(PERSIST_ID)
        if existing:
            existing.name = catalogue.name
            existing.description_vector = catalogue.description_vector
            created = await service.update_catalogue(existing)
            print("1. Updated existing entity (already persisted):")
        else:
            created = await service.create_catalogue(catalogue)
            print("1. Created and persisted entity:")
        print(f"   id={created.id!r} name={created.name!r} description_vector={created.description_vector!r}")
        print()

        # 2. Search with the same vector and output results
        criteria = ModelCatalogueSearchCriteria(
            vector=VectorSearchCriteria(
                vector=VECTOR_4D,
                vector_limit=10,
            ),
            deployment_types=[],
        )
        results = await service.search_catalogues(criteria)
        print("2. Search results (same vector [0.1, 0.2, 0.3, 0.4]):")
        print(f"   count={len(results)}")
        for i, r in enumerate(results):
            _print_result(i, r)
    finally:
        await manager.remove_provider(IDatabaseManager.DEFAULT_DATABASE_NAME())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] [%(levelname)s] %(name)s - %(message)s",
    )
    if not _config_path().is_file():
        print(f"Config not found: {_config_path()}. Exiting.")
        sys.exit(1)
    asyncio.run(main())
