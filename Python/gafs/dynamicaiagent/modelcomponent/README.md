# gafs.dynamicaiagent.modelcomponent

Model catalogue and AI model functionality. Provides the model catalogue (metadata store for AI models), catalogue service (CRUD and search), search criteria, and payload types for completion/embedding. `model_provider_service` and `model_component` are to be implemented.

## Structure of the Component

### Folder

```
modelcomponent/
├── __init__.py
├── i_model_catalogue_service.py
├── model_catalogue.py
├── model_catalogue_service.py
├── model_options.py
├── payload.py
├── requirements.txt
├── README.md
├── test/
│   ├── __init__.py
│   ├── test_model_catalogue_search_criteria.py
│   └── test_model_catalogue_service.py
├── i_model_component.py          (to be implemented)
├── i_model_provider_service.py  (to be implemented)
├── model_component.py           (to be implemented)
└── model_provider_service.py    (to be implemented)
```

### File and Public Classes

| File | Public Classes / Types |
|------|------------------------|
| `model_catalogue.py` | `ModelType`, `ModelStatus`, `ModelDeploymentType`, `RemoteProviderType`, `ModelDeployment`, `LocalModelDeployment`, `RemoteModelDeployment`, `CloudModelDeployment`, `ModelCatalogue` (cloud_provider_type uses `CloudAiProviderType` from cloudaicomponent) |
| `model_catalogue_service.py` | `ModelCatalogueService`, `LogicalOperator`, `HnswSearchMethod`, `VectorSearchCriteria`, `TagsSearchCriteria`, `ModelCatalogueSearchCriteria` |
| `i_model_catalogue_service.py` | `IModelCatalogueService` |
| `model_options.py` | `ModelOptions` |
| `payload.py` | `Payload`, `TextCompletionPayload`, `ChatCompletionPayload`, `EmbeddingPayload`, `Message`, `Part`, `ContentType` |

## Public API (intended to be called / accessed from outside)

### IModelCatalogueService

- `DEFAULT_COLLECTION_NAME() -> str` (static): Default collection/table name.
- `create_catalogue(catalogue: ModelCatalogue) -> ModelCatalogue` (async)
- `update_catalogue(catalogue: ModelCatalogue) -> ModelCatalogue` (async)
- `get_catalogue(id: str) -> ModelCatalogue | None` (async)
- `search_catalogues(catalogue_search_criteria: object) -> list[ModelCatalogue]` (async)
- `delete_catalogue(id: str) -> bool` (async)

### ModelCatalogueService

- `__init__(logger: Logger) -> None`
- `initialize(database_manager: IDatabaseManager, collection_name: str = ..., *, vector_index_dimension: int | None = 1536) -> bool` (async): Ensures indexes exist. The HNSW dimension is set at index creation time via `vector_index_dimension`; query vectors must use the same dimension. Before creating the vector index, the service checks the existing index dimension (INFO FOR TABLE); if it differs from `vector_index_dimension`, the index is removed and recreated. Other indexes use DEFINE INDEX IF NOT EXISTS.
- `create_catalogue(catalogue: ModelCatalogue) -> ModelCatalogue` (async)
- `update_catalogue(catalogue: ModelCatalogue) -> ModelCatalogue` (async)
- `get_catalogue(id: str) -> ModelCatalogue | None` (async)
- `search_catalogues(catalogue_search_criteria: ModelCatalogueSearchCriteria) -> list[ModelCatalogue]` (async)
- `delete_catalogue(id: str) -> bool` (async)

### ModelCatalogue (data class)

- Attributes: `id`, `name`, `type`, `status`, `description`, `description_vector`, `priority`, `tags`, `deployments`
- `to_json() -> str`

### ModelCatalogueSearchCriteria (data class)

- Attributes: `name`, `type`, `status`, `vector`, `keywords`, `min_priority`, `tags`, `deployment_types`, `min_confidence_level`, `limit`
- `to_query(database_provider: IDatabaseProvider, collection_name: str) -> str`: Build SurrealQL query string.

### VectorSearchCriteria (data class)

- Attributes: `vector`, `vector_limit`, `options` (distance uses the HNSW index default; not selectable here. `effort` is the only supported option now.)

### TagsSearchCriteria

- Attributes: `tags`, `operator`
- `__init__(tags: list[str], operator: LogicalOperator = ...) -> None`

### Enums (model_catalogue.py)

- `ModelType`: EMBEDDING, COMPLETION, CHAT
- `ModelStatus`: RECOMMENDED, ACTIVE, MAINTENANCE, DEPRECATED, RETIRED
- `ModelDeploymentType`: LOCAL, REMOTE, CLOUD
- `RemoteProviderType`; cloud deployment uses `CloudAiProviderType` (cloudaicomponent) for cloud_provider_type

### Enums (model_catalogue_service.py)

- `LogicalOperator`: AND, OR
- `HnswSearchMethod`: EUCLIDEAN, COSINE, MANHATTAN, MINKOWSKI, CHEBYSHEV, HAMMING (COSINE is the default for vector search criteria and index configuration)

## Dependencies & Libraries

No external serialization libraries are used.

Internal dependencies (same project):

- `gafs.dynamicaiagent.common.databasemanager` (IDatabaseManager)
- `gafs.dynamicaiagent.utils.databaseprovider` (IDatabaseProvider, SurrealDbRemoteProvider)

## Integration tests (real DB)

Integration tests under `test/` run against a real SurrealDB instance using connection settings from **`test/secret_test_db_config.json`** (gitignored; not committed).

Required JSON keys: `endpoint`, `namespace`, `database`, `username`, `password`.

- If the config file is missing, integration tests are skipped (when run via pytest).
- Run from the project Python root, for example: `python -m pytest gafs/dynamicaiagent/modelcomponent/test -v`

## Index creation in `initialize()`

`ModelCatalogueService.initialize()` creates an FTS analyzer and the following indexes using SurrealQL `DEFINE ANALYZER IF NOT EXISTS` and `DEFINE INDEX IF NOT EXISTS`:

- The analyzer/index is created **only when it does not exist**.
- If it **already exists**, the statement succeeds and is treated as success (no error).

**Full-Text Search (FTS)**

- **Target SurrealDB version**: 1.x / 2.x. Index clause uses **SEARCH ANALYZER**. SurrealDB 3.0+ uses **FULLTEXT ANALYZER**; when migrating to 3.x, update the index DDL accordingly. See [SurrealDB Full-Text Search](https://surrealdb.com/docs/surrealdb/models/full-text-search).
- **Language**: Catalogue `name` and `description` are assumed to be primarily in **English**. The FTS analyzer is optimized for English (snowball stemming: e.g. "running" → "run", "manager" → "manag").

**Analyzer**

| Name | Definition |
|------|------------|
| `model_catalogue_fts` | TOKENIZERS class FILTERS lowercase, ascii, snowball(english) |

**Indexes**

| Field | Index type | Index name |
|-------|------------|-------------|
| `description_vector` | HNSW (when `vector_index_dimension` is set) | `idx_model_catalogues_description_vector` |
| `name` | Fulltext (SEARCH ANALYZER model_catalogue_fts) | `idx_model_catalogues_name` |
| `type` | Standard | `idx_model_catalogues_type` |
| `status` | Standard | `idx_model_catalogues_status` |
| `description` | Fulltext (SEARCH ANALYZER model_catalogue_fts) | `idx_model_catalogues_description` |
| `tags` | Standard | `idx_model_catalogues_tags` |

Other fields (e.g. `priority`, `deployments`) are not indexed by the service; add them via SurrealDB DDL or by extending `_ensure_indexes` if needed.
