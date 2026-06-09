## `ToolComponentConfigurations`

### constants

| name                                  | type               | value                        |
| ------------------------------------- | ------------------ | ---------------------------- |
| `COLLECTION_NAME()`                   | `str`              | `"component_configurations"` |
| `DEFAULT_DOCUMENT_ID()`               | `str`              | `"tool_component"`           |
| `DEFAULT_VECTOR_DATA_TYPE()`          | `VectorDataType`   | `F32`                        |
| `DEFAULT_DIMENSIONS()`                | `int`              | `3072`                       |
| `DEFAULT_VECTOR_SEARCH_METHOD()`      | `HnswSearchMethod` | `COSINE`                     |
| `DEFAULT_VECTOR_EXPLORATION_FACTOR()` | `int`              | `150`                        |
| `DEFAULT_VECTOR_MAX_CONNECTIONS()`    | `int`              | `12`                         |
| `DEFAULT_NAME_ANALYZER()`             | `str`              | `"default_analyzer"`         |
| `DEFAULT_DESCRIPTION_ANALYZER()`      | `str`              | `"default_english_analyzer"` |


### attributes

| name                                      | type               | required | default                               | description                                                                                                                                                                                                                    |
| ----------------------------------------- | ------------------ | -------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `embedding_catalogue_id`                  | `str \| None`      | no       | `None`                                | ID of the embedding model catalogue entry used to generate `description_vector`. Required for vector search.                                                                                                                   |
| `embedding_deployment_id`                 | `str \| None`      | no       | `None`                                | Preferred deployment ID for embedding. If set, this deployment is used for vector generation.                                                                                                                                  |
| `vector_data_type`                        | `VectorDataType`   | no       | `DEFAULT_VECTOR_DATA_TYPE()`          | Numeric type of vector elements stored in the HNSW index                                                                                                                                                                       |
| `vector_dimensions`                       | `int`              | no       | `DEFAULT_DIMENSIONS()`                | Number of dimensions in the embedding vector                                                                                                                                                                                   |
| `vector_search_method`                    | `HnswSearchMethod` | no       | `DEFAULT_VECTOR_SEARCH_METHOD()`      | Distance metric for HNSW similarity search                                                                                                                                                                                     |
| `vector_exploration_factor`               | `int`              | no       | `DEFAULT_VECTOR_EXPLORATION_FACTOR()` | HNSW `ef_construction` / `ef` parameter (exploration factor)                                                                                                                                                                   |
| `vector_max_connections`                  | `int`              | no       | `DEFAULT_VECTOR_MAX_CONNECTIONS()`    | HNSW `m` parameter (max connections per node)                                                                                                                                                                                  |
| `name_analyzer`                           | `str`              | no       | `DEFAULT_NAME_ANALYZER()`             | Full text analyzer for `name` field of `ToolCatalogueEntry` and `SandboxCatalogueEntry`.<br>Analyzers are defined and managed by `DatabaseManager` component and the analyzer name here must reference an existing analyzer.        |
| `description_analyzer`                    | `str`              | no       | `DEFAULT_DESCRIPTION_ANALYZER()`      | Full text analyzer for `description` field of `ToolCatalogueEntry`.<br>Analyzers are defined and managed by `DatabaseManager` component and the analyzer name here must reference an existing analyzer. |
| `docker_default_image_max_stand_by`       | `int`              | no       | `3`                                   | The maximum number of containers standing by per a single default sandbox definition                                                                                                                                           |
| `docker_total_default_image_max_stand_by` | `int`              | no       | `10`                                  | The maximum number of containers standing by. This limits the total number of all the default containers standing by.                                                                                                          |
| `app_data_folder`                         | `str`              | yes      | —                                     | Absolute path to the application data folder. Used as the base path for `{app_data_folder}/tools/codes/` and `{app_data_folder}/tools/files/`. |
