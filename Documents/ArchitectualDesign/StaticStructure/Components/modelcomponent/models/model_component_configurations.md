---
class: ModelComponentConfigurations
kind: data_class
roles: [stored_model]
module: gafs.dynamicaiagent.modelcomponent.models
collection: component_configurations
dependencies:
  - VectorDataType
  - HnswSearchMethod

---
## notes on dependencies

- `VectorDataType` and `HnswSearchMethod` are defined in `gafs.dynamicaiagent.common.models`.

## constants

| name                                  | type               | value                        | description                                         |
| ------------------------------------- | ------------------ | ---------------------------- | --------------------------------------------------- |
| `COLLECTION_NAME()`                   | `str`              | `"component_configurations"` | SurrealDB collection name                           |
| `DEFAULT_DOCUMENT_ID()`               | `str`              | `"model_component"`          | Record ID for the single configuration document     |
| `DEFAULT_VECTOR_DATA_TYPE()`          | `VectorDataType`   | `F32`                        | Default vector element type                         |
| `DEFAULT_DIMENSIONS()`                | `int`              | `3072`                       | Default vector dimensions                           |
| `DEFAULT_VECTOR_SEARCH_METHOD()`      | `HnswSearchMethod` | `COSINE`                     | Default HNSW distance metric                        |
| `DEFAULT_VECTOR_EXPLORATION_FACTOR()` | `int`              | `150`                        | Default HNSW `ef` parameter                         |
| `DEFAULT_VECTOR_MAX_CONNECTIONS()`    | `int`              | `12`                         | Default HNSW `m` parameter                          |
| `DEFAULT_NAME_ANALYZER()`             | `str`              | `"default_analyzer"`        | Full text analyzer name for the `name` field        |
| `DEFAULT_DESCRIPTION_ANALYZER()`      | `str`              | `"default_english_analyzer"` | Full text analyzer name for the `description` field |

## attributes

| name                        | type               | required | default                          | description                                                                                                                                                                                                             |
| --------------------------- | ------------------ | -------- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `embedding_catalogue_id`    | `str \| None`      | no       | `None`                           | ID of the embedding model catalogue entry used to generate `description_vector`. Required for vector search.                                                                                                            |
| `embedding_deployment_id`   | `str \| None`      | no       | `None`                           | Preferred deployment ID for embedding. If set, this deployment is used for vector generation.                                                                                                                           |
| `vector_data_type`          | `VectorDataType`   | no       | `F32`                            | Numeric type of vector elements stored in the HNSW index                                                                                                                                                                |
| `vector_dimensions`         | `int`              | no       | `3072`                           | Number of dimensions in the embedding vector                                                                                                                                                                            |
| `vector_search_method`      | `HnswSearchMethod` | no       | `COSINE`                         | Distance metric for HNSW similarity search                                                                                                                                                                              |
| `vector_exploration_factor` | `int`              | no       | `150`                            | HNSW `ef_construction` / `ef` parameter (exploration factor)                                                                                                                                                            |
| `vector_max_connections`    | `int`              | no       | `12`                             | HNSW `m` parameter (max connections per node)                                                                                                                                                                           |
| `name_analyzer`             | `str`              | no       | `DEFAULT_NAME_ANALYZER()`        | Full text analyzer for `name` field of `ModelCatalogueEntry` and `ModelDeployment`.<br>Analyzers are defined and managed by `DatabaseManager` component and the analyzer name here must reference an existing analyzer. |
| `description_analyzer`      | `str`              | no       | `DEFAULT_DESCRIPTION_ANALYZER()` | Full text analyzer for `description` field of `ModelCatalogueEntry` and `ModelDeployment`.<br>Analyzers are defined and managed by `DatabaseManager` component and the analyzer name here must reference an existing analyzer. |

## notes

- Stored as a single record with `id = "model_component"` in the `component_configurations` collection.
